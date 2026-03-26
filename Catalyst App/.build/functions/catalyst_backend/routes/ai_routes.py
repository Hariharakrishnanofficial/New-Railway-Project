"""
AI Routes — NLP search, booking assistant, recommendations, analytics AI.
All endpoints require authentication. API keys loaded from environment only.
"""

import os
import json
import logging
import requests
from flask import Blueprint, jsonify, request
from core.security import require_auth, require_admin
from core.exceptions import AIServiceError, RailwayException
from ai.nlp_search import nlp_search_engine, booking_assistant, recommendation_engine, analytics_ai
from services.analytics_service import analytics_service
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES

logger   = logging.getLogger(__name__)
ai_bp    = Blueprint('ai', __name__)


# ── QWEN PROXY (via Zoho Catalyst QuickML) ────────────────────────────────────
# Catalyst access token can be set via env var for direct use
CATALYST_ACCESS_TOKEN = os.getenv('CATALYST_ACCESS_TOKEN', '')

@ai_bp.route('/api/ai/qwen', methods=['POST'])
def qwen_proxy():
    """
    POST /api/ai/qwen
    Proxies requests to Zoho Catalyst QuickML LLM API (Qwen model).
    Body: { messages, max_tokens, temperature, system }
    Uses Catalyst access token from environment variable.
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    if not data.get('messages'):
        return jsonify({'success': False, 'error': 'messages is required'}), 400

    # Build messages for Catalyst QuickML
    messages = list(data.get('messages', []))

    # Add system message if provided
    system_content = data.get('system', '')
    if system_content:
        if not messages or messages[0].get('role') != 'system':
            messages = [{'role': 'system', 'content': system_content}] + messages

    # Build the prompt from messages (Catalyst may expect a single prompt)
    # Convert chat messages to a single prompt string for compatibility
    prompt_parts = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            prompt_parts.append(f"System: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Assistant: {content}")
        else:
            prompt_parts.append(f"User: {content}")

    full_prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"

    try:
        # Use static CATALYST_ACCESS_TOKEN from environment
        access_token = CATALYST_ACCESS_TOKEN or os.getenv('CATALYST_ACCESS_TOKEN', '')
        if not access_token:
            return jsonify({'success': False, 'error': 'No Catalyst access token configured'}), 503
        auth_header = f'Zoho-oauthtoken {access_token}'

        # Build system prompt from system messages
        system_parts = []
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                system_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(content)

        catalyst_payload = {
            "prompt": "\n\n".join(prompt_parts) if prompt_parts else full_prompt,
            "model": os.getenv("CATALYST_MODEL", "crm-di-qwen_text_14b-fp8-it"),
            "system_prompt": "\n\n".join(system_parts),
            "temperature": float(data.get('temperature', 0.7)),
            "max_tokens": int(data.get('max_tokens', 2048)),
            "top_p": 0.9,
            "top_k": 50,
            "best_of": 1,
        }

        logger.info(f"Calling Zoho Catalyst QuickML with prompt: {catalyst_payload['prompt'][:100]}")

        # Call Zoho Catalyst QuickML LLM endpoint (JSON body)
        response = requests.post(
            'https://api.catalyst.zoho.in/quickml/v2/project/31207000000011084/llm/chat',
            headers={
                'Authorization': auth_header,
                'Content-Type': 'application/json',
                'CATALYST-ORG': os.getenv('CATALYST_ORG', '60066581545'),
            },
            json=catalyst_payload,
            timeout=90
        )
        
        logger.info(f"Zoho Catalyst response status: {response.status_code}")
        logger.debug(f"Zoho Catalyst response body: {response.text[:1000]}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"Zoho Catalyst parsed response: {str(result)[:500]}")
            
            # Normalize response - Catalyst may return different formats
            choices = []
            
            # Check for OpenAI-compatible format
            if 'choices' in result and result['choices']:
                choices = result['choices']
            # Check for direct message format
            elif 'message' in result:
                choices = [{'message': result['message']}]
            # Check for content field
            elif 'content' in result:
                choices = [{'message': {'role': 'assistant', 'content': result['content']}}]
            # Check for response field
            elif 'response' in result:
                resp = result['response']
                if isinstance(resp, str):
                    choices = [{'message': {'role': 'assistant', 'content': resp}}]
                elif isinstance(resp, dict) and 'content' in resp:
                    choices = [{'message': {'role': 'assistant', 'content': resp['content']}}]
            # Check for output field (some Catalyst endpoints use this)
            elif 'output' in result:
                out = result['output']
                if isinstance(out, str):
                    choices = [{'message': {'role': 'assistant', 'content': out}}]
                elif isinstance(out, dict):
                    choices = [{'message': {'role': 'assistant', 'content': out.get('content', str(out))}}]
            # Check for text field
            elif 'text' in result:
                choices = [{'message': {'role': 'assistant', 'content': result['text']}}]
            # Check for generated_text field
            elif 'generated_text' in result:
                choices = [{'message': {'role': 'assistant', 'content': result['generated_text']}}]
            # Check for completion field
            elif 'completion' in result:
                choices = [{'message': {'role': 'assistant', 'content': result['completion']}}]
            
            return jsonify({
                'success': True,
                'id': result.get('id', ''),
                'model': 'qwen',
                'choices': choices,
                'usage': result.get('usage', {}),
                'raw_response': result  # Include for debugging
            }), 200
        else:
            logger.error(f'Zoho Catalyst Qwen API error: {response.status_code} - {response.text}')
            return jsonify({
                'success': False,
                'error': {
                    'type': 'api_error',
                    'message': f'Zoho Catalyst API returned {response.status_code}',
                    'details': response.text
                }
            }), 502 if response.status_code in (401, 403) else response.status_code
            
    except requests.exceptions.Timeout:
        logger.error('Zoho Catalyst Qwen API timeout')
        return jsonify({'success': False, 'error': {'type': 'timeout', 'message': 'Request timed out'}}), 504
    except requests.exceptions.RequestException as e:
        logger.exception(f'Qwen proxy error: {e}')
        return jsonify({'success': False, 'error': {'type': 'network_error', 'message': str(e)}}), 502
    except Exception as e:
        logger.exception(f'Qwen proxy unexpected error: {e}')
        return jsonify({'success': False, 'error': {'type': 'server_error', 'message': str(e)}}), 500


# ── NLP SEARCH ────────────────────────────────────────────────────────────────
@ai_bp.route('/api/ai/search', methods=['POST'])
def ai_search():
    """
    POST /api/ai/search
    Body: { "query": "Show all cancelled bookings this week" }
    Translates NL query to Zoho criteria and executes it.
    """
    data  = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'query is required'}), 400

    try:
        result = nlp_search_engine.process_query(query)
    except AIServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        logger.exception(f'ai_search error: {e}')
        return jsonify({'success': False, 'error': 'AI search failed'}), 500

    result_type = result.get('type', 'search')

    # If booking intent — return intent for frontend to handle
    if result_type == 'booking':
        return jsonify({'success': True, 'type': 'booking',
                        'booking_intent': result.get('booking_intent', {}),
                        'engine': result.get('engine')}), 200

    # If analysis intent — run analytics
    if result_type == 'analysis':
        analysis_type = result.get('analysis_type', 'booking_trends')
        days          = result.get('date_range', 30)
        try:
            if analysis_type == 'top_trains':
                data_result = analytics_service.get_top_trains()
            elif analysis_type == 'booking_trends':
                data_result = analytics_service.get_booking_trends(days=days)
            elif analysis_type == 'revenue':
                data_result = analytics_service.get_class_revenue()
            else:
                data_result = analytics_service.get_overview_stats()
            insight = analytics_ai.generate_insights(data_result, query)
        except Exception as e:
            logger.warning(f'analytics error: {e}')
            data_result = {}
            insight     = 'Analytics unavailable'
        return jsonify({'success': True, 'type': 'analysis',
                        'data': data_result, 'insight': insight,
                        'engine': result.get('engine')}), 200

    # Search/filter intent — execute against CloudScale
    report   = result.get('report', 'Bookings')
    criteria = result.get('translated_criteria')
    is_count = result.get('is_count', False)

    # Map report display name to table name
    report_map = {
        'All_Bookings': TABLES['bookings'],
        'All_Trains':   TABLES['trains'],
        'All_Users':    TABLES['users'],
        'All_Stations': TABLES['stations'],
        'Bookings':     TABLES['bookings'],
        'Trains':       TABLES['trains'],
        'Users':        TABLES['users'],
        'Stations':     TABLES['stations'],
    }
    table_name = report_map.get(report, report)

    try:
        fetch_result = cloudscale_repo.get_all_records(table_name, criteria=criteria, limit=200)
        if not fetch_result.get('success'):
            return jsonify({'success': False, 'error': fetch_result.get('error', 'Query failed'),
                            'engine': result.get('engine')}), 500

        records = fetch_result.get('data', {}).get('data', []) or []
        count   = len(records)

        return jsonify({
            'success':             True,
            'type':                'search',
            'report':              report,
            'criteria':            criteria,
            'count':               count,
            'records':             records if not is_count else [],
            'is_count':            is_count,
            'description':         result.get('description', ''),
            'engine':              result.get('engine'),
            'confidence':          result.get('confidence', 1.0),
        }), 200

    except Exception as e:
        logger.exception(f'ai_search execution error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── BOOKING ASSISTANT (conversational) ───────────────────────────────────────
@ai_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """
    POST /api/ai/chat
    Body: {
        "message": "Chennai",
        "history": [...],
        "booking_state": { "stage": "from", ... }  # Optional: booking flow state
    }
    Conversational booking assistant with intent-first routing and stage-based flow.
    """
    from ai.booking_conversation import (
        booking_conversation, dict_to_state, state_to_dict,
        BookingState, CLASS_FARE_KEY, CLASS_SEAT_KEY
    )
    from repositories.cloudscale_repository import CriteriaBuilder

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    history = data.get('history', [])
    state_dict = data.get('booking_state') or {}
    user_id = data.get('user_id')

    if not message:
        return jsonify({'success': False, 'error': 'message is required'}), 400

    try:
        # Reconstruct state from frontend
        state = dict_to_state(state_dict)

        # Process message through conversation flow
        response = booking_conversation.process_message(message, state, history)

        # Handle triggers
        if response.trigger == 'search_trains':
            # Search trains from Zoho
            trains = _search_trains_for_booking(response.state)
            response.state.trains_list = trains

            if trains:
                response.state.stage = 'select_train'
                response.state.menu_type = 'train_select'
                train_display = booking_conversation.format_train_results(trains, response.state)
                response.reply = response.reply.rstrip('.') + '\n\n' + train_display
            else:
                response.state.menu_type = 'no_trains_found'
                response.reply = f"No trains found from {response.state.from_station} to {response.state.to_station} on {response.state.date_display} in {response.state.class_display} class.\n\nWould you like to:\n1. Try a different date\n2. Try a different class\n3. Change the route"

        elif response.trigger == 'create_booking':
            # Create booking via BookingService
            if user_id:
                booking_result = _create_booking_from_state(response.state, user_id)
                if booking_result.get('success'):
                    pnr = booking_result.get('pnr', 'N/A')
                    response.reply = f"✅ Booking confirmed!\n\nYour PNR: {pnr}\n\nPlease save this number for future reference. You can check your booking status anytime using this PNR."
                    response.state = BookingState()  # Reset state
                    response.state.stage = 'done'
                    response.trigger = 'booking_complete'
                else:
                    response.reply = f"❌ Booking failed: {booking_result.get('error', 'Unknown error')}\n\nPlease try again or contact support."
            else:
                response.reply = "❌ Please log in to complete your booking."

        elif response.trigger == 'pnr_check':
            # Check PNR status
            pnr = message.upper()
            pnr_result = _check_pnr_status(pnr)
            if pnr_result:
                response.reply = pnr_result
            else:
                response.reply = f"Could not find booking with PNR {pnr}. Please check the number and try again."

        return jsonify({
            'success': True,
            'reply': response.reply,
            'booking_state': state_to_dict(response.state),
            'trigger': response.trigger,
        }), 200

    except Exception as e:
        logger.exception(f'ai_chat error: {e}')
        return jsonify({'success': False, 'error': 'Chat assistant unavailable'}), 500


def _search_trains_for_booking(state):
    """Search trains based on booking state."""
    try:
        table_name = TABLES['trains']

        # Get station codes for search
        from_station = state.from_station or ''
        to_station = state.to_station or ''

        # Fetch all trains and filter locally
        result = cloudscale_repo.get_all_records(table_name, criteria=None, limit=100)

        if not result.get('success'):
            logger.error(f"Train search failed: {result.get('error')}")
            return []

        records = result.get('data', {}).get('data', []) or []

        # Filter by route
        filtered = []
        for train in records:
            from_disp = ''
            to_disp = ''

            # Handle lookup field format
            from_field = train.get('From_Station', '')
            to_field = train.get('To_Station', '')

            if isinstance(from_field, dict):
                from_disp = (from_field.get('display_value') or '').lower()
            else:
                from_disp = str(from_field).lower()

            if isinstance(to_field, dict):
                to_disp = (to_field.get('display_value') or '').lower()
            else:
                to_disp = str(to_field).lower()

            # Check if stations match (partial match)
            from_match = from_station.lower() in from_disp if from_station else True
            to_match = to_station.lower() in to_disp if to_station else True

            # Also check if train is active
            is_active = train.get('Is_Active', True)
            if isinstance(is_active, str):
                is_active = is_active.lower() == 'true'

            if from_match and to_match and is_active:
                filtered.append(train)

        return filtered[:10]  # Return max 10 trains

    except Exception as e:
        logger.exception(f"Train search error: {e}")
        return []


def _create_booking_from_state(state, user_id):
    """Create a booking from the conversation state."""
    try:
        from services.booking_service import booking_service

        booking_data = {
            'train_id': state.train_id,
            'user_id': user_id,
            'journey_date': state.date,
            'travel_class': state.travel_class,
            'passengers': state.passengers,
            'quota': 'GN',  # Default to General quota
        }

        result = booking_service.create(booking_data)
        return result

    except Exception as e:
        logger.exception(f"Booking creation error: {e}")
        return {'success': False, 'error': str(e)}


def _check_pnr_status(pnr):
    """Check PNR status from CloudScale."""
    try:
        table_name = TABLES['bookings']

        # Search by PNR
        cb = CriteriaBuilder().eq('PNR', pnr)
        result = cloudscale_repo.get_all_records(table_name, criteria=cb.build(), limit=1)

        if not result.get('success'):
            return None

        records = result.get('data', {}).get('data', []) or []
        if not records:
            return None

        booking = records[0]

        # Format PNR status response
        train_name = booking.get('Train_Name', 'N/A')
        from_station = booking.get('From_Station', 'N/A')
        to_station = booking.get('To_Station', 'N/A')
        journey_date = booking.get('Journey_Date', 'N/A')
        travel_class = booking.get('Travel_Class', 'N/A')
        status = booking.get('Status', 'N/A')
        total_fare = booking.get('Total_Fare', 0)

        # Handle lookup fields
        if isinstance(from_station, dict):
            from_station = from_station.get('display_value', 'N/A')
        if isinstance(to_station, dict):
            to_station = to_station.get('display_value', 'N/A')

        response = f"""📋 PNR Status: {pnr}
