# Patching & Attacking

Here follows a brief overview of how to patch your service, and how to use the reference attacker provided in this spec to attack other teams.

Before you get started, please ensure that you:
- Are connected to the player VPN (and can reach https://app.infra.wicc.ie)
- Have installed Docker on your machine (https://docs.docker.com/get-docker/)
- Have authenticated with the WICC platform Docker registry. Information on how to do this is in your player handout. You should have ran a command like this:

```
cat registry-credentials.json | docker login -u _json_key --password-stdin https://europe-west2-docker.pkg.dev
```

If you are not familiar with Docker, we strongly recommend also reading the Docker documentation on building and running containers: https://docs.docker.com/get-started/.

## Patching

To patch a service, you will need to build a new Docker image for your service. First, you need to check which container is actually allowed to be patched by the platform. Open up the `manifest.yaml` in the handout; it should look something like this (though obviously with different names and service-specific changes):

```yaml
deployments:
  - name: web
    patchable: true
    tcpdump: true
    exposedPorts:
      - name: http
        port: 8089
    volumes:
      - name: data
        sizeGb: 1
    podSpec:
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 15
      containers:
        # only this container is patchable btw
        - name: app
          image: overseers/example-service-app:latest
          ports:
            - name: http
              containerPort: 8089
          resources:
            requests:
              cpu: "300m"
              memory: "128Mi"
            limits:
              cpu: "1"
              memory: "512Mi"
        - name: mysql
          image: overseers/example-service-db:latest
          args: ["--datadir=/var/lib/mysql/data"]
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
          resources:
            requests:
              cpu: "300m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
```

Note that this specific challenge involves two containers: `app` and `mysql`. As per the comment, you're only allowed to patch the `app` container. If there's only a single container listed, then that container is the one you can patch.

Next, go to the `docker-compose.yml` file in the handout. Find the definition for the container you are allowed to patch. It should look something like this:

```yaml
  app:
    build: ./app
    ports:
      - "8089:8089"
    depends_on:
      db:
        condition: service_healthy
```

Note the `build` directive. This is the path to the directory containing the Dockerfile for your service. You will need to make your changes in this directory, and then build a new image.

Head into the `app` directory and patch what you need. Depending on the challenge, this might involve changing source, patching a binary, adding new files, or anything else. If you're just changing source files, you don't need to touch the `Dockerfile`. Otherwise, you might need to change how the image is being built. Refer to the Docker documentation for more information on how to build images.

Once you're ready to submit your patch, you need to tag and push it to the platform. Head over to the platform and grab the Docker push command for the challenge. It should look something like this:

```
docker push europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo:$TAG
```

Note the URL and the `$TAG` variable. You will need to replace `$TAG` with the tag you want to use for your image. This can be anything, but it is shown on the platform so it's probably a good idea to use something descriptive. For example, if you're fixing a login bypass, you might want to use `login-bypass-fixed`.

First, build the image with the tag you want to use (run this in the directory containing the Dockerfile):

```
docker build -t europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo:login-bypass-fixed .
```

If that succeeds, you can push the image to the platform:

```
docker push europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo:login-bypass-fixed
```

If the image is accepted, it should be available for activation on the platform once you're within range of the challenge. **You will need to activate your patch on the platform for it to take effect.** Note that while your new image is being deployed, you may suffer downtime for your service.

Good luck defending!

## Attacking

> Note: this section assumes that you're using our [reference attacker](./reference-attacker/). If you're using your own attacker, you probably know how to push it to the platform already.

To use the built-in attacker, you need to follow three steps:

- Grab a fresh copy of the attacker
- Adjust the beginning of the `attack` function to target the team you want to attack
- Build and push the attacker to the platform

As long as you have the logic for attacking a team implemented properly, the attacker will make sure that it runs on time, attacks teams, and submits the obtained flags.

Let's assume there's a challenge where going to `/notes?show_secret=1` lets you read secret notes, and secret notes contain the flag. Make a fresh copy of the reference attacker, then open `solve.py` and find the `attack` function. It should look something like this:

```python
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
    # [...]
```

To implement your exploit, replace the lines between the `print` and the `to_submit` initialization with your exploit logic, then adjust the regex to iterate over your output. For example, if you want to read the secret notes, you might do something like this:

```python
async def attack(
    sub: Submitter, team_id: int, min_round_id: int, team_status: TeamStatus
) -> None:
    print(f"attack {team_id=} {min_round_id=} {team_status=}")
    
    # == beginning of exploit ==
    import requests
    flags = requests.get(f"http://{team_status['ip']}:8089/notes?show_secret=1").text
    # == end of exploit ==

    to_submit: list[str] = []
    seen: set[str] = set()
    # replaced `d.decode(...)` with `flags`
    for flag_match in re.finditer(FLAG_RE, flags):
```

When a team needs exploiting, your code will now request the `/notes?show_secret=1` endpoint for that team, iterate over all flags in the response, and submit them to the platform if they're valid and haven't been submitted yet.

To submit your attacker, you need to build and push it to the platform. The process is the same as for patching a service: build the image with a tag, then push it to the platform. The platform will then run your attacker on time and submit any flags it finds. Head over to the attack tab in the platform and grab the Docker push command for the attacker. It should look something like this:

```
docker push europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo/exploit:$TAG
```

Choose an appropriate tag describing your exploit (for example `notes-list-secret`), then build and push the image:

```
docker build -t europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo/exploit:notes-list-secret .
docker push europe-west2-docker.pkg.dev/overseers/t0-test/d0-demo/exploit:notes-list-secret
```

**Finally, activate the attacker on the platform once you're within range of the challenge.** The platform will then run your attacker on time and submit any flags it finds.

Note that the reference attacker also supports flag IDs if needed. To access those, you can use `team_status["vulns"]`. The format of the data contained in this will vary per challenge.

Good luck exploiting!