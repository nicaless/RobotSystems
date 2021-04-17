from picarx_class import Controller, Interpreter, PiCarX, Sensor

def move_forward(sensitivity=50, polarity=1, target=300, speed=20, delay=1000):
    pi = PiCarX()
    sens = Sensor()
    interp = Interpreter(sensitivity=sensitivity,
                             polarity=polarity)
    con = Controller(pi)

    while True:
        adc_values = sens.get_adc_values()
        rel_line_pos = interp.relative_line_position(adc_values,
                                                     target=target)
        steer_angle = con.turn_to_line(rel_line_pos)
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

def test_controller(sens, interp, c):
    adc_values = sens.get_adc_values()
    print(adc_values)
    rel_line_pos = interp.relative_line_position(adc_values, 500)
    print(rel_line_pos)
    c.turn_to_line(rel_line_pos)


if __name__ == "__main__":
    pi = PiCarX(logging_on=True)
    sens = Sensor(logging_on=True)
    interp = Interpreter(sensitivity=10, logging_on=True)
    con = Controller(pi, scale=30, logging_on=True)

    #test_sensor(sens)
    #test_interpreter(sens, interp)
    test_controller(sens, interp, con)

    # move_forward()


