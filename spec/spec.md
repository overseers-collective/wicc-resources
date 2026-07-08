_Please Note: This document describes only the aspects of the competition organized/monitored by the Overseers infrastructure. For additional rules and guidelines regarding the competition as a whole, please refer to the official competition rules._

# Time

- [Tick]: The platform works in units of ticks, which are the smallest discrete time steps used by the platform. All other time measurements are derived from ticks. There are @TICKS_PER_SECOND ticks in one second.
- [Round]: A round is the smallest time unit for [Attack-Defense] and [KotH] challenges. Each round consists of @TICKS_PER_ROUND ticks. The first round starts at tick 0.
- The game will run for @GAME_TOTAL_TICKS ticks.

# Scoring

- [Score]: The total score of a team is the sum of all points earned by the team for [Attack-Defense], [KotH], [Bonus], and [Encounter] challenges, as well as any [In-Bounds Bonus] points earned by the team.
- Teams are ranked by their [Score]. The components that make up their score are publicly visible on the platform leaderboard, as specified in more detail for each challenge type in the relevant sections below.
- After @FREEZE_SCOREBOARD_AFTER_TICKS [Tick]s, the scoreboard will be frozen and no longer updated. Teams will remain able to gain points after this time, but the scoreboard will not reflect these changes until the end of the game. The [SLA] status of [Attack-Defense] challenges will continue to be updated and shown to teams even if the scoreboard is frozen.

# Map, Movement, Vision

## Controls

- [Controller]: At most one connection to the platform for each team can be the controller. The controller is the only connection that can send commands on behalf of the team, such as movement and challenge activation. The team may change their controller at any time, and this change is reflected immediately. The controller system exists to ensure that teams have a clear indication of which connection is currently controlling the team, and to prevent multiple connections from sending conflicting commands on behalf of the team.

## Map

- [Unit]: The unit of measurement for the map is the "unit". Units are tied to [Tick]s, specifically they are chosen such that one tick of movement corresponds to one unit of (possibly diagonal) distance.
- The map is a slice of a circle, with side-length @EDGE_LENGTH and angle @CENTER_ANGLE.
- The side-edges of the map wrap around, such that moving off the bottom edge of the map will place you at the top edge.

## Movement

- Teams may choose a direction to navigate to, including no direction at all. The direction may be changed at any time by the [Controller], and will apply from the next [Tick] onwards. Each [Tick], the team will automatically move 1 [Unit] in the chosen direction. Movement is clamped if this would take the team outside of the map. If no direction is active, the team will not move.
- There is no collision. Teams may occupy the same location as another team or challenge, and may move through them without restriction.

## Spawning

- At the beginning of the first day, each team will spawn evenly distributed at a random location at the far edge of the map. Teams will not know the spawn location of other teams.
- At the beginning of the second day, teams will spawn according to the following permutation rule relative to their position from the first day: `1 2 3 4 5 6 7 8` -> `3 5 1 7 2 8 4 6`. That is, the team that spawned at position 1 on the first day will spawn at position 3 on the second day, and so on. This ensures that teams closer to the starting challenge on day 1 will be further away from the starting challenge on day 2, and vice versa. Teams will not know the spawn location of other teams.

## Vision

- Teams will always see the location of their own character, [Attack-Defense] challenges, [KotH] challenges, and [Bonus] challenges.
- Teams will only see the location of other teams if the center-to-center distance between the two teams is @VISION_RANGE_UNITS or less.

## Bounds

