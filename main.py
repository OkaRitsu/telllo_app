import threading
import time

from src import DroneManeger
from src import app


def run_app():
    app.run()


if __name__ == '__main__':
    app_thread = threading.Thread(target=run_app)
    app_thread.start()

    drone = DroneManeger(host_ip='0.0.0.0')
    drone.takeoff()
    time.sleep(1)
    drone.land()
    drone.stop()
