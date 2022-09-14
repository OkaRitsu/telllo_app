import json

from flask import (
    Flask,
    Response
)

from src.drone_manager import DroneManeger


app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello World'


@app.route('/video/streaming')
def video_feed():
    return Response(
        video_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


def get_drone():
    return DroneManeger(host_ip='0.0.0.0')


def video_generator():
    drone = get_drone()
    for jpeg in drone.video_jpeg_generator():
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + jpeg
               + b'\r\n\r\n')


@app.route('/api/state')
def state_feed():
    drone = get_drone()
    return json.dumps(drone.state)
