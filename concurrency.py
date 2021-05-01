"""
concurrency.py
Written Nicole Fronda - April 2021

Bus class that acts as FIFO queue for messages between processes
"""

class Bus:
    def __init__(self, message_type):
        '''
        :param message_type: string, one of ['sensor', 'rel_line_pos', 'angle']
        '''
        self.message_type = message_type
        self.message = []

    def write(self, value):
        '''
        Writes value to the message queue
        :param value:
        :return: None
        '''

        # Don't want to queue up control input messages
        # This is intended to ensure controller uses only the latest processed data
        if self.message_type != 'sensor':
            self.message = [value]
        else:
            self.message.append(value)

    def read(self):
        """
        Returns the earliest value in the queue
        """
        if len(self.message) == 0:
            return None
        value = self.message.pop(0)
        return value
