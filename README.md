# json-flattering
json-flattering

This is a simple JSON flattering module that move inner properties to top level. 
The module works on the following type of JSON:

```
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
The result is:

```
{
  "t": 1700860806416,
  "tz": "2023-11-24T21:20:06.416Z",
  "uuid": "9c3d7476-87a4-4bb9-9e73-a0bf2062107b",
  "cuid": "bd565d22-1eff-46a9-9bb4-4704a06f82d5",
  "ref": "jzp://edv#0501.0000",
  "type": "luxmeter",
  "cat": "0620",
  "sn": 38,
  "device_temperature": 34.8461,
  "battery_level": 3.5496,
  "orientation": 0,
  "back_front": 0,
  "regular": 0,
  "movement_level": 0,
  "posture_tilt": 0,
  "rssi": -43.1038,
  "position": 0,
  "adc_channel_00": 147.6494,
  "illuminance": 323.03,
  "coordinator": 1,
  "pressure": 99687.8489,
  "adc_channel_01": 0
}
```

## Running with Docker

You can use Docker to run the container image available on Docker hub.
Check the example in [docker-example](docker-example) folder with the available `run.sh` command.

```
#!/bin/sh

docker kill flat
docker rm flat

docker run -d \
    --name=flat \
    -v config.json:/app/config.json \
    massimocallisto/json-flattering:1.0.0

docker logs -f flat
```

You can move in the folder, update the [config.json](docker-example/config.json) file and then execute:

    cd docker-example
    ./run.sh

## Running with Python

You can use [Poetry](https://python-poetry.org/docs/) in order to execute the module.

After you cloned this repository, you can execute the installation of the dependencies:

    poetry shell
    poetry install

Then execute the main file:

    poetry run python main.py

## Configuration

The module reads the configuration from the [config.json](config.json) JSON file structured as follows:

```
{
  "MQTT_IN_BROKER": "localhost",    // MQTT source broker
  "MQTT_IN_PORT": "1883",           // tcp port
  "MQTT_IN_USERNAME": "",           // username, empty if none
  "MQTT_IN_PASSWORD": "",           // password, empry if none
  "MQTT_IN_TOPIC": "/sample.it/#",  // subscription topic

  "-MQTT_OUT_BROKER": "localhost",  // MQTT destination broker
  "-MQTT_OUT_PORT": "1882",         // ...
  "MQTT_OUT_USERNAME": "",
  "MQTT_OUT_PASSWORD": "",
  "MQTT_OUT_TOPIC_PREFIX": "/flat", // The profeix to appento to the new topic
  "THINGSBOARD_GW": "false"         // Use ThingsBoard Gateway as a destination broker
}
```
Note that using the same broker, in the subription you cannot use a `#` character otherwise the new topic will create a loop.
