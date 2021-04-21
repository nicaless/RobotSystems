import cv2
import logging
from logdecorator import log_on_start, log_on_end, log_on_error
import math
import numpy as np
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


class PhotoSensorInterpreter:
    def __init__(self, sensitivity=50, polarity=1, target=300,
                 logging_on=False):
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
        self.target = target

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
    def relative_line_position(self, adv_values):
        '''
        get direction to turn towards, scaled by line offset,
        line offset is avg % difference from target of
        channels with sighted target

        :param adv_values: from sensor object
        :return:
        '''
        target_locs = self._find_target(adv_values, self.target)
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
                diffs.append(abs(self.target - v) / self.sensitivity)
        offset = min(1, sum(diffs) / len(diffs))

        return direction * offset

    def consume_sensor_produce_control(self, sensor_bus, control_bus, delay):
        lock = Lock()
        while True:
            time.sleep(delay)
            with lock:
                sensor_reading = sensor_bus.read()
            rel_line_pos = self.relative_line_position(sensor_reading)
            control_bus.write(rel_line_pos)

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

    @log_on_start(logging.DEBUG, "BEGIN Interpreter.relative_line_position")
    @log_on_end(logging.DEBUG, "END Interpreter.relative_line_position")
    @log_on_error(logging.ERROR, "ERROR Interpreter.relative_line_position {e!r}")
    def steering_angle(self, frame):
        lane_lines = self._get_line_segments(frame)
        # return None if no lanes detected
        if len(lane_lines) == 0:
            return None
        height, width, _ = frame.shape
        lane_line = lane_lines[0]  # only using first line
        x1, _, x2, _ = lane_line
        x_offset = (x2 - x1)
        y_offset = int(height / 2)

        angle_to_mid_radian = math.atan(x_offset / y_offset)
        angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / np.pi)
        steering_angle = angle_to_mid_deg + 90
        return steering_angle

    def consume_sensor_produce_control(self, sensor_bus, control_bus, delay):
        while True:
            time.sleep(delay)
            sensor_reading = sensor_bus.read()
            steering_angle = self.steering_angle(sensor_reading)
            control_bus.write(steering_angle)

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
