from picarx_class import Controller, Interpreter, PiCarX, Sensor

def move_forward(sensitivity=50, polarity=1, target=300, speed=20, delay=1000):
    pi = PiCarX()
    sensor = Sensor()
    interpreter = Interpreter(sensitivity=sensitivity,
                             polarity=polarity)
    controller = Controller(pi)

    while True:
        adc_values = sensor.get_adc_values()
        rel_line_pos = interpreter.relative_line_position(adc_values,
                                                          target=target)
        steer_angle = controller.turn_to_line(rel_line_pos)
        pi.forward(speed, turn_angle=steer_angle)
        pi.delay(delay)


def test_sensor(sensor):
    for i in range(50):
        print(sensor.get_adc_values())

def test_interpreter(sensor, interpreter):
    for i in range(50):
        adc_values = sensor.get_adc_values()
        print(interpreter._find_target(adc_values))
        print(interpreter.relative_line_position(adc_values))

def test_controller(sensor, interpreter, controller):
    rel_line_pos = interpreter.relative_line_position(sensor.get_adc_values())
    controller.turn_to_line(rel_line_pos)


if __name__ == "__main__":
    pi = PiCarX()
    sensor = Sensor()
    interpreter = Interpreter()
    controller = Controller(pi)

    test_sensor(sensor)
    test_interpreter(sensor, interpreter)
    test_controller(sensor, interpreter, controller)

    # move_forward()

