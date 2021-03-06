import sys
sys.path.append('/home/pi/ArmPi/')
from ArmController import ArmController
from ArmIK.ArmMoveIK import ArmIK
from ArmIK.Transform import convertCoordinate, getCenter, getMaskROI, getROI
import Camera
import cv2
import HiwonderSDK.Board as Board
import logging
import numpy as np
import time

ESCAPE_KEY = 27
SIZE = (640, 480)
KEY_LENGTH = 2


class PianoTracker:
    def __init__(self):
        self.camera = Camera.Camera()
        self.capture_mode = False
        self.img_h = None
        self.img_w = None
        self.white_key_width = None
        self.white_key_bottom = None
        self.black_key_bottom = None
        self.key_top = None
        self.latest_img = None

        self.key_map = {
            'c1': 1, 'd1': 2, 'e1': 3, 'f1': 4, 'g1': 5, 'a1': 6, 'b1': 7,
            'c2': 8, 'd2': 9, 'e2': 10
        }

    def camera_open(self):
        self.camera.camera_open()
        self.capture_mode = True

    def camera_close(self):
        self.camera.camera_close()
        self.capture_mode = False

    def get_frame(self):
        if self.capture_mode:
            self.latest_img = self.camera.frame
            return self.latest_img
        else:
            return None

    def calibrate(self):
        """
        Line up the piano keys
        :return: None
        """
        self.camera.camera_open()
        while True:
            img = self.camera.frame
            if img is not None:
                img_copy = img.copy()
                img_h, img_w = img.shape[:2]

                white_key_width = int(img_w / 10)
                white_key_bottom = int(img_h / 8)
                black_key_bottom = img_h - int(img_h / 3)
                key_top = img_h - white_key_bottom

                # Draw All Keys
                for i in self.key_map.values():
                    # TODO: I think key_top and key_bottom are swapped
                    cv2.line(img, (white_key_width*i, key_top),
                            (white_key_width*i, white_key_bottom),
                            (0, 0, 200), 1)

                cv2.line(img, (0, black_key_bottom),
                               (img_w, black_key_bottom),
                               (0, 0, 200), 1)

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
        self.latest_img = img_copy

        self.camera.camera_close()
        cv2.destroyAllWindows()

    def get_key_pos(self, key):            
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

        rect = cv2.minAreaRect(np.array([top_left, top_right,
                                         bottom_left, bottom_right]))
        box = np.int0(cv2.boxPoints(rect))
        roi = getROI(box)

        img_centerx, img_centery = getCenter(rect, roi, SIZE, KEY_LENGTH)
        world_x, world_y = convertCoordinate(img_centerx, img_centery, SIZE)
        coords = (world_x, world_y)

        return box, coords, key


if __name__ == '__main__':
    arm = ArmIK()
    controller = ArmController(arm, Board)
    controller.close(full=True)
    time.sleep(0.5)

    tracker = PianoTracker()
    tracker.calibrate()

    tracker.camera_open()
    # TODO BREAK THREAD ONCE ALL NOTES ARE PLAYED
    all_keys = ['rest', 'c1']
    beat = 0
    while True:
        img = tracker.get_frame()
        if img is not None:
            cv2.imshow('Keyboard', img)
            key = cv2.waitKey(1)
            if key == ESCAPE_KEY:
                break
            if beat < len(all_keys):
                if all_keys[beat] == 'rest':
                    box, coords = tracker.get_key_pos(all_keys[beat+1])
#                     cv2.imshow('Keyboard', img)
#                     key = cv2.waitKey(1)
#                     if key == ESCAPE_KEY:
#                         break
                    
                    controller.play_rest(coords)
                else:
                    box, coords = tracker.get_key_pos(all_keys[beat])

                    # DRAW BOX
#                     cv2.drawContours(img, [box], -1, (0, 0, 200), 2)
#                     cv2.imshow('Keyboard', img)
#                     cv2.putText(img, '(' + str(coords[0]) + ',' + str(coords[1]) + ')',
#                                  (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
#                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1)
#                     key = cv2.waitKey(1)
#                     if key == ESCAPE_KEY:
#                         break
                
                    controller.play_key(coords)
                beat += 1
                
#             key = cv2.waitKey(1)
#             if key == ESCAPE_KEY:
#                 break

    controller.initial_position()
    tracker.camera_close()
    cv2.destroyAllWindows()

