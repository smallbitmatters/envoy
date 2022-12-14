from flask import Flask
from flask import request
import os
import requests
import socket
import sys

app = Flask(__name__)

TRACE_HEADERS_TO_PROPAGATE = [
    'X-Ot-Span-Context',
    'X-Request-Id',

    # Zipkin headers
    'X-B3-TraceId',
    'X-B3-SpanId',
    'X-B3-ParentSpanId',
    'X-B3-Sampled',
    'X-B3-Flags',

    # Jaeger header (for native client)
    "uber-trace-id",

    # SkyWalking headers.
    "sw8"
]


@app.route('/service/<service_number>')
def hello(service_number):
    return f"Hello from behind Envoy (service {os.environ['SERVICE_NAME']})! hostname: {socket.gethostname()} resolvedhostname: {socket.gethostbyname(socket.gethostname())}\n"


@app.route('/trace/<service_number>')
def trace(service_number):
    # call service 2 from service 1
    if int(os.environ['SERVICE_NAME']) == 1:
        headers = {
            header: request.headers[header]
            for header in TRACE_HEADERS_TO_PROPAGATE
            if header in request.headers
        }
        requests.get("http://localhost:9000/trace/2", headers=headers)
    return f"Hello from behind Envoy (service {os.environ['SERVICE_NAME']})! hostname: {socket.gethostname()} resolvedhostname: {socket.gethostbyname(socket.gethostname())}\n"


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)
