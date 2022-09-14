import logging
import time

from src import DroneManeger
from src import app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    app.run()
