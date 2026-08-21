'''
Config.py
Configuration vars for rpi cam sync project
'''
from cv2 import FONT_HERSHEY_SIMPLEX

# device name for the chip
CHIP_ID = "/dev/gpiochip15"

# line for LED
LED_LINE_ID = "GPIO16"

# input signal line
INPUT_LINE_ID = "GPIO23"

# folder for video/data files
DATA_FOLDER = "/home/cclab/work/data"

# overlay text
OV_TEXT_COLOR = (0, 255, 0)
OV_TEXT_ORIGIN = (0, 30)
OV_TEXT_FONT = FONT_HERSHEY_SIMPLEX
OV_TEXT_SCALE = 1
OV_TEXT_THICKNESS = 2

# camera settings
CAMERA_FRAMERATE = 30.0
CAMERA_BITRATE = 1000000
CAMERA_MAIN_SIZE = (800, 600)
CAMERA_MAIN_FORMAT = 'RGB888'
CAMERA_LORES_SIZE = (640, 320)
CAMERA_LORES_FORMAT = 'YUV420'
