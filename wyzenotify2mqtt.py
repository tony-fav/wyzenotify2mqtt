import re
import paho.mqtt.client as mqtt

# MQTT_HOST = os.getenv('MQTT_HOST')
# MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
# MQTT_USER = os.getenv('MQTT_USER')
# MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
# MQTT_CLIENT = os.getenv('MQTT_CLIENT', 'wyzenotify2mqtt')
# MQTT_QOS = int(os.getenv('MQTT_QOS', 1))

from secrets import MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_CLIENT, MQTT_QOS

# tasker_topic = 'pixeltasker/'
tasker_topic = 'bluestacks/'
base_topic = 'wyzenotify2mqtt/'


contact_sensor_re = re.compile(r"(Wyze, )(?P<name>.+)( was )(?P<state>opened|closed)")
contact_sensor_discovered = []
contact_sensor_state_topic = r'wyzenotify2mqtt/%better_name%/state'
contact_sensor_discovery_topic = r'homeassistant/binary_sensor/wyzenotify2mqtt/%better_name%/config'
contact_sensor_discovery_payload = r'{"name":"WyzeNotify2MQTT %name%","avty_t":"wyzenotify2mqtt/LWT","stat_t":"wyzenotify2mqtt/%better_name%/state","dev_cla":"door","dev":{"ids":["FAFAFA"],"name":"WyzeNotify2MQTT","mdl":"Contact Sensor","sw":"tony-fav","mf":"tony-fav"}}'

motion_sensor_re = re.compile(r"(Wyze, )(?P<name>.+)( )(?P<state>detected motion|is clear)")
motion_sensor_discovered = []
motion_sensor_state_topic = r'wyzenotify2mqtt/%better_name%/state'
motion_sensor_discovery_topic = r'homeassistant/binary_sensor/wyzenotify2mqtt/%better_name%/config'
motion_sensor_discovery_payload = r'{"name":"WyzeNotify2MQTT %name%","avty_t":"wyzenotify2mqtt/LWT","stat_t":"wyzenotify2mqtt/%better_name%/state","dev_cla":"motion","dev":{"ids":["FAFAFA"],"name":"WyzeNotify2MQTT","mdl":"Motion Sensor","sw":"tony-fav","mf":"tony-fav"}}'



def send_ha_disovery_contact_sensor(name):
    global contact_sensor_discovered
    better_name = name.lower().replace(' ', '_')
    if better_name not in contact_sensor_discovered:
        topic = contact_sensor_discovery_topic.replace(r'%better_name%', better_name)
        payload = contact_sensor_discovery_payload.replace(r'%better_name%', better_name).replace(r'%name%', name)
        publish(topic, payload=payload, retain=True)
        contact_sensor_discovered.append(better_name)

def publish_contact_sensor_state(name, state):
    global contact_sensor_discovered
    better_name = name.lower().replace(' ', '_')
    if state == 'opened':
        payload = 'ON'
    elif state == 'closed':
        payload = 'OFF'
    else:
        payload = 'UNKNOWN'
    topic = contact_sensor_state_topic.replace(r'%better_name%', better_name)
    publish(topic, payload=payload, retain=False)

def send_ha_disovery_motion_sensor(name):
    global motion_sensor_discovered
    better_name = name.lower().replace(' ', '_')
    if better_name not in motion_sensor_discovered:
        topic = motion_sensor_discovery_topic.replace(r'%better_name%', better_name)
        payload = motion_sensor_discovery_payload.replace(r'%better_name%', better_name).replace(r'%name%', name)
        publish(topic, payload=payload, retain=True)
        motion_sensor_discovered.append(better_name)

def publish_motion_sensor_state(name, state):
    global motion_sensor_discovered
    better_name = name.lower().replace(' ', '_')
    if state == 'detected motion':
        payload = 'ON'
    elif state == 'is clear':
        payload = 'OFF'
    else:
        payload = 'UNKNOWN'
    topic = motion_sensor_state_topic.replace(r'%better_name%', better_name)
    publish(topic, payload=payload, retain=False)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))
    if rc == 0:
        client.subscribe(tasker_topic + '#')
        publish(base_topic + 'LWT', payload='online', retain=True)

def on_message(client, userdata, msg):
    payload_str = str(msg.payload.decode("utf-8"))

    if msg.topic == tasker_topic + 'LWT':
        return

    # Match Contact Sensor Notification
    match_contact_sensor = contact_sensor_re.match(payload_str)
    if match_contact_sensor:
        sensor_name = match_contact_sensor.group('name')
        sensor_state = match_contact_sensor.group('state')
        send_ha_disovery_contact_sensor(sensor_name)
        publish_contact_sensor_state(sensor_name, sensor_state)
        print('%s, %s' % (sensor_name, sensor_state))
        return

    # Match Motion Sensor Notification
    match_motion_sensor = motion_sensor_re.match(payload_str)
    if match_motion_sensor:
        sensor_name = match_motion_sensor.group('name')
        sensor_state = match_motion_sensor.group('state')
        send_ha_disovery_motion_sensor(sensor_name)
        publish_motion_sensor_state(sensor_name, sensor_state)
        print('%s, %s' % (sensor_name, sensor_state))
        return

    publish(base_topic + 'log', payload='%s, %s' % (msg.topic, payload_str))

client = mqtt.Client(MQTT_CLIENT)
client.username_pw_set(MQTT_USER , MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, port=MQTT_PORT)
client.will_set(base_topic + 'LWT', payload='offline', qos=MQTT_QOS, retain=True)

# Redefine Publish with The QOS Setting
def publish(topic, payload=None, qos=MQTT_QOS, retain=True, properties=None):
    print('%s: %s' % (topic, payload))
    client.publish(topic, payload=payload, qos=qos, retain=retain, properties=properties)

client.loop_forever()