"""OpenTelemetry instrumentation for Stock Analysis application."""

import logging
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from opentelemetry.sdk.metrics import MeterProvider
    from sqlalchemy.ext.asyncio import AsyncEngine

    from stock_analysis.settings import Settings


class _Providers:
    """Mutable container for OTel provider singletons."""

    tracer: TracerProvider | None = None
    meter: MeterProvider | None = None
    logger: LoggerProvider | None = None
    log_handler: LoggingHandler | None = None


_providers = _Providers()


def _build_resource(service_name: str) -> Resource:
    """Create the OTel resource describing this service."""
    return Resource.create({SERVICE_NAME: service_name})


def setup_telemetry(service_name: str = "stock-analysis-api") -> None:
    """Initialise OpenTelemetry providers and exporters.

    Call once during application startup (inside the FastAPI lifespan).

    Args:
        settings: Application settings containing monitoring host/port.
        service_name: Logical service name used in telemetry data.
    """
    settings: Settings = get_settings()
    otlp_endpoint: str = f"http://{settings.monitoring_host}:{settings.monitoring_port}"
    resource: Resource = _build_resource(service_name)

    _providers.tracer = TracerProvider(resource=resource)
    _providers.tracer.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True),
        )
    )
    trace.set_tracer_provider(_providers.tracer)

    _providers.logger = LoggerProvider(resource=resource)
    _providers.logger.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otlp_endpoint, insecure=True),
        )
    )
    set_logger_provider(_providers.logger)

    if _providers.log_handler is None:
        _providers.log_handler = LoggingHandler(
            logger_provider=_providers.logger,
            level=logging.INFO,
        )
        logging.getLogger().addHandler(_providers.log_handler)

    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    LangchainInstrumentor().instrument()


def instrument_app(app: FastAPI) -> None:
    """Apply automatic FastAPI instrumentation for traces.

    Args:
        app: The FastAPI application instance.
    """
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics",
    )


def instrument_db_engine(engine: AsyncEngine) -> None:
    """Apply automatic SQLAlchemy instrumentation for traces.

    Args:
        engine: The async SQLAlchemy engine.
    """
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
    )


def start_metrics_server(port: int = 9464) -> None:
    """Start a lightweight HTTP server exposing /metrics for Prometheus.

    Args:
        port: Port to bind the metrics server on.
    """
    start_http_server(port)


def shutdown_telemetry() -> None:
    """Flush and shut down all OTel providers gracefully."""
    if _providers.log_handler is not None:
        logging.getLogger().removeHandler(_providers.log_handler)
        _providers.log_handler = None

    if _providers.tracer is not None:
        _providers.tracer.shutdown()
    if _providers.meter is not None:
        _providers.meter.shutdown()
    if _providers.logger is not None:
        _providers.logger.shutdown()

    LoggingInstrumentor().uninstrument()
    HTTPXClientInstrumentor().uninstrument()
    RequestsInstrumentor().uninstrument()
    RedisInstrumentor().uninstrument()
    PsycopgInstrumentor().uninstrument()
    LangchainInstrumentor().uninstrument()
