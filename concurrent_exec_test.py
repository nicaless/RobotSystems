"""
concurrency_exec_test.py
Written Nicole Fronda - April 2021

Script to test the producer-consumer functions in the Sensor, Interpreter,
and Controller classes.
"""

from rossros import Bus, ConsumerProducer, Printer, Producer, \
    runConcurrently, Timer
from controller_class import Controller
from interpreter_class import PhotoSensorInterpreter
from picarx_class import PiCarX
from sensor_class import Sensor

pi = PiCarX(logging_on=True)

### SET UP TIMER
timer_bus = Bus(name='timer bus')
timer = Timer(timer_bus)


### SET UP GREYSCALE SENSOR AS A PRODUCER
sens = Sensor(logging_on=True)
sensor_bus = Bus(name='sensor bus')
sensor_producer = Producer(sens.get_adc_values,
                           sensor_bus,
                           delay=1,
                           termination_busses=timer_bus,
                           name='sensor producer')


### SET UP INTERPRETER AS CONSUMER-PRODUCER
interp = PhotoSensorInterpreter(logging_on=True)
interp_bus = Bus(name='interpreter bus')
interp_con_prod = ConsumerProducer(interp.relative_line_position,
                                   sensor_bus,
                                   interp_bus,
                                   delay=1,
                                   termination_busses=timer_bus,
                                   name='interpreter consumer-producer')


### SET UP CONTROLLER AS CONSUMER
controller = Controller(pi, logging_on=True)
control_bus = Bus(name='controller bus')
controller_con_prod = ConsumerProducer(controller.turn_to_line,
                                       interp_bus,
                                       control_bus,
                                       delay=1,
                                       termination_busses=timer_bus,
                                       name='controller consumer-producer')


### SET UP PRINTERS
sensor_printer = Printer(sensor_bus,
                         termination_busses=timer_bus,
                         name='sensor printer',
                         print_prefix='sensor values: ')
interp_printer = Printer(interp_bus,
                         termination_busses=timer_bus,
                         name='interpreter printer',
                         print_prefix='interpreter values: ')
controller_printer = Printer(control_bus,
                             termination_busses=timer_bus,
                             name='controller printer',
                             print_prefix='controller values: ')

producer_consumer_list = [timer,
                          sensor_producer,
                          interp_con_prod,
                          controller_con_prod]


if __name__ == '__main__':
    runConcurrently(producer_consumer_list)
