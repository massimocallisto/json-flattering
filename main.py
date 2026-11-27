import json
import time
from pathlib import Path

import psutil
import paho.mqtt.client as mqtt
import logging
import traceback
import os
import sys
from datetime import datetime
from tb_gateway_mqtt import TBGatewayMqttClient
from flattering import flatter_json, etl
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path(__file__).resolve().parent / ".env",
    override=False,
)

log_level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
log_level = getattr(logging, log_level_name, None)

if not isinstance(log_level, int):
    raise ValueError(f"LOG_LEVEL non valido: {log_level_name}")

logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("mqtt_connector")

use_tbgw = os.getenv('THINGSBOARD_GW', "false") == "true"
if use_tbgw :
    gateway_token = os.getenv('THINGSBOARD_GW_TOKEN', "xxxx")
logger.info("Using ThingsBoard gateway? " + str(use_tbgw))

MQTT_IN = {
    'host': os.getenv('MQTT_IN_BROKER', "localhost"),
    'port': int(os.getenv('MQTT_IN_PORT', "1883")),
    'transport': os.getenv('MQTT_IN_TRANSPORT', "tcp"),
    'username': os.getenv('MQTT_IN_USERNAME', ""),
    'password': os.getenv('MQTT_IN_PASSWORD', ""),
    'source_topic': os.getenv('MQTT_IN_TOPIC', "/in/#"),
    'client': None
}

MQTT_OUT = {
    'host': os.getenv('MQTT_OUT_BROKER', None),
    'port': int(os.getenv('MQTT_OUT_PORT', "1883")),
    'transport': os.getenv('MQTT_OUT_TRANSPORT', "tcp"),
    'username': os.getenv('MQTT_OUT_USERNAME', ""),
    'password': os.getenv('MQTT_OUT_PASSWORD', ""),
    'out_topic': os.getenv('MQTT_OUT_TOPIC_PREFIX', "/flat"),
    'client' : None,
    'gateway': None
}

logger.info(
    "MQTT sorgente: broker=%s porta=%s trasporto=%s topic=%s, authentication=%s",
    MQTT_IN["host"],
    MQTT_IN["port"],
    MQTT_IN["transport"],
    MQTT_IN["source_topic"],
    "yes" if MQTT_IN["username"] else "no"
)

logger.info(
    "MQTT destinazione: broker=%s porta=%s trasporto=%s "
    "prefisso_topic=%s modalità=%s, authentication=%s",
    MQTT_OUT["host"] or MQTT_IN["host"],
    MQTT_OUT["port"] if MQTT_OUT["host"] else MQTT_IN["port"],
    MQTT_OUT["transport"] if MQTT_OUT["host"] else MQTT_IN["transport"],
    MQTT_OUT["out_topic"],
    "yes" if MQTT_OUT["username"] else "no",
    "ThingsBoard Gateway" if use_tbgw else "MQTT",
)

def on_connect_in(client, userdata, flags, rc):
    topic = MQTT_IN['source_topic']
    logger.info("CONNECT to IN BROKER " + MQTT_IN['host'])
    if "," in topic:
        topics = topic.split(",")
        for t in topics:
            client.subscribe(t)
            logger.info("SUBSCRIBED to: " + t)
    else:
        client.subscribe(topic)
        logger.info("SUBSCRIBED to: " + topic)


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

