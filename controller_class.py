"""
controller_class.py
Written Nicole Fronda - April 2021

Moves PiCar along a line given processed data from an Interpreter class
"""

import logging
from logdecorator import log_on_start, log_on_end, log_on_error
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


class Controller:
    def __init__(self, picarx_obj, scale=10, logging_on=False):
        """
        :param picarx_obj: PiCarX object, the PiCar to control
        :param scale: int, scaling factor for steering angle
        :param logging_on: bool, whether or not to enable ERROR message logging
        """
        self.pi = picarx_obj
        self.scale = scale
        self.logging = logging_on
        if self.logging:
            self.toggle_logging()

    def toggle_logging(self):
        if self.logging:
            logging.getLogger().setLevel(logging.ERROR)
            self.logging = False
        else:
            logging.getLogger().setLevel(logging.DEBUG)
            self.logging = True

    @log_on_start(logging.DEBUG, "BEGIN Controller.turn_to_line")
    @log_on_end(logging.DEBUG, "END Controller.turn_to_line")
    @log_on_error(logging.ERROR, "ERROR Controller.turn_to_line {e!r}")
    def turn_to_line(self, rel_line_pos, scale=None, delay=50):
        """
        Given relative line position, turn towards the line
        :param rel_line_pos: int [-1, 1] relative offset of the
            line from the PiCar (positive values indicate line is to the right)
        :param scale: int, scaling factor for steering angle.
            If None, the class default is used
        :param delay: int, ms to wait after turning
        :return: int, steering angle
        """
        if rel_line_pos is None:
            self.pi.stop()
            return None
        scale = self.scale if scale is None else scale
        steering_angle = rel_line_pos * scale
        self.pi.set_dir_servo_angle(steering_angle)
        self.pi.delay(delay)
        return steering_angle

    @log_on_start(logging.DEBUG, "BEGIN Controller.turn_to_angle")
    @log_on_end(logging.DEBUG, "END Controller.turn_to_angle")
    @log_on_error(logging.ERROR, "ERROR Controller.turn_to_angle {e!r}")
    def turn_to_angle(self, angle, scale=None, delay=50):
        """
        Given angle of line from center of camera frame, turn towards the line
        :param angle: int, angle offset of the line from the PiCar center
            (positive values indicate line is to the right)
        :param scale: int, scaling factor for steering angle.
            If None, the class default is used
        :param delay: int, ms to wait after turning
        :return: int, steering angle
        """
        if angle is None:
            self.pi.stop()
            return None
        scale = self.scale if scale is None else scale
        steering_angle = angle * scale
        self.pi.set_dir_servo_angle(steering_angle)
        self.pi.delay(delay)
        return steering_angle

    def consume_control_input(self, bus, delay, **kwargs):
        """
        Reads control input readings from a bus at delay intervals.
        Acts upon the readings depending on the type of reading.

        :param bus: Bus object, the bus to read from
        :param delay: Bus object, the bus to write to
        :param kwargs: Any other optional args for control functions
        :return: int, steering angle
        """
        while True:
            time.sleep(delay)
            control_input = bus.read()
            if control_input is None:
                pass
            if bus.message_type == 'rel_line_pos':
                return self.turn_to_line(control_input, **kwargs)
            else:
                return self.turn_to_angle(control_input, **kwargs)
