# json-flattering

An MQTT connector that receives JSON messages, flattens supported measurement
structures, applies the project's ETL transformations, and forwards the result to
an MQTT broker or a ThingsBoard Gateway connection.

In DIPME, it can forward data from the edge MQTT broker to a remote cloud broker.
The payload passes through `flatter_json()` and `etl()` before forwarding; this
service is therefore not a byte-for-byte MQTT replication tool.

## JSON transformation example

For supported messages, entries in the `m` array become top-level properties,
using `k` as the property name and `v` as its value. For example:

```json
{
  "t": 1700860560324,
  "tz": "2023-11-24T21:16:00.324Z",
  "uuid": "d55c2beb-c2c1-4a88-99a9-eae5083eb24a",
  "cuid": "9cf967dd-f15e-4801-ba5b-f05f05c2f043",
  "ref": "jzp://edv#0501.0000",
  "type": "luxmeter",
  "cat": "0620",
  "sn": 193,
  "m": [
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "device_temperature",
      "v": 26.5689,
      "u": "℃"
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "battery_level",
      "v": 3.3119,
      "u": "V"
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "orientation",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "back_front",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "regular",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "movement_level",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "posture_tilt",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "rssi",
      "d": "jzp://coo#ffffffff00000500.0000",
      "v": -54.8503,
      "u": "dB"
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "position",
      "v": 0,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "adc_channel_00",
      "v": 464.1732,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "illuminance",
      "v": 17.6629,
      "u": "lx"
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "coordinator",
      "d": "jzp://coo#ffffffff00000500.0000",
      "v": 1,
      "u": ""
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "pressure",
      "v": 24830.0977,
      "u": "Pa"
    },
    {
      "t": 1700860560324,
      "tz": "2023-11-24T21:16:00.324Z",
      "k": "adc_channel_01",
      "v": 0,
      "u": ""
    }
  ]
}
```

The corresponding flattened structure is:

```json
{
  "t": 1700860560324,
  "tz": "2023-11-24T21:16:00.324Z",
  "uuid": "d55c2beb-c2c1-4a88-99a9-eae5083eb24a",
  "cuid": "9cf967dd-f15e-4801-ba5b-f05f05c2f043",
  "ref": "jzp://edv#0501.0000",
  "type": "luxmeter",
  "cat": "0620",
  "sn": 193,
  "device_temperature": 26.5689,
  "battery_level": 3.3119,
  "orientation": 0,
  "back_front": 0,
  "regular": 0,
  "movement_level": 0,
  "posture_tilt": 0,
  "rssi": -54.8503,
  "position": 0,
  "adc_channel_00": 464.1732,
  "illuminance": 17.6629,
  "coordinator": 1,
  "pressure": 24830.0977,
  "adc_channel_01": 0
}
```

Additional transformations depend on the project's ETL implementation.

## Configuration

Copy the example configuration from the repository root:

```bash
cp .env.example .env
```

Edit `.env` before starting the application. Use the source and destination broker
IP addresses or DNS names directly; no `extra_hosts` aliases are required.
For example:

```dotenv
MQTT_IN_BROKER=192.168.1.25
MQTT_IN_PORT=1883
MQTT_IN_TRANSPORT=tcp
MQTT_IN_USERNAME=
MQTT_IN_PASSWORD=
MQTT_IN_TOPIC=/in/#

MQTT_OUT_BROKER=mqtt-backup.example.org
MQTT_OUT_PORT=1883
MQTT_OUT_TRANSPORT=tcp
MQTT_OUT_USERNAME=
MQTT_OUT_PASSWORD=
MQTT_OUT_TOPIC_PREFIX=/out

THINGSBOARD_GW=false
THINGSBOARD_GW_TOKEN=
LOG_LEVEL=INFO
```

Replace the example addresses with reachable brokers. The following table
summarizes the variables; some optional entries are commented out or absent in
`.env.example` and can be added when needed.

