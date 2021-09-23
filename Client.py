import numpy as np
import socket
import time
import RPi.GPIO as GPIO
import sys
import subprocess
from os import listdir, system


DEVICE_FOLDER = "/sys/bus/w1/devices/"
DEVICE_SUFFIX = "/w1_slave"
WAIT_INTERVAL = 0.005

IP = '172.20.10.13'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

system('modprobe w1-gpio')
system('modprobe w1_therm')

button_click_counter = 0


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
        temperature_celsius = round(float(temperature) / 1000.0, 2)
        
    return temperature_celsius


def button_callback(channel, initial_timestamp):
    print("Handling button interaption")
    global heater_PWM
    global button_click_counter
    button_click_counter += 1
    if button_click_counter % 2 == 0:
        heater_PWM.ChangeDutyCycle(100)
        for level in range(6):
            timestamp = time.time() - initial_timestamp
            s.sendall(bytes("DATA CPU_POWER %f %f\n" % (10 / 5 * level, timestamp), 'utf-8'))
            time.sleep(0.003)
    elif button_click_counter % 2 == 1:
        heater_PWM.ChangeDutyCycle(0)
        for level in range(5, -1, -1):
            timestamp = time.time() - initial_timestamp
            s.sendall(bytes("DATA CPU_POWER %f %f\n" % (10 / 5 * level, timestamp), 'utf-8'))
            time.sleep(0.003)


def set_resolution(sensorpath, resolution: int, persist: bool = False):
    if not 9 <= resolution <= 12:
            print(
                "The given sensor resolution '{0}' is out of range (9-12)".format(
                    resolution
                )
            )
            return False
    exitcode = subprocess.call(
            "echo {0} > {1}".format(resolution, sensorpath), shell=True
        )
    if exitcode != 0:
        print(
            "Failed to change resolution to {0} bit. "
            "You might have to be root to change the resolution".format(resolution)
        )
        return False

    if persist:
        exitcode = subprocess.call(
            "echo 0 > {0}".format(sensorpath), shell=True
        )
        if exitcode != 0:
            print(
                "Failed to write resolution configuration to sensor EEPROM"
            )
        return False
    return True
            
            
def get_resolution(sensor):
    data = raw_temperature(sensor)
    print(data)
    

GPIO.setmode(GPIO.BOARD)

# Fan setup
GPIO.setup(12, GPIO.OUT)  # Set GPIO pin 12 to output mode.
fan_PWM = GPIO.PWM(12, 25000)  

# Button setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

# Heater setup
GPIO.setup(13, GPIO.OUT)
heater_PWM = GPIO.PWM(13, 100)   # Initialize PWM on pwmPin 100Hz frequency

# Peltier setup
GPIO.setup(15, GPIO.OUT)
peltier_PWM = GPIO.PWM(15, 100)

initial_button_state = GPIO.input(10)
if initial_button_state == 1:
    button_click_counter += 1

# PWMs start
fan_PWM.start(100)                      # Start PWM with 0% duty cycle
peltier_PWM.start(0)
heater_PWM.start(100)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((IP, PORT))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_HIGH\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_LOW\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT FAN_SPEED\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT CPU_POWER\n", 'utf-8'))
    initial_timestamp = time.time()
    GPIO.add_event_detect(10, GPIO.BOTH, callback=lambda channel: button_callback(channel, initial_timestamp), bouncetime=500) # Setup event on pin 10 rising edge
    devices = get_temperature_sensors()
    for device in devices:
        if not set_resolution(DEVICE_FOLDER + device + DEVICE_SUFFIX, 11):
            print("Fail to set resolution!")
    while True:
        timestamp = time.time() - initial_timestamp
        for idx in range(0, len(devices)):
            temperature = read_temperature(devices[idx], "Thermometer_%d" % idx)
            if idx == 0:
                # Control fan
                step = temperature / 10 # 5 steps control from 20 to 100 degrees
                fan_PWM.ChangeDutyCycle(step / 10 * 100)
                s.sendall(bytes("DATA FAN_SPEED %f %f\n" % (3000 / 10 * step, timestamp), 'utf-8'))
                # Temperature package
                print("TEMPERATURE_LOW value: %f" % (temperature))
                s.sendall(bytes("DATA TEMPERATURE_LOW %f %f\n" % (temperature, timestamp), 'utf-8'))
            elif idx == 1:
                print("TEMPERATURE_HIGH value: %f" % (temperature))
                s.sendall(bytes("DATA TEMPERATURE_HIGH %f %f\n" % (temperature, timestamp), 'utf-8'))
            else:
                s.sendall(bytes("DATA TEMPERATURE %f %f\n" % (temperature, timestamp), 'utf-8'))

