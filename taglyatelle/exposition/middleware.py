"""Middleware to handle requests from smee server."""

import logging
import os
from typing import Callable

from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from taglyatelle.exposition.monitoring import tracing_request
from taglyatelle.webhooks.core.webhook_factory import WebhookSender

logger = logging.getLogger(__name__)

if os.path.exists(".env"):
    load_dotenv()

WEBHOOK_SECRET = str(os.getenv("WEBHOOK_SECRET"))
USE_TRACING_REQUEST = os.getenv("USE_TRACING_REQUEST") in ("true", "1", "yes")


class SmeeMiddleware(BaseHTTPMiddleware):
    """Middleware to process requests from smee server before reaching the API endpoints."""

    @tracing_request(enabled=USE_TRACING_REQUEST)
    async def dispatch(self, request: Request, call_next: Callable) -> Request | JSONResponse:
        """
        Process incoming requests to verify signatures and log details.

        Parameters
        ----------
        request
            The incoming request object

        call_next
            The next middleware or endpoint to call

        Returns
        -------
        The response from the next middleware or endpoint
        """
        payload_body = await request.body()

        webhook_sender = WebhookSender(request)
        webhook_sender.verify_signature(payload_body, WEBHOOK_SECRET)
        logger.info("Signature verified.")

        response = await call_next(request)

        return response
