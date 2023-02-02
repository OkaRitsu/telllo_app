import json
import logging

from flask import Response, jsonify, render_template, request

import config
from src.models.drone_manager import DroneManeger

logger = logging.getLogger(__name__)
app = config.app


def get_drone():
    return DroneManeger()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/controller")
def controller():
    return render_template("controller.html")


@app.route("/api/command/", methods=["POST"])
def command():
    drone = get_drone()
    cmd = request.form.get("command")
    logger.info(
        {
            "action": "command",
            "command": cmd,
        }
    )

    # 離着陸
    if cmd == "takeOff":
        drone.takeoff()
    elif cmd == "land":
        drone.land()
    # 緊急停止
    elif cmd == "emergency":
        drone.emergency()
    # 速度設定
    elif cmd == "speed":
        speed = request.form.get("speed")
        logger.info(
            {
                "action": "commnad",
                "command": cmd,
                "speed": speed,
            }
        )
        if speed:
            drone.set_speed(speed)
    # 前後左右
    elif cmd == "forward":
        drone.forward()
    elif cmd == "back":
        drone.back()
    elif cmd == "left":
        drone.left()
    elif cmd == "right":
        drone.right()
    # 上昇下降
    elif cmd == "up":
        drone.up()
    elif cmd == "down":
        drone.down()
    # 左右回転
    elif cmd == "turnLeft":
        drone.turn_left()
    elif cmd == "turnRight":
        drone.turn_right()

    return jsonify(status="success"), 200


@app.route("/video/streaming")
def video_feed():
    return Response(
        video_generator(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def video_generator():
    drone = get_drone()
    for jpeg in drone.video_jpeg_generator():
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n\r\n")


@app.route("/api/state")
def state_feed():
    drone = get_drone()
    return json.dumps(drone.state)


def run():
    app.run(host=config.WEB_ADDRESS, port=config.WEB_PORT)