━━━━━━━━━━━━━━━━━━━━━━━
🚂 Train: {train_name}
🚉 Route: {from_station} → {to_station}
📅 Date: {journey_date}
🎫 Class: {travel_class}
💰 Fare: ₹{total_fare}

📌 Status: {status.upper()}
━━━━━━━━━━━━━━━━━━━━━━━"""

        return response

    except Exception as e:
        logger.exception(f"PNR check error: {e}")
        return None


# ── RECOMMENDATIONS ───────────────────────────────────────────────────────────
@ai_bp.route('/api/ai/recommendations', methods=['GET'])
def ai_recommendations():
    """
    GET /api/ai/recommendations?user_id=X&source=MAS&destination=SBC
    Returns personalized train recommendations.
    """
    user_id     = request.args.get('user_id', '').strip()
    source      = request.args.get('source', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()

    if not user_id:
        return jsonify({'success': False, 'error': 'user_id is required'}), 400

    try:
        recs = recommendation_engine.get_recommendations(user_id, source, destination)
        return jsonify({'success': True, 'recommendations': recs, 'count': len(recs)}), 200
    except Exception as e:
        logger.exception(f'recommendations error: {e}')
        return jsonify({'success': False, 'error': 'Recommendations unavailable'}), 500


# ── ANALYTICS AI ──────────────────────────────────────────────────────────────
@ai_bp.route('/api/ai/analyze', methods=['POST'])
@require_admin
def ai_analyze():
    """
    POST /api/ai/analyze
    Body: { "type": "booking_trends|top_trains|revenue|routes", "question": "...", "days": 30 }
    Admin-only. Returns structured analytics + Gemini-generated insight text.
    """
    data      = request.get_json(silent=True) or {}
    atype     = data.get('type', 'overview')
    question  = data.get('question', '')
    days      = int(data.get('days', 30))

    try:
        if atype == 'booking_trends':
            analytics_data = analytics_service.get_booking_trends(days=days)
        elif atype == 'top_trains':
            analytics_data = analytics_service.get_top_trains()
        elif atype == 'routes':
            analytics_data = analytics_service.get_route_popularity()
        elif atype == 'revenue':
            analytics_data = analytics_service.get_class_revenue()
        else:
            analytics_data = analytics_service.get_overview_stats()

        insight = analytics_ai.generate_insights(analytics_data, question)
        return jsonify({'success': True, 'analytics': analytics_data, 'insight': insight, 'type': atype}), 200

    except Exception as e:
        logger.exception(f'ai_analyze error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── SEAT AVAILABILITY PREDICTION ──────────────────────────────────────────────
@ai_bp.route('/api/ai/predict-availability', methods=['GET'])
def predict_availability():
    """
    GET /api/ai/predict-availability?train_id=X&date=YYYY-MM-DD&class=SL
    Returns a prediction label and recommendation.
    """
    from repositories.cache_manager import cache
    train_id     = request.args.get('train_id', '').strip()
    journey_date = request.args.get('date', '').strip()
    cls          = request.args.get('class', 'SL').strip()

    if not train_id or not journey_date:
        return jsonify({'success': False, 'error': 'train_id and date are required'}), 400

    cache_key = f'predict:{train_id}:{journey_date}:{cls}'
    cached    = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, **cached, 'cached': True}), 200

    try:
        from datetime import datetime as dt
        days_ahead = (dt.strptime(journey_date, '%Y-%m-%d') - dt.now()).days
    except Exception:
        days_ahead = 7

    # Rule-based prediction (no ML needed — uses booking history patterns)
    # For a production system, replace with Gemini-powered or ML prediction
    if days_ahead <= 3:
        prediction = 'LOW'
        label      = 'Very Limited'
        suggestion = 'Book immediately — very few seats remain'
        color      = 'red'
    elif days_ahead <= 14:
        prediction = 'MEDIUM'
        label      = 'Filling Fast'
        suggestion = 'Book soon — seats filling up'
        color      = 'orange'
    else:
        prediction = 'HIGH'
        label      = 'Good Availability'
        suggestion = 'Good time to book'
        color      = 'green'

    result = {'prediction': prediction, 'label': label, 'suggestion': suggestion,
              'color': color, 'days_ahead': days_ahead, 'class': cls}
    cache.set(cache_key, result, ttl=3600)
    return jsonify({'success': True, **result}), 200


# ── CACHE STATS (admin only) ──────────────────────────────────────────────────
@ai_bp.route('/api/ai/cache-stats', methods=['GET'])
@require_admin
def cache_stats():
    from repositories.cache_manager import cache
    from ai.qwen_client import qwen_breaker
    return jsonify({
        'success': True,
        'cache': cache.stats(),
        'circuit_breaker': qwen_breaker.stats(),
        'model': 'qwen',
    }), 200


# ── CACHE CLEAR (admin only) ──────────────────────────────────────────────────
@ai_bp.route('/api/ai/cache/invalidate', methods=['POST'])
@require_admin
def cache_invalidate():
    from repositories.cache_manager import cache
    data   = request.get_json(silent=True) or {}
    prefix = data.get('prefix', '')
    if prefix:
        count = cache.invalidate(prefix)
        return jsonify({'success': True, 'message': f'Invalidated {count} keys with prefix "{prefix}"'}), 200
    cache.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'}), 200
# ── AI AGENT (intent detection + skill routing via Qwen) ──────────────────────
@ai_bp.route('/api/ai/agent', methods=['POST'])
def ai_agent_chat():
    """
    POST /api/ai/agent
    Body: {
      "message": "Book 2 tickets from Chennai to Bangalore tomorrow",
      "history": [...],
      "user_role": "User"
    }
    AI agent with intent detection and skill routing (powered by Qwen).
    """
    from ai.gemini_agent import gemini_agent

    data      = request.get_json(silent=True) or {}
    message   = (data.get('message') or '').strip()
    history   = data.get('history', [])
    user_role = data.get('user_role', 'User')

    if not message:
        return jsonify({'success': False, 'error': 'message is required'}), 400

    try:
        result = gemini_agent.chat(message, history, user_role)
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        logger.exception(f'ai_agent error: {e}')
        return jsonify({'success': False, 'error': 'Agent unavailable'}), 500


# ── MCP QUERY (structured database query execution) ─────────────────────────
# Lookup fields that need `contains` instead of `eq` (they store display_value like "MAS-Chennai Central")
_LOOKUP_FIELDS = {
    'Trains': {'From_Station', 'To_Station'},
    'Bookings': {'Users', 'Trains'},
    'Fares': {'Train', 'From_Station', 'To_Station'},
    'Train_Routes': {'Trains'},
    'Route_Stops': {'Train_Routes', 'Stations'},
    'Passengers': {'Booking'},
    'Announcements': {'Trains', 'Stations'},
    'Inventory': {'Train'},
    'Coach_Layouts': {'Train'},
}

# Module name → Zoho report name
_MODULE_REPORT_MAP = {
    'Stations':       'stations',
    'Trains':         'trains',
    'Bookings':       'bookings',
    'Users':          'users',
    'Fares':          'fares',
    'Train_Routes':   'train_routes',
    'Route_Stops':    'route_stops',
    'Passengers':     'passengers',
    'Announcements':  'announcements',
    'Inventory':      'train_inventory',
    'Quotas':         'quotas',
    'Coach_Layouts':  'coach_layouts',
    'Settings':       'settings',
    'Admin_Logs':     'admin_logs',
}


@ai_bp.route('/api/ai/mcp-query', methods=['POST'])
def mcp_query():
    """
    POST /api/ai/mcp-query
    Body: { "method": "GET", "module": "Trains", "filters": { "From_Station": "Chennai" } }
    Executes a structured MCP query against CloudScale and returns real records.
    Only GET (read) operations are allowed.
    """
    data = request.get_json(silent=True) or {}
    method  = (data.get('method') or 'GET').upper()
    module  = (data.get('module') or '').strip()
    filters = data.get('filters') or {}

    # Security: only allow reads
    if method != 'GET':
        return jsonify({'success': False, 'error': 'Only GET queries are allowed'}), 403

    if not module:
        return jsonify({'success': False, 'error': 'module is required'}), 400

    # Resolve table name
    config_key = _MODULE_REPORT_MAP.get(module)
    if not config_key:
        return jsonify({
            'success': False,
            'error': f'Unknown module: {module}',
            'available_modules': list(_MODULE_REPORT_MAP.keys())
        }), 400

    table_name = TABLES.get(config_key)
    if not table_name:
        return jsonify({'success': False, 'error': f'No table configured for {module}'}), 400

    # Normalize all filter values for case-insensitive local matching.
    local_filters = {}
    for field, value in filters.items():
        value_str = str(value).strip()
        if not value_str:
            continue
        local_filters[field] = value_str.lower()

    try:
        result = cloudscale_repo.get_all_records(table_name, criteria=None, limit=200)
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Query failed'),
                'module': module,
                'filters_applied': filters,
            }), 500

        records = result.get('data', {}).get('data', []) or []

        # Local filtering — handles lookups, strings, numbers uniformly
        if local_filters:
            filtered = []
            for rec in records:
                match = True
                for field, search_val in local_filters.items():
                    field_data = rec.get(field, '')
                    if isinstance(field_data, dict):
                        display = (field_data.get('display_value') or '').lower()
                    else:
                        display = str(field_data).lower()
                    if search_val not in display:
                        match = False
                        break
                if match:
                    filtered.append(rec)
            records = filtered

        return jsonify({
            'success': True,
            'module': module,
            'filters_applied': filters,
            'criteria': None,
            'count': len(records),
            'records': records,
        }), 200

    except Exception as e:
        logger.exception(f'mcp_query error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── SCHEMA DISCOVERY (Dynamic MCP) ─────────────────────────────────────────────

@ai_bp.route('/api/ai/schema', methods=['GET'])
def get_schema():
    """
    GET /api/ai/schema
    Returns the dynamically discovered CloudScale schema.
    Query params:
      - refresh=true: Force refresh schema
    """
    try:
        from services.schema_discovery import schema_discovery

        force_refresh = request.args.get('refresh', '').lower() == 'true'

        if force_refresh:
            schema = schema_discovery.refresh_schema()
        else:
            schema = schema_discovery.discover_all_schemas()

        return jsonify({
            'success': True,
            'schema': schema,
            'tables_count': len(schema.get('tables', {})),
        }), 200

    except Exception as e:
        logger.exception(f'Schema discovery error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai/schema/modules', methods=['GET'])
def get_queryable_modules():
    """
    GET /api/ai/schema/modules
    Returns simplified list of queryable modules and their fields.
    This is what the MCP query generator uses.
    """
    try:
        from services.schema_discovery import schema_discovery

        modules = schema_discovery.get_queryable_modules()

        return jsonify({
            'success': True,
            'modules': modules,
            'count': len(modules),
        }), 200

    except Exception as e:
        logger.exception(f'Get modules error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai/schema/prompt', methods=['GET'])
def get_mcp_prompt():
    """
    GET /api/ai/schema/prompt
    Returns the dynamically generated MCP query prompt.
    Useful for debugging what the AI sees.
    """
    try:
        from services.schema_discovery import schema_discovery

        prompt = schema_discovery.build_mcp_prompt()

        return jsonify({
            'success': True,
            'prompt': prompt,
        }), 200

    except Exception as e:
        logger.exception(f'Get MCP prompt error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai/mcp/test', methods=['POST'])
def test_mcp_query():
    """
    POST /api/ai/mcp/test
    Test MCP query generation and execution.
    Body: { "query": "show all stalls" }
    """
    try:
        from services.schema_discovery import schema_discovery
        from ai.booking_conversation import booking_conversation

        data = request.get_json(silent=True) or {}
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'success': False, 'error': 'query is required'}), 400

        # Get dynamic prompt
        dynamic_prompt = schema_discovery.build_mcp_prompt()

        # Execute query
        mcp_result = booking_conversation._execute_mcp_query(query)

        return jsonify({
            'success': True,
            'query': query,
            'result': mcp_result,
            'prompt_used': dynamic_prompt[:500] + '...',  # Preview of prompt
        }), 200

    except Exception as e:
        logger.exception(f'MCP test error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500