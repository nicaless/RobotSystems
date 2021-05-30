#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
from ArmController import ArmController
from ArmIK.ArmMoveIK import ArmIK
import cv2
import HiwonderSDK.Board as Board
from multiprocessing import Process, Queue
from one_item_queue import OneItemQueue
from PianoTracker import PianoTracker
import time


ESCAPE_KEY = 27


def user_input(tracker, input_queue, end_queue):
    while True:
        try:
            end = end_queue.get_nowait()
            if end == 'END':
                break
        except:
            continue

        print('Available Notes: ')
        print(tracker.key_map.values())

        note = input('Enter note(s) to play: ')

        input_queue.put({'play': note})

    input_queue.put('END')


def display(tracker, end_queue):
    while True:
        img = tracker.get_frame()
        if img is not None:
            cv2.imshow('Keyboard', img)
            key = cv2.waitKey(1)

            if key == ESCAPE_KEY:
                break

    end_queue.put('END')
    tracker.camera_close()
    cv2.destroyAllWindows()


def process_note(tracker, input_queue, coords_queue):
    while True:
        if input_queue.empty():
            continue
        note = input_queue.get()
        if note == 'END':
            break

        box, coords = tracker.get_key_pos(note)
        coords_queue.put({'coords': coords})

    coords_queue.put('END')



def play(controller, coords_queue):
    while True:
        if coords_queue.empty():
            continue
        coords = coords_queue.get()
        if coords == 'END':
            break

        controller.play_key(coords['coords'])

    controller.initial_position()


def print(queue):
    while True:
        if queue.empty():
            continue
        item = queue.get()
        print(item)


if __name__ == '__main__':
    arm = ArmIK()
    controller = ArmController(arm, Board)
    controller.close(full=True)

    tracker = PianoTracker()
    tracker.calibrate()

    tracker.camera_open()

    end_queue = OneItemQueue()
    input_queue = Queue()
    coords_queue = Queue()

    # p1 = Process(target=user_input,
    #              args=(tracker, input_queue, end_queue))
    p1 = Process(target=display,
                 args=(tracker, end_queue))
    p2 = Process(target=process_note,
                 args=(tracker, input_queue, coords_queue))
    p3 = Process(target=play,
                 args=(controller, coords_queue))
    p4 = Process(target=print,
                 args=(input_queue))

    p1.start()
    p4.start()

    user_input(tracker, input_queue, end_queue)






