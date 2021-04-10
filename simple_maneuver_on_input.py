import simple_maneuvers as sm

KEY_MAPPING = {'go forward': 'w',
               'go backward': 'a',
               'parallel park': 'p',
               'k turn': 'k',
               'end program': 'e'}

FUNC_MAPPING = {KEY_MAPPING['go forward']: sm.go_forward_at_angle,
                KEY_MAPPING['go backward']: sm.go_backward_at_angle,
                KEY_MAPPING['parallel park']: sm.parallel_park,
                KEY_MAPPING['k turn']: sm.k_turn
                }

REQUIRES_ANGLE_INPUT = [KEY_MAPPING['go forward'],
                        KEY_MAPPING['go backward']]

def get_prompt():
    print('Enter one of the following keys')
    for k, v in KEY_MAPPING.items():
        print('To {k}, press {v}'.format(k=k, v=v))

def get_command(x):
    if x in REQUIRES_ANGLE_INPUT:
        angle = input('Enter turn angle (0 to go straight): ')
        try:
            angle = int(angle)
            if angle < -90:
                angle = -90
            if angle > 90:
                angle = 90

            FUNC_MAPPING[x](angle)
        except:
            print('invalid input. Turn angle must be an integer')

    else:
        direction = input('Enter initial turn direction (left or right): ')
        if direction not in ['left', 'right']:
            print('invalid input.  Direction must be left or right')
        else:
            FUNC_MAPPING[x](direction=direction)


if __name__ == "__main__":
    get_prompt()
    while True:
        x = input('Enter command: ')
        if x == 'e':
            break

        if x not in KEY_MAPPING.values():
            print('invalid input')
            get_prompt()
        else:
            get_command(x)
