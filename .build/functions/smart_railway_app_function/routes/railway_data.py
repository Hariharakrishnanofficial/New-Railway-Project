"""
Targeted CloudScale Record Creator for Railway Modules
Focuses only on: Trains, Stations, Train_Inventory, Train_Routes, Fares, Quotas
Uses field testing to find working schemas for each table.
"""

import logging
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

from repositories.cloudscale_repository import get_catalyst_app
from config import TABLES

logger = logging.getLogger(__name__)
railway_data_bp = Blueprint('railway_data', __name__)

@railway_data_bp.route('/railway-data/create-all-modules', methods=['POST'])
def create_railway_modules_data():
    """Create sample data for all 6 required railway modules."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        zcql = catalyst_app.zcql()

        results = {}

        # 1. STATIONS - Try multiple field combinations
        print("Creating Stations...")
        stations_schemas = [
            {'Name': 'Mumbai Central Station', 'Code': 'MMCT', 'City': 'Mumbai'},
            {'Station_Name': 'Delhi Junction', 'Station_Code': 'DLI', 'City': 'Delhi'},
            {'Name': 'Bangalore City', 'City': 'Bangalore', 'State': 'Karnataka'},
            {'Title': 'Chennai Central', 'Code': 'MAS', 'Location': 'Chennai'},
            {'Name': 'Kolkata Terminal', 'Zone': 'ER'}
        ]

        stations_created = 0
        stations_table = datastore.table('Stations')

        for schema in stations_schemas:
            try:
                insert_result = stations_table.insert_row(schema)
                if insert_result:
                    stations_created += 1
                    print(f"  ✓ Station created with schema: {list(schema.keys())}")
                    break  # Use first working schema
            except Exception as e:
                print(f"  ✗ Station schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify stations
        try:
            verify_query = "SELECT * FROM Stations LIMIT 5"
            stations_verify = zcql.execute_query(verify_query)
            stations_count = len(stations_verify) if stations_verify else 0
        except:
            stations_count = 0

        results['stations'] = {
            'created': stations_created,
            'verified': stations_count,
            'status': 'success' if stations_count > 0 else 'failed'
        }

        # 2. TRAINS - Try multiple field combinations
        print("Creating Trains...")
        trains_schemas = [
            {'Name': 'Rajdhani Express', 'Number': '12951', 'Type': 'Express'},
            {'Train_Name': 'Shatabdi Express', 'Train_Number': '12002'},
            {'Name': 'Mumbai Duronto', 'Code': 'MD001', 'Route': 'Mumbai-Delhi'},
            {'Title': 'Chennai Express', 'Service_Number': '12345'},
            {'Name': 'Kolkata Mail', 'Service': 'Mail'}
        ]

        trains_created = 0
        trains_table = datastore.table('Trains')

        for schema in trains_schemas:
            try:
                insert_result = trains_table.insert_row(schema)
                if insert_result:
                    trains_created += 1
                    print(f"  ✓ Train created with schema: {list(schema.keys())}")
                    break
            except Exception as e:
                print(f"  ✗ Train schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify trains
        try:
            verify_query = "SELECT * FROM Trains LIMIT 5"
            trains_verify = zcql.execute_query(verify_query)
            trains_count = len(trains_verify) if trains_verify else 0
        except:
            trains_count = 0

        results['trains'] = {
            'created': trains_created,
            'verified': trains_count,
            'status': 'success' if trains_count > 0 else 'failed'
        }

        # 3. FARES - Try multiple field combinations
        print("Creating Fares...")
        fares_schemas = [
            {'Amount': '500', 'Class': 'SL', 'Distance': '500'},
            {'Fare': '800', 'Type': '3A', 'Route': 'Mumbai-Delhi'},
            {'Price': '1200', 'Category': '2A', 'Zone': 'WR'},
            {'Cost': '300', 'Service': 'General'},
            {'Rate': '600', 'Travel_Class': 'AC'}
        ]

        fares_created = 0
        fares_table = datastore.table('Fares')

        for schema in fares_schemas:
            try:
                insert_result = fares_table.insert_row(schema)
                if insert_result:
                    fares_created += 1
                    print(f"  ✓ Fare created with schema: {list(schema.keys())}")
                    break
            except Exception as e:
                print(f"  ✗ Fare schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify fares
        try:
            verify_query = "SELECT * FROM Fares LIMIT 5"
            fares_verify = zcql.execute_query(verify_query)
            fares_count = len(fares_verify) if fares_verify else 0
        except:
            fares_count = 0

        results['fares'] = {
            'created': fares_created,
            'verified': fares_count,
            'status': 'success' if fares_count > 0 else 'failed'
        }

        # 4. QUOTAS - Try multiple field combinations
        print("Creating Quotas...")
        quotas_schemas = [
            {'Type': 'GENERAL', 'Amount': '100', 'Class': 'SL'},
            {'Quota_Type': 'TATKAL', 'Quantity': '50', 'Category': '3A'},
            {'Name': 'Ladies Quota', 'Count': '25', 'Service': '2A'},
            {'Allocation': 'Senior Citizen', 'Limit': '15'},
            {'Category': 'Physically Handicapped', 'Seats': '10'}
        ]

        quotas_created = 0
        quotas_table = datastore.table('Quotas')

        for schema in quotas_schemas:
            try:
                insert_result = quotas_table.insert_row(schema)
                if insert_result:
                    quotas_created += 1
                    print(f"  ✓ Quota created with schema: {list(schema.keys())}")
                    break
            except Exception as e:
                print(f"  ✗ Quota schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify quotas
        try:
            verify_query = "SELECT * FROM Quotas LIMIT 5"
            quotas_verify = zcql.execute_query(verify_query)
            quotas_count = len(quotas_verify) if quotas_verify else 0
        except:
            quotas_count = 0

        results['quotas'] = {
            'created': quotas_created,
            'verified': quotas_count,
            'status': 'success' if quotas_count > 0 else 'failed'
        }

        # 5. TRAIN_ROUTES - Try multiple field combinations
        print("Creating Train Routes...")
        routes_schemas = [
            {'Name': 'Mumbai-Delhi Route', 'Train': '12951', 'Distance': '1384'},
            {'Route_Name': 'Chennai-Bangalore', 'Train_Number': '12008'},
            {'Title': 'Kolkata-Mumbai', 'Service': 'Express', 'Duration': '26hrs'},
            {'Name': 'Delhi-Amritsar', 'Type': 'Shatabdi'},
            {'Route': 'Pune-Mumbai', 'Code': 'PMR001'}
        ]

        routes_created = 0
        routes_table = datastore.table('Train_Routes')

        for schema in routes_schemas:
            try:
                insert_result = routes_table.insert_row(schema)
                if insert_result:
                    routes_created += 1
                    print(f"  ✓ Route created with schema: {list(schema.keys())}")
                    break
            except Exception as e:
                print(f"  ✗ Route schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify routes
        try:
            verify_query = "SELECT * FROM Train_Routes LIMIT 5"
            routes_verify = zcql.execute_query(verify_query)
            routes_count = len(routes_verify) if routes_verify else 0
        except:
            routes_count = 0

        results['train_routes'] = {
            'created': routes_created,
            'verified': routes_count,
            'status': 'success' if routes_count > 0 else 'failed'
        }

        # 6. TRAIN_INVENTORY - Try multiple field combinations
        print("Creating Train Inventory...")
        inventory_schemas = [
            {'Train': '12951', 'Date': '2026-04-15', 'Available': '50'},
            {'Train_Number': '12002', 'Journey_Date': '2026-04-16', 'Seats': '75'},
            {'Service': 'Rajdhani', 'Travel_Date': '2026-04-17', 'Capacity': '100'},
            {'Name': 'Mumbai Express Inventory', 'Count': '80'},
            {'Train_ID': '1', 'Quota': '60', 'Status': 'Available'}
        ]

        inventory_created = 0
        inventory_table = datastore.table('Train_Inventory')

        for schema in inventory_schemas:
            try:
                insert_result = inventory_table.insert_row(schema)
                if insert_result:
                    inventory_created += 1
                    print(f"  ✓ Inventory created with schema: {list(schema.keys())}")
                    break
            except Exception as e:
                print(f"  ✗ Inventory schema failed: {list(schema.keys())} - {str(e)[:50]}")
                continue

        # Verify inventory
        try:
            verify_query = "SELECT * FROM Train_Inventory LIMIT 5"
            inventory_verify = zcql.execute_query(verify_query)
            inventory_count = len(inventory_verify) if inventory_verify else 0
        except:
            inventory_count = 0

        results['train_inventory'] = {
            'created': inventory_created,
            'verified': inventory_count,
            'status': 'success' if inventory_count > 0 else 'failed'
        }

        # Summary
        successful_modules = sum(1 for r in results.values() if r.get('status') == 'success')
        total_verified = sum(r.get('verified', 0) for r in results.values())

        return jsonify({
            'status': 'completed',
            'message': f'Railway modules data creation completed: {successful_modules}/6 successful',
            'summary': {
                'successful_modules': successful_modules,
                'total_records_verified': total_verified,
                'target_modules': ['stations', 'trains', 'fares', 'quotas', 'train_routes', 'train_inventory']
            },
            'detailed_results': results
        }), 200

    except Exception as e:
        logger.exception(f'Railway data creation error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Railway data creation failed',
            'error': str(e)
        }), 500


@railway_data_bp.route('/railway-data/bulk-create', methods=['POST'])
def bulk_create_railway_data():
    """Create multiple records in working tables using discovered schemas."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        datastore = catalyst_app.datastore()
        zcql = catalyst_app.zcql()

        results = {}

        # Create multiple records using schemas that worked
        bulk_data = {
            'Stations': [
                {'Name': 'Mumbai Central', 'City': 'Mumbai', 'Code': 'MMCT'},
                {'Name': 'New Delhi', 'City': 'Delhi', 'Code': 'NDLS'},
                {'Name': 'Bangalore City', 'City': 'Bangalore', 'Code': 'BNC'},
                {'Name': 'Chennai Central', 'City': 'Chennai', 'Code': 'MAS'},
                {'Name': 'Kolkata Howrah', 'City': 'Kolkata', 'Code': 'HWH'}
            ],
            'Trains': [
                {'Name': 'Rajdhani Express', 'Number': '12951'},
                {'Name': 'Shatabdi Express', 'Number': '12002'},
                {'Name': 'Duronto Express', 'Number': '12259'},
                {'Name': 'Garib Rath', 'Number': '12234'},
                {'Name': 'Vande Bharat', 'Number': '22435'}
            ],
            'Fares': [
                {'Amount': '500', 'Class': 'SL'},
                {'Amount': '800', 'Class': '3A'},
                {'Amount': '1200', 'Class': '2A'},
                {'Amount': '2000', 'Class': '1A'},
                {'Amount': '300', 'Class': 'CC'}
            ]
        }

        for table_name, records_list in bulk_data.items():
            created_count = 0
            table = datastore.table(table_name)

            for record in records_list:
                try:
                    insert_result = table.insert_row(record)
                    if insert_result:
                        created_count += 1
                except Exception as e:
                    print(f"Failed to create {table_name} record: {e}")

            # Verify
            try:
                verify_query = f"SELECT * FROM {table_name} LIMIT 10"
                verify_result = zcql.execute_query(verify_query)
                verified_count = len(verify_result) if verify_result else 0
            except:
                verified_count = 0

            results[table_name.lower()] = {
                'attempted': len(records_list),
                'created': created_count,
                'verified': verified_count,
                'status': 'success' if verified_count > 0 else 'failed'
            }

        successful_modules = sum(1 for r in results.values() if r.get('status') == 'success')
        total_verified = sum(r.get('verified', 0) for r in results.values())

        return jsonify({
            'status': 'completed',
            'message': f'Bulk railway data creation: {successful_modules} successful modules',
            'summary': {
                'successful_modules': successful_modules,
                'total_records_verified': total_verified
            },
            'detailed_results': results
        }), 200

    except Exception as e:
        logger.exception(f'Bulk railway data creation error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Bulk creation failed',
            'error': str(e)
        }), 500


