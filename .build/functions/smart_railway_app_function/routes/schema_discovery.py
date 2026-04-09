"""
CloudScale Schema Discovery for Railway Tables
This will systematically test different field combinations to find working schemas.
"""

import logging
import time
from datetime import datetime
from flask import Blueprint, jsonify

from repositories.cloudscale_repository import get_catalyst_app
from config import TABLES

logger = logging.getLogger(__name__)
schema_discovery_bp = Blueprint('schema_discovery', __name__)

@schema_discovery_bp.route('/schema-discovery/test-fields', methods=['POST'])
def test_field_combinations():
    """Test different field combinations to discover working schemas."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        results = {}

        # Define comprehensive field tests for each table
        field_tests = {
            'Stations': [
                # Test 1: Basic name fields
                {'Name': 'Test Station'},
                {'Station_Name': 'Test Station'},
                {'Title': 'Test Station'},

                # Test 2: Code fields
                {'Code': 'TST'},
                {'Station_Code': 'TST'},
                {'ID': 'TST'},

                # Test 3: Location fields
                {'City': 'Mumbai'},
                {'Location': 'Mumbai'},
                {'Place': 'Mumbai'},

                # Test 4: Combinations
                {'Name': 'Mumbai Station', 'Code': 'MUM'},
                {'Station_Name': 'Delhi Station', 'Station_Code': 'DEL'},
                {'Title': 'Test', 'City': 'Test City'},

                # Test 5: Simple single fields
                {'Description': 'Test station description'},
                {'Status': 'Active'},
                {'Type': 'Junction'},
                {'Zone': 'WR'},

                # Test 6: Minimal data
                {'Value': 'Station1'},
                {'Data': 'StationData'},
                {'Info': 'Station Info'}
            ],

            'Trains': [
                # Test 1: Train identification
                {'Name': 'Test Train'},
                {'Train_Name': 'Test Train'},
                {'Title': 'Test Train'},

                # Test 2: Numbers
                {'Number': '12345'},
                {'Train_Number': '12345'},
                {'ID': '12345'},
                {'Code': '12345'},

                # Test 3: Type/Service
                {'Type': 'Express'},
                {'Service': 'Express'},
                {'Category': 'Express'},

                # Test 4: Combinations
                {'Name': 'Rajdhani', 'Number': '12951'},
                {'Train_Name': 'Shatabdi', 'Train_Number': '12002'},
                {'Title': 'Express', 'Code': 'EXP001'},

                # Test 5: Simple fields
                {'Description': 'Express train service'},
                {'Status': 'Active'},
                {'Route': 'Mumbai-Delhi'},

                # Test 6: Minimal
                {'Value': 'Train1'},
                {'Data': 'TrainData'}
            ],

            'Fares': [
                # Test 1: Amount/Price
                {'Amount': '500'},
                {'Price': '500'},
                {'Cost': '500'},
                {'Fare': '500'},
                {'Rate': '500'},

                # Test 2: Currency
                {'Amount': 500},  # Numeric
                {'Price': 500.0},  # Float

                # Test 3: Class/Type
                {'Class': 'SL'},
                {'Type': 'SL'},
                {'Category': 'SL'},

                # Test 4: Combinations
                {'Amount': '500', 'Class': 'SL'},
                {'Price': '800', 'Type': '3A'},
                {'Fare': '1200', 'Category': '2A'},

                # Test 5: Simple fields
                {'Value': '500'},
                {'Description': 'Base fare'},
                {'Status': 'Active'}
            ],

            'Quotas': [
                # Test 1: Type
                {'Type': 'GENERAL'},
                {'Quota_Type': 'GENERAL'},
                {'Category': 'GENERAL'},

                # Test 2: Amount/Count
                {'Amount': '100'},
                {'Count': '100'},
                {'Quantity': '100'},
                {'Limit': '100'},

                # Test 3: Combinations
                {'Type': 'GENERAL', 'Amount': '100'},
                {'Quota_Type': 'TATKAL', 'Count': '50'},
                {'Category': 'LADIES', 'Limit': '25'},

                # Test 4: Simple fields
                {'Value': '50'},
                {'Description': 'General quota'},
                {'Status': 'Available'}
            ]
        }

        for table_name, field_combinations in field_tests.items():
            print(f"\nTesting {table_name}...")
            table_results = []

            try:
                table = datastore.table(table_name)

                for i, test_fields in enumerate(field_combinations):
                    test_result = {
                        'test_number': i + 1,
                        'fields': test_fields,
                        'field_names': list(test_fields.keys()),
                        'success': False,
                        'error': None
                    }

                    try:
                        insert_result = table.insert_row(test_fields)
                        if insert_result:
                            test_result['success'] = True
                            test_result['insert_result'] = str(insert_result)
                            print(f"  ✓ SUCCESS: {list(test_fields.keys())} = {test_fields}")

                            # Stop at first success to avoid cluttering
                            table_results.append(test_result)
                            break
                        else:
                            test_result['error'] = 'No result returned'

                    except Exception as e:
                        test_result['error'] = str(e)
                        print(f"  ✗ FAILED: {list(test_fields.keys())} - {str(e)[:60]}")

                    table_results.append(test_result)

                results[table_name.lower()] = {
                    'tests_run': len(table_results),
                    'successful_tests': sum(1 for t in table_results if t['success']),
                    'test_results': table_results
                }

            except Exception as e:
                results[table_name.lower()] = {
                    'tests_run': 0,
                    'successful_tests': 0,
                    'table_error': str(e),
                    'test_results': []
                }

        # Summary
        total_tables = len(field_tests)
        successful_tables = sum(1 for r in results.values() if r.get('successful_tests', 0) > 0)

        return jsonify({
            'status': 'completed',
            'message': f'Schema discovery completed: {successful_tables}/{total_tables} tables have working schemas',
            'summary': {
                'total_tables_tested': total_tables,
                'tables_with_working_schema': successful_tables,
                'working_schemas_found': successful_tables > 0
            },
            'detailed_results': results
        }), 200

    except Exception as e:
        logger.exception(f'Schema discovery error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Schema discovery failed',
            'error': str(e)
        }), 500


@schema_discovery_bp.route('/schema-discovery/create-with-working-schemas', methods=['POST'])
def create_with_discovered_schemas():
    """Create records using any working schemas we discovered."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        zcql = catalyst_app.zcql()

        # Use the schemas we know work from previous discovery
        known_working_schemas = {
            'Settings': {'Name': 'RAILWAY_SETTING', 'Value': 'Test Value'},
            'Announcements': {'Title': 'Railway Notice', 'Message': 'Important railway announcement'}
        }

        # Additional schemas to test for railway tables
        potential_schemas = {
            'Stations': [
                {'Description': 'Mumbai Central Railway Station'},
                {'Name': 'Delhi Junction'},
                {'Value': 'Station Data'},
                {'Status': 'Operational'},
                {'Type': 'Junction'}
            ],
            'Trains': [
                {'Description': 'Express train service'},
                {'Name': 'Rajdhani Express'},
                {'Value': 'Train Data'},
                {'Status': 'Active'},
                {'Type': 'Express'}
            ],
            'Fares': [
                {'Description': 'Standard fare pricing'},
                {'Value': '500'},
                {'Status': 'Active'},
                {'Type': 'Base'}
            ],
            'Quotas': [
                {'Description': 'Passenger quota allocation'},
                {'Value': '100'},
                {'Status': 'Available'},
                {'Type': 'General'}
            ],
            'Train_Routes': [
                {'Description': 'Mumbai to Delhi route'},
                {'Name': 'Western Route'},
                {'Value': 'Route Data'},
                {'Status': 'Active'}
            ],
            'Train_Inventory': [
                {'Description': 'Available seat inventory'},
                {'Value': '50'},
                {'Status': 'Available'},
                {'Type': 'Seats'}
            ]
        }

        results = {}

        for table_name, schema_list in potential_schemas.items():
            created_count = 0
            working_schema = None

            try:
                table = datastore.table(table_name)

                for schema in schema_list:
                    try:
                        insert_result = table.insert_row(schema)
                        if insert_result:
                            created_count += 1
                            working_schema = schema
                            print(f"✓ Created {table_name} record with: {schema}")
                            break
                    except Exception as e:
                        print(f"✗ Failed {table_name} with {schema}: {str(e)[:50]}")
                        continue

                # Verify records exist
                try:
                    verify_query = f"SELECT * FROM {table_name} LIMIT 3"
                    verify_result = zcql.execute_query(verify_query)
                    verified_count = len(verify_result) if verify_result else 0
                except:
                    verified_count = 0

                results[table_name.lower()] = {
                    'created': created_count,
                    'verified': verified_count,
                    'working_schema': working_schema,
                    'status': 'success' if verified_count > 0 else 'failed'
                }

            except Exception as e:
                results[table_name.lower()] = {
                    'created': 0,
                    'verified': 0,
                    'working_schema': None,
                    'status': 'error',
                    'error': str(e)
                }

        successful_tables = sum(1 for r in results.values() if r.get('status') == 'success')
        total_verified = sum(r.get('verified', 0) for r in results.values())

        return jsonify({
            'status': 'completed',
            'message': f'Record creation with discovered schemas: {successful_tables} successful',
            'summary': {
                'successful_tables': successful_tables,
                'total_records_verified': total_verified
            },
            'detailed_results': results
        }), 200

    except Exception as e:
        logger.exception(f'Schema-based creation error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Schema-based creation failed',
            'error': str(e)
        }), 500


