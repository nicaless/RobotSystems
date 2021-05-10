"""
concurrency_exec_test.py
Written Nicole Fronda - April 2021

Script to test the producer-consumer functions in the Sensor, Interpreter,
and Controller classes.
"""

from rossros import Bus, ConsumerProducer, Printer, Producer, \
    runConcurrently, Timer
from controller_class import Controller
from interpreter_class import PhotoSensorInterpreter, UltrasonicInterpreter
from picarx_class import PiCarX
from sensor_class import Sensor

pi = PiCarX(logging_on=True)

### SET UP TIMER
timer_bus = Bus(name='timer bus')
timer = Timer(timer_bus, delay=3)


### SET UP SENSORS AS PRODUCERS
sens = Sensor(logging_on=True)
photosensor_bus = Bus(name='greyscale sensor bus')
ultrasonic_bus = Bus(name='greyscale sensor bus')
photosensor_producer = Producer(sens.get_adc_values,
                                photosensor_bus,
                                delay=0,
                                termination_busses=[timer_bus],
                                name='photosensor producer')
ultrasonic_producer = Producer(sens.get_collision_distance,
                               ultrasonic_bus,
                               delay=0,
                               termination_busses=[timer_bus],
                               name='photosensor producer')


### SET UP INTERPRETERS AS CONSUMER-PRODUCER
photosensor_interp_bus = Bus(name='photosensor interpreter bus')
photosensor_interp = PhotoSensorInterpreter(logging_on=True)
photosensor_con_prod = ConsumerProducer(photosensor_interp.relative_line_position,
                                        photosensor_bus,
                                        photosensor_interp_bus,
                                        delay=1,
                                        termination_busses=[timer_bus],
                                        name='photosensor consumer-producer')

ultrasonic_interp_bus = Bus(name='ultrasonic interpreter bus')
ultrasonic_interp = UltrasonicInterpreter(logging_on=True)
ultrasonic_con_prod = ConsumerProducer(ultrasonic_interp.obstacle_check,
                                        ultrasonic_bus,
                                        ultrasonic_interp_bus,
                                        delay=1,
                                        termination_busses=[timer_bus],
                                        name='ultrasonic consumer-producer')


### SET UP CONTROLLER AS CONSUMER
controller = Controller(pi, logging_on=True)

stop_bus = Bus(name='stop bus')
stop_bus_con_prod = ConsumerProducer(controller.safety_stop,
                                     ultrasonic_interp,
                                     stop_bus,
                                     delay=2,
                                     termination_busses=[timer_bus],
                                     name = 'controller consumer-producer for stopping')

control_bus = Bus(name='controller bus')
controller_con_prod = ConsumerProducer(controller.turn_to_line,
                                       photosensor_interp_bus,
                                       control_bus,
                                       delay=2,
                                       termination_busses=[timer_bus, stop_bus],
                                       name='controller consumer-producer')


### SET UP PRINTERS
photosensor_printer = Printer(photosensor_bus,
                         termination_busses=[timer_bus],
                         name='sensor printer',
                         print_prefix='sensor values: ')
ultrasonic_printer = Printer(ultrasonic_bus,
                         termination_busses=[timer_bus],
                         name='interpreter printer',
                         print_prefix='interpreter values: ')
controller_printer = Printer(control_bus,
                             termination_busses=[timer_bus],
                             name='controller printer',
                             print_prefix='controller values: ')
stop_printer = Printer(stop_bus,
                       termination_busses=[timer_bus],
                       name='controller printer',
                       print_prefix='controller values: ')

producer_consumer_list = [timer,
                          photosensor_producer,
                          ultrasonic_producer,
                          photosensor_con_prod,
                          ultrasonic_con_prod,
                          stop_bus_con_prod,
                          controller_con_prod,
                          photosensor_printer,
                          ultrasonic_printer,
                          controller_printer,
                          stop_printer
                          ]


if __name__ == '__main__':
    runConcurrently(producer_consumer_list)
