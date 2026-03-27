"""
Expand Railway Data Using Successful Fares Schema Pattern
Creates more fares and tests similar patterns for other railway modules.
"""

import logging
import time
from datetime import datetime
from flask import Blueprint, jsonify

from repositories.cloudscale_repository import get_catalyst_app

logger = logging.getLogger(__name__)
expand_railway_bp = Blueprint('expand_railway', __name__)

@expand_railway_bp.route('/expand-railway/create-more-fares', methods=['POST'])
def create_more_fares():
    """Create multiple fare records using the working schema pattern."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        zcql = catalyst_app.zcql()

        # Use the working pattern: Base_Fare and Class fields
        fare_records = [
            {'Base_Fare': '500', 'Class': 'SL'},
            {'Base_Fare': '800', 'Class': '3A'},
            {'Base_Fare': '1200', 'Class': '2A'},
            {'Base_Fare': '2000', 'Class': '1A'},
            {'Base_Fare': '300', 'Class': 'CC'},
            {'Base_Fare': '600', 'Class': 'SL'},
            {'Base_Fare': '900', 'Class': '3A'},
            {'Base_Fare': '1500', 'Class': '2A'}
        ]

        fares_table = datastore.table('Fares')
        created_count = 0

        for fare_data in fare_records:
            try:
                insert_result = fares_table.insert_row(fare_data)
                if insert_result:
                    created_count += 1
                    print(f"✓ Created fare: {fare_data}")
            except Exception as e:
                print(f"✗ Failed fare: {fare_data} - {e}")

        # Verify total fares
        verify_query = "SELECT * FROM Fares LIMIT 20"
        verify_result = zcql.execute_query(verify_query)
        total_fares = len(verify_result) if verify_result else 0

        return jsonify({
            'status': 'success',
            'message': f'Created {created_count} additional fare records',
            'created_new': created_count,
            'total_fares': total_fares,
            'working_schema': {'Base_Fare': 'string', 'Class': 'string'}
        }), 200

    except Exception as e:
        logger.exception(f'Create more fares error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create more fares',
            'error': str(e)
        }), 500


@expand_railway_bp.route('/expand-railway/test-similar-patterns', methods=['POST'])
def test_similar_patterns():
    """Test similar field patterns for other railway tables."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        zcql = catalyst_app.zcql()

        results = {}

        # Test similar patterns based on successful Fares schema
        table_tests = {
            'Stations': [
                {'Station_Name': 'Mumbai Central', 'Station_Code': 'MMCT'},
                {'Name': 'Delhi Junction', 'Code': 'DLI'},
                {'Station_Name': 'Bangalore', 'City': 'Bangalore'},
                {'Name': 'Chennai Central', 'Zone': 'SR'},
            ],
            'Trains': [
                {'Train_Name': 'Rajdhani Express', 'Train_Number': '12951'},
                {'Name': 'Shatabdi Express', 'Number': '12002'},
                {'Train_Name': 'Duronto', 'Service': 'Express'},
                {'Name': 'Garib Rath', 'Type': 'AC'},
            ],
            'Quotas': [
                {'Quota_Type': 'GENERAL', 'Quota_Amount': '100'},
                {'Type': 'TATKAL', 'Amount': '50'},
                {'Quota_Type': 'LADIES', 'Class': 'SL'},
                {'Type': 'SENIOR', 'Limit': '25'},
            ],
            'Train_Routes': [
                {'Route_Name': 'Mumbai-Delhi', 'Distance': '1384'},
                {'Name': 'Chennai-Bangalore', 'Duration': '5hrs'},
                {'Route_Name': 'Kolkata-Mumbai', 'Type': 'Express'},
                {'Name': 'Delhi-Amritsar', 'Service': 'Shatabdi'},
            ],
            'Train_Inventory': [
                {'Train_Number': '12951', 'Available_Seats': '50'},
                {'Service': 'Rajdhani', 'Capacity': '100'},
                {'Train_Number': '12002', 'Date': '2026-04-15'},
                {'Name': 'Inventory_Entry', 'Count': '75'},
            ]
        }

        for table_name, test_schemas in table_tests.items():
            created_count = 0
            working_schema = None

            try:
                table = datastore.table(table_name)

                for schema in test_schemas:
                    try:
                        insert_result = table.insert_row(schema)
                        if insert_result:
                            created_count += 1
                            working_schema = schema
                            print(f"✓ {table_name} success: {schema}")
                            break
                    except Exception as e:
                        print(f"✗ {table_name} failed: {schema} - {str(e)[:50]}")

                # Verify records
                verify_query = f"SELECT * FROM {table_name} LIMIT 5"
                verify_result = zcql.execute_query(verify_query)
                total_count = len(verify_result) if verify_result else 0

                results[table_name.lower()] = {
                    'created': created_count > 0,
                    'total_records': total_count,
                    'working_schema': working_schema,
                    'status': 'success' if total_count > 0 else 'failed'
                }

            except Exception as e:
                results[table_name.lower()] = {
                    'created': False,
                    'total_records': 0,
                    'working_schema': None,
                    'status': 'error',
                    'error': str(e)
                }

        successful_tables = sum(1 for r in results.values() if r.get('status') == 'success')
        total_records = sum(r.get('total_records', 0) for r in results.values())

        return jsonify({
            'status': 'completed',
            'message': f'Pattern testing completed: {successful_tables} successful tables',
            'summary': {
                'successful_tables': successful_tables,
                'total_new_records': total_records
            },
            'detailed_results': results
        }), 200

    except Exception as e:
        logger.exception(f'Pattern testing error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Pattern testing failed',
            'error': str(e)
        }), 500


@expand_railway_bp.route('/expand-railway/final-status', methods=['GET'])
def get_final_railway_status():
    """Get final comprehensive status of all railway data."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        zcql = catalyst_app.zcql()

        # Check all railway tables
        railway_tables = ['Stations', 'Trains', 'Fares', 'Quotas', 'Train_Routes', 'Train_Inventory']
        status = {}

        for table_name in railway_tables:
            try:
                query = f"SELECT * FROM {table_name} LIMIT 10"
                result = zcql.execute_query(query)

                count = len(result) if result else 0
                sample_record = result[0] if result and len(result) > 0 else None

                # Extract sample fields
                sample_fields = []
                if sample_record and isinstance(sample_record, dict):
                    for key, value in sample_record.items():
                        if isinstance(value, dict):
                            # Get non-system fields
                            for field, field_value in value.items():
                                if not field.startswith('CREATED') and not field.startswith('MODIFIED') and field != 'ROWID':
                                    sample_fields.append(f"{field}: {field_value}")
                            break

                status[table_name.lower()] = {
                    'record_count': count,
                    'status': 'populated' if count > 0 else 'empty',
                    'sample_fields': sample_fields[:5]  # First 5 fields
                }

            except Exception as e:
                status[table_name.lower()] = {
                    'record_count': 0,
                    'status': 'error',
                    'error': str(e),
                    'sample_fields': []
                }

        # Summary statistics
        total_records = sum(s.get('record_count', 0) for s in status.values())
        populated_tables = sum(1 for s in status.values() if s.get('record_count', 0) > 0)

        return jsonify({
            'status': 'success',
            'summary': {
                'total_railway_tables': len(railway_tables),
                'populated_tables': populated_tables,
                'total_railway_records': total_records,
                'success_rate': f"{(populated_tables/len(railway_tables))*100:.1f}%"
            },
            'table_details': status
        }), 200

    except Exception as e:
        logger.exception(f'Final status error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Final status check failed',
            'error': str(e)
        }), 500