def send_to_thingsboard(json_str: str, topic_in : str = ""):
    if MQTT_OUT["gateway"] is None:
        return

    json_obj = json.loads(json_str)
    json_to_send = json_obj
    device_id = None
    is_gateway = False

    if "/device/message" in topic_in:
        device_ref = json_obj['id']
        device_type = json_obj['sensorType']
        device_panid = json_obj['panid']
        device_id = f"{device_type}-{device_panid}-{device_ref}"
    elif "/accelerometer/message" in topic_in or "/gateway/message" in topic_in:
        #/ sacconi / ap / accelerometer / message / dipme3
        device_ref = json_obj['id']
        device_type = json_obj['sensorType']
        device_id = f"{device_type}-{device_ref}"
        if "/gateway/message" in topic_in:
            is_gateway = True
    elif "device_id" in json_obj:
        device_id = json_obj['device_id']
    elif "ref" in json_obj and "type" in json_obj :
        device_ref = json_obj['ref']
        device_type = json_obj['type']
        device_id = device_type + "_" + device_ref

    if device_id is None:
        logging.warning(f"No device id found in message in {topic_in}")
        return

    if not is_gateway:
        MQTT_OUT["gateway"].gw_connect_device(device_id)
        logging.info("Sending message value to " + device_id)
        MQTT_OUT["gateway"].gw_send_telemetry(device_id, json_to_send)
        MQTT_OUT["gateway"].gw_disconnect_device(device_id)
    else:
        logging.info("Sent gateway telemetry" + device_id)
        MQTT_OUT["gateway"].send_telemetry(json_to_send)


def send_to_mqtt(client, topic_in : str, json_text):
    if MQTT_OUT["client"] is not None:
        curr_client = MQTT_OUT["client"]
    else:
        if detect_loop(topic_in):
            return
        curr_client = client

    publish_topic = MQTT_OUT["out_topic"]
    if not topic_in.startswith("/") and \
            not publish_topic.startswith("/"):
        publish_topic = publish_topic + "/" + topic_in
    else:
        publish_topic = publish_topic + topic_in

    logger.info(f"publish on {publish_topic}")
    logger.debug(f".. new message {json_text}")
    curr_client.publish(publish_topic, payload=json.dumps(json_text))


def on_message_in(client, userdata, msg):
    try:
        text = msg.payload.decode('utf-8')
        logger.info(f"got new msg on topic {msg.topic}")
        json_text = flatter_json(text, topic=msg.topic)
        json_text = etl(json_text, topic=msg.topic)

        if use_tbgw:
            json_str = json.dumps(json_text)
            send_to_thingsboard(json_str, topic_in=msg.topic)
        else:
            send_to_mqtt(client, msg.topic, json_text)

    except Exception as e:
        print(traceback.format_exc())
        print(f"ERROR: {e}")

def on_connect_out(client, userdata, msg):
    pass

def on_disconnect_in(client, userdata, rc):
    logger.info("Disconnected MQTT BROKER: " + MQTT_IN["host"] )

def on_disconnect_out(client, userdata, rc):
    logger.info("Disconnected OUT MQTT BROKER: " + MQTT_OUT["host"] )

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
            on_disconnect=on_disconnect_out,
            transport=MQTT_OUT["transport"]
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


def get_client(username: str = None, password: str = None, on_connect=None, on_message=None, on_disconnect=None, transport:str="tcp"):
    client = mqtt.Client(transport=transport, client_id='flatter' + str(time.time()))
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    if username:
        client.username_pw_set(
            username=username,
            password=password
        )
    
    # Add TLS configuration for WebSocket connection
    if transport == "websockets":
        client.tls_set()  # Uses default certification validation
    
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
        on_disconnect=on_disconnect_in,
        transport=MQTT_IN["transport"]
    )
    client_in.connect(
        MQTT_IN["host"],
        MQTT_IN["port"],
        60)
    MQTT_IN["client"] = client_in

    # SET OUT CLIENT
    if use_tbgw:
        gateway = TBGatewayMqttClient(MQTT_OUT["host"], MQTT_OUT["port"], gateway_token)
        #gateway = TBGatewayMqttClient("193.205.92.131", 1883, "zrXhq3axnjp0FJpPzGqp")

        MQTT_OUT["gateway"] = gateway
        gateway.connect()
    else:
        set_mqtt_out()

    client_in.loop_start()

    logger.info("Start loop with simple CPU data from this client")

    counter = 0
    wait_time = 3
    
    while True:
        time.sleep(30)

        logger.info("wake up...in broker " + MQTT_IN["host"] + ", out broker: " + MQTT_IN["host"])
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