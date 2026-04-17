#!/usr/bin/env python
import os
import time
import glob
from flask import Flask, render_template, Response, request, jsonify, send_from_directory
import flask_cors

# local hardware-specific definitions here
import config_vidsync as config

# camera
from picamera2 import MappedArray, Picamera2, Preview
from picamera2.encoders import H264Encoder, MJPEGEncoder
from picamera2.outputs import FileOutput
from libcamera import controls

# opencv
import cv2

# numpy
import numpy as np

# local camera wrapper
from camera_pi2 import Camera

# local gpio wrapper
from RPiVidSyncGPIO import RPiVidSyncGPIO   

# camera status class
# Source - https://stackoverflow.com/a/47955313
# Posted by Martijn Pieters, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-14, License - CC BY-SA 4.0

from dataclasses import dataclass

@dataclass(unsafe_hash=True)
class CameraStatus:
    '''Class for keeping track of camera status.'''
    is_recording: bool = False
    recording_start_time: float = 0.0
    recording_frame_count: int = 0
    recording_filename: str = ''
    data_filename: str = ''
    data: np.ndarray = None

    def __post_init__(self):
        if self.data is None:
            self.data = np.full((21600), -1, dtype=np.int8)		# 2 hours at 30fps

    def status(self) -> str:
        if self.is_recording:
            elapsed_time = time.time() - self.recording_start_time
            return f"Recording: {self.recording_filename}<br>Elapsed Time: {elapsed_time:.2f} seconds<br>Frames Recorded: {self.recording_frame_count}"
        return "Not recording"



gpio = RPiVidSyncGPIO(chip_id=config.CHIP_ID, led_line_id=config.LED_LINE_ID, input_line_id=config.INPUT_LINE_ID)

camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
camera.start()
camera_status = CameraStatus()

app = Flask(__name__)
flask_cors.CORS(app)


def render_index():
    filenames=[os.path.basename(f) for f in glob.glob(os.path.join(config.DATA_FOLDER, '*.mjpeg'))]
    return render_template('index.html', is_recording=camera_status.is_recording, files=filenames)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_index()

def cb_frame(request):
    
    # check status of input bit, save it
    camera_status.data[camera_status.recording_frame_count] = gpio.get_input()

    # txt on preview
    txt = "{:05d} : {:s}".format(camera_status.recording_frame_count, time.strftime("%Y-%m-%d %X"))
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, txt, config.OV_TEXT_ORIGIN, config.OV_TEXT_FONT, config.OV_TEXT_SCALE, config.OV_TEXT_COLOR, config.OV_TEXT_THICKNESS)
    camera_status.recording_frame_count += 1

@app.route('/stop', methods=['GET'])
def stop_recording():
    print("Stop recording requested")
    camera_status.is_recording = False
    camera.pre_callback = None
    camera.stop_encoder()
    full_data_path = os.path.join(config.DATA_FOLDER, camera_status.data_filename)
    print("Saving {:d} frames of data to {:s}".format(camera_status.recording_frame_count, full_data_path))
    np.save(full_data_path, camera_status.data[:camera_status.recording_frame_count])
    return render_index()

@app.route('/start', methods=['GET'])
def start_recording():

    basename = request.args.get('basename', default=None, type=str)
    print("Start recording requested {:s}".format(basename))

    # generate filename based on timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{basename}_{timestamp}.mjpeg"
    full_path = os.path.join(config.DATA_FOLDER, filename)

    # create encoder and start recording. Pre-pend data folder to filename
    camera.pre_callback = cb_frame

    encoder = MJPEGEncoder(1000000)
    fileoutput = FileOutput(os.path.join(config.DATA_FOLDER, filename))
    encoder.output = fileoutput
    camera.start_encoder(encoder)

    camera_status.is_recording = True
    camera_status.recording_start_time = time.time()
    camera_status.recording_frame_count = 0
    camera_status.recording_filename = filename
    camera_status.data_filename = filename + ".npy"
    camera_status.data = np.full((21600), -1, dtype=np.int8)

    return render_index()   

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera(camera)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def get_camera_status():
    while True:
        #yield f"data: The time is {time.strftime('%X')}\n\n"
        yield f"data: {camera_status.status()}\n\n"
        time.sleep(1)

@app.route('/status')
def status():
    return Response(get_camera_status(), mimetype='text/event-stream')

# @app.route("/files")
# def list_files():
#     """Endpoint to list files on the server."""
#     files = []
#     for filename in os.listdir(config.DATA_FOLDER):
#         path = os.path.join(config.DATA_FOLDER, filename)
#         if os.path.isfile(path):
#             files.append(filename)
#     return jsonify(files)

@app.route('/files')
def list_files():
     filenames=os.listdir(config.DATA_FOLDER)
     return render_template('list.html', files=filenames )

@app.route('/files/<path:filename>')
def download(filename):
    return send_from_directory(os.path.abspath(config.DATA_FOLDER), filename, as_attachment=False)
#here for attachment i went with flase otherwise it gonna download all the contents of the files



if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)

