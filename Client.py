import numpy as np
import socket
import functions 
import time
import RPi.GPIO as GPIO
import sys
import subprocess
from os import listdir, system


DEVICE_FOLDER = "/sys/bus/w1/devices/"
DEVICE_SUFFIX = "/w1_slave"
WAIT_INTERVAL = 0.005


Q_C0 = 12.16**2 / 15.6
T_CRITICAL = 30
CONTROL_TIME_FAN = 30
CONTROL_TIME_PELTIER = 30

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
    while not lines and len(lines) < 2 and lines[0].strip()[-3:] != 'YES':
        # If we haven't got a valid response, wait for the WAIT_INTERVAL
        # (seconds) and try 
        time.sleep(WAIT_INTERVAL)
        lines = raw_temperature()

    # Split out the raw temperature number
    temperature = lines[1].split('t=')[1]

    # Check that the temperature is not invalid
    if temperature != -1:
        temperature_celsius = round(float(temperature) / 1000.0, 2)
        
    return temperature_celsius


def button_callback(channel, initial_timestamp):
    print("Handling button interaption")
    global button_click_counter, CPU_power
    button_click_counter += 1
    GPIO.setup(19, GPIO.OUT)
    if button_click_counter % 2 == 0:
        GPIO.output(19, GPIO.HIGH)
        for level in range(6):
            timestamp = time.time() - initial_timestamp
            CPU_power = 60
            s.sendall(bytes("DATA CPU_POWER %f %f\n" % (60 / 5 * level, timestamp), 'utf-8'))
    elif button_click_counter % 2 == 1:
        GPIO.output(19, GPIO.LOW)
        for level in range(5, -1, -1):
            timestamp = time.time() - initial_timestamp
            CPU_power = 0
            s.sendall(bytes("DATA CPU_POWER %f %f\n" % (60 / 5 * level, timestamp), 'utf-8'))


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
    

def calculate_control_parameters(temperatures_hot, temperature_heatsink, timestamps, CPU_power, threshold, steps_number = 10):
    global control_process_start
    step = temperatures_hot[1] // 10
    fan_speed = 0
    peltier_voltage = 0
    current_control_time = time.time() - control_process_start
    if abs(temperatures_hot[1] - temperatures_hot[0]) / (timestamps[1] - timestamps[0]) > threshold and current_control_time > CONTROL_TIME_FAN:
        print("Temperature spikes detected")
        control_process_start = time.time()
        fan_speed = 3000
    elif abs(temperatures_hot[1] - temperatures_hot[0]) / (timestamps[1] - timestamps[0]) < threshold:
        fan_speed = 3000 * step / steps_number

    if current_control_time > CONTROL_TIME_FAN:
        control_process_start = 0

    if temperatures_hot[1] > T_CRITICAL:
        peltier_voltage = functions.U_static(Q_C0, temperatures_hot[1] + 273.15, temperature_heatsink + 273.15)
        # peltier_voltage = 12
        fan_speed = 3000
        if peltier_voltage > 12:
            peltier_voltage = 12
        print(f"Updated peltier voltage: {peltier_voltage}")
    return fan_speed, peltier_voltage


def calculate_peltier_voltage(temperatures, timestamps, threshold, steps_number = 10):
    global control_process_start
    step = temperatures[1] / 10
    if abs(temperatures[1] - temperatures[0]) / (timestamps[1] - timestamps[0]) > threshold:
        return 3000
    return 3000 * step / 10


GPIO.setmode(GPIO.BOARD)

# Fan setup
GPIO.setwarnings(False)
GPIO.setup(12, GPIO.OUT)  # Set GPIO pin 12 to output mode.
fan_PWM = GPIO.PWM(12, 25000)  

# Button setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

# Peltier setup
GPIO.setup(15, GPIO.OUT)
peltier_PWM = GPIO.PWM(15, 100)   # Initialize PWM on pwmPin 100Hz frequency
  
# Heater setup
GPIO.setup(19, GPIO.OUT)
GPIO.output(19, GPIO.HIGH)

initial_button_state = GPIO.input(10)
if initial_button_state == 1:
    button_click_counter += 1

# PWMs start
fan_PWM.start(0)                      # Start PWM with 0% duty cycle
peltier_PWM.start(10)

devices = get_temperature_sensors()

temperatures_hot = [0, read_temperature(devices[1], "Thermometer_%d" % 1)]
temperature_heatsink = 0
timestamps = [0, 0]
control_process_start = 0

CPU_power = 0


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((IP, PORT))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_CPU 20 60 9\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT TEMPERATURE_HEATSINK 20 60 9\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT FAN_SPEED 0 3000 11\n", 'utf-8'))
    s.sendall(bytes("ADD_PLOT CPU_POWER 0 60 2\n", 'utf-8'))
    initial_timestamp = time.time()
    GPIO.add_event_detect(10, GPIO.BOTH, callback=lambda channel: button_callback(channel, initial_timestamp), bouncetime=200) # Setup event on pin 10 rising edge

    for device in devices:
        if not set_resolution(DEVICE_FOLDER + device + DEVICE_SUFFIX, 11):
            print("Fail to set resolution!")
    while True:
        timestamp = time.time() - initial_timestamp
        for idx in range(0, len(devices)):
            temperature = read_temperature(devices[idx], "Thermometer_%d" % idx)
            if idx == 0:
                # Temperature package
                temperature_heatsink = temperature
                print("TEMPERATURE_HEATSINK value: %f" % (temperature))
                s.sendall(bytes("DATA TEMPERATURE_HEATSINK %f %f\n" % (temperature, timestamp), 'utf-8'))
            elif idx == 1:
                temperatures_hot[0], temperatures_hot[1] = temperatures_hot[1], temperature
                timestamps[0], timestamps[1] = timestamps[1], timestamp
                print("TEMPERATURE_CPU value: %f" % (temperature))
                s.sendall(bytes("DATA TEMPERATURE_CPU %f %f\n" % (temperature, timestamp), 'utf-8'))
            else:
                s.sendall(bytes("DATA TEMPERATURE %f %f\n" % (temperature, timestamp), 'utf-8'))
        # Control fan and peltier
        fan_speed, peltier_voltage = calculate_control_parameters(temperatures_hot, temperature_heatsink, timestamps, CPU_power, 1) # 5 steps control from 20 to 100 degrees
        fan_PWM.ChangeDutyCycle(fan_speed / 3000 * 100)
        peltier_PWM.ChangeDutyCycle(peltier_voltage / 12 * 100)
        s.sendall(bytes("DATA FAN_SPEED %f %f\n" % (fan_speed, timestamp), 'utf-8'))

