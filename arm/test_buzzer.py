import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
#GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
BUZZER = 23
GPIO.setup(BUZZER, GPIO.OUT, initial=GPIO.LOW)

def buzz(noteFreq, duration):
    halveWaveTime = 1 / (noteFreq * 2 )
    waves = int(duration * noteFreq)
    for i in range(waves):
       GPIO.output(BUZZER, True)
       time.sleep(halveWaveTime)
       GPIO.output(BUZZER, False)
       time.sleep(halveWaveTime)
       
notes = {'c1': 33, 'd1': 37, 'e1': 41, 'f1': 44, 'g1': 49}
buzz(notes['c1'], 0.5)
time.sleep(1.5)
buzz(notes['e1'], 0.5)
time.sleep(1.5)
buzz(notes['g1'], 0.5)
time.sleep(1.5)

# import sys
# sys.path.append('/home/pi/ArmPi/')
# import HiwonderSDK.Board as Board
# import time
# 
# 
# Board.setBuzzer(0) # 关闭
# 
# Board.setBuzzer(1) # 打开
# time.sleep(0.1) # 延时
# Board.setBuzzer(0) #关闭
# 
# time.sleep(1) # 延时
# 
# Board.setBuzzer(1)
# time.sleep(0.5)
# Board.setBuzzer(0)
