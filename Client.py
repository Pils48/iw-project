import numpy as np
import socket
import time
import RPi.GPIO as GPIO
from os import listdir, system


DEVICE_FOLDER = "/sys/bus/w1/devices/"
DEVICE_SUFFIX = "/w1_slave"
WAIT_INTERVAL = 0.005

IP = '172.20.10.13'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

system('modprobe w1-gpio')
system('modprobe w1_therm')


def get_temperature_sensors():
    """
    Try guessing the location of the installed temperature sensor
    """
    devices = listdir(DEVICE_FOLDER)
    devices = [device for device in devices if device.startswith('28-')]
    if devices:
        print ("Found", len(devices), "devices which maybe temperature sensors.")
        return devices
    else:
        sys.exit("Sorry, no temperature sensors found")
        
        
def raw_temperature(device):
    """
    Get a raw temperature reading from the temperature sensor
    """
    raw_reading = None
    with open(device, 'r') as sensor:
        raw_reading = sensor.readlines()
    return raw_reading


def read_temperature(device, name):
    """
    Keep trying to read the temperature from the sensor until
    it returns a valid result
    """
    lines = raw_temperature(DEVICE_FOLDER + device + DEVICE_SUFFIX)

    # Keep retrying till we get a YES from the thermometer
    # 1. Make sure that the response is not blank
    # 2. Make sure the response has at least 2 lines
    # 3. Make sure the first line has a "YES" at the end
#     while not lines and len(lines) < 2 and lines[0].strip()[-3:] != 'YES':
#         # If we haven't got a valid response, wait for the WAIT_INTERVAL
#         # (seconds) and try 
#         time.sleep(WAIT_INTERVAL)
#         lines = raw_temperature()

    # Split out the raw temperature number
    temperature = lines[1].split('t=')[1]

    # Check that the temperature is not invalid
    if temperature != -1:
        temperature_celsius = round(float(temperature) / 1000.0, 1)
        
    return temperature_celsius


bytes_counter = 0

GPIO.setmode(GPIO.BOARD)

GPIO.setup(12, GPIO.OUT)  # Set GPIO pin 12 to output mode.
FAN_PWM = GPIO.PWM(12, 100)   # Initialize PWM on pwmPin 100Hz frequency

duty_cycle =0                               # set dc variable to 0 for 0%
FAN_PWM.start(duty_cycle)                      # Start PWM with 0% duty cycle

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((IP, PORT))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_0\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_1\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT FAN_SPEED\n", 'utf-8'))
    initial_timestamp = time.time()
    while True:
        devices = get_temperature_sensors()
        timestamp = time.time() - initial_timestamp
        for idx in range(0, len(devices)):
            temperature = read_temperature(devices[idx], "Thermometer_%d" % idx)
            if idx == 0:
                step = temperature % 16 # 5 steps control from 20 to 100 degrees
                FAN_PWM.ChangeDutyCycle((step + 1) * 20)
            print("Thermometer_%d value: %f" % (idx, temperature))
            s.sendall(bytes("DATA TEMPERATURE_%d %f %f\n" % (idx, temperature, timestamp), 'utf-8'))
    
        
