# -*- coding: utf-8 -*-

import base64
import logging
import requests
import time
from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JustCallAPI(models.AbstractModel):
    """API client for JustCall with rate limiting"""
    _name = 'justcall.api'
    _description = 'JustCall API Client'

    # Rate limiting (Team plan: 30 req/min)
    _rate_limit = 30  # requests per minute
    _request_times = {}
    _request_counts = {}

    def _get_config(self):
        """Get active JustCall configuration"""
        return self.env['ptt.justcall.config'].get_active_config()

    def _get_auth_headers(self):
        """Generate authentication headers"""
        config = self._get_config()
        return config._get_auth_headers()

    def _check_rate_limit(self):
        """Check and enforce rate limits"""
        current_minute = int(time.time() / 60)
        company_id = self.env.company.id
        key = f"{company_id}_{current_minute}"
        
        # Initialize if needed
        if key not in self._request_counts:
            self._request_counts[key] = 0
        
        # Check rate limit
        if self._request_counts[key] >= self._rate_limit:
            # Wait until next minute
            wait_time = 60 - (time.time() % 60)
            _logger.warning("JustCall API: Rate limit reached, waiting %d seconds", wait_time)
            time.sleep(wait_time)
            # Reset for new minute
            current_minute = int(time.time() / 60)
            key = f"{company_id}_{current_minute}"
            self._request_counts[key] = 0
        
        self._request_counts[key] += 1

    def _make_request(self, method, endpoint, data=None, params=None):
        """Make API request to JustCall"""
        self._check_rate_limit()
        
        headers = self._get_auth_headers()
        url = f"https://api.justcall.io{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise UserError(_("Unsupported HTTP method: %s") % method)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            _logger.error("JustCall API error: %s", error_msg)
            raise UserError(_("JustCall API error: %s") % error_msg)
        except requests.exceptions.RequestException as e:
            _logger.error("JustCall API request error: %s", str(e))
            raise UserError(_("JustCall API request error: %s") % str(e))

    def make_call(self, from_number, to_number, user_id=None):
        """Initiate a call via JustCall API"""
        data = {
            'from': from_number,
            'to': to_number,
        }
        if user_id:
            data['user_id'] = user_id
        
        return self._make_request('POST', '/v1/calls/make', data=data)

    def get_call(self, call_id):
        """Get call details"""
        return self._make_request('GET', f'/v1/calls/get', params={'id': call_id})

    def send_sms(self, from_number, to_number, message, user_id=None):
        """Send SMS via JustCall API"""
        data = {
            'from': from_number,
            'to': to_number,
            'text': message,
        }
        if user_id:
            data['user_id'] = user_id
        
        return self._make_request('POST', '/v1/texts/new', data=data)

    def add_contact(self, name, phone, email=None, company=None):
        """Add contact to JustCall"""
        data = {
            'name': name,
            'phone': phone,
        }
        if email:
            data['email'] = email
        if company:
            data['company'] = company
        
        return self._make_request('POST', '/v1/contacts/add', data=data)

    def get_users(self):
        """Get list of JustCall users"""
        return self._make_request('GET', '/v2.1/users')
