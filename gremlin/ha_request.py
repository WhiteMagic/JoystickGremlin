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


def set_ha_entity_states(entity, state, attributes, friendly_name=None):
    if len(attributes) == 0:
        attributes = None
    if "sensor" in entity:
        post_request(entity=entity, state=state, friendly_name=friendly_name, attributes=attributes)
    elif "light" in entity:
        post_service_to_ha(domain="light", entity=entity, state="turn_on", attributes=attributes)
    else:
        print(f"entity is wrong")


def post_request(entity, state, friendly_name=None, attributes=None):
    now = datetime.now()
    date_time = now.strftime("%d.%m.%y %H:%M")
    post_url = f"{config_ha_jg.HA_URL}/api/states/{entity}"
    post_attributes = {
            "friendly_name": friendly_name,
            "timestamp": date_time,
    }
    if attributes is not None:
        attr = json.loads(attributes)
        post_attributes.update(attr)
    requests.post(post_url,
                  headers={
                      "Authorization": "Bearer " + config_ha_jg.TOKEN,
                      "content-type": "application/json",
                  },
                  json={"state": state, "attributes": post_attributes}
                  )


def post_service_to_ha(domain, entity, state, attributes=None):
    post_url = f"{config_ha_jg.HA_URL}/api/services/{domain}/{state}"
    payload = {"entity_id": entity}
    if attributes is not None:
        payload.update(attributes)
    requests.post(post_url,
                  headers={
                      "Authorization": "Bearer " + config_ha_jg.TOKEN,
                      "content-type": "application/json",
                  },
                  json=payload
                  )


def get_entity_items(entity):
    get_url = f"{config_ha_jg.HA_URL}/api/states/{entity}"
    var = dict(get_from_ha(get_url))
    return var


if __name__ == "__main__":
    #post_to_ha("asd", "lal aus module3")
    import pprint
    #pprint.pprint(get_entity("light.desk_segment_2"))
    #post_service_to_ha("light", "light.desk_segment_2", "turn_on", '{"rgb_color":[100,0,200]}')
