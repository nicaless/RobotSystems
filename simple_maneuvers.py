from ezblock import delay
import logging
from logdecorator import log_on_start, log_on_end, log_on_error
import picarx_improved as pi


DEFAULT_SPEED = 50
DEFAULT_DELAY = 1000
PARALLEL_PARK_ANGLE = 30
K_TURN_ANGLE = 30

@log_on_start(logging.DEBUG, "BEGIN go_forward_straight")
@log_on_error(logging.ERROR, "ERROR go_forward_straight, {e!r}", reraise=True)
@log_on_end(logging.DEBUG, "ERROR go_forward_straight")
def go_forward_straight():
    pi.forward(DEFAULT_SPEED)
    delay(DEFAULT_DELAY)
    pi.stop()
    delay(DEFAULT_DELAY)

@log_on_start(logging.DEBUG, "BEGIN go_backward_straight")
@log_on_error(logging.DEBUG, "ERROR go_backward_straight, {e!r}", reraise=True)
@log_on_end(logging.DEBUG, "ERROR go_backward_straight")
def go_backward_straight():
    pi.backward(DEFAULT_SPEED)
    delay(DEFAULT_DELAY)
    pi.stop()
    delay(DEFAULT_DELAY)

@log_on_start(logging.DEBUG, "BEGIN go_forward_at_angle {angle:d}")
@log_on_error(logging.DEBUG, "ERROR go_forward_at_angle, {e!r}", reraise=True)
@log_on_end(logging.DEBUG, "ERROR go_forward_at_angle")
def go_forward_at_angle(angle):
    pi.set_dir_servo_angle(angle)
    delay(DEFAULT_DELAY)
    pi.forward(DEFAULT_SPEED, turn_angle=angle)
    delay(DEFAULT_DELAY)
    pi.stop()
    delay(DEFAULT_DELAY)

@log_on_start(logging.DEBUG, "BEGIN go_backward_at_angle {angle:d}")
@log_on_error(logging.DEBUG, "ERROR go_backward_at_angle, {e!r}")
@log_on_end(logging.DEBUG, "ERROR go_backward_at_angle")
def go_backward_at_angle(angle):
    pi.backward(DEFAULT_SPEED, turn_angle=angle)
    delay(DEFAULT_DELAY)
    pi.stop()
    delay(DEFAULT_DELAY)

@log_on_start(logging.DEBUG, "BEGIN parallel_park")
@log_on_error(logging.ERROR, "ERROR parallel_park, {e!r}")
@log_on_end(logging.DEBUG, "ERROR parallel_park")
def parallel_park(direction='left'):
    '''
    drives forward for a time, then stops
    turns towards park direction
    drives backward at angle for a time, then stops
    turns towards opposite direction
    drives backward at angle for a time, then stops
    drives forward for a short time, then stopssud

    :param direction:
    '''
    go_forward_straight()
    if direction == 'left':
        angle = PARALLEL_PARK_ANGLE
    else:
        angle = -1*PARALLEL_PARK_ANGLE
    print(angle)
    #delay(DEFAULT_DELAY)
    go_backward_at_angle(angle)

    #pi.set_dir_servo_angle(-1*angle)
    #delay(DEFAULT_DELAY)
    go_backward_at_angle(-1*angle)

    #pi.set_dir_servo_angle(0)
    #delay(DEFAULT_DELAY)
    go_forward_at_angle(0)
    #delay(DEFAULT_DELAY)
    #pi.stop()
    #delay(DEFAULT_DELAY)

@log_on_start(logging.DEBUG, "BEGIN k_turn, direction: {direction:s}")
@log_on_error(logging.DEBUG, "ERROR k_turn, {e!r}")
@log_on_end(logging.DEBUG, "ERROR k_turn")
def k_turn(direction='left'):
    """
    drives forward for a time, then stops
    turns towards direction
    drives forward at angle for a time, then stops
    turns towards opposite direction
    drives backward at angle for a time, then stops
    drives forward for a time, then stops

    :param direction:
    """
    pass


if __name__ == "__main__":
    go_forward_straight()
    go_backward_straight()
    go_forward_at_angle(30)
    go_backward_at_angle(30)
    go_forward_at_angle(-30)
    go_backward_at_angle(-30)
    #parallel_park()
