import sys
sys.path.append('/home/pi/ArmPi/')
from ArmIK.ArmMoveIK import ArmIK
from ArmIK.Transform import getAngle
from ColorTracker import ColorTracker
import HiwonderSDK.Board as Board
import logging
import time


DEBUG = logging.DEBUG
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO,
                    datefmt ="%H:%M:%S")

CLAW_SERVO = 1
WRIST_SERVO = 2
CLOSE = 500  # angle when claw is closed
OPEN = CLOSE - 280  # angle when claw is open
INIT_CLAW = CLOSE - 50
PICKUP_HEIGHT = 2
GOAL_COORDS = {
    'red':   (-15 + 0.5, 12 - 0.5, 1.5),
    'green': (-15 + 0.5, 6 - 0.5,  1.5),
    'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
}


class ArmController:
    def __init__(self, arm, board):
        self.arm = arm
        self.board = board
        self.initial_position(INIT_CLAW)

    def initial_position(self, claw_angle):
        self.board.setBusServoPulse(CLAW_SERVO, claw_angle, 300)
        self.board.setBusServoPulse(WRIST_SERVO, 500, 500)
        self.arm.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
        time.sleep(2)

    def pickup(self, block_coordinates):
        self.open()

        x = block_coordinates[0]
        y = block_coordinates[1]
        angle = getAngle(x, y, 0)
        self.rotate_to(angle)

        pickup_coord = (x, y, PICKUP_HEIGHT)
        self.move_to(pickup_coord)

        self.close()

        self.initial_position(CLOSE)

    def place(self, goal_coordinates):
        x = goal_coordinates[0]
        y = goal_coordinates[1]
        angle = getAngle(x, y, -90)
        self.rotate_to(angle)

        self.move_to(goal_coordinates)

        self.open()

        self.initial_position(INIT_CLAW)

    def open(self):
        self.board.setBusServoPulse(CLAW_SERVO, OPEN, 500)
        time.sleep(0.5)

    def close(self):
        self.board.setBusServoPulse(CLAW_SERVO, CLOSE, 500)
        time.sleep(0.5)

    def rotate_to(self, angle):
        self.board.setBusServoPulse(WRIST_SERVO, angle, 500)
        time.sleep(0.5)

    def move_to(self, coord):
        result = self.arm.setPitchRangeMoving(coord, -90, -90, 0, 1000)
        if not result:
            raise ValueError('Destination out of reach')

        wait_time = result[2]
        time.sleep(wait_time/1000)


if __name__ == '__main__':
    arm = ArmIK()
    controller = ArmController(arm, Board)

    tracker = ColorTracker()
    tracker.set_target_colors('red')
    tracker.calibrate()
    tracker.track()

    # TODO: Implement multithreading (Currently stops video to move block.)
    coords = tracker.coords['red']
    controller.pickup(coords)
    controller.place(GOAL_COORDS['red'])
