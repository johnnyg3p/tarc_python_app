#!/usr/bin/python

# Import required Python libraries
import paho.mqtt.client as mqtt
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import spidev
import json
from libsoc import gpio
from time import sleep
from libsoc_zero.GPIO import Button


# Define GPIO to use 
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=10000
spi.mode = 0b00
spi.bits_per_word = 8
channel_select=[0x01, 0xA0, 0x00]
channel_select2=[0x01, 0x80, 0x00]

READ_SENSE = gpio.GPIO(18, gpio.DIRECTION_OUTPUT)
tilt = Button('GPIO-C')


# read if Tilt happened
def hasEarthQuake():     
    if tilt.is_pressed():
       print({'earthquake':'true'})        
       return json.dumps({'earthquake':'true'}) 
    else:        
       print({'earthquake':'false'})
       return json.dumps({'earthquake':'false'}) 
            

# read the temperature sensor 
def readTempSense():                                 
    READ_SENSE.set_high()
    sleep(0.00001)
    READ_SENSE.set_low()
    rx = spi.xfer(channel_select)
    READ_SENSE.set_high()

    TEMP_VALUE = (rx[1] << 8) & 0b1100000000
    TEMP_VALUE = TEMP_VALUE | (rx[2] & 0xff)   
    TEMP_VALUE = TEMP_VALUE/6

    print({'temperature':round(TEMP_VALUE,2)})
    return json.dumps({'temperature':round(TEMP_VALUE,2)})       

#read the light sensor
def readLighSense():                                      
    READ_SENSE.set_high()
    sleep(0.00001)
    READ_SENSE.set_low()
    rx = spi.xfer(channel_select2)
    READ_SENSE.set_high()

    LIGHT_VALUE = (rx[1] << 8) & 0b1100000000
    LIGHT_VALUE = LIGHT_VALUE | (rx[2] & 0xff)   

    print({'light':round(LIGHT_VALUE,2)})
    return json.dumps({'light':round(LIGHT_VALUE,2)})    
          

# Start read all sensors
def start():         
        while True :                        
            hasEarthQuake() 
            readTempSense()
            readLighSense()
            sleep(2)

def customCallback(data):            
    print(data)

def sendMessage():
    while True :
        print("Send message")
        # For certificate based connection
        myMQTTClient = AWSIoTMQTTClient("dragon")
        # For Websocket connection
        # myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
        # Configurations
        # For TLS mutual authentication
        myMQTTClient.configureEndpoint("a8mgf2amxmior.iot.us-east-2.amazonaws.com", 8883)
        # For Websocket
        # myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
        myMQTTClient.configureCredentials("/home/linaro/Desktop/awsConnect/root-CA.crt", "/home/linaro/Desktop/awsConnect/dragon.private.key", "/home/linaro/Desktop/awsConnect/dragon.cert.pem")
        # For Websocket, we only need to configure the root CA
        # myMQTTClient.configureCredentials("YOUR/ROOT/CA/PATH")
        myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        myMQTTClient.connect()
        myMQTTClient.publish("temp", readTempSense(), 0)
        myMQTTClient.publish("light", readLighSense(), 0)
        myMQTTClient.publish("earthquake", hasEarthQuake(), 0)            
        myMQTTClient.disconnect()
        sleep(5)

     
if __name__ == '__main__':    
    with gpio.request_gpios([READ_SENSE]):        
        sendMessage()
        