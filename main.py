import logging

from src.controllers import server

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    server.run()
