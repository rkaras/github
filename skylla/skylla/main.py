#!/usr/bin/env python

import logging

import starlette_prometheus
from fastapi import FastAPI

from .routes.api import router as api_router
from .settings import cfg

logger = logging.getLogger(__name__)

if cfg["sentry"]["dsn"] != "":
    import sentry_sdk

    sentry_sdk.init(cfg["sentry"]["dsn"], ca_certs=cfg["ca_certs"])


def get_application() -> FastAPI:
    app = FastAPI(title="Release manegement integration service",)
    app.add_middleware(starlette_prometheus.PrometheusMiddleware)
    app.add_route("/metrics", starlette_prometheus.metrics)
    app.include_router(api_router)
    return app


app = get_application()


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
