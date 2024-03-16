"""
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
from time import sleep
from datetime import datetime
import json

def byte_array_to_dict(msg:bytearray):
        try:
            string_bytes = msg.payload
            string_utf8 = string_bytes.decode('utf-8')
            data_dict = json.loads(string_utf8) 
        except UnicodeDecodeError:
            string_utf8 = string_bytes.decode('latin-1')      
            data_dict = json.loads(string_utf8)
        return data_dict

def main():
    hostname='127.0.0.1'
    message = subscribe.simple("mi/topico", hostname=hostname)
    pData = byte_array_to_dict(message)
    print(pData)

if __name__ == '__main__':
    main()"""


import paho.mqtt.subscribe as subscribe
from threading import Thread
from time import sleep

def on_message_print(client, userdata, message):
    print("%s %s" % (message.topic, message.payload))
    global val
    val = message.payload

def mqtt_subscribe():
    subscribe.callback(on_message_print, "mi/topico", hostname="localhost", userdata={"message_count": 0})

# Crear y ejecutar el hilo para la suscripción MQTT
mqtt_thread = Thread(target=mqtt_subscribe)
mqtt_thread.start()

# Bucle principal
val = 0
while True: 
    print(f'hola: {val}')
    sleep(1)