import re
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# Regex:
#  - ^/?                  : opzionale slash iniziale
#  - (?:bridge[^/]+/)?    : prefisso opzionale tipo /bridgeap/, /bridge1/, /bridge-foo/, ecc.
#  - (?P<tenant>[^/]+)    : TENANT (tutto fino al prossimo '/')
#  - /(?P<installation_id>[^/]+) : INSTALLATION_ID (il segmento subito dopo TENANT)
#  - (?:/|$)              : seguito da uno slash o fine stringa
_TOPIC_RE = re.compile(
    r"^/?(?:bridge[^/]+/)?(?P<tenant>[^/]+)/(?P<installation_id>[^/]+)(?:/|$)"
)

logger = logging.getLogger("mqtt_connector")

def extract_tenant_installation(topic: str):
    """
    Estrae TENANT e INSTALLATION_ID da un topic MQTT.

    Gestisce sia i topic standard:        /TENANT/INSTALLATION_ID/...
    sia quelli con prefisso di backup:    /bridge*/TENANT/INSTALLATION_ID/...

    Ritorna (tenant, installation_id) oppure (None, None) se non combacia.
    """
    if topic is None:
        return None, None
    topic = topic.strip()
    m = _TOPIC_RE.match(topic)
    if not m:
        return None, None
    return m.group("tenant"), m.group("installation_id")


def flatter_json(text, topic=None):
    # now = datetime.now().isoformat()
    json_text = json.loads(text)
    new_message = json_text

    if "m" in json_text:
        for elem in json_text["m"]:
            if "k" in elem and "v" in elem:
                json_text[elem["k"]] = elem["v"]
        del json_text["m"]
        new_message = json_text

    if "meta" in json_text:
        meta = json_text["meta"]
        for k, v in meta.items():
            json_text[k] = v
        del json_text["meta"]
        new_message = json_text

    if "readings" in json_text:
        readings = json_text["readings"]
        objectValue = readings[0]["objectValue"]
        new_message = objectValue

    if "sensors" in json_text:
        sensors = json_text["sensors"]
        for k, v in sensors.items():
            json_text[k] = v
        del json_text["sensors"]
        new_message = json_text
    
    # Add tenant and installation_id extraction if topic is provided
    if topic:
        tenant, installation_id = extract_tenant_installation(topic)
        if tenant and installation_id:
            logger.info(f"Extracted tenant: {tenant}, installation_id: {installation_id} from topic: {topic}")
            new_message['tenant'] = tenant
            new_message['installation_id'] = installation_id

    return new_message

def etl(message, topic=None):
    if "tz" not in message:
        if "collected_at" in message:
            message["tz"] = datetime.fromtimestamp(message["collected_at"], tz=ZoneInfo("Europe/Rome")).isoformat()
        else:
            message["tz"] = datetime.now(tz=ZoneInfo("Europe/Rome")).isoformat()

    return message

