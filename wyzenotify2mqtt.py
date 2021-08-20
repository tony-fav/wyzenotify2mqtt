import os
import json
import time
import re
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_CLIENT = os.getenv('MQTT_CLIENT', 'wyzenotify2mqtt')
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))

from secrets import MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_CLIENT, MQTT_QOS, contact_sensor_list

tasker_topic = 'pixeltasker/'
base_topic = 'wyzenotify2mqtt/'


contact_sensor_re = re.compile(r"(Wyze, )(?P<name>.+)( was )(?P<state>opened|closed)( at )(?P<hours>[0-9][0-9])(:)(?P<minutes>[0-9][0-9])( )(?P<AMPM>AM|PM)(\.)")
contact_sensor_discovered = []
contact_sensor_discovery_topic = r'homeassistant/binary_sensor/wyzenotify2mqtt/%better_name%/config'
contact_sensor_discovery_payload = r'{"name":"WyzeNotify2MQTT %name%","stat_t":"wyzenotify2mqtt/%better_name%/state","dev_cla":"door","dev":{"ids":["wyzenotify2mqtt"],"name":"WyzeNotify2MQTT","mdl":"Contact Sensor","sw":"tony-fav","mf":"tony-fav"}}'



def send_ha_disovery_contact_sensor(name):
    global contact_sensor_discovered
    better_name = name.lower().replace(' ', '_')
    if better_name not in contact_sensor_discovered:
        topic = contact_sensor_discovery_topic.replace(r'%better_name%', better_name)
        payload = contact_sensor_discovery_payload.replace(r'%better_name%', better_name).replace(r'%name%', name)
        publish(topic, payload=payload, retain=False)
        contact_sensor_discovered.append(better_name)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))
    if rc == 0:
        client.subscribe(tasker_topic + '#')

def on_message(client, userdata, msg):
    payload_str = str(msg.payload.decode("utf-8"))

    # try match contact_sensor notificationa
    match_contact_sensor = contact_sensor_re.match(payload_str)
    if match_contact_sensor:
        sensor_name = match_contact_sensor.group('name')
        send_ha_disovery_contact_sensor(sensor_name)
        if match_contact_sensor.group('state') == 'opened':
            sensor_state = 'ON'
        elif match_contact_sensor.group('state') == 'closed':
            sensor_state = 'OFF'
        else:
            sensor_state = 'UNKNOWN'
        # print(int(m.group('hours')))
        # print(int(m.group('minutes')))
        # print(m.group('AMPM'))
        print('%s, %s' % (sensor_name, sensor_state))

client = mqtt.Client(MQTT_CLIENT)
client.username_pw_set(MQTT_USER , MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, port=MQTT_PORT)

# Redefine Publish with The QOS Setting
def publish(topic, payload=None, qos=MQTT_QOS, retain=True, properties=None):
    print('%s: %s' % (topic, payload))
    client.publish(topic, payload=payload, qos=qos, retain=retain, properties=properties)

client.loop_start()

press_timeout = 1000

while True:
    pass