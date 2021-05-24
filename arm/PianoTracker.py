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
                white_key_bottom = int(img_h / 5)
                white_key_top = 5 * white_key_bottom

                # Draw All Keys
                for i in self.key_map.values():
                    cv2.line(img, (white_key_width*i, white_key_bottom),
                            (white_key_width*i, white_key_top),
                            (0, 0, 200), 1)

                cv2.imshow('Align Frame', img)
                key = cv2.waitKey(1)
                if key == ESCAPE_KEY:
                    break
        self.camera.camera_close()
        cv2.destroyAllWindows()



if __name__ == '__main__':
    tracker = PianoTracker()
    tracker.calibrate()
