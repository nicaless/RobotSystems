from ezblock import __reset_mcu__, delay
import time
__reset_mcu__()
time.sleep(0.01)
import picarx_improved as pi

CALIBRATION_ANGLE = 2  # MODIFY THIS UNTIL CAR DRIVES STRAIGHT
TEST_TURN_ANGLE = 30
pi.dir_servo_angle_calibration(CALIBRATION_ANGLE)
if __name__ == "__main__":
    pi.forward(50)
    delay(1000)
    pi.stop()
    pi.set_dir_servo_angle(TEST_TURN_ANGLE)
    delay(1000)
    pi.forward(60, turn_angle=TEST_TURN_ANGLE)
    delay(1000)
    pi.set_dir_servo_angle(0)
    delay(1000)
    pi.forward(50)
    delay(1000)