import time
import sched
import grovepi
import subprocess
import math
import RPi.GPIO as GPIO

# Config
config_moisture_threshold = 200
config_water_time = 1
config_pump_time = 10
config_upload_time = 5

# Pins for GPIO
pump_1 = 14
pump_2 = 15
GPIO.setmode(GPIO.BCM)
GPIO.setup(pump_1, GPIO.OUT)
GPIO.setup(pump_2, GPIO.OUT)

# Pins for GROVE atmega
light_sensor = 0
mositure_sensor_1 = 1
mositure_sensor_2 = 2
temp_humidity_sensor	= 6

# Scheduler
s = sched.scheduler(time.time, time.sleep)

# Activate pump
def activate_pumps(sc):
    [moisture_1,moisture_2,light,temp,humidity] = read_sensor()

    # Check if they need water
    # Pump 1
    if moisture_1 < config_moisture_threshold:
        GPIO.output(pump_1,0)
        time.sleep(config_water_time)
        GPIO.output(pump_1,1)
        
    # Pump 2
    if moisture_2 < config_moisture_threshold:
        GPIO.output(pump_2,0)
        time.sleep(config_water_time)
        GPIO.output(pump_2,1)   
        
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
except:
   print ("exception occured") 
finally:
    # Deactivate pins
    GPIO.cleanup()
