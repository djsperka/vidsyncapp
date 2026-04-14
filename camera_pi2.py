import io
import time
from picamera2 import Picamera2
from base_camera import BaseCamera

class Camera(BaseCamera):
    def __init__(self, camera: Picamera2):
        super().__init__(camera)

    @staticmethod
    def frames():
        stream = io.BytesIO()
        try:
            while True:
                BaseCamera.camera.capture_file(stream, format='jpeg')
                stream.seek(0)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
        finally:
            pass


