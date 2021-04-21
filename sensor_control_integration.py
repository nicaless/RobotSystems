from controller_class import Controller
from interpreter_class import ColorInterpreter, PhotoSensorInterpreter
from picarx_class import PiCarX
from sensor_class import Sensor


def move_forward(sensor_type='photosensor', sensitivity=10, polarity=1,
                 target=500, speed=1, delay=20):
    pi = PiCarX()
    sens = Sensor()
    if sensor_type == 'photosensor':
        interp = PhotoSensorInterpreter(sensitivity=sensitivity,
                                      polarity=polarity)
    else:
        interp = ColorInterpreter()
    con = Controller(pi)

    while True:
        # TODO: sample multiple values before commanding controller
        sensor_values = sens.get_sensor_reading(sensor_type=sensor_type)
        if sensor_type == 'photosensor':
            rel_line_pos = interp.relative_line_position(sensor_values,
                                                         target=target)
            steer_angle = con.turn_to_line(rel_line_pos)
        else:
            steer_angle = interp.steering_angle(sensor_values)
            steer_angle = con.turn_to_angle(steer_angle, scale=1)
        if steer_angle is None:
            break
        pi.forward(speed, turn_angle=steer_angle)
        pi.delay(delay)


def test_sensor(sensor):
    for i in range(10):
        print(sensor.get_adc_values())

def test_interpreter(sens, interp):
    for i in range(10):
        adc_values = sens.get_adc_values()
        print(interp._find_target(adc_values, 500))
        print(interp.relative_line_position(adc_values, 500))

def test_controller(sens, interp, con):
    adc_values = sens.get_adc_values()
    print(adc_values)
    rel_line_pos = interp.relative_line_position(adc_values, 500)
    print(rel_line_pos)
    con.turn_to_line(rel_line_pos)


if __name__ == "__main__":
    # pi = PiCarX(logging_on=True)
    # sens = Sensor(logging_on=True)
    # interp = GreyScaleInterpreter(sensitivity=10, logging_on=True)
    # con = Controller(pi, scale=30, logging_on=True)
    #
    # test_sensor(sens)
    # test_interpreter(sens, interp)
    # test_controller(sens, interp, con)

    move_forward()
