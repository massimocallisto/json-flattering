import json
import time
import psutil

import paho.mqtt.client as mqtt
import logging
import traceback
import os
import sys
from datetime import datetime
from tb_gateway_mqtt import TBGatewayMqttClient
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mqtt_connector")

def _set_environment():
    env_file_path = '.env'
    json_file_path = 'config.json'

    # Check if the file exists
    if os.path.exists(env_file_path):
        # Open the file and read its contents
        with open(env_file_path, 'r') as file:
            lines = file.readlines()
            # Iterate through each line
            for line in lines:
                # Remove whitespace and split the line by '='
                key, value = line.strip().split('=')
                # Set the environmental variable
                os.environ[key] = value
                logger.info(f"SET: os.environ[{key}] = {value}")
    else:
        logger.info("File not found or unable to read .env file.")

    if os.path.exists(json_file_path):
        for k, v in json.load(open(json_file_path)).items():
            print(f"SET: os.environ[{k}] = {v}")
            os.environ[k] = v
    else:
        logger.info("File not found or unable to read config.json file.")

_set_environment()
use_tbgw = os.getenv('THINGSBOARD_GW', "false") == "true"
logger.info("Using ThingsBoard gateway? " + str(use_tbgw))

for name, value in os.environ.items():
    print("{0}: {1}".format(name, value))

MQTT_IN = {
    'host': os.getenv('MQTT_IN_BROKER', "localhost"),
    'port': int(os.getenv('MQTT_IN_PORT', "1883")),
    'username': os.getenv('MQTT_IN_USERNAME', ""),
    'password': os.getenv('MQTT_IN_PASSWORD', ""),
    'source_topic': os.getenv('MQTT_IN_TOPIC', "/in/#"),
    'client': None
}

MQTT_OUT = {
    'host': os.getenv('MQTT_OUT_BROKER', None),
    'port': int(os.getenv('MQTT_OUT_PORT', "1883")),
    'username': os.getenv('MQTT_OUT_USERNAME', ""),
    'password': os.getenv('MQTT_OUT_PASSWORD', ""),
    'out_topic': os.getenv('MQTT_OUT_TOPIC_PREFIX', "/flat"),
    'client' : None,
    'gateway': None
}

def on_connect_in(client, userdata, flags, rc):
    client.subscribe(MQTT_IN['source_topic'])
    logger.info("CONNECTED to IN BROKER " + MQTT_IN['host'] + " AND SUBSCRIBED to: " + MQTT_IN['source_topic'])


def on_connect_out_2(client, userdata, flags, rc):
    logger.info("CONNECTED to OUT broker " + MQTT_OUT['host'])

def detect_loop(topic_in : str):
    if MQTT_IN["source_topic"] == "#":
        logger.warning("You cannot publish on the same broker by using # subscription otherwise "
                        "a loop will happen!")
        return True
    if topic_in.startswith(MQTT_OUT["out_topic"]):
        logger.warning(f"Loop detected! Input topic {topic_in} start with out topic"
                        + MQTT_OUT["out_topic"] + "!")
        return True

    return False

def send_to_thingsboard(json_str: str):
    if MQTT_OUT["gateway"] is None:
        return
    json_obj = json.loads(json_str)
    json_to_send = json_obj
    device_ref = json_obj['ref']
    device_type = json_obj['type']
    device_id = device_type + "_" + device_ref

    MQTT_OUT["gateway"].gw_connect_device(device_id)
    logging.info("Sending temperature value to " + device_id)
    MQTT_OUT["gateway"].gw_send_telemetry(device_id, json_to_send)
    MQTT_OUT["gateway"].gw_disconnect_device(device_id)

def send_to_mqtt(client, topic_in : str, json_text):
    if MQTT_OUT["client"] is not None:
        curr_client = MQTT_OUT["client"]
    else:
        if detect_loop(topic_in):
            return
        #if MQTT_IN["source_topic"] == "#":
        #    logger.warning("You cannot publish on the same broker by using # subscription otherwise "
        #                   "a loop will happen!")
        #    return
        #if msg.topic.startswith(MQTT_OUT["out_topic"]):
        #    logger.warning(f"Loop detected! Input topic {msg.topic} start with out topic"
        #                   + MQTT_OUT["out_topic"] + "!")
        #    return
        curr_client = client

    publish_topic = MQTT_OUT["out_topic"]
    if not topic_in.startswith("/") and \
            not publish_topic.startswith("/"):
        publish_topic = publish_topic + "/" + topic_in
    else:
        publish_topic = publish_topic + topic_in

    logger.info(f"publish on {publish_topic} new message {json_text}")
    curr_client.publish(publish_topic, payload=json.dumps(json_text))


