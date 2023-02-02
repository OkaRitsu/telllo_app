import os

from flask import Flask

WEB_ADDRESS = "127.0.0.1"
WEB_PORT = 5000

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(PROJECT_ROOT, "src/templates")
STATIC_FOLDER = os.path.join(PROJECT_ROOT, "src/static")
app = Flask(
    __name__,
    template_folder=TEMPLATES,
    static_folder=STATIC_FOLDER,
)
