#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
from ArmController import ArmController
import cv2
import HiwonderSDK.Board as Board
from PianoTracker import PianoTracker
from rossros import Bus, Consumer, Producer, Timer
from rossros import runConcurrently

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)


tracker = PianoTracker()

### SET UP TIMER
timer_bus = Bus(name='timer bus')
timer = Timer(timer_bus, delay=5)


### THREAD FOR GETTING IMAGES
img_bus = Bus(name='Image Bus')
img_producer = Producer(tracker.get_frame, img_bus,
                        delay=0, termination_busses=[timer_bus])

### THREAD FOR DISPLAYING IMAGES
def display(img):
    cv2.imshow('Keyboard', img)
img_consumer = Consumer(display, img_bus,
                        delay=0, termination_busses=[timer_bus])

note_bus = Bus(name='Note Bus')
def get_notes(tracker):
    print('Available Notes: ')
    print(tracker.key_map.values())

    note = input('Enter note(s) to play: ')

    return note


def display_key(tracker, note):
    img = tracker.latest_img
    box, coords = tracker.get_key_pos(note)

    # TEST DRAW BOX
    cv2.drawContours(img, [box], -1, (0, 0, 200), 2)
    cv2.imshow('Align Frame', img)
    cv2.putText(img, '(' + str(coords[0]) + ',' + str(coords[1]) + ')',
                (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1)


### FULL THREAD LIST
thread_list = [timer, img_producer, img_consumer]


if __name__ == '__main__':
    tracker.calibrate()
    runConcurrently()