def on_message_in(client, userdata, msg):
    try:
        text = msg.payload.decode('utf-8')
        logger.info(f"got new msg on topic {msg.topic}\nText: {text}")
        json_text = flatter_json(text)
        if use_tbgw:
            json_str = json.dumps(json_text)
            send_to_thingsboard(json_str)
        else:
            send_to_mqtt(client, msg.topic, json_text)

    except Exception as e:
        print(traceback.format_exc())
        print(f"ERROR: {e}")

def on_connect_out(client, userdata, msg):
    pass


def flatter_json(text):
    # now = datetime.now().isoformat()
    json_text = json.loads(text)
    if "m" in json_text:
        for elem in json_text["m"]:
            if "k" in elem and "v" in elem:
                json_text[elem["k"]] = elem["v"]
        del json_text["m"]
    if "meta" in json_text:
        meta = json_text["meta"]
        for k, v in meta.items():
            json_text[k] = v
        del json_text["meta"]
    return json_text


def on_disconnect_in(client, userdata, rc):
    logger.info("Disconnected MQTT BROKER")


def on_message_out(client, userdata, rc):
    # logger.info("on_message_out MQTT BROKER")
    pass

def set_mqtt_out():
    logger.info("SET standard MQTT OUT client")
    if MQTT_OUT["host"] is not None and \
        (MQTT_IN["host"] != MQTT_OUT["host"] or
         MQTT_IN["port"] != MQTT_OUT["port"]):
        client_out = get_client(
            username=MQTT_OUT["username"],
            password=MQTT_OUT["password"],
            on_connect=on_connect_out_2,
            on_disconnect=on_disconnect_in
        )
        client_out.connect(
            MQTT_OUT["host"],
            MQTT_OUT["port"],
            60)

        print("Going to connect to MQTT server Out ")
        client_out.loop_start()
        MQTT_OUT["client"] = client_out

    else:
        print("Going to use the same broker " + (MQTT_IN["host"] + ":"
                                                 + str(MQTT_IN["port"])) + " for flattering output!")


def get_client(username: str = None, password: str = None, on_connect=None, on_message=None, on_disconnect=None):
    client = mqtt.Client(transport='tcp', client_id='flatter' + str(time.time()))
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    if username is not None or username != "":
        client.username_pw_set(
            username=username,
            password=password
        )
    # context = ssl.SSLContext()
    # client.tls_set_context()
    # callback = on_badge_message
    # main_topic = topic

    return client


def send_cpu_memory_usage():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    data = {'cpu': cpu_percent, 'memory': memory_percent}
    json_data = json.dumps(data)
    logging.info("Sending gateway telemetries: " + json_data)
    MQTT_OUT["gateway"].send_telemetry(data)


if __name__ == '__main__':
    client_in = get_client(
        username=MQTT_IN["username"],
        password=MQTT_IN["password"],
        on_connect=on_connect_in,
        on_message=on_message_in,
        on_disconnect=on_disconnect_in
    )
    client_in.connect(
        MQTT_IN["host"],
        MQTT_IN["port"],
        60)
    MQTT_IN["client"] = client_in

    # SET OUT CLIENT
    if use_tbgw:
        gateway = TBGatewayMqttClient(MQTT_OUT["host"], MQTT_OUT["port"], MQTT_OUT["username"], MQTT_OUT["password"])
        MQTT_OUT["gateway"] = gateway
        gateway.connect()
    else:
        set_mqtt_out()

    client_in.loop_start()

    logger.info("Start loop with simple CPU data from this client")
    #send_cpu_memory_usage()

    counter = 0
    wait_time = 3
    
    while True:
        time.sleep(30)
        #send_cpu_memory_usage()
        
        logger.info("wake up...")
        if not MQTT_IN["client"].is_connected() \
                or (MQTT_OUT["client"] and not MQTT_OUT["client"].is_connected()):
            if counter == 10:
                logger.error(f"too long waiting.. going to exit after {wait_time} secs")
                break

            wait_time = wait_time + counter
            counter = counter + 1
            logger.warning(f"going to wait for reconnect... sleep for {wait_time} secs")
        else:
            counter = 0