| Variable | Example or default | Purpose |
| --- | --- | --- |
| `MQTT_IN_BROKER` | `localhost` in the template | Source broker hostname or IP address. |
| `MQTT_IN_PORT` | `1883` | Source broker port. |
| `MQTT_IN_TRANSPORT` | `tcp` | Source transport: `tcp` or `websockets`. |
| `MQTT_IN_USERNAME` | Empty | Optional source username. |
| `MQTT_IN_PASSWORD` | Empty | Optional source password. |
| `MQTT_IN_TOPIC` | `/in/#` | Source subscription filter. Multiple filters can be separated by commas. |
| `MQTT_OUT_BROKER` | `localhost` in the template | Destination broker hostname or IP address. Set it explicitly for a remote broker. |
| `MQTT_OUT_PORT` | `1883` | Destination broker port. |
| `MQTT_OUT_TRANSPORT` | `tcp` | Destination transport: `tcp` or `websockets`. |
| `MQTT_OUT_USERNAME` | Empty | Optional destination username. |
| `MQTT_OUT_PASSWORD` | Empty | Optional destination password. |
| `MQTT_OUT_TOPIC_PREFIX` | `/out` in the template | Prefix added to the input topic in standard MQTT mode. |
| `THINGSBOARD_GW` | `false` | Use `true` to enable ThingsBoard Gateway output. |
| `THINGSBOARD_GW_TOKEN` | Empty | Gateway token required when ThingsBoard Gateway mode is enabled. |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

Use `MQTT_OUT_USERNAME` for the destination username. If your copy of
`.env.example` contains `MQTT_OUT_USER`, rename that entry: the application reads
`MQTT_OUT_USERNAME`.

The configuration uses environment variables instead of `config.json`. For local
Python execution, `python-dotenv` loads `.env` next to `main.py` before the logging
and MQTT configuration are initialized, with `override=False`: variables already
set in the process environment take precedence. In Docker, pass the variables
through Compose as shown below; mounting `.env` inside the container is not needed.

Keep the actual `.env` out of version control and the Docker build context using
`.gitignore` and `.dockerignore`. Commit `.env.example` with placeholders.

## Running with Docker Compose

Install Docker Engine or Docker Desktop with the Docker Compose plugin.
Create `compose.yaml` next to `.env` and copy this configuration:

