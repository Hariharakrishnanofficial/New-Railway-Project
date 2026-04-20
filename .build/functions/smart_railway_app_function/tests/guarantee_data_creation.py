"""
GUARANTEED CloudScale Data Population
This script will ACTUALLY put data into CloudScale and verify it exists.
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

def api_request(method, endpoint, data=None, expected_status=[200, 201]):
    """Make API request and return result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)

        start_time = time.time()
        response = urllib.request.urlopen(request_obj, timeout=120, context=ctx)
        elapsed = (time.time() - start_time) * 1000

        response_data = json.loads(response.read().decode())

        success = response.status in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:45} | {response.status} | {elapsed:6.0f}ms")

        return {
            'success': success,
            'status': response.status,
            'data': response_data,
            'time': elapsed
        }

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = {'message': str(e)}

        success = e.code in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:45} | {e.code} | {elapsed:6.0f}ms")

        return {
            'success': success,
            'status': e.code,
            'data': error_data,
            'time': elapsed
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:45} | ERR | 0ms | {str(e)[:40]}")
        return {
            'success': False,
            'status': 0,
            'data': {'error': str(e)},
            'time': 0
        }

print("="*100)
print("GUARANTEED CLOUDSCALE DATA POPULATION - DIRECT METHOD")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Create real working data using direct method
print("\n[STEP 1: CREATE REAL WORKING DATA IN CLOUDSCALE]")
print("-" * 80)

create_result = api_request('POST', '/direct-data/create-real-data')

if create_result['success']:
    summary = create_result['data'].get('summary', {})
    results = create_result['data'].get('detailed_results', {})

    print(f"\nDirect Data Creation Results:")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records Verified: {summary.get('total_records_verified', 0)}")

    print(f"\nModule-by-Module Results:")
    for module, info in results.items():
        status = info.get('status', 'unknown')
        verified = info.get('verify_count', 0)
        print(f"  {module:<15} | {status.upper():<7} | {verified} verified records")
        if status == 'error':
            print(f"    Error: {info.get('error', 'Unknown error')[:60]}")

else:
    print("FAILED to create real data!")
    print(f"Error: {create_result['data']}")

# Step 2: Bulk populate ALL modules
print(f"\n[STEP 2: BULK POPULATE ALL MODULES]")
print("-" * 80)

bulk_result = api_request('POST', '/direct-data/bulk-populate')

if bulk_result['success']:
    summary = bulk_result['data'].get('summary', {})
    results = bulk_result['data'].get('detailed_results', {})

    print(f"\nBulk Population Results:")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records Verified: {summary.get('total_records_verified', 0)}")

    print(f"\nDetailed Results:")
    for module, info in results.items():
        status = info.get('status', 'unknown')
        attempted = info.get('attempted', 0)
        verified = info.get('verified', 0)
        print(f"  {module:<15} | {status.upper():<7} | {verified}/{attempted} records")

# Step 3: Verify ALL data exists using direct ZCQL queries
print(f"\n[STEP 3: VERIFY ALL DATA EXISTS IN CLOUDSCALE]")
print("-" * 80)

verify_result = api_request('GET', '/direct-data/verify-all')

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    details = verify_result['data'].get('table_details', {})

    print(f"\nCloudScale Verification Results:")
    print(f"  Tables Checked: {summary.get('total_tables_checked', 0)}")
    print(f"  Tables with Data: {summary.get('populated_tables', 0)}")
    print(f"  Total Records Found: {summary.get('total_records_found', 0)}")

    print(f"\nTable-by-Table Verification:")
    populated_tables = []

    for table, info in details.items():
        status = info.get('status', 'unknown')
        count = info.get('record_count', 0)
        print(f"  {table:<15} | {status.upper():<10} | {count:>3} records")

        if count > 0:
            populated_tables.append(table)
            # Show sample record fields
            sample_records = info.get('sample_records', [])
            if sample_records:
                first_record = sample_records[0]
                if isinstance(first_record, dict):
                    # Look for the actual table data
                    for key, value in first_record.items():
                        if isinstance(value, dict):
                            fields = list(value.keys())[:4]  # First 4 fields
                            print(f"    Sample fields: {fields}")
                            break

    print(f"\n*** POPULATED TABLES: {populated_tables} ***")

# Step 4: Test public GET endpoints to confirm data is accessible
print(f"\n[STEP 4: TEST PUBLIC ENDPOINTS FOR DATA ACCESS]")
print("-" * 80)

public_endpoints = ['/settings', '/stations', '/trains', '/announcements', '/fares', '/quotas']

accessible_data = {}

for endpoint in public_endpoints:
    result = api_request('GET', endpoint)
    if result['success']:
        data = result['data'].get('data', [])
        count = len(data)
        accessible_data[endpoint] = count
        print(f"  {endpoint:<15} | {count:>3} records accessible via API")

        if count > 0:
            # Show first record structure
            first_record = data[0]
            if isinstance(first_record, dict):
                sample_keys = list(first_record.keys())[:4]
                print(f"    API fields: {sample_keys}")

# FINAL SUMMARY
print(f"\n" + "="*100)
print("FINAL CLOUDSCALE DATA POPULATION SUMMARY")
print("="*100)

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    total_records = summary.get('total_records_found', 0)
    populated_tables = summary.get('populated_tables', 0)

    print(f"\nCLOUDSCALE DATABASE STATUS:")
    print(f"  Total Records in CloudScale: {total_records}")
    print(f"  Tables with Data: {populated_tables}/6")

    if total_records > 0:
        print(f"\n*** SUCCESS! DATA IS NOW IN CLOUDSCALE! ***")
        print(f"You now have {total_records} records across {populated_tables} tables.")
    else:
        print(f"\n*** NO DATA CREATED - STILL INVESTIGATING ***")

    # Show accessible data via API
    api_records = sum(accessible_data.values())
    if api_records > 0:
        print(f"\nAPI ACCESS:")
        print(f"  Records accessible via API: {api_records}")
        print(f"  Working endpoints: {[ep for ep, count in accessible_data.items() if count > 0]}")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)