import time
import grovepi
import subprocess
import math
import RPi.GPIO as GPIO


# Moisture sensor pins
mositure_sensor_1 = 0
mositure_sensor_2 = 1

pump_1 = 12
pump_2 = 16

# General Purpose
light_sensor = 2
temp_humidity_sensor	= 4

time_for_sensor		= 1
time_to_sleep		 = 1
c_moisture_threshold = 300
c_water_time = 1


GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)

#Read the data from the sensors
def read_sensor():
	try:
		moisture = [grovepi.analogRead(mositure_sensor_1),
                            grovepi.analogRead(mositure_sensor_2)]
		
		light = grovepi.analogRead(light_sensor)
		[temp,humidity] = grovepi.dht(temp_humidity_sensor,0)
		
		#Return -1 in case of bad temp/humidity sensor reading
		if math.isnan(temp) or math.isnan(humidity):		#temp/humidity sensor sometimes gives nan
			return [-1,-1,-1,-1,-1]
		return [moisture[0], moisture[1], light, temp, humidity]
	
	#Return -1 in case of sensor error
	except IOError as TypeError:
			return [-1,-1,-1,-1,-1]

#Save the initial time, we will use this to find out when it is time to take a picture or save a reading
last_read_sensor= int(time.time())

while True:
	curr_time_sec=int(time.time())
	
	# If it is time to take the sensor reading
	if curr_time_sec-last_read_sensor>time_for_sensor:
		[moisture_1,moisture_2,light,temp,humidity]=read_sensor()

		curr_time = time.strftime("%Y-%m-%d:%H-%M-%S")
		print(("Time:%s\nMoisture: %d\nMoisture2: %d\nLight: %d\nTemp: %.2f\nHumidity:%.2f %%\n" %(curr_time,moisture_1,moisture_2,light,temp,humidity)))
		
		# Update the last read time
		last_read_sensor=curr_time_sec
	
                # Check if they need water
		if moisture_1 < c_moisture_threshold:
                    GPIO.output(pump_1,0)
                    time.sleep(c_water_time)
                    GPIO.output(pump_1,1)
                    
		if moisture_2 < c_moisture_threshold:
                    GPIO.output(pump_2,0)
                    time.sleep(c_water_time)
                    GPIO.output(pump_2,1)
	
	#Slow down the loop
	time.sleep(time_to_sleep)

