import requests
from datetime import datetime
import config_ha_jg
import json


# todo make async with aiohttp
# todo start light Service with colour
# curl -k -X POST -H "Authorization: Bearer myVeryLoooo0ooOOOngAndSecretToken" -H "Content-Type: application/json" -d '{"entity_id": "switch.socket"}' https://hass.example.org:8123/api/services/switch/turn_on

def post_to_ha(state, message):
    now = datetime.now()
    date_time = now.strftime("%d.%m %H:%M")
    requests.post(config_ha_jg.HA_SENSOR_URL,
                  headers={
                      "Authorization": "Bearer " + config_ha_jg.TOKEN,
                      "content-type": "application/json",
                  },
                  json={
                      "state": state, "attributes": {
                          "friendly_name": "Joystick Gremlin",
                          "messages": message, "timestamp": date_time
                      }
                  }
                  )


def get_from_ha(url):
    response = requests.get(url,
                            headers={
                                "Authorization": "Bearer " + config_ha_jg.TOKEN,
                                "content-type": "application/json",
                            },
                            )
    return response.json()


def set_ha_entity_states(entity, state, attributes, friendly_name="Joystick Gremlin", ):
    if len(attributes) == 0:
        attributes = None
    if "sensor" in entity:
        post_request(entity=entity, state=state, friendly_name=friendly_name, attributes=attributes)
    elif "light" in entity:
        post_service_light_to_ha(entity=entity, state=state, attributes=attributes)
    else:
        print(f"entity is wrong")


def post_request(entity, state, friendly_name="Joystick Gremlin", attributes=None):
    now = datetime.now()
    date_time = now.strftime("%d.%m.%y %H:%M")
    post_url = f"{config_ha_jg.HA_URL}/api/states/{entity}"
    post_attributes = {"friendly_name": friendly_name, "timestamp": date_time,
                       "mode": state}
    if attributes is not None:
        attr = json.loads(attributes)
        print(attr)
        if "rgb" in attr:
            if not "brightness_pct" in attr:
                attr.update({"brightness_pct": 20})
        post_attributes.update(attr)
    requests.post(post_url,
                  headers={
                      "Authorization": "Bearer " + config_ha_jg.TOKEN,
                      "content-type": "application/json",
                  },
                  json={"state": state, "attributes": post_attributes}
                  )


def post_service_light_to_ha(entity, state, attributes):
    """
    todo create services
    ha_url + switch_suffix
    add service 'turn_on' and 'turn_off'

    params:
        entity_id
    """
    print(entity)
    print(f"state is {state} with {attributes}")


def get_friendly_name_from_entity(entity):
    get_url = f"{config_ha_jg.HA_URL}/api/states/{entity}"
    var = dict(get_from_ha(get_url))
    return var["attributes"]["friendly_name"]


if __name__ == "__main__":
    post_to_ha("asd", "lal aus module3")
