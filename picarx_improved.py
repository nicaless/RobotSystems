import atexit
import logging
from logdecorator import log_on_start, log_on_end, log_on_error

try:
    from ezblock import *
    from ezblock import __reset_mcu__
    import time
    __reset_mcu__()
    time.sleep(0.01)
except ImportError:
    print('This computer does not appear to be a PiCar -X system (/opt/ezblock '
          'is not present). Shadowing hardware call swith substitute functions')
    from sim_ezblock import *

'''BEGIN LOGGING SETUP'''
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO,
                    datefmt ="%H:%M:%S")
# COMMENT OUT BELOW LINE TO SUPPRESS DEBUG/ERROR MESSAGES
logging.getLogger().setLevel(logging.DEBUG)
# logging.getLogger().setLevel(logging.ERROR)
'''END LOGGING SETUP'''

PERIOD = 4095
TIMEOUT = 0.02
VEHICLE_WITH = 7  # 7 centimeters
CALIBRATION_ANGLE = 0  # use calibration_steering.py to determine this

dir_servo_pin = Servo(PWM('P2'))
camera_servo_pin1 = Servo(PWM('P0'))
camera_servo_pin2 = Servo(PWM('P1'))
left_rear_pwm_pin = PWM("P13")
right_rear_pwm_pin = PWM("P12")
left_rear_dir_pin = Pin("D4")
right_rear_dir_pin = Pin("D5")

S0 = ADC('A0')
S1 = ADC('A1')
S2 = ADC('A2')

Servo_dir_flag = 1
dir_cal_value = 0
cam_cal_value_1 = 0
cam_cal_value_2 = 0
motor_direction_pins = [left_rear_dir_pin, right_rear_dir_pin]
motor_speed_pins = [left_rear_pwm_pin, right_rear_pwm_pin]
cali_dir_value = [1, -1]
cali_speed_value = [0, 0]

for pin in motor_speed_pins:
    pin.period(PERIOD)

def set_motor_speed(motor, speed):
    global cali_speed_value,cali_dir_value
    motor -= 1
    if speed >= 0:
        direction = 1 * cali_dir_value[motor]
    elif speed < 0:
        direction = -1 * cali_dir_value[motor]
    speed = abs(speed)
    if speed != 0:
        speed = int(speed /2 ) + 50
    speed = speed - cali_speed_value[motor]
    if direction < 0:
        motor_direction_pins[motor].high()
        motor_speed_pins[motor].pulse_width_percent(speed)
    else:
        motor_direction_pins[motor].low()
        motor_speed_pins[motor].pulse_width_percent(speed)

def motor_speed_calibration(value):
    global cali_speed_value,cali_dir_value
    cali_speed_value = value
    if value < 0:
        cali_speed_value[0] = 0
        cali_speed_value[1] = abs(cali_speed_value)
    else:
        cali_speed_value[0] = abs(cali_speed_value)
        cali_speed_value[1] = 0

def motor_direction_calibration(motor, value):
    # 0: positive direction
    # 1:negative direction
    global cali_dir_value
    motor -= 1
    if value == 1:
        cali_dir_value[motor] = -1*cali_dir_value[motor]


def dir_servo_angle_calibration(value):
    global dir_cal_value
    dir_cal_value = value
    set_dir_servo_angle(dir_cal_value)
    # dir_servo_pin.angle(dir_cal_value)

def set_dir_servo_angle(value):
    global dir_cal_value
    dir_servo_pin.angle(value+dir_cal_value)

def camera_servo1_angle_calibration(value):
    global cam_cal_value_1
    cam_cal_value_1 = value
    set_camera_servo1_angle(cam_cal_value_1)
    # camera_servo_pin1.angle(cam_cal_value)

def camera_servo2_angle_calibration(value):
    global cam_cal_value_2
    cam_cal_value_2 = value
    set_camera_servo2_angle(cam_cal_value_2)
    # camera_servo_pin2.angle(cam_cal_value)

def set_camera_servo1_angle(value):
    global cam_cal_value_1
    camera_servo_pin1.angle(-1 *(value+cam_cal_value_1))

def set_camera_servo2_angle(value):
    global cam_cal_value_2
    camera_servo_pin2.angle(-1 * (value+cam_cal_value_2))

def get_adc_value():
    adc_value_list = []
    adc_value_list.append(S0.read())
    adc_value_list.append(S1.read())
    adc_value_list.append(S2.read())
    return adc_value_list

def set_power(speed):
    set_motor_speed(1, speed)
    set_motor_speed(2, speed) 

@log_on_error(logging.DEBUG, "ERROR backward {e!r}", reraise=True)
def backward(speed, turn_angle=0):
    if turn_angle == 0:
        set_motor_speed(1, speed)
        set_motor_speed(2, speed)
    else:
        v1 = speed
        r = (speed * 360) / (turn_angle * 2 * 3.14)
        v2 = v1 * (r/VEHICLE_WITH + 1) / (r/VEHICLE_WITH - 1)
        if turn_angle > 0:
            set_motor_speed(1, v1)
            set_motor_speed(2, v2)
        else:
            set_motor_speed(2, v1)
            set_motor_speed(1, v2)

@log_on_error(logging.DEBUG, "ERROR forward {e!r}", reraise=True)
def forward(speed, turn_angle=0):
    if turn_angle == 0:
        set_motor_speed(1, -1*speed)
        set_motor_speed(2, -1*speed)
    else:
        v1 = -1*speed
        r = (speed * 360) / (turn_angle * 2 * 3.14)
        v2 = v1 * (r/VEHICLE_WITH + 1) / (r/VEHICLE_WITH - 1)
        if turn_angle > 0:
            set_motor_speed(1, v1)
            set_motor_speed(2, v2)
        else:
            set_motor_speed(2, v1)
            set_motor_speed(1, v2)


def stop():
    set_motor_speed(1, 0)
    set_motor_speed(2, 0)


def Get_distance():
    timeout=0.01
    trig = Pin('D8')
    echo = Pin('D9')

    trig.low()
    time.sleep(0.01)
    trig.high()
    time.sleep(0.000015)
    trig.low()
    pulse_end = 0
    pulse_start = 0
    timeout_start = time.time()
    while echo.value()==0:
        pulse_start = time.time()
        if pulse_start - timeout_start > timeout:
            return -1
    while echo.value()==1:
        pulse_end = time.time()
        if pulse_end - timeout_start > timeout:
            return -2
    during = pulse_end - pulse_start
    cm = round(during * 340 / 2 * 100, 2)
    #print(cm)
    return cm
     
def test():
    # dir_servo_angle_calibration(-10) 
    set_dir_servo_angle(-40)
    # time.sleep(1)
    # set_dir_servo_angle(0)
    # time.sleep(1)
    # set_motor_speed(1, 1)
    # set_motor_speed(2, 1)
    # camera_servo_pin.angle(0)


# if __name__ == "__main__":
#     try:
#         # dir_servo_angle_calibration(-10) 
#         while 1:
#             test()
#     finally: 
#         stop()

'''SET CALIBRATION ANGLE ON IMPORT'''
dir_servo_angle_calibration(CALIBRATION_ANGLE)

'''SET MOTORS TO 0 SPEED AT EXIT'''
atexit.register(stop)
