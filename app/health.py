import threading
from flask import Flask


class HealthCheckServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.thread = None

    def start(self):
        def run():

            app = Flask(__name__)
            @app.route("/")
            def health():
                return "OK", 200
            app.run(host=self.host, port=self.port)
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()