- [Storm]: A bounds system is in place to gradually shrink the size of the map over time. The bounds are represented by a storm that shrinks the playable area of the map.
- The storm will begin after @SHRINK_DELAY_TICKS [Tick]s have passed. After this time, it will linearly shrink the map by @SHRINK_SPEED_PER_TICK [Unit]s per [Tick] until the end of the game.
- [Attack-Defense] and [KotH] challenges whose center lies within the storm bounds will retire. Retired challenges will no longer participate in [Round]s.
- In order to motivate teams to stay within bounds, teams whose center lies within the storm bounds will not receive [In-Bounds Bonus] points until they move back into the playable area of the map.
- [In-Bounds Bonus]: In-Bounds Bonus points are rewarded to teams for staying within the playable area of the map. A team gains @IN_RANGE_REWARD_POINTS [In-Bounds Bonus] points for every @IN_RANGE_REWARD_EVERY_TICKS [Tick]s that they are within the playable area of the map. This counter resets if the team moves into the storm bounds, and begins counting as soon as the team moves back into the playable area of the map. 

# Attack-Defense

## Basics

- [Attack-Defense]: Attack-Defense challenges are challenges that involve actively defending a service from attacks by other teams, while at the same time attempting to attack the same service on other teams.
- A team is considered to be within range of an [Attack-Defense] challenge if the center-to-center distance between the team and the challenge is @VISION_RANGE_UNITS or less.
- The name of an [Attack-Defense] challenge is publicly available to all teams as soon as the game starts.
- [Attack-Defense] challenges must be activated by a team. The [Controller] of the team may do so at any time while within range of the challenge. Once activated, the challenge will remain active until the end of the game, or until the service retires due to the [Storm].
- As soon as the [Attack-Defense] challenge is activated, the team will have access to the description and attachments of the challenge. This information will remain accessible, even if the team is no longer within range of the challenge.

## Flags

- The flag format for [Attack-Defense] challenges matches the regular expression `WICC\{[A-Za-z0-9_-]{91}\}`. The contents of the flag are signed and contain the team ID, challenge ID, and [Round] number for the flag. A team can verify a flag without needing to submit it. An example of this is provided in the team handout.
- Flags are valid for at most @FLAG_ACCEPTED_ROUNDS [Round]s after they are generated. After this time, the flag will be considered expired and will not be accepted by the platform.
- If a team submits an invalid, expired, or duplicate flag, their ability to submit flags will be disabled for the next @FLAG_SUBMISSION_WRONG_COOLDOWN seconds. Teams should validate flags before submitting them to avoid unnecessary cooldowns.
- [Flag ID]: Some services may expose information needed to obtain a flag, such as the username under which a flag was placed by the [SLA] checker. This information is referred to as a [Flag ID]. The [Flag ID] information is visible to a team only while they are within range of the challenge, and is visible to the hosted attacker instance provided by the platform at all times.

## Hosting

- The platform hosts a dedicated instance of the challenge for each team. The IP address of the instance is shown on the platform once the challenge is activated.
- The teams will not have direct machine (SSH) access to their challenge instance.
- Teams have access to streamed logs of their challenge instance while within range of the challenge.

## Networking

- As soon as the [Attack-Defense] challenge is activated, the hosted instance of the challenge will be accessible to other teams.
- Traffic arriving to the hosted instance of the challenge will be routed through a single IP such that the attacked team cannot identify the source.
- As soon as the [Attack-Defense] challenge is activated, the team will have access to the instances of other teams that have activated the challenge.
- All team instances of the [Attack-Defense] challenge, including the team's own instance, are only accessible over the player VPN connection while the team is within range of the challenge. If the team moves out of range, further packets will be dropped by the networking layer until the team moves back into range. The exception to this rule is the hosted attacker instance provided by the platform, which can always access other teams but can never access the own team's instance.

## Traffic Captures

