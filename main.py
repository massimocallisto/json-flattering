import json
import time

import paho.mqtt.client as mqtt
import logging
import traceback
import os
import sys
from datetime import datetime

MQTT_IN = {
    'host' : os.getenv('MQTT_IN_BROKER', "localhost"),
    'port': int(os.getenv('MQTT_IN_PORT', "1883")),
    'username': os.getenv('MQTT_IN_USERNAME', ""),
    'password': os.getenv('MQTT_IN_PASSWORD', ""),
    'source_topic': os.getenv('MQTT_IN_TOPIC', "/in/#"),
    'client' : None
}

MQTT_OUT = {
    'host' : os.getenv('MQTT_OUT_BROKER', None),
    'port': int(os.getenv('MQTT_OUT_PORT', "1883")),
    'username': os.getenv('MQTT_OUT_USERNAME', ""),
    'password': os.getenv('MQTT_OUT_PASSWORD', ""),
    'out_topic': os.getenv('MQTT_OUT_TOPIC_PREFIX', "/flat"),
    'client' : None
}

logger = logging.getLogger("mqtt_connector")


def on_connect_in(client, userdata, flags, rc):
    client.subscribe(MQTT_IN['source_topic'])
    logger.info("CONNECTED to IN BROKER " + MQTT_IN['host'] + " AND SUBSCRIBED to: " + MQTT_IN['source_topic'])


def on_connect_out_2(client, userdata, flags, rc):
    logger.info("CONNECTED to OUT broker " + MQTT_OUT['host'])


def on_message_in(client, userdata, msg):
    try:
        text = msg.payload.decode('utf-8')
        logger.info(f"got new msg on topic {msg.topic}\nText: {text}")
        json_text = flatter_json(text)

        if MQTT_OUT["client"] is not None:
            curr_client = MQTT_OUT["client"]
        else:
            if MQTT_IN["source_topic"] == "#":
                logger.warning("You cannot publish on the same broker by using # subscription otherwise "
                               "a loop will happen!")
                return
            if msg.topic.startswith(MQTT_OUT["out_topic"]):
                logger.warning(f"Loop detected! Input topic {msg.topic} start with out topic"
                               + MQTT_OUT["out_topic"] + "!")
                return
            curr_client = client

        publish_topic = MQTT_OUT["out_topic"]
        if not msg.topic.startswith("/") and \
                not publish_topic.startswith("/"):
            publish_topic = publish_topic + "/" + msg.topic
        else:
            publish_topic = publish_topic + msg.topic

        logger.info(f"publish on {publish_topic} new message {json_text}")
        curr_client.publish(publish_topic, payload=json.dumps(json_text))

    except Exception as e:
        print(traceback.format_exc())
        print(f"ERROR: {e}")


def on_connect_out(client, userdata, msg):
    pass


def flatter_json(text):
    #now = datetime.now().isoformat()
    json_text = json.loads(text)
    if "m" in json_text:
        for elem in json_text["m"]:
            if "k" in elem and "v" in elem:
                json_text[elem["k"]] = elem["v"]
        del json_text["m"]
    return json_text


def on_disconnect_in(client, userdata, rc):
    logger.info("Disconnected MQTT BROKER")


def on_message_out(client, userdata, rc):
    #logger.info("on_message_out MQTT BROKER")
    pass


def get_client(username: str = None, password: str = None, on_connect=None, on_message=None,on_disconnect=None):
    client = mqtt.Client(transport='tcp', client_id='flatter'+str(time.time()))
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

    # OUT Broker
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
    client_in.loop_start()

    counter = 0
    wait_time = 3
    while True:
        time.sleep(wait_time)
        logger.info("wake up...")
        if not MQTT_IN["client"].is_connected() \
                or not MQTT_OUT["client"].is_connected():
            if counter == 10:
                logger.error(f"too long waiting.. going to exit after {wait_time} secs")
                break

            wait_time = wait_time + counter
            counter = counter + 1
            logger.warning(f"going to wait for reconnect... sleep for {wait_time} secs")
        else:
            counter = 0