```yaml
services:
  json-flattering:
    image: massimocallisto/json-flattering:1.1.0-dipme
    restart: unless-stopped
    environment:
      MQTT_IN_BROKER: "${MQTT_IN_BROKER:?Set MQTT_IN_BROKER in .env}"
      MQTT_IN_PORT: "${MQTT_IN_PORT:-1883}"
      MQTT_IN_TRANSPORT: "${MQTT_IN_TRANSPORT:-tcp}"
      MQTT_IN_USERNAME: "${MQTT_IN_USERNAME:-}"
      MQTT_IN_PASSWORD: "${MQTT_IN_PASSWORD:-}"
      MQTT_IN_TOPIC: "${MQTT_IN_TOPIC:-/in/#}"
      MQTT_OUT_BROKER: "${MQTT_OUT_BROKER:?Set MQTT_OUT_BROKER in .env}"
      MQTT_OUT_PORT: "${MQTT_OUT_PORT:-1883}"
      MQTT_OUT_TRANSPORT: "${MQTT_OUT_TRANSPORT:-tcp}"
      MQTT_OUT_USERNAME: "${MQTT_OUT_USERNAME:-}"
      MQTT_OUT_PASSWORD: "${MQTT_OUT_PASSWORD:-}"
      MQTT_OUT_TOPIC_PREFIX: "${MQTT_OUT_TOPIC_PREFIX:-/out}"
      THINGSBOARD_GW: "${THINGSBOARD_GW:-false}"
      THINGSBOARD_GW_TOKEN: "${THINGSBOARD_GW_TOKEN:-}"
      LOG_LEVEL: "${LOG_LEVEL:-INFO}"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

Compose substitutes `${VARIABLE}` from the selected environment file and passes
the resulting values to the container. `${VARIABLE:-default}` supplies a fallback;
`${VARIABLE:?message}` requires a non-empty value. No configuration-file mount or
host aliases are required.

**Broker addresses:** inside a container, `localhost` refers to that container.
Replace the template's `localhost` values with addresses reachable from the
container. A broker service name can be used when both services share a Docker
network. No broker port needs to be published by this connector: it initiates
outgoing connections to the source and destination brokers.

Validate the Compose configuration without printing the resolved values:

```bash
docker compose --env-file .env config --quiet
```

Start the service and inspect its status and logs:

```bash
docker compose --env-file .env up -d
docker compose --env-file .env ps
docker compose --env-file .env logs -f json-flattering
```

After changing `.env`, run `docker compose --env-file .env up -d` again so Compose
can recreate the container with the updated environment. A plain container restart
does not reload changed environment variables.

Stop and remove the Compose service:

```bash
docker compose --env-file .env down
```

To use a different installation configuration, pass its path consistently:

```bash
docker compose --env-file conf/unicam-ap.env up -d
```

If running several installations concurrently, use separate Compose project names
with `-p`, together with the corresponding environment files.

## Building the Docker image

Run the provided `build.sh` from the repository root, where the `Dockerfile` and
application sources are located. Docker must be running and accessible to your user.

```bash
chmod +x build.sh
./build.sh
```

The script currently defines:

```bash
VERSION="1.1.0-dipme"
IMAGE_NAME="massimocallisto/json-flattering"
```

It builds the local image using:

```bash
docker build --no-cache -t massimocallisto/json-flattering:1.1.0-dipme .
```

The build does not reuse cached image layers. If it fails, the script exits before
asking about publication. After a successful build it prompts:

```text
Push on Docker Hub? (y/n):
```

- Enter `y` or `yes`, case-insensitively, to run `docker push` for the same image tag.
- Enter `n` or any other answer to keep the image local and skip publication.

Before publishing, authenticate with an account allowed to push to the selected
Docker Hub repository:

```bash
docker login
```

To change the version or repository, edit `VERSION` and/or `IMAGE_NAME` at the top
of `build.sh`. The script does not accept these values as command-line arguments.
Update the `image` reference in `compose.yaml` to match the tag you built.

After rebuilding locally, recreate the running container to use the new image:

```bash
docker compose --env-file .env up -d --force-recreate
```

When deploying a published image on another gateway, retrieve it before starting:

```bash
docker compose --env-file .env pull
docker compose --env-file .env up -d
```

Skip `pull` when you intend to run an unpublished image built locally. The script
uses a standard `docker build`; it does not create a multi-platform image.

## Running with Python

Install [Poetry](https://python-poetry.org/docs/) and the Python version required
by the repository's `pyproject.toml`. From the repository root:

```bash
poetry install
cp .env.example .env
```

Edit `.env` and start the application:

```bash
poetry run python main.py
```

Do not overwrite an existing `.env` when repeating the setup. The project's
dependencies must include `python-dotenv` for local `.env` loading. If it has not
yet been added to `pyproject.toml`, add it once and update the lock file:

```bash
poetry add python-dotenv
```

## Logging

Set the desired level in `.env`:

```dotenv
LOG_LEVEL=INFO
```

Use `INFO` for the startup configuration, connections, subscriptions and relevant
service events. Use `DEBUG` for detailed message processing. `WARNING`, `ERROR`
and `CRITICAL` progressively reduce the log output.

The startup summary should identify source and destination broker addresses,
ports, transports, subscription filters and output mode. In standard MQTT mode,
it should also show the output topic prefix. Passwords and tokens must not be
included in the log, even at `DEBUG` level.

## Output modes and operational notes

### Standard MQTT output

With `THINGSBOARD_GW=false`, transformed messages are published to the destination
broker using `MQTT_OUT_TOPIC_PREFIX`. For example, with input topic
`/in/device-01` and prefix `/out`, the destination topic is `/out/in/device-01`.

When source and destination are the same broker, choose a subscription filter
that excludes the output topics. For example, `/in/#` excludes `/out/in/...`.
Do not use `#` for same-broker forwarding: it also includes the connector's output
and can create a loop. Using `#` with two distinct brokers is a different setup.

### ThingsBoard Gateway output

Set `THINGSBOARD_GW=true` and provide `THINGSBOARD_GW_TOKEN`, together with the
destination broker address and port. In this mode, output uses the ThingsBoard
Gateway client; `MQTT_OUT_TOPIC_PREFIX` is not used for telemetry forwarding.

The device identification and telemetry mapping follow the implementation in
`send_to_thingsboard()`. Check that mapping when introducing a new input schema.

### Remote backup

The connector applies transformations before forwarding. Do not assume that it
preserves the original payload, MQTT delivery metadata or topic unchanged.
This configuration does not establish durable Store-and-Forward guarantees:
verify disconnection, reconnection and message recovery behavior separately if
the remote broker is used as a backup destination.

## References

- [Docker Compose environment variables](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Passing environment variables to containers](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
- [python-dotenv](https://bbc2.github.io/python-dotenv/)
