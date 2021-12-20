Home Assistent Integration
----------------------------

HA Switch Mode is a Joystick Gremlin Plugin. 
With this plugin Joystick Gremlin is able to send a status to Home Assistant. 

## Joystick Gremlin Setup 
- copy and rename the config_ha_jg.py root dir
- copy ha_switch_mode actionplugins  dir
- copy ha_request.py gremlin dir


## Home Assistent Setup
- create a Sensor Template in
```
sensor:
  joystick_gremlin:
    friendly_name: "Joystick Gremlin"
    icon_template: mdi:gamepad-variant
    value_template: >-
      '{{ value_json.state }}'
    attribute_templates:
      messages: '{{ value_json.messages }}'
      timestamp: '{{ value_json.tst }}'
```