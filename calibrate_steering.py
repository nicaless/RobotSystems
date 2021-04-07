from ezblock import __reset_mcu__
import time
__reset_mcu__()
time.sleep(0.01)
import picarx_improved as pi

CALIBRATION_ANGLE = 2  # MODIFY THIS UNTIL CAR DRIVES STRAIGHT
pi.dir_servo_angle_calibration(CALIBRATION_ANGLE)
if __name__ == "__main__":
    pi.forward(50)
    time.sleep(2)  # seconds
