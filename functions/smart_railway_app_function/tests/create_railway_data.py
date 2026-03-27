"""
Create Targeted Railway Data in CloudScale
Specifically for: Trains, Stations, Train_Inventory, Train_Routes, Fares, Quotas
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from datetime import datetime

# Disable SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

def api_request(method, endpoint, data=None):
    """Make API request and return result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)
        response = urllib.request.urlopen(request_obj, timeout=120, context=ctx)
        response_data = json.loads(response.read().decode())

        success = response.status in [200, 201]
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:50} | {response.status}")

        return {
            'success': success,
            'data': response_data
        }

    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = {'message': str(e)}

        status_icon = "FAIL"
        print(f"{status_icon} {method:6} {endpoint:50} | {e.code}")

        return {
            'success': False,
            'data': error_data
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:50} | ERR | {str(e)[:50]}")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("="*100)
print("TARGETED RAILWAY DATA CREATION IN CLOUDSCALE")
print("Creating records for: Trains, Stations, Train_Inventory, Train_Routes, Fares, Quotas")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Create targeted railway module data
print("\n[STEP 1: CREATE RAILWAY MODULE DATA]")
print("-" * 80)

create_result = api_request('POST', '/railway-data/create-all-modules')

if create_result['success']:
    summary = create_result['data'].get('summary', {})
    results = create_result['data'].get('detailed_results', {})

    print(f"\nRailway Data Creation Summary:")
    print(f"  Target Modules: 6 (stations, trains, fares, quotas, train_routes, train_inventory)")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records Verified: {summary.get('total_records_verified', 0)}")

    print(f"\nModule-by-Module Results:")
    print(f"{'Module':<20} {'Status':<10} {'Created':<8} {'Verified':<10}")
    print("-" * 60)

    for module, info in results.items():
        status = info.get('status', 'unknown').upper()
        created = info.get('created', 0)
        verified = info.get('verified', 0)
        print(f"{module:<20} {status:<10} {created:<8} {verified:<10}")

else:
    print("FAILED to create railway data!")
    print(f"Error: {create_result['data']}")

# Step 2: Create bulk data for working modules
print(f"\n[STEP 2: BULK CREATE ADDITIONAL RECORDS]")
print("-" * 80)

bulk_result = api_request('POST', '/railway-data/bulk-create')

if bulk_result['success']:
    summary = bulk_result['data'].get('summary', {})
    results = bulk_result['data'].get('detailed_results', {})

    print(f"\nBulk Creation Summary:")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records Verified: {summary.get('total_records_verified', 0)}")

    print(f"\nBulk Creation Details:")
    for module, info in results.items():
        status = info.get('status', 'unknown').upper()
        attempted = info.get('attempted', 0)
        verified = info.get('verified', 0)
        print(f"  {module:<15} | {status:<7} | {verified}/{attempted} records")

# Step 3: Verify all railway data
print(f"\n[STEP 3: VERIFY RAILWAY DATA IN CLOUDSCALE]")
print("-" * 80)

verify_result = api_request('GET', '/railway-data/verify')

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    details = verify_result['data'].get('verification_details', {})

    print(f"\nCloudScale Verification Summary:")
    print(f"  Total Tables Checked: {summary.get('total_tables', 0)}")
    print(f"  Tables with Data: {summary.get('populated_tables', 0)}")
    print(f"  Total Records Found: {summary.get('total_records', 0)}")

    print(f"\nTable Verification Details:")
    print(f"{'Table':<20} {'Records':<8} {'Status':<12} {'Sample Data'}")
    print("-" * 80)

    successful_tables = []

    for table, info in details.items():
        count = info.get('record_count', 0)
        status = info.get('status', 'unknown').upper()

        sample_info = ""
        if count > 0:
            successful_tables.append(table)
            sample_record = info.get('sample_record')
            if sample_record and isinstance(sample_record, dict):
                # Extract table data from CloudScale response format
                for key, value in sample_record.items():
                    if isinstance(value, dict):
                        # Show first few fields from the actual record
                        record_fields = list(value.keys())[:3]
                        sample_info = f"Fields: {record_fields}"
                        break

        print(f"{table:<20} {count:<8} {status:<12} {sample_info}")

    if successful_tables:
        print(f"\n*** SUCCESS! Data created in tables: {successful_tables} ***")

# Step 4: Test public API access to verify data is accessible
print(f"\n[STEP 4: TEST API ACCESS TO CREATED DATA]")
print("-" * 80)

api_endpoints = [
    ('/stations', 'Stations'),
    ('/trains', 'Trains'),
    ('/fares', 'Fares'),
    ('/quotas', 'Quotas'),
    ('/train-routes', 'Train Routes'),
    ('/inventory', 'Train Inventory')
]

accessible_data = {}

for endpoint, module_name in api_endpoints:
    result = api_request('GET', endpoint)
    if result['success']:
        data = result['data'].get('data', [])
        count = len(data)
        accessible_data[module_name] = count
        print(f"  {module_name:<20} | {count:>3} records accessible")

        if count > 0:
            # Show sample record structure
            first_record = data[0]
            if isinstance(first_record, dict):
                key_fields = [k for k in first_record.keys() if not k.startswith('CREATED') and not k.startswith('MODIFIED')][:3]
                print(f"    Sample fields: {key_fields}")

# FINAL SUCCESS SUMMARY
print(f"\n" + "="*100)
print("RAILWAY DATA CREATION RESULTS")
print("="*100)

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    total_records = summary.get('total_records', 0)
    populated_tables = summary.get('populated_tables', 0)

    print(f"\nFINAL CLOUDSCALE STATUS:")
    print(f"  Requested Modules: 6 (stations, trains, train_inventory, train_routes, fares, quotas)")
    print(f"  Tables with Data: {populated_tables}/6")
    print(f"  Total Records in CloudScale: {total_records}")

    # API accessibility
    api_records = sum(accessible_data.values())
    accessible_modules = [module for module, count in accessible_data.items() if count > 0]

    if api_records > 0:
        print(f"\nAPI ACCESS STATUS:")
        print(f"  Records accessible via API: {api_records}")
        print(f"  Accessible modules: {accessible_modules}")

    if total_records > 0:
        print(f"\n*** SUCCESS! CloudScale now contains railway data! ***")
        print(f"You can access your data via the API endpoints shown above.")
    else:
        print(f"\n*** STILL WORKING - Some schema challenges remain ***")
        print(f"CloudScale has specific field requirements we're still discovering.")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)