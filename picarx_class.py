import atexit
import logging
from logdecorator import log_on_start, log_on_end, log_on_error
import time

try:
    from ezblock import *
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

class PiCarX:
    def __init__(self, logging_on=False):
        self.logging = logging_on
        if self.logging:
            self.toggle_logging()
        self.LEFT_MOTOR = 0
        self.RIGHT_MOTOR = 1

        atexit.register(self.cleanup)

        self._calibration_angle = 0
        self._period = 4095
        self._timeout = 0.02
        self._vehicle_width = 7

        self._dir_servo_pin = Servo(PWM('P2'))
        self._camera_servo_pin1 = Servo(PWM('P0'))
        self._camera_servo_pin2 = Servo(PWM('P1'))
        self._left_rear_pwm_pin = PWM("P13")
        self._right_rear_pwm_pin = PWM("P12")
        self._left_rear_dir_pin = Pin("D4")
        self._right_rear_dir_pin = Pin("D5")

        self._Servo_dir_flag = 1
        self._dir_cal_value = 0
        self._cam_cal_value_1 = 0
        self._cam_cal_value_2 = 0
        self._motor_direction_pins = [self._left_rear_dir_pin,
                                      self._right_rear_dir_pin]
        self._motor_speed_pins = [self._left_rear_pwm_pin,
                                  self._right_rear_pwm_pin]
        self._cali_dir_value = [1, -1]
        self._cali_speed_value = [0, 0]

        for pin in self._motor_speed_pins:
            pin.period(self._period)

    def toggle_logging(self):
        if self.logging:
            logging.getLogger().setLevel(logging.ERROR)
            self.logging = False
        else:
            logging.getLogger().setLevel(logging.DEBUG)
            self.logging = True

    @staticmethod
    def delay(ms):
        time.sleep(ms / 1000)

    @log_on_start(logging.DEBUG, "BEGIN cleanup")
    @log_on_end(logging.DEBUG, "END cleanup")
    @log_on_error(logging.ERROR, "ERROR backward {e!r}")
    def cleanup(self):
        self.stop()

    @log_on_error(logging.ERROR, "ERROR backward {e!r}")
    def backward(self, speed, turn_angle=0):
        if turn_angle == 0:
            self._set_motor_speed(self.LEFT_MOTOR, speed)
            self._set_motor_speed(self.RIGHT_MOTOR, speed)
        else:
            v1 = speed
            r = (speed * 360) / (turn_angle * 2 * 3.14)
            vehicle_width = self._vehicle_width
            v2 = v1 * (r / vehicle_width + 1) / (r / vehicle_width - 1)
            if turn_angle > 0:
                self._set_motor_speed(self.LEFT_MOTOR, -1 * max([v1, v2]))
                self._set_motor_speed(self.RIGHT_MOTOR, -1 * min([v1, v2]))
            else:
                self._set_motor_speed(self.RIGHT_MOTOR, -1 * max([v1, v2]))
                self._set_motor_speed(self.LEFT_MOTOR, -1 * min([v1, v2]))

    @log_on_error(logging.ERROR, "ERROR forward {e!r}")
    def forward(self, speed, turn_angle=0):
        if turn_angle == 0:
            self._set_motor_speed(self.LEFT_MOTOR, -1 * speed)
            self._set_motor_speed(self.RIGHT_MOTOR, -1 * speed)
        else:
            v1 = speed
            r = (speed * 360) / (turn_angle * 2 * 3.14)
            vehicle_width = self._vehicle_width
            v2 = v1 * (r / vehicle_width + 1) / (r / vehicle_width - 1)
            if turn_angle > 0:
                self._set_motor_speed(self.LEFT_MOTOR, -1 * max([v1, v2]))
                self._set_motor_speed(self.RIGHT_MOTOR, -1 * min([v1, v2]))
            else:
                self._set_motor_speed(self.RIGHT_MOTOR, -1 * max([v1, v2]))
                self._set_motor_speed(self.LEFT_MOTOR, -1 * min([v1, v2]))

    @log_on_error(logging.ERROR, "ERROR stop {e!r}", reraise=True)
    def stop(self):
        self._set_motor_speed(self.LEFT_MOTOR, 0)
        self._set_motor_speed(self.RIGHT_MOTOR, 0)
        self.set_dir_servo_angle(self._calibration_angle)

    def set_dir_servo_angle(self, value):
        self._dir_servo_pin.angle(value + self._dir_cal_value)

    def _dir_servo_angle_calibration(self, value):
        self._dir_cal_value = value
        self.set_dir_servo_angle(self._dir_cal_value)

    def _set_motor_speed(self, motor, speed):
        if speed >= 0:
            direction = 1 * self._cali_dir_value[motor]
        else:
            direction = -1 * self._cali_dir_value[motor]
        speed = abs(speed)

        if speed != 0:
            speed = int(speed / 2) + 50

        speed = speed - self._cali_speed_value[motor]
        if direction < 0:
            self._motor_direction_pins[motor].high()
            self._motor_speed_pins[motor].pulse_width_percent(speed)
        else:
            self._motor_direction_pins[motor].low()
            self._motor_speed_pins[motor].pulse_width_percent(speed)

    def _motor_speed_calibration(self, value):
        self._cali_speed_value = value
        if value < 0:
            self._cali_speed_value[0] = 0
            self._cali_speed_value[1] = abs(self._cali_speed_value)
        else:
            self._cali_speed_value[0] = abs(self._cali_speed_value)
            self._cali_speed_value[1] = 0

    def _motor_direction_calibration(self, motor, value):
        # 0: positive direction
        # 1: negative direction
        if value == 1:
            self._cali_dir_value[motor] = -1 * self._cali_dir_value[motor]

    def _set_power(self, speed):
        self._set_motor_speed(self.LEFT_MOTOR, speed)
        self._set_motor_speed(self.RIGHT_MOTOR, speed)


