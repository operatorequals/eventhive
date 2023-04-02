import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter

from fastapi_websocket_pubsub import PubSubEndpoint

import threading, multiprocessing
import contextlib

from ..logger import logger
import logging

for logger_name in ["uvicorn.access", "uvicorn.error"]:
    logging.getLogger(logger_name).handlers.clear()
    logging.getLogger(logger_name).propagate = False


class FastAPIPubSubServer:

    def __init__(self, connector_id, connector_config, global_config):
        self.conn_id = connector_id
        self.conn_conf = connector_config
        self.global_conf = global_config
        

        self.host = self.conn_conf['init']['host']
        self.port = self.conn_conf['init']['port']
        endpoint = self.conn_conf['init']['endpoint']
        self.endpoint = endpoint if endpoint.startswith(
            '/') else '/' + endpoint

        self.app = FastAPI()
        router = APIRouter()
        endpoint = PubSubEndpoint()
        endpoint.register_route(router)
        self.app.include_router(router)
        self.uvicorn_config = uvicorn.Config(self.app, host=self.host, port=self.port)
        self.uvicorn_server = uvicorn.Server(config=self.uvicorn_config)

        logger.info("FastAPI PubSub Server '%s' initialized" % self.conn_id)

    def run(self):
        self.uvicorn_server.run()

    def stop(self):
        self.process.terminate()

    def run_in_thread(self):
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