@railway_data_bp.route('/railway-data/verify', methods=['GET'])
def verify_railway_data():
    """Verify all railway module data exists and show sample records."""
    try:
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        zcql = catalyst_app.zcql()
        verification = {}

        target_tables = ['Stations', 'Trains', 'Fares', 'Quotas', 'Train_Routes', 'Train_Inventory']

        for table_name in target_tables:
            try:
                # Get sample records
                query = f"SELECT * FROM {table_name} LIMIT 3"
                result = zcql.execute_query(query)

                if result and len(result) > 0:
                    verification[table_name.lower()] = {
                        'record_count': len(result),
                        'status': 'populated',
                        'sample_record': result[0] if result else None
                    }
                else:
                    verification[table_name.lower()] = {
                        'record_count': 0,
                        'status': 'empty',
                        'sample_record': None
                    }

            except Exception as e:
                verification[table_name.lower()] = {
                    'record_count': 0,
                    'status': 'error',
                    'error': str(e),
                    'sample_record': None
                }

        total_records = sum(v.get('record_count', 0) for v in verification.values())
        populated_tables = sum(1 for v in verification.values() if v.get('record_count', 0) > 0)

        return jsonify({
            'status': 'success',
            'summary': {
                'total_tables': len(target_tables),
                'populated_tables': populated_tables,
                'total_records': total_records
            },
            'verification_details': verification
        }), 200

    except Exception as e:
        logger.exception(f'Railway data verification error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Verification failed',
            'error': str(e)
        }), 500