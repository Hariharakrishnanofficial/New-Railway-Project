"""
Test Expand Railway Routes - Build Upon Successful Patterns
Tests the new expansion routes to create more railway data.
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
        status = "SUCCESS" if success else "FAILED"
        print(f"{status} - {method} {endpoint}")

        return {
            'success': success,
            'data': response_data
        }

    except Exception as e:
        print(f"ERROR - {method} {endpoint}: {str(e)[:50]}")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("="*80)
print("EXPAND RAILWAY DATA - BUILD ON SUCCESSFUL PATTERNS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Step 1: Create more fare records using working schema
print("\\nSTEP 1: CREATE MORE FARE RECORDS")
print("-" * 60)

create_fares_result = api_request('POST', '/expand-railway/create-more-fares')

if create_fares_result['success']:
    data = create_fares_result['data']
    created_new = data.get('created_new', 0)
    total_fares = data.get('total_fares', 0)
    working_schema = data.get('working_schema', {})

    print(f"  New Fares Created: {created_new}")
    print(f"  Total Fares Now: {total_fares}")
    print(f"  Working Schema: {working_schema}")
else:
    print(f"  Failed: {create_fares_result['data'].get('error', 'Unknown error')}")

# Step 2: Test similar patterns on other railway tables
print(f"\\nSTEP 2: TEST SIMILAR PATTERNS ON OTHER RAILWAY TABLES")
print("-" * 60)

pattern_test_result = api_request('POST', '/expand-railway/test-similar-patterns')

if pattern_test_result['success']:
    data = pattern_test_result['data']
    summary = data.get('summary', {})
    detailed_results = data.get('detailed_results', {})

    print(f"  Successful Tables: {summary.get('successful_tables', 0)}")
    print(f"  Total New Records: {summary.get('total_new_records', 0)}")

    print(f"\\nTable Results:")
    for table, info in detailed_results.items():
        status = info.get('status', 'unknown').upper()
        total_records = info.get('total_records', 0)
        working_schema = info.get('working_schema')

        print(f"  {table:<20} | {status:<7} | {total_records} records")
        if working_schema:
            print(f"    Working schema: {working_schema}")
else:
    print(f"  Failed: {pattern_test_result['data'].get('error', 'Unknown error')}")

# Step 3: Get final comprehensive status
print(f"\\nSTEP 3: FINAL RAILWAY DATA STATUS")
print("-" * 60)

final_status_result = api_request('GET', '/expand-railway/final-status')

if final_status_result['success']:
    data = final_status_result['data']
    summary = data.get('summary', {})
    table_details = data.get('table_details', {})

    print(f"  Total Railway Tables: {summary.get('total_railway_tables', 0)}")
    print(f"  Populated Tables: {summary.get('populated_tables', 0)}")
    print(f"  Total Records: {summary.get('total_railway_records', 0)}")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")

    print(f"\\nRailway Table Status:")
    print(f"{'Table':<20} {'Records':<8} {'Status':<12}")
    print("-" * 50)

    railway_tables_with_data = []

    for table, info in table_details.items():
        count = info.get('record_count', 0)
        status = info.get('status', 'unknown').upper()
        sample_fields = info.get('sample_fields', [])

        print(f"{table:<20} {count:<8} {status:<12}")

        # Show sample fields for populated tables
        if count > 0 and sample_fields:
            railway_tables_with_data.append(table)
            print(f"  Sample fields: {sample_fields[:3]}")

    print(f"\\nRAILWAY MODULES WITH DATA: {railway_tables_with_data}")
else:
    print(f"  Failed: {final_status_result['data'].get('error', 'Unknown error')}")

# FINAL SUCCESS SUMMARY
print(f"\\n" + "="*80)
print("EXPANSION RESULTS SUMMARY")
print("="*80)

if final_status_result['success']:
    summary = final_status_result['data'].get('summary', {})
    total_records = summary.get('total_railway_records', 0)
    populated_tables = summary.get('populated_tables', 0)

    print(f"\\nCLOUDSCALE RAILWAY DATA STATUS:")
    print(f"  Total Records: {total_records}")
    print(f"  Populated Tables: {populated_tables}")

    # Check the 6 requested modules specifically
    print(f"\\nREQUESTED 6 RAILWAY MODULES STATUS:")
    requested_modules = ['trains', 'stations', 'train_inventory', 'train_routes', 'fares', 'quotas']

    if 'table_details' in final_status_result['data']:
        table_details = final_status_result['data']['table_details']
        success_count = 0

        for module in requested_modules:
            if module in table_details:
                count = table_details[module].get('record_count', 0)
                status = "✓ HAS DATA" if count > 0 else "✗ EMPTY"
                print(f"  {module:<20} | {status}")
                if count > 0:
                    success_count += 1
            else:
                print(f"  {module:<20} | ✗ NOT FOUND")

        print(f"\\nSUCCESS: {success_count}/6 requested railway modules now have data!")

    if total_records > 0:
        print(f"\\n*** EXPANSION SUCCESS! {total_records} railway records now in CloudScale! ***")
        print("You now have sample data for your railway ticketing system.")
    else:
        print(f"\\n*** Still working on creating railway data... ***")

print(f"\\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)