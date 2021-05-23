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


class ColorTracker:
    def __init__(self):
        self.target_colors = []
        self.rects = {}
        self.rois = {}
        self.coords = {}
        self.camera = Camera.Camera()

    def set_target_colors(self, colors):
        if isinstance(colors, list):
            for c in colors:
                if c not in RGB_RANGE.keys():
                    raise ValueError('Unexpected Color')
                self.target_colors.append(colors)
        else:
            if colors not in RGB_RANGE.keys():
                raise ValueError('Unexpected Color')
            self.target_colors.append(colors)

    def reset(self):
        self.rects = {}
        self.rois = {}
        self.coords = {}

    def calibrate(self):
        """
        Waits for ESC key to confirm that camera is
        :return: None
        """
        self.camera.camera_open()
        while True:
            img = self.camera.frame
            if img is not None:
                img_h, img_w = img.shape[:2]
                cv2.line(img, (0, int(img_h / 2)),
                         (img_w, int(img_h / 2)),
                         (0, 0, 200), 1)
                cv2.line(img, (int(img_w / 2), 0),
                         (int(img_w / 2), img_h),
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


    def image_intake(self, img):
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        cv2.line(img, (0, int(img_h / 2)),
                 (img_w, int(img_h / 2)),
                 (0, 0, 200), 1)
        cv2.line(img, (int(img_w / 2), 0),
                 (int(img_w / 2), img_h),
                 (0, 0, 200), 1)

        return img, img_copy

    def pre_process(self, img_copy, roi=None):
        # RESIZE IMAGE, REDUCE IMAGE NOISE AND DETAIL TO ENABLE DETECTION
        frame_resize = cv2.resize(img_copy, SIZE,
                                  interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (11, 11), 11)

        # IF WE ALREADY HAVE AN ROI, BLACK OUT THE NEW FRAME EXCEPT FOR THE ROI
        if roi is not None:
            frame_gb = getMaskROI(frame_gb, roi, SIZE)

        # convert the image to LAB space
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)

        return frame_lab

    def detect_colors(self, frame_lab):
        color_contours = {}
        for c in self.target_colors:
            contours = self.find_contours(frame_lab, c)
            max_contour, max_contour_area = self.get_area_max_contour(contours)
            color_contours[c] = (max_contour, max_contour_area)
        return color_contours

    def post_process(self, img):
        detected_colors = self.rois.keys()

        assert detected_colors == self.rects.keys()

        for r in list(detected_colors):
            rect = self.rects[r]
            roi = self.rois[r]
            box = np.int0(cv2.boxPoints(rect))

            # get the center coordinates of block
            img_centerx, img_centery = getCenter(rect, roi,
                                                 SIZE, square_length)
            # convert to world coordinates
            world_x, world_y = convertCoordinate(img_centerx, img_centery,
                                                 SIZE)

            self.coords[r] = (world_x, world_y)

            # DRAW A BOX AROUND THE ROI AND DISPLAY THE REAL WORLD COORDINATES
            cv2.drawContours(img, [box], -1, RGB_RANGE[r], 2)
            cv2.putText(img, '(' + str(world_x) + ',' + str(world_y) + ')',
                        (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, RGB_RANGE[r], 1)

        return img

    def find_contours(self, frame_lab, color):
        frame_mask = cv2.inRange(frame_lab,
                                 color_range[color][0],
                                 color_range[color][1])
        # Opening (morphology)
        opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN,
                                  np.ones((6, 6), np.uint8))
        # Closing (morphology)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE,
                                  np.ones((6, 6), np.uint8))
        contours = cv2.findContours(closed, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_NONE)[-2]
        return contours

    def get_area_max_contour(self, contours):
        """
        copies getAreaMaxContour from the original ColorTracking.py code
        :param contours:
        :return:
        """
        max_contour = None
        max_contour_area = 0

        for c in contours:  # for all contours
            contour_area_temp = math.fabs(
                cv2.contourArea(c))  # calculate the contour area
            if contour_area_temp > max_contour_area:
                max_contour_area = contour_area_temp
                # only when the area is greater than 300,
                # the contour of the maximum area is effective to filter interference
                if contour_area_temp > 300:
                    max_contour = c

        return max_contour, max_contour_area  # return the max area contour

    def save_rois(self, color_contours):
        for color, contour_info in color_contours.items():
            contour = contour_info[0]
            contour_area = contour_info[1]
            if contour_area > AREA_THRESH:
                rect = cv2.minAreaRect(contour)
                self.rects[color] = rect
                box = np.int0(cv2.boxPoints(rect))
                roi = getROI(box)
                self.rois[color] = roi


if __name__ == '__main__':
    tracker = ColorTracker()
    tracker.set_target_colors('red')
    tracker.calibrate()
    tracker.track()
    tracker.set_target_colors('green')
    tracker.set_target_colors('blue')
    tracker.track()
