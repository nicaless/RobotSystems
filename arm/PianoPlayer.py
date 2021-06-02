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
        if not end_queue.empty():
            print(end_queue.get())
            break

        print('Available Notes: ')
        print(tracker.key_map.keys())

        note = input('Enter note(s) to play: ')
        
        if note == 'q':
            break

        input_queue.put({'play': note})

    input_queue.put('END')


def display(tracker, end_queue, box_queue):
    while True:
        if not end_queue.empty():
            break
        img = tracker.get_frame()
        if img is not None:
            if not box_queue.empty():
                box_info = box_queue.get()
                box = box_info['box']
                key = box_info['key']
                cv2.drawContours(img, [box], -1, (0, 0, 200), 2)
                cv2.putText(img, key,
                            (min(box[0, 0], box[2, 0]), box[2, 1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1)

            cv2.imshow('Keyboard', img)
            key = cv2.waitKey(1)

            if key == ESCAPE_KEY:
                break

    tracker.camera_close()
    cv2.destroyAllWindows()


def process_note(tracker, input_queue, coords_queue, box_queue):
    while True:
        if input_queue.empty():
            continue
        note = input_queue.get()
        if note == 'END':
            break
        if note == 'rest':
            coords_queue.put('rest')
        else:
            box, coords, key = tracker.get_key_pos(note)
            coords_queue.put({'coords': coords})

    box_queue.put({'box': box, 'key': key})
    coords_queue.put('END')



def play(controller, coords_queue):
    previous_coords = None
    while True:
        if coords_queue.empty():
            continue
        coords = coords_queue.get()
        if coords == 'END':
            break
        
        if coords == 'rest':
            controller.play_rest(previous_coords)
        else:
            controller.play_key(coords['coords'])
            previous_coords = coords['coords']

    controller.initial_position()


def printer(my_queue):
    while True:
        if my_queue.empty():
            continue
        print('PRINTING')
        item = my_queue.get()
        print(item)
        if item == 'END':
            break


if __name__ == '__main__':
    arm = ArmIK()
    controller = ArmController(arm, Board)
    controller.close(full=True)

    tracker = PianoTracker()
    tracker.calibrate()

    tracker.camera_open()
    _, coords = tracker.get_key_pos('c1')
    controller.play_rest(coords)

    end_queue = Queue()
    input_queue = Queue()
    coords_queue = Queue()
    box_queue = Queue()
    
    input_queue.put('c1')
    #input_queue.put('rest')
    input_queue.put('e1')
    input_queue.put('g1')
    input_queue.put('END')

    p1 = Process(target=user_input,
                 args=(tracker, input_queue, end_queue))
    #p1 = Process(target=display,
    #             args=(tracker, end_queue))
    p2 = Process(target=process_note,
                 args=(tracker, input_queue, coords_queue, box_queue))
    p3 = Process(target=play,
                 args=(controller, coords_queue))
    p4 = Process(target=printer,
                 args=(coords_queue,))

    #p1.start()
    p2.start()
    #p4.start()
    time.sleep(1)
    p3.start()

    #user_input(tracker, input_queue, end_queue)
    display(tracker, end_queue, box_queue)
    
    controller.initial_position()






