"""
Fares and Concessions routes.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from services.zoho_service import zoho
from core.security import require_admin

fares_bp = Blueprint('fares', __name__)


# ==================== FARES ====================

@fares_bp.route('/api/fares', methods=['GET'])
def get_fares():
    try:
        params = request.args
        conditions = []
        if params.get('train_id'):
            conditions.append(f'(Train == "{params["train_id"]}")')
        if params.get('from_station'):
            conditions.append(f'(From_Station == "{params["from_station"]}")')
        if params.get('to_station'):
            conditions.append(f'(To_Station == "{params["to_station"]}")')
        if params.get('class'):
            conditions.append(f'(Class == "{params["class"]}")')
        if params.get('concession_type'):
            conditions.append(f'(Concession_Type == "{params["concession_type"]}")')
        if params.get('is_active') == 'true':
            conditions.append('(Is_Active == true)')
        elif params.get('is_active') == 'false':
            conditions.append('(Is_Active == false)')

        criteria = " && ".join(conditions) if conditions else None

        data = zoho.get_all_records(zoho.forms['reports']['fares'], criteria=criteria)
        return jsonify(data), data.get('status_code', 200)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/fares/<id>', methods=['GET'])
def get_fare(id):
    try:
        data = zoho.get_record_by_id(zoho.forms['reports']['fares'], id)
        return jsonify(data), data.get('status_code', 200)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/fares', methods=['POST'])
@require_admin
def create_fare():
    try:
        data = request.get_json()

        # Validate required fields (CloudScale uses _ID suffix for foreign keys)
        required = ['Train_ID', 'From_Station_ID', 'To_Station_ID', 'Class', 'Base_Fare']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"success": False, "error": f"Missing: {', '.join(missing)}", "status_code": 400}), 400

        # Normalize Is_Active
        is_active = data.get('Is_Active', True)
        if isinstance(is_active, str):
            is_active = is_active.lower() not in ('false', '0', 'no', 'inactive')

        base_fare    = float(data.get('Base_Fare', 0))
        dynamic_fare = float(data.get('Dynamic_Fare') or base_fare)

        # CloudScale payload - uses direct ROWID values (no extract_lookup_id needed)
        payload = {
            "Train_ID":           data.get('Train_ID'),
            "From_Station_ID":    data.get('From_Station_ID'),
            "To_Station_ID":      data.get('To_Station_ID'),
            "Class":              data.get('Class'),
            "Base_Fare":          base_fare,
            "Dynamic_Fare":       dynamic_fare,
            "Concession_Type":    data.get('Concession_Type', 'General'),
            "Concession_Percent": float(data.get('Concession_Percent') or 0),
            "Distance_KM":        float(data.get('Distance_KM') or 0) if data.get('Distance_KM') else None,
            "Effective_From":     data.get('Effective_From') or None,
            "Effective_To":       data.get('Effective_To') or None,
            "Is_Active":          is_active,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        result = zoho.create_record(zoho.forms['forms']['fares'], payload)
        return jsonify(result), result.get('status_code', 201)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/fares/<id>', methods=['PUT'])
@require_admin
def update_fare(id):
    try:
        data = request.get_json()

        is_active = data.get('Is_Active', True)
        if isinstance(is_active, str):
            is_active = is_active.lower() not in ('false', '0', 'no', 'inactive')

        # CloudScale payload - uses direct ROWID values (no extract_lookup_id needed)
        payload = {
            "Train_ID":           data.get('Train_ID'),
            "From_Station_ID":    data.get('From_Station_ID'),
            "To_Station_ID":      data.get('To_Station_ID'),
            "Class":              data.get('Class'),
            "Base_Fare":          float(data.get('Base_Fare', 0)),
            "Dynamic_Fare":       float(data.get('Dynamic_Fare') or data.get('Base_Fare') or 0),
            "Concession_Type":    data.get('Concession_Type', 'General'),
            "Concession_Percent": float(data.get('Concession_Percent') or 0),
            "Distance_KM":        float(data.get('Distance_KM') or 0) if data.get('Distance_KM') else None,
            "Effective_From":     data.get('Effective_From') or None,
            "Effective_To":       data.get('Effective_To') or None,
            "Is_Active":          is_active,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        result = zoho.update_record(zoho.forms['reports']['fares'], id, payload)
        return jsonify(result), result.get('status_code', 200)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/fares/<id>', methods=['DELETE'])
@require_admin
def delete_fare(id):
    try:
        result = zoho.delete_record(zoho.forms['reports']['fares'], id)
        return jsonify(result), result.get('status_code', 200)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/fares/calculate', methods=['POST'])
def calculate_fare():
    """
    Calculate final fare with all IRCTC-style factors:
    Base Fare, Reservation Charge, Superfast Surcharge, Tatkal Premium, GST (AC only), Catering.
    """
    try:
        data = request.get_json()

        train_id        = data.get("train_id")
        cls_raw         = data.get("class", "SL").upper()
        cls_map         = {'SLEEPER': 'SL', '3A': '3AC', '2A': '2AC', '1A': '1AC'}
        cls             = cls_map.get(cls_raw, cls_raw)
        
        passenger_count = int(data.get('passenger_count', 1))
        concession_type = data.get('concession_type', 'General')
        journey_date    = data.get('journey_date')
        quota           = data.get('quota', 'GN').upper()
        opt_catering    = data.get('opt_catering', False)

        base_fare    = 0.0
        train_type   = "EXPRESS"

        # 1. Fetch Train details unconditionally for Train_Type and fallback fares
        train_result = zoho.get_record_by_id(zoho.forms['reports']['trains'], train_id)
        if not train_result.get('success'):
            return jsonify({"success": False, "error": "Train not found", "status_code": 404}), 404
            
        rec = train_result.get('data', {}).get('data', {})
        train_type = rec.get("Train_Type", "EXPRESS").upper()

        # 2. Try to get explicit fare from Fares table
        criteria = f'(Train == "{train_id}") && (Class == "{cls}")'
        fares_result = zoho.get_all_records(zoho.forms['reports']['fares'], criteria=criteria)
        fares = fares_result.get('data', {}).get('data', []) if fares_result.get('success') else []

        if fares:
            base_fare = float(fares[0].get('Base_Fare', 0))
        else:
            # Fallback: use Train record's fare fields
            fare_field_map = {
                'SL': 'Fare_SL', '3AC': 'Fare_3A', '2AC': 'Fare_2A', '1AC': 'Fare_1A',
                'CC': 'Fare_CC', 'EC': 'Fare_EC', '2S': 'Fare_2S',
            }
            fare_field = fare_field_map.get(cls, 'Fare_SL')
            base_fare  = float(rec.get(fare_field) or rec.get('Fare_SL') or 0)

        # 3. Reservation Charge
        res_charge_map = {'2S': 15, 'SL': 20, 'CC': 40, '3AC': 40, '2AC': 50, '1AC': 60, 'EC': 60}
        reservation_charge = res_charge_map.get(cls, 20)
        
        # 4. Superfast Surcharge
        superfast_charge = 0
        if "SUPERFAST" in train_type or "SF" in train_type:
            sf_charge_map = {'2S': 15, 'SL': 30, 'CC': 45, '3AC': 45, '2AC': 45, '1AC': 75, 'EC': 75}
            superfast_charge = sf_charge_map.get(cls, 30)
            
        # 5. Tatkal Premium
        tatkal_premium = 0
        if quota in ["TQ", "PT"]: # Tatkal or Premium Tatkal
            tatkal_rate = 0.30 if cls in ['2S', 'SL'] else 0.30 # Standard 30% for all? IRCTC is complex, let's use 30% 
            raw_tatkal = base_fare * tatkal_rate
            # Apply Min/Max limits
            limits = {
                '2S': (10, 15), 'SL': (100, 200), 'CC': (125, 225), 
                '3AC': (300, 400), '2AC': (400, 500), '1AC': (400, 500)
            }
            min_t, max_t = limits.get(cls, (100, 200))
            tatkal_premium = max(min_t, min(raw_tatkal, max_t))
            
            # Premium Tatkal applies dynamic pricing on top
            if quota == "PT":
                surge_multiplier = _get_surge_multiplier(journey_date)
                tatkal_premium += (base_fare * (surge_multiplier - 1.0))

        # 6. Concessions (Not applicable on Tatkal)
        concession_amount = 0
        if quota not in ["TQ", "PT"]:
            concession_percent = _get_concession_percent(concession_type)
            concession_amount = (base_fare * concession_percent / 100)

        # 7. Taxable Subtotal (Per Passenger)
        taxable_subtotal = base_fare + reservation_charge + superfast_charge + tatkal_premium - concession_amount
        
        # 8. GST 5% (Only for AC Classes)
        gst = 0
        is_ac_class = cls in ['3A', '3AC', '2A', '2AC', '1A', '1AC', 'CC', 'EC', 'FC']
        if is_ac_class:
            gst = taxable_subtotal * 0.05
            
        # 9. Catering
        catering_charge = 0
        if opt_catering:
            # Varies by class
            cat_map = {'SL': 0, '2S': 0, 'CC': 185, '3AC': 185, '2AC': 250, '1AC': 350, 'EC': 350}
            catering_charge = cat_map.get(cls, 150)
            
        # 10. Convenience Fee (Per Ticket, not per passenger, but we spread it or just add at end)
        # Let's say IRCTC convenience fee is ~R30 for AC, R15 for non-AC
        conv_fee = 35.4 if is_ac_class else 17.7 # Including GST on convenience fee

        # Total Per Passenger
        fare_per_pax = taxable_subtotal + gst + catering_charge
        
        # Grand Total
        grand_total = round((fare_per_pax * passenger_count) + conv_fee, 2)

        breakdown = {
            "base_fare":               round(base_fare * passenger_count, 2),
            "reservation_charge":      round(reservation_charge * passenger_count, 2),
            "superfast_charge":        round(superfast_charge * passenger_count, 2),
            "tatkal_premium":          round(tatkal_premium * passenger_count, 2),
            "concession_discount":     round(-concession_amount * passenger_count, 2),
            "gst":                     round(gst * passenger_count, 2),
            "catering_charge":         round(catering_charge * passenger_count, 2),
            "convenience_fee":         round(conv_fee, 2),
            "total":                   grand_total,
            "concession_type":         concession_type,
            "passenger_count":         passenger_count,
            "quota":                   quota
        }

        return jsonify({"success": True, "data": breakdown, "status_code": 200})

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


# ==================== CONCESSIONS ====================

@fares_bp.route('/api/concessions', methods=['GET'])
def get_concessions():
    try:
        params = request.args
        criteria = 'Is_Active == true' if params.get('is_active') == 'true' else ""
        data = zoho.get_all_records('All_Concessions', criteria=criteria)
        return jsonify({"success": True, "data": data, "status_code": 200})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/concessions', methods=['POST'])
@require_admin
def create_concession():
    try:
        data = request.get_json()
        result = zoho.create_record('Concessions', data)
        return jsonify({"success": True, "data": result, "status_code": 201})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/concessions/<id>', methods=['PUT'])
@require_admin
def update_concession(id):
    try:
        data = request.get_json()
        result = zoho.update_record('All_Concessions', id, data)
        return jsonify({"success": True, "data": result, "status_code": 200})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


@fares_bp.route('/api/concessions/<id>', methods=['DELETE'])
@require_admin
def delete_concession(id):
    try:
        result = zoho.delete_record('All_Concessions', id)
        return jsonify({"success": True, "data": result, "status_code": 200})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "status_code": 500}), 500


# ==================== FARE HELPER FUNCTIONS ====================

def _calculate_dynamic_fare(base_fare):
    """Apply dynamic pricing based on demand"""
    import random
    surge = random.choice([0, 0, 0, 50, 100, 200])
    return float(base_fare) + surge


def _get_concession_percent(concession_type):
    """Get discount percentage for concession type"""
    concessions = {
        'General': 0,
        'Senior': 40,
        'Student': 50,
        'Disabled': 50,
        'Armed Forces': 50
    }
    return concessions.get(concession_type, 0)


def _get_surge_multiplier(journey_date):
    """Calculate surge based on how close journey date is"""
    if not journey_date:
        return 1.0

    journey = datetime.strptime(journey_date, '%Y-%m-%d')
    today = datetime.now()
    days_diff = (journey - today).days

    if days_diff < 2:
        return 2.0
    elif days_diff < 7:
        return 1.5
    elif days_diff < 30:
        return 1.2
    return 1.0
