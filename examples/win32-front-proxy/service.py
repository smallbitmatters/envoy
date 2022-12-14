from flask import Flask
import os
import requests
import socket
import sys

app = Flask(__name__)


@app.route('/service/<service_number>')
def hello(service_number):
    return f"Hello from behind Envoy (service {os.environ['SERVICE_NAME']})! hostname: {socket.gethostname()} resolvedhostname: {socket.gethostbyname(socket.gethostname())}\n"


@app.route('/trace/<service_number>')
def trace(service_number):
    if int(os.environ['SERVICE_NAME']) == 1:
        requests.get("http://localhost:9000/trace/2")
    return f"Hello from behind Envoy (service {os.environ['SERVICE_NAME']})! hostname: {socket.gethostname()} resolvedhostname: {socket.gethostbyname(socket.gethostname())}\n"


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
