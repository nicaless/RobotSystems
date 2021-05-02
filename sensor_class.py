"""
sensor_class.py
Written Nicole Fronda - April 2021

Produces readings for the sensors on the PiCar
"""

import cv2
import logging
from threading import Lock
import time


try:
    from ezblock import ADC
    from ezblock import __reset_mcu__
    __reset_mcu__()
    time.sleep(0.01)
except ImportError:
    print('This computer does not appear to be a PiCar -X system (/opt/ezblock '
          'is not present). Shadowing hardware call swith substitute functions')
    from sim_ezblock import *

'''BEGIN LOGGING SETUP'''
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO,
                    datefmt ="%H:%M:%S")
'''END LOGGING SETUP'''


class Sensor:
    def __init__(self, logging_on=False):
        self.adc = [ADC('A0'), ADC('A1'), ADC('A2')]
        self.ultrasonic_trig = Pin('D0')
        self.ultrasonic_echo = Pin('D1')
        self.logging = logging_on
        self.cam = cv2.VideoCapture(0)
        if self.logging:
            self.toggle_logging()

    def toggle_logging(self):
        if self.logging:
            logging.getLogger().setLevel(logging.ERROR)
            self.logging = False
        else:
            logging.getLogger().setLevel(logging.DEBUG)
            self.logging = True

    def get_adc_values(self):
        """
        sensor returns high value for lighter value
        approximately (200-500 black, 1100-1200 for white)
        :return: list of three ADC values
        """
        return [adc.read() for adc in self.adc]

    def get_collision_distance(self, timeout=0.02):
        """
        returns distance of closest object using ultrasonic sensor

        code largely taken from ezblock/modules.py

        :return: int, distance in cm from closest object ahead
        """
        # trig step (not entirely sure the purpose of this step, to initiate the reading?)
        self.ultrasonic_trig.low()
        time.sleep(0.01)
        self.ultrasonic_trig.high()
        time.sleep(0.00001)
        self.ultrasonic_trig.low()

        # get pulse measurements using the echo sensor
        pulse_end = 0
        pulse_start = 0

        start = time.time()
        while self.ultrasonic_echo.value() == 0:
            pulse_start = time.time()
            if pulse_start - start > timeout:
                return -1
        while self.ultrasonic_echo.value() == 1:
            pulse_end = time.time()
            if pulse_end - start > timeout:
                return -1
        duration = pulse_end - pulse_start
        cm = round((duration * 340) / 200, 2)

        return cm

    def get_camera_frame(self):
        """
        Wrapper around camera.read() from cv2 to return current frame
        :return: frame, matrix of pixel values
        """
        _, frame = self.cam.read()
        return frame

    def get_sensor_reading(self, sensor_type='photosensor'):
        """
        Wrapper function to get sensor readings from provided sensor_type,
        (defaults to photosensor)
        :param sensor_type: string, the sensor from which to get a reading
        :return: sensor value
        """
        if sensor_type == 'photosensor':
            return self.get_adc_values()
        elif sensor_type == 'ultrasonic':
            return self.get_collision_distance()
        else:
             return self.get_camera_frame()

    def produce_readings(self, bus, delay, sensor_type='photosensor'):
        """
        Writes sensor readings to a bus at delay intervals

        :param bus: Bus object, the bus to write to
        :param delay: int, seconds between writes to bus
        :param sensor_type: string, the sensor from which to get readings
        :return: None
        """
        lock = Lock()
        while True:
            time.sleep(delay)
            with lock:
                readings = self.get_sensor_reading(sensor_type=sensor_type)
            bus.write(readings)
