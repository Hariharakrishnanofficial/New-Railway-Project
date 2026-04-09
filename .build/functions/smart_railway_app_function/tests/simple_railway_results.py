"""
Simple Railway Data Results Viewer
Shows working schemas and creates more data.
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
        response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
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
print("RAILWAY DATA WORKING SCHEMAS AND CREATION")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Step 1: Create records with discovered working schemas
print("\nSTEP 1: CREATE RECORDS WITH WORKING SCHEMAS")
print("-" * 60)

create_result = api_request('POST', '/schema-discovery/create-with-working-schemas')

if create_result['success']:
    results = create_result['data'].get('detailed_results', {})

    print("\nRecord Creation Results:")
    for table, info in results.items():
        status = info.get('status', 'unknown')
        verified = info.get('verified', 0)
        working_schema = info.get('working_schema')

        print(f"  {table:<20} | {status.upper():<7} | {verified} records")
        if working_schema:
            print(f"    Working schema: {working_schema}")

# Step 2: Check final verification
print(f"\nSTEP 2: CHECK ALL RAILWAY DATA")
print("-" * 60)

verify_result = api_request('GET', '/schema-discovery/final-verification')

if verify_result['success']:
    verification = verify_result['data'].get('table_verification', {})

    print("\nCloudScale Table Status:")
    total_records = 0

    for table, info in verification.items():
        count = info.get('record_count', 0)
        status = info.get('status', 'unknown')
        total_records += count

        print(f"  {table:<20} | {count:>3} records | {status.upper()}")

    print(f"\nTotal Records in CloudScale: {total_records}")

# Step 3: Test API access to working data
print(f"\nSTEP 3: TEST API ACCESS")
print("-" * 60)

endpoints = ['/fares', '/settings', '/announcements', '/stations', '/trains', '/quotas']

working_endpoints = []

for endpoint in endpoints:
    try:
        result = api_request('GET', endpoint)
        if result['success']:
            data = result['data'].get('data', [])
            count = len(data)

            if count > 0:
                working_endpoints.append(endpoint)
                print(f"  {endpoint:<20} | {count:>3} records | ACCESSIBLE")

                # Show first record structure for railway modules
                if endpoint in ['/fares', '/stations', '/trains', '/quotas']:
                    first_record = data[0]
                    if isinstance(first_record, dict):
                        # Show key fields (non-system fields)
                        key_fields = []
                        for k, v in first_record.items():
                            if not k.startswith('CREATED') and not k.startswith('MODIFIED') and not k.startswith('ROWID'):
                                key_fields.append(f"{k}={v}")

                        if key_fields:
                            print(f"    Sample data: {key_fields[:3]}")
            else:
                print(f"  {endpoint:<20} |   0 records | EMPTY")
    except:
        print(f"  {endpoint:<20} | ERR records | ERROR")

# FINAL SUCCESS SUMMARY
print(f"\n" + "="*80)
print("FINAL RAILWAY DATA STATUS")
print("="*80)

print(f"\nSUCCESS SUMMARY:")

if verify_result['success']:
    summary = verify_result['data'].get('summary', {})
    total = summary.get('total_records_in_cloudscale', 0)
    populated = summary.get('populated_tables', 0)

    print(f"  Total Records Created: {total}")
    print(f"  Tables with Data: {populated}")

    if working_endpoints:
        print(f"  Working API Endpoints: {len(working_endpoints)}")
        print(f"  Accessible endpoints: {working_endpoints}")

    # Check specific railway modules
    railway_modules = ['stations', 'trains', 'fares', 'quotas', 'train_routes', 'train_inventory']
    railway_success = []

    if 'table_verification' in verify_result['data']:
        verification = verify_result['data']['table_verification']
        for module in railway_modules:
            if module in verification and verification[module].get('record_count', 0) > 0:
                railway_success.append(module)

    if railway_success:
        print(f"\nRAILWAY MODULES WITH DATA: {railway_success}")
    else:
        print(f"\nRAILWAY MODULES: Still discovering working schemas...")

    if total > 0:
        print(f"\n*** SUCCESS! {total} RECORDS NOW IN CLOUDSCALE! ***")
        print(f"Your railway system now has real data you can access via API.")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)