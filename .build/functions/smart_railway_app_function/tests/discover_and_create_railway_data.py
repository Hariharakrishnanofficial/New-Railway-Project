"""
Railway Schema Discovery and Data Creation
Systematically finds working schemas and creates data in specific railway tables.
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
        response = urllib.request.urlopen(request_obj, timeout=180, context=ctx)
        response_data = json.loads(response.read().decode())

        success = response.status in [200, 201]
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:50}")

        return {
            'success': success,
            'data': response_data
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:50} | {str(e)[:50]}")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("="*100)
print("CLOUDSCALE SCHEMA DISCOVERY FOR RAILWAY TABLES")
print("Target tables: Trains, Stations, Train_Inventory, Train_Routes, Fares, Quotas")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Systematic field testing to find working schemas
print("\n[STEP 1: SYSTEMATIC FIELD TESTING]")
print("-" * 80)

test_result = api_request('POST', '/schema-discovery/test-fields')

if test_result['success']:
    summary = test_result['data'].get('summary', {})
    results = test_result['data'].get('detailed_results', {})

    print(f"\nSchema Discovery Results:")
    print(f"  Tables Tested: {summary.get('total_tables_tested', 0)}")
    print(f"  Working Schemas Found: {summary.get('tables_with_working_schema', 0)}")

    print(f"\nDetailed Test Results:")
    for table, info in results.items():
        tests_run = info.get('tests_run', 0)
        successful = info.get('successful_tests', 0)
        print(f"  {table:<15} | {successful}/{tests_run} successful tests")

        # Show successful schema if any
        if successful > 0:
            test_results = info.get('test_results', [])
            for test in test_results:
                if test.get('success'):
                    fields = test.get('field_names', [])
                    values = test.get('fields', {})
                    print(f"    ✓ Working schema: {fields} = {values}")

# Step 2: Create records using any discovered working schemas
print(f"\n[STEP 2: CREATE RECORDS WITH DISCOVERED SCHEMAS]")
print("-" * 80)

create_result = api_request('POST', '/schema-discovery/create-with-working-schemas')

if create_result['success']:
    summary = create_result['data'].get('summary', {})
    results = create_result['data'].get('detailed_results', {})

    print(f"\nRecord Creation Results:")
    print(f"  Successful Tables: {summary.get('successful_tables', 0)}")
    print(f"  Total Records Verified: {summary.get('total_records_verified', 0)}")

    print(f"\nTable-by-Table Results:")
    for table, info in results.items():
        status = info.get('status', 'unknown').upper()
        verified = info.get('verified', 0)
        working_schema = info.get('working_schema')

        print(f"  {table:<20} | {status:<7} | {verified} records")
        if working_schema:
            print(f"    Working schema: {working_schema}")

# Step 3: Final comprehensive verification
print(f"\n[STEP 3: FINAL CLOUDSCALE VERIFICATION]")
print("-" * 80)

verify_result = api_request('GET', '/schema-discovery/final-verification')

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    verification = verify_result['data'].get('table_verification', {})

    print(f"\nFinal CloudScale Status:")
    print(f"  Total Tables Checked: {summary.get('total_tables_checked', 0)}")
    print(f"  Tables with Data: {summary.get('populated_tables', 0)}")
    print(f"  Total Records in CloudScale: {summary.get('total_records_in_cloudscale', 0)}")

    print(f"\nTable Verification:")
    print(f"{'Table':<20} {'Records':<8} {'Status':<12}")
    print("-" * 50)

    railway_tables_with_data = []

    for table, info in verification.items():
        count = info.get('record_count', 0)
        status = info.get('status', 'unknown').upper()

        print(f"{table:<20} {count:<8} {status:<12}")

        # Track railway-specific tables
        if table in ['stations', 'trains', 'fares', 'quotas', 'train_routes', 'train_inventory'] and count > 0:
            railway_tables_with_data.append(table)

    # Show sample data from populated tables
    populated_tables = [t for t, info in verification.items() if info.get('record_count', 0) > 0]

    if populated_tables:
        print(f"\n*** DATA FOUND IN TABLES: {populated_tables} ***")

        for table in populated_tables[:3]:  # Show first 3 populated tables
            info = verification[table]
            sample_records = info.get('sample_records', [])

            if sample_records:
                print(f"\nSample {table.upper()} data:")
                first_record = sample_records[0]
                if isinstance(first_record, dict):
                    for key, value in first_record.items():
                        if isinstance(value, dict):
                            # Show actual record fields
                            for field, field_value in list(value.items())[:5]:
                                if not field.startswith('CREATED') and not field.startswith('MODIFIED'):
                                    print(f"  {field}: {field_value}")
                            break

# Step 4: Test API access to verify data is accessible
print(f"\n[STEP 4: TEST API ACCESS TO CREATED DATA]")
print("-" * 80)

api_endpoints = ['/stations', '/trains', '/fares', '/quotas', '/train-routes', '/inventory', '/settings', '/announcements']

total_accessible_records = 0

for endpoint in api_endpoints:
    try:
        result = api_request('GET', endpoint)
        if result['success']:
            data = result['data'].get('data', [])
            count = len(data)
            total_accessible_records += count

            status = "HAS DATA" if count > 0 else "EMPTY"
            print(f"  {endpoint:<20} | {count:>3} records | {status}")

            if count > 0 and endpoint in ['/stations', '/trains', '/fares', '/quotas']:
                # Show sample for requested railway modules
                first_record = data[0]
                if isinstance(first_record, dict):
                    key_fields = [k for k in first_record.keys() if not k.startswith('CREATED')][:3]
                    print(f"    Sample fields: {key_fields}")
    except:
        print(f"  {endpoint:<20} | ERR records | ERROR")

# FINAL RESULTS SUMMARY
print(f"\n" + "="*100)
print("FINAL RESULTS - RAILWAY DATA IN CLOUDSCALE")
print("="*100)

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    total_records = summary.get('total_records_in_cloudscale', 0)
    populated_tables = summary.get('populated_tables', 0)

    print(f"\nCLOUDSCALE DATABASE STATUS:")
    print(f"  Total Records: {total_records}")
    print(f"  Populated Tables: {populated_tables}")

    print(f"\nREQUESTED RAILWAY MODULES STATUS:")
    requested_modules = ['trains', 'stations', 'train_inventory', 'train_routes', 'fares', 'quotas']

    railway_data_found = False
    for module in requested_modules:
        if module in verification:
            count = verification[module].get('record_count', 0)
            status = "✓ HAS DATA" if count > 0 else "✗ EMPTY"
            print(f"  {module:<20} | {status}")
            if count > 0:
                railway_data_found = True

    print(f"\nAPI ACCESS:")
    print(f"  Total Accessible Records: {total_accessible_records}")

    if total_records > 0:
        print(f"\n*** SUCCESS! CloudScale now contains {total_records} records! ***")
        if railway_data_found:
            print(f"*** Railway-specific data has been created! ***")
        print(f"You can access your data via the API endpoints listed above.")
    else:
        print(f"\n*** Still working on CloudScale schema requirements ***")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)