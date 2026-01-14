# -*- coding: utf-8 -*-

import hmac
import hashlib
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class JustCallWebhookController(http.Controller):
    """Handle webhook events from JustCall"""

    @http.route('/ptt_justcall/webhook', type='http', auth='public',
                methods=['POST'], csrf=False)
    def justcall_webhook(self):
        """Process webhook events from JustCall"""
        try:
            # Get raw payload for signature validation
            payload = request.httprequest.data.decode('utf-8')
            
            # Parse JSON data
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                _logger.error("JustCall webhook: Invalid JSON payload")
                return http.Response(status=400)
            
            # Validate webhook signature (if configured)
            if not self._validate_signature(payload):
                _logger.warning("JustCall webhook: Invalid signature")
                return http.Response(status=401)
            
            # Log webhook receipt
            _logger.info("JustCall webhook received: %s", json.dumps(data, indent=2))
            
            # Process webhook event
            event_type = data.get('event_type') or data.get('type') or data.get('event')
            
            if event_type in ['call.completed', 'call.updated', '1', '2']:
                self._handle_call_event(data)
            elif event_type in ['sms.received', 'sms.sent', '3', '4']:
                self._handle_sms_event(data)
            else:
                _logger.info(f"JustCall webhook: Unhandled event type {event_type}")
            
            # Always return 200 to acknowledge receipt
            return http.Response(status=200)
            
        except Exception as e:
            _logger.error("JustCall webhook error: %s", str(e), exc_info=True)
            # Still return 200 to prevent JustCall from retrying
            return http.Response(status=200)

    def _validate_signature(self, payload):
        """Validate webhook signature using HMAC"""
        try:
            config = request.env['ptt.justcall.config'].sudo().search([
                ('active', '=', True)
            ], limit=1)
            
            if not config or not config.webhook_secret:
                # If no secret configured, allow (for development)
                # In production, you should always configure webhook secret
                _logger.warning("JustCall webhook: No webhook secret configured")
                return True
            
            # Get signature from header
            # JustCall may use different header names, check common ones
            signature = (
                request.httprequest.headers.get('X-JustCall-Signature') or
                request.httprequest.headers.get('X-Webhook-Signature') or
                request.httprequest.headers.get('X-Signature')
            )
            
            if not signature:
                _logger.warning("JustCall webhook: No signature header found")
                return False
            
            # Compute expected signature (HMAC-SHA256)
            expected = hmac.new(
                config.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(signature, expected)
            
        except Exception as e:
            _logger.error("JustCall webhook signature validation error: %s", str(e))
            return False

    def _handle_call_event(self, data):
        """Handle call-related webhook events"""
        try:
            # Create or update call record
            call = request.env['ptt.justcall.call'].sudo().create_from_webhook(data)
            if call:
                _logger.info("JustCall webhook: Created/updated call %s", call.justcall_call_id)
            else:
                _logger.warning("JustCall webhook: Failed to create call record")
        except Exception as e:
            _logger.error("JustCall webhook: Error handling call event: %s", str(e), exc_info=True)

    def _handle_sms_event(self, data):
        """Handle SMS-related webhook events"""
        try:
            # For now, log SMS events
            # You can extend this to create SMS records if needed
            _logger.info("JustCall webhook: SMS event received: %s", data.get('id'))
            
            # TODO: Create SMS model if needed
            # sms = request.env['justcall.sms'].sudo().create_from_webhook(data)
            
        except Exception as e:
            _logger.error("JustCall webhook: Error handling SMS event: %s", str(e), exc_info=True)
