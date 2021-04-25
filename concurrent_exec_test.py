"""
concurrency_exec_test.py
Written Nicole Fronda - April 2021

Script to test the producer-consumer functions in the Sensor, Interpreter,
and Controller classes.
"""

import concurrent.futures
from concurrency import Bus
from controller_class import Controller
from interpreter_class import PhotoSensorInterpreter
from picarx_class import PiCarX
from sensor_class import Sensor

pi = PiCarX(logging_on=True)

sens = Sensor(logging_on=True)
sensor_bus = Bus('sensor')
sensor_delay = 1

interp = PhotoSensorInterpreter(logging_on=True)
interp_delay = 1

con = Controller(pi, logging_on=True)
control_bus = Bus('rel_line_pos')
con_delay = 1


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    eSensor = executor.submit(sens.produce_readings, sensor_bus, sensor_delay)
    #eInterpreter = executor.submit(interp.consume_sensor_produce_control,
    #                               sensor_bus, control_bus, interp_delay)
    #eController = executor.submit(con.consume_control_input,
    #                              control_bus, con_delay)
    #print(eInterpreter.result())
    #print(eController.result())
print(Bus.message)
