import logging

class Servo():
    def __init__(self, pwm):
        pass

    # angle ranges -90 to 90 degrees
    def angle(self, angle):
        pass

class I2C():
    def __init__(self, *args, **kargs):
        pass

    def _i2c_write_byte(self, addr, data):
        return 0

    def _i2c_write_byte_data(self, addr, reg, data):
        return 0

    def _i2c_write_word_data(self, addr, reg, data):
        return 0

    def _i2c_write_i2c_block_data(self, addr, reg, data):
        return 0

    def _i2c_read_byte(self, addr):
        return 0

    def _i2c_read_i2c_block_data(self, addr, reg, num):
        return 0

    def is_ready(self, addr):
        return True

    def scan(self):
        return []

    def send(self, send, addr, timeout=0):
        return 0

    def recv(self, recv, addr=0x00, timeout=0):
        return False

    def mem_write(self, data, addr, memaddr, timeout=5000, addr_size=8):
        return 0

    def mem_read(self, data, addr, memaddr, timeout=5000, addr_size=8):
        return False

    def readfrom_mem_into(self, addr, memaddr, buf):
        return buf

    def writeto_mem(self, addr, memaddr, data):
        return 0

class PWM(I2C):
    def __init__(self, channel, debug="critical"):
        super().__init__()
        pass

    def i2c_write(self, reg, value):
        return 0

    def freq(self, *freq):
        return 0

    def prescaler(self, *prescaler):
        return 0

    def period(self, *arr):
        return 0

    def pulse_width(self, *pulse_width):
        return 0

    def pulse_width_percent(self, *pulse_width_percent):
        return 0

class Pin():
    def __init__(self, *value):
        pass

    def check_board_type(self):
        pass

    def init(self, mode, pull=None):
        pass

    def dict(self, *_dict):
        pass

    def __call__(self, value):
        return self.value(value)

    def value(self, *value):
        return value

    def on(self):
        return self.value(1)

    def off(self):
        return self.value(0)

    def high(self):
        return self.on()

    def low(self):
        return self.off()

    def mode(self, *value):
        return (0, 0)

    def pull(self, *value):
        return value

    def irq(self, handler=None, trigger=None, bouncetime=200):
        pass

    def name(self):
        return 0

    def names(self):
        return [0, 0]

    class cpu(object):
        def __init__(self):
            pass

class ADC(I2C):
    def __init__(self, chn):
        super().__init__()

    def read(self):
        return 0

    def read_voltage(self):
        return 0
