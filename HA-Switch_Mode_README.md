Home Assistent Integration
----------------------------

HA Switch Mode is a Joystick Gremlin Plugin. 
With this plugin Joystick Gremlin is able to send a status to Home Assistant. 

## Joystick Gremlin Setup 
- copy and rename the config_ha_jg.py root dir
- copy ha_switch_mode actionplugins  dir
- copy ha_request.py gremlin dir


## Home Assistent Setup
- create a Long Term Token in Home Asistent 
- change the config in `config_ha_jg.py.example` and rename it to  `config_ha_jg.py`
like this:
```
# Home Assistent
HA_SENSOR_URL = "https://xxx.duckdns.org:xxx/api/states/sensor.xxxx"
TOKEN = "xxx.xxx.xxx"

HA_URL = "https://xxxx.duckdns.org:xxxx"
# Entity Name : Friendly_Name
light_entities = {"light.desk_segment_2": "Cockpit Unterbodenlicht",
                  "light.desk_segment_1": "Haus Aussen",
                  "light.desk": "Haus Innen"
                  }
```