import time
import sched
import grovepi
import subprocess
import math
import RPi.GPIO as GPIO
import requests

# Config
config_moisture_threshold = 250
config_water_time = 1

# Schedules
config_pump_time = 60
config_upload_time = 1800

# Pushover config
token = "pushoverToken"

users = {
            "userToken":"deviceName",
        }

# Pins for GPIO
pump_1 = 14
pump_2 = 15
GPIO.setmode(GPIO.BCM)
GPIO.setup(pump_1, GPIO.OUT)
GPIO.setup(pump_2, GPIO.OUT)
GPIO.output(pump_1,1)
GPIO.output(pump_2,1)

# Pins for GROVE atmega
light_sensor = 0
mositure_sensor_1 = 1
mositure_sensor_2 = 2
temp_humidity_sensor = 6

# Scheduler
s = sched.scheduler(time.time, time.sleep)

# Send post data
def send_pushover_message(title, message,sound):
    for key in users:
        r = requests.post(
            "https://api.pushover.net/1/messages.json",
            data = {
                'token' : token,
                'html' : 1,
                'title' : title,
                'sound': sound,
                'message' : message,
                'user' : key,
                'device' : users[key]
            }
        );
        
        print(r.status_code, r.reason)

# Moisture reading to
def moisture_level_str(level):
    if level > 600:
        return "freshly watered"
    elif level < config_moisture_threshold:
        return "thirsty"
    else:
        return "happy"

# Moisture reading to
def light_level_str(level):
    if level > 500:
        return "bright"
    elif level < 150:
        return "dark"
    else:
        return "dim"

# Activate pump
def activate_pumps(sc):
    [moisture_1,moisture_2,light,temp,humidity] = read_sensor()

    # Message
    # POST to pushover
    message = "";

    # Check if they need water
    # Pump 1
    if moisture_1 < config_moisture_threshold:
        GPIO.output(pump_1,0)
        time.sleep(config_water_time)
        GPIO.output(pump_1,1)
        message += "<b>Plant 1</b> has been watered.<br>"
        
    # Pump 2
    if moisture_2 < config_moisture_threshold:
        GPIO.output(pump_2,0)
        time.sleep(config_water_time)
        GPIO.output(pump_2,1)
        message += "<b>Plant 2</b> has been watered.<br>"
        
    # Send POST
    if message != "":
        send_pushover_message("Plant Update", message,"pushover")
    
    # Retrigger function
    sc.enter(config_pump_time, 1, activate_pumps, (sc,))

# Activate pump
def upload_readings(sc):
    # Print 
    [moisture_1,moisture_2,light,temp,humidity] = read_sensor()
    
    if moisture_1 == -1:
        print("Sensor Error!")
    else:
        curr_time = time.strftime("%Y-%m-%d:%H-%M-%S")
        print(("Time:%s\nMoisture: %d\nMoisture2: %d\nLight: %d\nTemp: %.2f\nHumidity:%.2f\n" %(curr_time,moisture_1,moisture_2,light,temp,humidity)))
    
        message = \
            "The temperature is " + str(temp) + "°C.<br>" +\
            "The relative humidity is " + str(humidity) + "%.<br>" +\
            "The light level is " + light_level_str(light) + ".<br>" +\
            "Plant 1 is " + moisture_level_str(moisture_1) + ".<br>" +\
            "Plant 2 is " + moisture_level_str(moisture_2) + ".<br>"
        send_pushover_message("APWS Update", message,"none")

    
    # Retrigger function
    sc.enter(config_upload_time, 1, upload_readings, (sc,))

# Read the data from the sensors
def read_sensor():
    try:
        # Read moisture
        moisture1 = grovepi.analogRead(mositure_sensor_1)
        moisture2 = grovepi.analogRead(mositure_sensor_2)
        
        # Read light
        light = grovepi.analogRead(light_sensor)
        
        # Read temp and humidity
        [temp,humidity] = grovepi.dht(temp_humidity_sensor,0)
        
        #Return -1 in case of bad temp/humidity sensor reading
        if math.isnan(temp) or math.isnan(humidity):		#temp/humidity sensor sometimes gives nan
            return [-1,-1,-1,-1,-1]
        return [moisture1, moisture2, light, temp, humidity]
    
    # Return -1 in case of sensor error
    except IOError as TypeError:
        return [-1,-1,-1,-1,-1]

# Main
try:
    # Run scheduled tasks
    s.enter(config_pump_time, 1, activate_pumps, (s,))
    s.enter(config_upload_time, 1, upload_readings, (s,))
    s.run()
except Exception as ex:
   print ("Exception occured:" + ex.__name__) 
finally:
    # Deactivate pins
    GPIO.cleanup()
