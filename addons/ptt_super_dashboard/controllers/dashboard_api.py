import json
import logging
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request, Controller, route

_logger = logging.getLogger(__name__)


class TeamDashboardAPI(Controller):
    """REST API for team dashboard data access and model discovery"""

    @route('/api/team-dashboard/models', type='http', auth='user', methods=['GET'])
    def get_available_models(self):
        """Get list of all available models"""
        try:
            registry = request.env.registry
            user = request.env.user
            
            # Priority models
            priority_models = [
                'crm.lead',
                'sale.order',
                'account.move',
                'project.project',
                'project.task',
                'res.partner',
                'calendar.event',
            ]
            
            all_models = []
            
            # Add priority models first
            for model_name in priority_models:
                if model_name in registry:
                    model = request.env[model_name]
                    all_models.append({
                        'name': model_name,
                        'label': model._description or model_name,
                        'is_priority': True,
                    })
            
            # Add remaining models
            for model_name in sorted(registry.models.keys()):
                if model_name not in priority_models and not model_name.startswith('ir.'):
                    try:
                        model = request.env[model_name]
                        if hasattr(model, '_auto') and model._auto:
                            all_models.append({
                                'name': model_name,
                                'label': model._description or model_name,
                                'is_priority': False,
                            })
                    except:
                        pass
            
            return http.Response(
                json.dumps({
                    'status': 'success',
                    'count': len(all_models),
                    'models': all_models,
                }),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching models')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    @route('/api/team-dashboard/model-fields', type='http', auth='user', methods=['POST'])
    def get_model_fields(self):
        """Get field metadata for a model"""
        try:
            data = request.get_json_data()
            model_name = data.get('model')
            
            if not model_name:
                return http.Response(
                    json.dumps({'status': 'error', 'message': 'Model name required'}),
                    content_type='application/json',
                    status=400,
                )
            
            model = request.env[model_name]
            fields = model.fields_get()
            
            # Filter and format fields
            formatted_fields = []
            for field_name, field_info in fields.items():
                formatted_fields.append({
                    'name': field_name,
                    'label': field_info.get('string', field_name),
                    'type': field_info.get('type'),
                    'required': field_info.get('required', False),
                    'readonly': field_info.get('readonly', False),
                    'relation': field_info.get('relation'),
                })
            
            return http.Response(
                json.dumps({
                    'status': 'success',
                    'model': model_name,
                    'count': len(formatted_fields),
                    'fields': formatted_fields,
                }),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching model fields')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    @route('/api/team-dashboard/data', type='http', auth='user', methods=['POST'])
    def get_dashboard_data(self):
        """Get aggregated data from a model"""
        try:
            data = request.get_json_data()
            model_name = data.get('model')
            fields = data.get('fields', [])
            domain = data.get('domain', [])
            group_by = data.get('group_by')
            aggregation = data.get('aggregation')
            limit = data.get('limit', 100)
            
            model = request.env[model_name]
            
            # Apply company filter
            domain = self._apply_company_filter(model, domain)
            
            # Fetch records
            records = model.search_read(domain, fields, limit=limit)
            
            # Apply aggregation if specified
            if aggregation and group_by:
                result = self._apply_aggregation(records, group_by, aggregation)
            else:
                result = records
            
            return http.Response(
                json.dumps({
                    'status': 'success',
                    'model': model_name,
                    'count': len(result),
                    'data': result,
                }),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching dashboard data')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    @route('/api/team-dashboard/time-series', type='http', auth='user', methods=['POST'])
    def get_time_series_data(self):
        """Get time-series data"""
        try:
            data = request.get_json_data()
            model_name = data.get('model')
            date_field = data.get('date_field', 'create_date')
            value_field = data.get('value_field')
            aggregation = data.get('aggregation', 'sum')
            group_period = data.get('group_period', 'month')
            domain = data.get('domain', [])
            limit = data.get('limit', 1000)
            
            model = request.env[model_name]
            domain = self._apply_company_filter(model, domain)
            
            fields = [date_field]
            if value_field and value_field != 'id':
                fields.append(value_field)
            
            records = model.search_read(domain, fields, limit=limit)
            result = self._group_by_period(records, date_field, value_field, aggregation, group_period)
            
            return http.Response(
                json.dumps({
                    'status': 'success',
                    'model': model_name,
                    'count': len(result),
                    'data': result,
                }),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching time-series data')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    @route('/api/team-dashboard/user-stats', type='http', auth='user', methods=['GET'])
    def get_user_stats(self):
        """Get personal user statistics"""
        try:
            user = request.env.user
            today = datetime.now().date()
            
            stats = {
                'total_tasks': request.env['project.task'].search_count([('user_ids', 'in', [user.id])]),
                'overdue_tasks': request.env['project.task'].search_count([
                    ('user_ids', 'in', [user.id]),
                    ('date_deadline', '<', today),
                    ('state', '!=', 'done')
                ]),
                'due_today': request.env['project.task'].search_count([
                    ('user_ids', 'in', [user.id]),
                    ('date_deadline', '=', today),
                    ('state', '!=', 'done')
                ]),
                'completed_this_week': request.env['project.task'].search_count([
                    ('user_ids', 'in', [user.id]),
                    ('date_deadline', '>=', today - timedelta(days=7)),
                    ('state', '=', 'done')
                ]),
            }
            
            return http.Response(
                json.dumps({'status': 'success', 'data': stats}),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching user stats')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    @route('/api/team-dashboard/team-metrics', type='http', auth='user', methods=['GET'])
    def get_team_metrics(self):
        """Get team metrics"""
        try:
            user = request.env.user
            today = datetime.now().date()
            
            metrics = {
                'total_team_members': request.env['res.users'].search_count([('company_id', '=', user.company_id.id)]),
                'active_projects': request.env['project.project'].search_count([
                    ('company_id', '=', user.company_id.id),
                    ('state', '=', 'open')
                ]),
                'open_opportunities': request.env['crm.lead'].search_count([
                    ('company_id', '=', user.company_id.id),
                    ('type', '=', 'opportunity'),
                    ('probability', '<', 100)
                ]),
                'overdue_tasks_company': request.env['project.task'].search_count([
                    ('company_id', '=', user.company_id.id),
                    ('date_deadline', '<', today),
                    ('state', '!=', 'done')
                ]),
                'total_revenue_this_month': sum(request.env['sale.order'].search([
                    ('company_id', '=', user.company_id.id),
                    ('create_date', '>=', today.replace(day=1)),
                    ('state', 'in', ['sale', 'done'])
                ]).mapped('amount_total')),
            }
            
            return http.Response(
                json.dumps({'status': 'success', 'data': metrics}),
                content_type='application/json',
            )
        except Exception as e:
            _logger.exception('Error fetching team metrics')
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
            )

    # Helper methods
    
    def _apply_company_filter(self, model, domain):
        """Apply company filtering"""
        user = request.env.user
        if hasattr(model, 'company_id'):
            domain = domain + [('company_id', '=', user.company_id.id)]
        return domain

    def _apply_aggregation(self, records, group_by, aggregation):
        """Apply aggregation to records"""
        result = {}
        
        for record in records:
            key = record.get(group_by, 'N/A')
            if key not in result:
                result[key] = {'group': key, 'count': 0, 'values': []}
            
            result[key]['count'] += 1
            for value in record.values():
                if isinstance(value, (int, float)):
                    result[key]['values'].append(value)
        
        final_result = []
        for key, data in result.items():
            agg_value = 0
            if aggregation == 'count':
                agg_value = data['count']
            elif aggregation == 'sum' and data['values']:
                agg_value = sum(data['values'])
            elif aggregation == 'avg' and data['values']:
                agg_value = sum(data['values']) / len(data['values'])
            elif aggregation == 'max' and data['values']:
                agg_value = max(data['values'])
            elif aggregation == 'min' and data['values']:
                agg_value = min(data['values'])
            
            final_result.append({group_by: key, 'value': agg_value, 'count': data['count']})
        
        return final_result

    def _group_by_period(self, records, date_field, value_field, aggregation, period):
        """Group records by time period"""
        grouped = {}
        
        for record in records:
            date_val = record.get(date_field)
            if not date_val:
                continue
            
            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                except:
                    continue
            elif not isinstance(date_val, datetime):
                continue
            
            if period == 'day':
                period_key = date_val.strftime('%Y-%m-%d')
            elif period == 'week':
                period_key = date_val.strftime('%Y-W%U')
            elif period == 'month':
                period_key = date_val.strftime('%Y-%m')
            elif period == 'year':
                period_key = date_val.strftime('%Y')
            else:
                period_key = date_val.strftime('%Y-%m')
            
            if period_key not in grouped:
                grouped[period_key] = {'period': period_key, 'count': 0, 'values': []}
            
            grouped[period_key]['count'] += 1
            if value_field and value_field in record:
                value = record[value_field]
                if isinstance(value, (int, float)):
                    grouped[period_key]['values'].append(value)
        
        result = []
        for period_key in sorted(grouped.keys()):
            data = grouped[period_key]
            agg_value = 0
            
            if aggregation == 'count':
                agg_value = data['count']
            elif aggregation == 'sum' and data['values']:
                agg_value = sum(data['values'])
            elif aggregation == 'avg' and data['values']:
                agg_value = sum(data['values']) / len(data['values'])
            elif aggregation == 'max' and data['values']:
                agg_value = max(data['values'])
            elif aggregation == 'min' and data['values']:
                agg_value = min(data['values'])
            
            result.append({'period': period_key, 'value': agg_value, 'count': data['count']})
        
        return result
