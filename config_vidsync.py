'''
Config.py
Configuration vars for rpi cam sync project
'''
from cv2 import FONT_HERSHEY_SIMPLEX

# device name for the chip
CHIP_ID = "/dev/gpiochip0"

# line for LED
LED_LINE_ID = "GPIO4"

# input signal line
INPUT_LINE_ID = "GPIO27"

# folder for video/data files
DATA_FOLDER = "/home/cclab/work/data"

# overlay text
OV_TEXT_COLOR = (0, 255, 0)
OV_TEXT_ORIGIN = (0, 30)
OV_TEXT_FONT = FONT_HERSHEY_SIMPLEX
OV_TEXT_SCALE = 1
OV_TEXT_THICKNESS = 2
