class Bus:
    '''
    Bus that acts as FIFO queue
    '''
    def __init__(self, message_type):
        '''

        :param message_type: string, one of ['sensor', 'rel_line_pos', 'angle']
        '''
        self.message_type = message_type
        self.message = []

    def write(self, value):
        '''
        :param value:
        :return:
        '''
        # Don't want to queue up control messages
        if self.message_type != 'sensor':
            self.message = [value]
        else:
            self.message.append(value)

    def read(self):
        if len(self.message) == 0:
            return None
        value = self.message.pop(0)
        return value
