import atexit
import cv2
import logging
from logdecorator import log_on_start, log_on_end, log_on_error
import numpy as np
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
                self._set_motor_speed(self.LEFT_MOTOR, max([v1, v2]))
                self._set_motor_speed(self.RIGHT_MOTOR, min([v1, v2]))
            else:
                self._set_motor_speed(self.RIGHT_MOTOR, max([v1, v2]))
                self._set_motor_speed(self.LEFT_MOTOR, min([v1, v2]))

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
    def __init__(self, logging_on=False):
        self.adc = [ADC('A0'), ADC('A1'), ADC('A2')]
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
        # sensor returns high value for lighter value
        # 200-500 black, 1100-1200 for white
        return [adc.read() for adc in self.adc]

    def get_camera_frame(self):
        _, frame = self.cam.read()
        return frame

    def get_sensor_reading(self, sensor_type='photosensor'):
        if sensor_type == 'photosensor':
            return self.get_adc_values()
        else:
             return self.get_camera_frame()


class PhotoSensorInterpreter:
    def __init__(self, sensitivity=50, polarity=1, logging_on=False):
        '''

        :param sensitivity: fine tune difference between line and floor
        :param polarity: [-1, 1],
            1 is line is darker than floor (or floor is really light colored)
            -1 is line is lighter than floor (or floor is really dark colored)
        '''

        self.logging = logging_on
        if self.logging:
            self.toggle_logging()
        self.LEFT = 0
        self.MID = 1
        self.RIGHT = 2
        self.sensitivity = sensitivity
        self.polarity = polarity

    def toggle_logging(self):
        if self.logging:
            logging.getLogger().setLevel(logging.ERROR)
            self.logging = False
        else:
            logging.getLogger().setLevel(logging.DEBUG)
            self.logging = True

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
            if (target > (adv_values[sensor_id] + self.sensitivity)) or \
                    (target > (adv_values[sensor_id] - self.sensitivity)):
                return 1
            else:
                return 0
        else:
            # if line is line than floor, want target value to be lower than
            # measured value
            if (target < (adv_values[sensor_id] - self.sensitivity)) or \
                    (target < adv_values[sensor_id] - self.sensitivity):
                return 1
            else:
                return 0


class ColorInterpreter:
    def __init__(self, logging_on=False):
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

    @log_on_error(logging.ERROR, "ERROR Interpreter._get_line_segments {e!r}")
    def _get_line_segments(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # TODO: move hardcoded values to class constants or parameters
        # create mask for line
        mask = cv2.inRange(hsv,
                           np.array([50, 80, 20]),
                           np.array([100, 120, 50]))

        # edge detection
        edges = cv2.Canny(mask, 200, 400)

        # crop edges
        height, width = edges.shape
        fill_mask = np.zeros_like(edges)
        polygon = np.array([[(0, 0.5 * height),
                             (width, 0.5 * height),
                             (width, height),
                             (0, height)]], np.int32)
        cv2.fillPoly(fill_mask, polygon, 255)
        cropped_edges = cv2.bitwise_and(edges, fill_mask)

        line_segments = cv2.HoughLinesP(cropped_edges, 1, np.pi / 180, 10,
                                        np.array([]), minLineLength=8,
                                        maxLineGap=4)

        return line_segments

    @log_on_error(logging.ERROR, "ERROR Interpreter._get_line_segments {e!r}")
    def _make_points(self, frame, line):
        height, width, _ = frame.shape
        slope, intercept = line
        y1 = height  # bottom of the frame
        y2 = int(y1 * 1 / 2)  # make points from middle of the frame down

        # bound the coordinates within the frame
        x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
        x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
        return [[x1, y1, x2, y2]]

    @log_on_error(logging.ERROR, "ERROR Interpreter._get_avg_slope_intercept {e!r}")
    def _average_slope_intercept(self, frame, line_segments):
        """
        This function combines line segments into one or two lane lines
        If all line slopes are < 0: then we only have detected left lane
        If all line slopes are > 0: then we only have detected right lane
        """
        lane_lines = []
        if line_segments is None:
            logging.info('No line_segment segments detected')
            return lane_lines

        height, width, _ = frame.shape
        left_fit = []
        right_fit = []

        boundary = 1 / 3
        left_region_boundary = width * (
        1 - boundary)  # left lane line segment should be on left 2/3 of the screen
        right_region_boundary = width * boundary  # right lane line segment should be on left 2/3 of the screen

        for line_segment in line_segments:
            for x1, y1, x2, y2 in line_segment:
                if x1 == x2:
                    continue
                fit = np.polyfit((x1, x2), (y1, y2), 1)
                slope = fit[0]
                intercept = fit[1]
                if slope < 0:
                    if x1 < left_region_boundary and x2 < left_region_boundary:
                        left_fit.append((slope, intercept))
                else:
                    if x1 > right_region_boundary and x2 > right_region_boundary:
                        right_fit.append((slope, intercept))

        left_fit_average = np.average(left_fit, axis=0)
        if len(left_fit) > 0:
            lane_lines.append(self._make_points(frame, left_fit_average))

        right_fit_average = np.average(right_fit, axis=0)
        if len(right_fit) > 0:
            lane_lines.append(self._make_points(frame, right_fit_average))

        return lane_lines


    @log_on_start(logging.DEBUG, "BEGIN Interpreter.relative_line_position")
    @log_on_end(logging.DEBUG, "END Interpreter.relative_line_position")
    @log_on_error(logging.ERROR, "ERROR Interpreter.relative_line_position {e!r}")
    def steering_angle(self, frame):
        lane_lines = self._get_line_segments(frame)
        height, width, _ = frame.shape
        lane_line = lane_lines[0]  # only using first line
        x1, _, x2, _ = lane_line
        x_offset = (x2 - x1)
        y_offset = int(height / 2)

        angle_to_mid_radian = math.atan(x_offset / y_offset)
        angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / np.pi)
        steering_angle = angle_to_mid_deg + 90
        return steering_angle


class Controller:
    def __init__(self, picarx_obj, scale=10, logging_on=False):
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
        if rel_line_pos is None:
            self.pi.stop()
            return None
        scale = self.scale if scale is None else scale
        steering_angle = rel_line_pos * scale
        self.pi.set_dir_servo_angle(steering_angle)
        self.pi.delay(delay)
        return steering_angle

    def turn_to_angle(self, angle, scale=None, delay=50):
        scale = self.scale if scale is None else scale
        steering_angle = angle * scale
        self.pi.set_dir_servo_angle(steering_angle)
        self.pi.delay(delay)
        return steering_angle