- Automatic PCAP traffic capture is enabled for the team instance, and accessible for download only while within range of the challenge. The PCAP files are rotated every @PCAP_ROTATION_SECS seconds, or when they exceed @PCAP_MAX_SIZE_MB megabytes in size.
- The source IP address of incoming traffic (as seen in the PCAPs) may change at any point in time, but is guaranteed to be within the @PCAP_SOURCE_IP_SUBNET subnet.
- The target IP address (i.e., the IP address of the team's instance as seen in the PCAPs) may change when a team activates a new image for the challenge, but is guaranteed to be within the @PCAP_TARGET_IP_SUBNET subnet. Note that this concernes only the IP address of the instance as seen in the PCAPs, and does not affect the IP address used to access the instance over the player VPN connection and from the hosted attacker instance.
- The name of the PCAP file provided by the platform is in the format `<challenge_slug>-yyyymmdd-hhmmss-<hash>.pcap`.
- The organization provides an example PCAP file that can be used to verify that ingestion of PCAP files is working correctly. This example PCAP file is available in the team handout.

## Defending

- Teams may patch their challenge by pushing a new Docker container image to the platform for the given registry path. Pushing images can be done at any time, even if not within range of the challenge. Pushed images are not automatically activated.
- Teams may activate any of their previously pushed images at any time while within range of the challenge. The activated image will be activated immediately, with the team incurring possible [SLA] penalties while the restart is ongoing.
- If a challenge consists of multiple containers, only one container will be patchable by the team. Which container is allowed to be patched is specified in the challenge handout. There are no verification checks on the pushed image.
- The compute resources available to the challenge are limited and vary per challenge. If your service becomes unresponsive due to resource exhaustion, you may need to optimize your service or reduce the number of containers in your image. The platform will not provide additional resources to your service.

## SLA Checks

- [SLA]: The platform will automatically check the availability and correctness of the team's challenge instance every [Round]. This functions to ensure that the challenge is still functioning correctly, and to provide a scoring mechanism for the challenge by inserting new flags into the challenge instance.
- If an [SLA] check is failing, the checker may provide information about which expected behavior is not being met. No additional information about the behavior checked by the [SLA] checker is provided to teams.
- The [SLA] checks are performed at random intervals and are designed to not be easily distinguishable from other traffic.
- The [SLA] status of a challenge may be viewed at any time by the team that owns the challenge, even if they are not within range of the challenge. The [SLA] status of other teams' challenges is never visible.

## Attacking

- Teams may attack other teams' [Attack-Defense] challenges through the player VPN connection while within range of the challenge.
- If a team wishes to attack other teams while outside of the range of the challenge, they can do so by containerizing their attack script into a Docker image and pushing it to the platform for the given registry path. Pushing images can be done at any time, even if not within range of the challenge. Pushed images are not automatically activated.
- Teams may activate their pushed attacker image at any time while within range of the challenge. The activated image will be activated immediately.
- The instance running the attacker image will be able to attack other teams' instances of the challenge, but will not be able to access the own team's instance.
- The activated image stays running until the end of the game, or until the team activates a different attacker image. It automatically restarts if it crashes. The attacker image is responsible for issuing new commands every [Round] on its own.
- Teams can expose a port on the attacker image to talk to their attacker instance. This port is only accessible to the own team, and only while the team is within range of the challenge.
- The attacker instance has a fixed resource limit of @ATTACKER_RESOURCE_LIMIT_CPU CPU cores and @ATTACKER_RESOURCE_LIMIT_MEM MB of memory. The platform will not provide additional resources to your attacker.
- The attacker instance has a @ATTACKER_MOUNT_SIZE GB persistent volume mounted at `/data`. This volume should be used to persist data across attacker restarts and updates.
- Teams have access to streamed logs of their Attacker while instance while within range of the challenge.
- An example implementation of an attacker is provided in the team handout. This example implementation details how to obtain [Flag ID]s, the list of active instances from other teams, and how to submit flags to the platform.

## Scoring

- [Attack Points]: Attack points are rewarded to teams for successfully submitting valid flags for other teams' [Attack-Defense] challenges.
- [Defense Points]: Defense points are rewarded to teams for successfully defending their own [Attack-Defense] challenge from attacks by other teams.
- A team gains @AD_ATTACK_POINTS [Attack Points] for each valid [Attack-Defense] flag submitted to the platform.
- A team gains @AD_DEFENSE_POINTS [Defense Points] for each other team that has the service activated and did not steal the flag for that [Round].
- A team gains no [Defense Points] for a [Round] if the [SLA] check for that [Round] failed, even if they successfully defended against attacks from other teams.
- The amount of [Attack Points] and [Defense Points] gained by a team for a given [Round] is shown on the platform after the [Round] has ended. This information is available to all teams, even if they did not have the service activated for that [Round].

# KotH

## Basics

- [KotH]: King of the Hill challenges are challenges that involve submitting a solution to a problem posed by the challenge, in a way that can be independently scored by the challenge. King of the Hill challenges will rank the solutions submitted by each team every [Round], awarding points based on the relative quality of the solution submitted by each team. Teams can submit new solutions at any time, and may need to do so in response to other teams' submissions in order to improve their own score.
- The name of a [KotH] challenge is publicly available to all teams as soon as the game starts.
- There is a single shared global challenge instance for each [KotH] challenge. 
- A team is considered to be within range of a [KotH] challenge if the center-to-center distance between the team and the challenge is @VISION_RANGE_UNITS or less. When a team first enters range of the challenge, the challenge will be marked as "seen" by that team.
- Once a [KotH] challenge is marked as "seen" by a team, the team will have access to the description and attachments of the challenge. This information will remain accessible, even if the team is no longer within range of the challenge.

## Submission

- Once a [KotH] challenge is marked as "seen" by a team, the team will have access to the instance of the challenge. This instance can be used to submit candidate solutions for the challenge. This instance is always accessible to the team, even if they are no longer within range of the challenge.
- If a team submits a candidate solution to the [KotH] challenge, they will receive a token that can be used to activate that submission. In order to activate the submission, the team must be within range of the challenge and enter the token on the platform. Once activated, the submission belonging to the token will be scored by the challenge for the next [Round]. The team may activate a different submission at any time while within range of the challenge, with only the most recently activated submission being scored for the next [Round].
- If a team has no activated submission, they do not participate in the scoring for that [Round]. A team may choose to deactivate their submission at any time while within range of the challenge, which will result in them not participating in the scoring for that [Round].

## Scoring

- [KotH Score]: The internal score awarded to a given submission by the [KotH] challenge is referred to as the [KotH Score]. The [KotH Score] is a non-negative integer, with higher scores being better. The [KotH Score] is determined by the challenge itself, and may be based on any criteria that the challenge author chooses.
- [KotH Rank]: The rank of a team for a given [Round] is determined by the [KotH Score] of the team's activated submission for that [Round]. Teams ranks are determined by ordering them from highest to lowest [KotH Score]. If two or more teams have the same [KotH Score], they will be considered tied and will receive the same rank, without compensating for the tie in the ranks of other teams. For example, if two teams tie for first place, they will both be considered to have rank 1, and the next team will be considered to have rank 2. Teams without an active submission for a given [Round] will be considered to have 0 [KotH Score] for that [Round], automatically placing them at the bottom of the ranking for that [Round].
- [KotH Point]: KotH points are rewarded to teams for submitting solutions to [KotH] challenges based on how they rank relative to other teams' submissions. This ranking is generally based on the [KotH Score] of each team's activated submission for that [Round].
- The number of [KotH Point]s awarded to a team for a given [Round] is determined by the [KotH Rank] achieved by the team, as well as the total number of teams that have activated submissions for that [Round]. The lowest [KotH Rank] will receive 0 [KotH Point]s, and each higher rank will receive 1 additional [KotH Point] relative to the rank below them. The maximum score achievable by a team is therefore bounded at the total number of teams that have activated submissions for that [Round] minus 1, achieved only if there are no ties between teams in that [Round].
- The amount of [KotH Point]s gained by a team for a given [Round] is shown on the platform after the [Round] has ended. This information is available to all teams, even if they did not have an activated submission for that [Round].

# Bonus Challenges

## Basic

- [Bonus]: A bonus challenge is a Jeopardy-style challenge solvable by at most one team.
- The name and category of a [Bonus] challenge is publicly available to all teams as soon as the challenge spawns.
- A team is considered to be within range of a [Bonus] challenge if the center-to-center distance between the team and the challenge is @VISION_RANGE_UNITS or less.
- Once a team is within range of a [Bonus] challenge, the team will have access to the description and attachments of the challenge. This information will remain accessible, even if the team is no longer within range of the challenge.
- [Bonus] challenges remain active until the end of the game or until they have been solved once. Unlike [Attack-Defense] and [KotH] challenges, [Bonus] challenges do not retire when the [Storm] bounds reach them.

## Spawning

- The first bonus challenge spawns after @BONUS_SPAWN_DELAY_TICKS [Tick]s. After this, a new bonus challenge will spawn every @BONUS_SPAWN_INTERVAL_TICKS [Tick]s.
- When a [Bonus] challenge spawns, it will be placed at the fairest eligible location on the map. A location is considered eligible if it will remain within bounds for at least the next @BONUS_SPAWN_SAFE_TICKS_TO_SHRINK [Tick]s and is not within @BONUS_SPAWN_SAFE_DISTANCE_TO_PLAYERS [Unit]s of any team. The fairest eligible location is the location that minimizes the total distance [Unit] sum to all teams, while being equidistant from the two nearest teams. If multiple such locations exist, a random one is chosen. If no eligible locations exist, another attempt at spawning the challenge will be made after @BONUS_SPAWN_RETRY_INTERVAL_TICKS [Tick]s. This process will repeat until a location is found or the game ends.

## Instances

- If a [Bonus] challenge has a server-side component to it, the platform will host a dedicated instance of the challenge for each team. The IP address of the instance is shown on the platform once the team is within range of the challenge. The team only has access to the instance while within range of the challenge.
- [Bonus] challenges with an instance are designed to not be brickable by the team. If a team suspects that they have irrepairly broken their instance of a [Bonus] challenge, they may request a reset of the instance. This needs to be done by contacting a member of the organizing team.

## Scoring

- A team may only submit a flag for the [Bonus] challenge while within range of the challenge.
- Once the first team has submitted a valid flag for the [Bonus] challenge, the challenge is considered solved and will no longer accept submissions from any team.
- [Bonus Points]: Bonus points are rewarded to the first team that submits a valid flag for a [Bonus] challenge.
- Whenever a team is the first to submit a valid flag for a [Bonus] challenge, they will receive @BONUS_POINTS [Bonus Points].
- The amount of [Bonus Points] gained by a team for a given [Bonus] challenge is shown on the platform after the challenge has been solved. This information is available to all teams, even if they did not participate in the challenge.

# Encounters

## Basics

- [Encounter]: An encounter challenge is an optional duel challenge between two teams that encountered each other on the map. An [Encounter] must be explicitly proposed by one of the teams and is only between the two teams that agreed to the [Encounter].
- [Encounter Eligible]: A team is considered eligible for an encounter if it is not currently within range of an [Attack-Defense], [KotH], or [Bonus] challenge, is not currently in an [Encounter], and is not currently subject to an [Encounter Cooldown].
- [Encounter Cooldown]: A team is considered to be on an [Encounter Cooldown] if it has recently completed or rejected an [Encounter]. The [Encounter Cooldown] lasts for @ENCOUNTER_COOLDOWN_TICKS [Tick]s after the [Encounter] has been completed or rejected. [Encounter Cooldown]s apply on a per-team-pair basis, meaning that if a team is on an [Encounter Cooldown] with one team, it may still propose or accept an [Encounter] with another team.
- [Encounter Category]: An [Encounter] challenge is associated with a specific [Encounter Category]. Each [Encounter Category] mirrors a conventional CTF jeopardy category, giving teams an indication as to the type of challenge they will face in the [Encounter].
- [Encounter Points]: Encounter points are rewarded to teams for successfully completing an [Encounter] challenge, or when an [Encounter] challenge is rejected by the challenged team.

## Challenging and Draft

- In order for an [Encounter] to be proposed, both teams need to be [Encounter Eligible], within @VISION_RANGE_UNITS [Unit]s of each other, and there must exist at least one [Encounter] challenge that has not been seen by either team.
- A team may propose an [Encounter] to another team by challenging them. The challenged team may accept or reject the challenge. If the challenged team does not respond within @ENCOUNTER_PENDING_ACCEPT_TIMEOUT_TICKS [Tick]s, the challenge will be automatically rejected. If a challenge is rejected (regardless of whether it was explicitly rejected or automatically rejected due to timeout), the challenging team will receive @ENCOUNTER_REJECT_POINTS [Encounter Points] and both teams will be placed on an [Encounter Cooldown].
- If a challenged team accepts, an initial set of eligible [Encounter Category]s will be selected. A category is eligible if it contains at least one challenge not seen by either team. Teams then alternate turns to ban an [Encounter Category] from the eligible set. Once only one [Encounter Category] remains, the [Encounter] will start with a random challenge from the remaining category.
- The team that got challenged in the [Encounter] will have the first turn to ban a category.
- If a team does not respond witin @ENCOUNTER_SELECT_CATEGORY_TIMEOUT_TICKS [Tick]s when it is their turn to ban a category, a random remaining category will be automatically banned on their behalf.
- From the moment a team proposes an [Encounter], up until the encounter is finished (due to rejection, timeout, or once the challenge has been completed), both teams will be unable to move from their current position.

## Instances

- If an [Encounter] challenge has a server-side component to it, the platform will host a dedicated instance of the challenge for each team. The IP address of the instance is shown on the platform.
- [Encounter] challenges with an instance are designed to not be brickable by the team. If a team suspects that they have irrepairly broken their instance of a [Encounter] challenge, they may request a reset of the instance. This needs to be done by contacting a member of the organizing team.

## Challenge Completion

- The first team to submit the valid flag for the [Encounter] challenge will be considered the winner of the [Encounter]. The winning team receives @ENCOUNTER_WIN_POINTS [Encounter Points], while the losing team receives no [Encounter Points]. Both teams will be placed on an [Encounter Cooldown].
- A team in an [Encounter] may choose to forfeit the current challenge at any time. This acts as if the opposing team has submitted the valid flag for the [Encounter] challenge, and exists solely to allow a team to end an [Encounter] early if they are unable or unwilling to complete the challenge.
- A team may propose to draw the [Encounter] challenge at any time. If the opposing team accepts, neither team will receive any [Encounter Points] and both teams will be placed on an [Encounter Cooldown]. A draw proposal has unlimited duration and cannot be taken back once proposed. If a draw proposal is rejected, either team may re-propose a draw at any time.
- The public scoreboard shows the amount of [Encounter]s that a team has rejected, been rejected, won, lost, and drawn. This information is available to all teams, even if they did not participate in the [Encounter]. No information is available about the specific teams that a team has encountered, or the outcome of those encounters.

# AI

_The guidelines below are only regarding the use of AI as integrated within the Overseers CTF platform. Please refer to the official competition rules for additional rules regarding the use of AI in the competition._

- The platform provides a simple chat interface that can be used to talk to an AI assistant. The AI assistant can be used to ask generic questions about programming and cybersecurity.
- The backing model used for the AI assistant is @AI_MODEL.
- The AI assistant endpoint is guarded by a CAPTCHA to prevent abuse. It is not allowed to automate access to the AI assistant endpoint, and any attempts to do so will be considered a violation of the competition rules.
- The AI assistant is not aware of the specific rules of the competition, and will not provide any information about the challenges or the game state.
- All messages sent to the AI assistant are logged and may be reviewed by the jury.
- Access to the AI assistant during an [Encounter] is disabled for both teams, as [Encounter] challenges are designed to be solved without external assistance.