@schema_discovery_bp.route('/schema-discovery/final-verification', methods=['GET'])
def final_verification():
    """Final verification of all data in CloudScale."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        zcql = catalyst_app.zcql()

        all_tables = ['Settings', 'Announcements', 'Stations', 'Trains', 'Fares', 'Quotas', 'Train_Routes', 'Train_Inventory']
        verification = {}

        for table_name in all_tables:
            try:
                query = f"SELECT * FROM {table_name} LIMIT 5"
                result = zcql.execute_query(query)

                verification[table_name.lower()] = {
                    'record_count': len(result) if result else 0,
                    'status': 'populated' if result and len(result) > 0 else 'empty',
                    'sample_records': result[:2] if result else []
                }

            except Exception as e:
                verification[table_name.lower()] = {
                    'record_count': 0,
                    'status': 'error',
                    'error': str(e)
                }

        total_records = sum(v.get('record_count', 0) for v in verification.values())
        populated_tables = sum(1 for v in verification.values() if v.get('record_count', 0) > 0)

        return jsonify({
            'status': 'success',
            'summary': {
                'total_tables_checked': len(all_tables),
                'populated_tables': populated_tables,
                'total_records_in_cloudscale': total_records
            },
            'table_verification': verification
        }), 200

    except Exception as e:
        logger.exception(f'Final verification error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Final verification failed',
            'error': str(e)
        }), 500