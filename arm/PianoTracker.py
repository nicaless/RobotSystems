import sys
sys.path.append('/home/pi/ArmPi/')
from ArmIK.Transform import convertCoordinate, getCenter, getMaskROI, getROI
import Camera
from CameraCalibration.CalibrationConfig import square_length
import cv2
from LABConfig import color_range
import logging
import math
import numpy as np

DEBUG = logging.DEBUG
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO,
                    datefmt ="%H:%M:%S")

ESCAPE_KEY = 27
SIZE = (640, 480)


class PianoTracker:
    def __init__(self):
        self.camera = Camera.Camera()
        self.img_h = None
        self.img_w = None
        self.white_key_width = None
        self.white_key_bottom = None
        self.black_key_bottom = None
        self.key_top = None

        self.key_map = {
            'c1': 1, 'd1': 2, 'e1': 3, 'f1': 4, 'g1': 5, 'a1': 6, 'b1': 7,
            'c2': 8, 'd2': 9, 'e2': 10
        }

    def calibrate(self):
        """
        Line up the piano keys
        :return: None
        """
        self.camera.camera_open()
        while True:
            img = self.camera.frame
            if img is not None:
                img_h, img_w = img.shape[:2]

                white_key_width = int(img_w / 10)
                white_key_bottom = int(img_h / 8)
                black_key_bottom = img_h - int(img_h / 3)
                key_top = img_h - white_key_bottom

                # Draw All Keys
                for i in self.key_map.values():
                    cv2.line(img, (white_key_width*i, key_top),
                            (white_key_width*i, white_key_bottom),
                            (0, 0, 200), 1)

                cv2.line(img, (0, black_key_bottom),
                               (img_w, black_key_bottom),
                               (0, 0, 200), 1)

                # TEST
                self.img_h = img_h
                self.img_w = img_w
                self.white_key_width = white_key_width
                self.white_key_bottom = white_key_bottom
                self.black_key_bottom = black_key_bottom
                self.key_top = key_top
                self.get_key_pos(img, 'c1')

                cv2.imshow('Align Frame', img)
                key = cv2.waitKey(1)
                if key == ESCAPE_KEY:
                    break

        self.img_h = img_h
        self.img_w = img_w
        self.white_key_width = white_key_width
        self.white_key_bottom = white_key_bottom
        self.black_key_bottom = black_key_bottom
        self.key_top = key_top

        self.camera.camera_close()
        cv2.destroyAllWindows()

    def get_key_pos(self, img, key):
        key_pos = self.key_map[key]
        key_rect_left = self.white_key_width * key_pos - self.white_key_width
        key_rect_right = key_rect_left + self.white_key_width

        # only playing white keys right now
        key_top = self.black_key_bottom
        key_bottom = self.img_h - self.white_key_bottom

        top_left = (key_rect_left, key_top)
        top_right = (key_rect_right, key_top)
        bottom_left = (key_rect_left, key_bottom)
        bottom_right = (key_rect_right, key_bottom)

        rect = cv2.minAreaRect(np.array([top_left, top_right, bottom_left, bottom_right]))
        box = np.int0(cv2.boxPoints(rect))

        # TEST DRAW BOX
        cv2.drawContours(img, [box], -1, (0, 0, 200), 2)




if __name__ == '__main__':
    tracker = PianoTracker()
    tracker.calibrate()
