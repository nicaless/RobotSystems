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

AREA_THRESH = 2500
ESCAPE_KEY = 27
RGB_RANGE = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}
SIZE = (640, 480)


class PianoTracker:
    def __init__(self):
        self.camera = Camera.Camera()


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
                white_key_width = img_w / 10

                cv2.line(img, (0, img_h),
                         (img_w, img_h),
                         (0, 0, 200), 1)

                cv2.imshow('Align Frame', img)
                key = cv2.waitKey(1)
                if key == ESCAPE_KEY:
                    break
        self.camera.camera_close()
        cv2.destroyAllWindows()

    def track(self):
        self.camera.camera_open()
        while True:
            input_img = self.camera.frame
            if input_img is not None:
                img, img_copy = self.image_intake(input_img)
                frame_lab = self.pre_process(img_copy)
                color_contours = self.detect_colors(frame_lab)
                self.save_rois(color_contours)
                output_img = self.post_process(img)
                cv2.imshow('Frame', output_img)
                key = cv2.waitKey(1)
                if key == ESCAPE_KEY:
                    break
        self.camera.camera_close()
        cv2.destroyAllWindows()



if __name__ == '__main__':
    tracker = PianoTracker()
    tracker.calibrate()