class Sensor:
    def __init__(self):
        self.adc = [ADC('A0'), ADC('A1'), ADC('A2')]

    @log_on_error(logging.ERROR, "ERROR Sensor.get_adc_values {e!r}")
    def get_adc_values(self):
        # sensor returns high value for lighter value
        # 200-500 black, 1100-1200 for white
        return [adc.read() for adc in self.adcs]

class Interpreter:
    def __init__(self, sensitivity=50, polarity=1):
        '''

        :param sensitivity: fine tune difference between line and floor
        :param polarity: [-1, 1],
            1 is line is darker than floor (or floor is really light colored)
            -1 is line is lighter than floor (or floor is really dark colored)
        '''
        self.LEFT = 0
        self.MID = 1
        self.RIGHT = 2
        self.sensitivity = sensitivity
        self.polarity = polarity

    @log_on_start(logging.DEBUG, "BEGIN Interpreter.relative_line_position")
    @log_on_end(logging.DEBUG, "END Interpreter.relative_line_position")
    @log_on_error(logging.ERROR, "ERROR Interpreter.relative_line_position {e!r}")
    def relative_line_position(self, adv_values, target=300):
        '''
        get direction to turn towards, scaled by line offset,
        line offset is avg % difference from target of
        channels with sighted target

        :param adv_values: from sensor object
        :param target: the
        :return:
        '''
        target_locs = self._find_target(adv_values, target)
        if target_locs == [0, 1, 0] or target_locs == [1, 1, 1]:
            direction = 0
        elif target_locs == [1, 0, 0] or target_locs == [1, 1, 0]:
            direction = -1
        elif target_locs == [0, 0, 1] or target_locs == [0, 1, 1]:
            direction = 1
        else:
            return None

        diffs = []
        for i, v in enumerate(adv_values):
            if target_locs[i] == 1:
                diffs.append(abs(target - v) / self.sensitivity)
        offset = min(1, sum(diffs) / len(diffs))

        return direction * offset

    @log_on_error(logging.ERROR, "ERROR Interpreter._find_target {e!r}")
    def _find_target(self, adv_values, target):
        left = self._sensor_sees_target(self.LEFT, adv_values, target)
        mid = self._sensor_sees_target(self.MID, adv_values, target)
        right = self._sensor_sees_target(self.RIGHT, adv_values, target)
        return [left, mid, right]

    @log_on_start(logging.DEBUG, "BEGIN Interpreter._sensor_sees_target")
    @log_on_end(logging.DEBUG, "END Interpreter._sensor_sees_target")
    @log_on_error(logging.ERROR, "ERROR Interpreter._sensor_sees_target {e!r}")
    def _sensor_sees_target(self, sensor_id, adv_values, target):
        if self.polarity == 1:
            # if line is darker than floor, want target value to be higher than
            # measured value
            if target > (adv_values[sensor_id] + self.sensitivity):
                return 1
            else:
                return 0
        else:
            # if line is line than floor, want target value to be lower than
            # measured value
            if target < (adv_values[sensor_id] - self.sensitivity):
                return 1
            else:
                return 0


class Controller:
    def __init__(self, picarx_obj, scale=10):
        self.pi = picarx_obj
        self.scale = scale

    @log_on_start(logging.DEBUG, "BEGIN Controller.turn_to_line")
    @log_on_end(logging.DEBUG, "END Controller.turn_to_line")
    @log_on_error(logging.ERROR, "ERROR Controller.turn_to_line {e!r}")
    def turn_to_line(self, rel_line_pos, scale=None):
        if rel_line_pos is None:
            self.pi.stop()
            return 0
        scale = self.scale if scale is None else scale
        steering_angle = rel_line_pos * scale
        self.pi.set_dir_servo_angle(steering_angle)
        return steering_angle











