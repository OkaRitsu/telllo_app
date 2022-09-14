import logging
import time

from src import DroneManeger
from src import app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    app.run()

    # drone = DroneManeger(host_ip='0.0.0.0')
    # drone.takeoff()
    # time.sleep(1)
    # drone.land()
    # drone.stop()
