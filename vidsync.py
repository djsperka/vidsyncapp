#!/usr/bin/python3

# local hardware-specific definitions here
import config_vidsync as config

# rPI gpio stuff
from gpiod import Chip, LineSettings
from gpiod.line import Direction, Value, Bias

# camera
from picamera2 import MappedArray, Picamera2, Preview
from picamera2.encoders import H264Encoder
from libcamera import controls

# numpy
import numpy as np

# regular python stuff
import time
import cv2
import typing
import logging
import sys
from pprint import pprint, pformat

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # The default is NOTSET
stream_handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(name)s] %(filename)s:%(lineno)d\t%(levelname)s:\t%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class MyGPIO():
    
    def __init__(self):

        self._chip = Chip(config.CHIP_ID)
        self._led_offset = self._chip.line_offset_from_id(config.LED_LINE_ID)
        self._input_offset = self._chip.line_offset_from_id(config.INPUT_LINE_ID)
        self._line_settings = {
            self._led_offset: LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
            self._input_offset: LineSettings(direction=Direction.INPUT, bias=Bias.PULL_DOWN)
        }
        self._lines = self._chip.request_lines(consumer="MyGPIO", config=self._line_settings)
        self._encoder = None
        
    def __del__(self):
        self._chip.close()

    def get_input(self) -> int:
        return 1 if (self._lines.get_value(self._input_offset) == Value.ACTIVE) else 0
        
    def set_led(self, v: int) -> None:
        self._lines.set_value(self._led_offset, Value.ACTIVE if v>0 else Value.INACTIVE)


class VidSync():
    def __init__(self, gpio: MyGPIO, stamp: bool = True, preview: bool = True):
        self._gpio = gpio
        self._picam2 = Picamera2()
        self._data = np.full((21600), -1, dtype=np.int8)		# 2 hours at 30fps
        self._counter = 0
        self._stamp = stamp
        
        if preview:
            self._picam2.start_preview(Preview.QTGL)

        # camera config. Will probably modify the default created with
        # args to the constructor
        self._video_config = self._picam2.create_video_configuration(main={"size":(800,600)})

        logger.info("video_config=\n" + pformat(self._video_config))
        self._picam2.configure(self._video_config)
        logger.info("Focus...")
        self._picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 2.0})
        logger.info("Focus...done")
        

    def _cb_frame(self, request):
        
        # check status of input bit, save it
        self._data[self._counter] = self._gpio.get_input()

        # will we be writing on the images?
        if self._stamp:
            txt = "{:05d} : {:d} : {:s}".format(self._counter, self._data[self._counter], time.strftime("%Y-%m-%d %X"))
            with MappedArray(request, "main") as m:
                cv2.putText(m.array, str(self._counter), config.OV_TEXT_ORIGIN, config.OV_TEXT_FONT, config.OV_TEXT_SCALE, config.OV_TEXT_COLOR, config.OV_TEXT_THICKNESS)

        # increment counter
        self._counter += 1


    def start(self, fname):
        #self._encoder = H264Encoder(bitrate=10000000)


        # Form two filenames
        self._video_filename = fname
        self._data_filename = fname + ".txt"
        logger.info("Starting recording video to file {}".format(fname))
        self._counter = 0
        self._encoder = H264Encoder()
        self._picam2.pre_callback = self._cb_frame
        self._picam2.start_recording(self._encoder, fname)
        #logger.info("LensPosition={}".format(self._picam2.capture_metadata().get('LensPosition', None))) 
        self._recording = True

    def stop(self, writedata: bool=True):
        if self._recording:
            self._picam2.stop_recording()
            self._recording = False
            logger.info("Recorded {:d} frames. Writing digital data to {:s}".format(self._counter, self._data_filename))
            with open(self._data_filename, 'wb') as f:
                np.save(f, self._data[:self._counter])
            logger.info("Writing done.")
        else:
            logger.info("Not started, can't stop.")

if __name__ == '__main__':
#    setup_logging()

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description='record video with sync signals', formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--test', action='store_true', help='record for 10 seconds')
    parser.add_argument('--verbose', action='store_true', help='increase verbosity (log at DEBUG level)')
    parser.add_argument('--file', default='', help='output filename')
    parser.add_argument('--seconds', type=int, default=10, help='seconds to record for')
    parser.add_argument('--stamp', action='store_true', help='Apply timestamp and frame counter to recorded video')
    parser.add_argument('--preview', action='store_true', help='Open preview window on Pi screen')
    
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)


    try:
        gpio = MyGPIO()
        cam = VidSync(gpio, stamp=args.stamp, preview=args.preview)
        started = False
        while True:
            
            inp = input("s(tart), q(uit): ")
            if inp=='s':
                if not started:
                    cam.start(args.file)
                    started = True
                else:
                    logger.warning("Camera already started.")
            elif inp == 'q':
                if started:
                    cam.stop()
                break
                
    except Exception as e:
        print(e)
        
        