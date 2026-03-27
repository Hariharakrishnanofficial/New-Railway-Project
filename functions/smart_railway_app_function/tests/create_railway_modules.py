"""
Create Railway Module Data - Build on Existing Success
Uses working endpoints to create data for the 6 requested railway modules.
"""

import urllib.request
import urllib.error
import json
import ssl
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
        return {'success': True, 'data': response_data}
    except Exception as e:
        return {'success': False, 'data': {'error': str(e)}}

print("="*70)
print("CREATE RAILWAY MODULE DATA - BUILD ON SUCCESS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# Step 1: Check current status
print("\\nSTEP 1: CHECK CURRENT DATA STATUS")
print("-" * 50)

verify_result = api_request('GET', '/schema-discovery/final-verification')
if verify_result['success']:
    table_verification = verify_result['data'].get('table_verification', {})
    print("Current CloudScale Data:")
    for table, info in table_verification.items():
        count = info.get('record_count', 0)
        status = "HAS DATA" if count > 0 else "EMPTY"
        print(f"  {table:<20} | {count:>3} records | {status}")

# Step 2: Try to create more data using working patterns
print("\\nSTEP 2: CREATE MORE RAILWAY DATA")
print("-" * 50)

# Use the working schema discovery creation endpoint
create_result = api_request('POST', '/schema-discovery/create-with-working-schemas')

if create_result['success']:
    summary = create_result['data'].get('summary', {})
    detailed_results = create_result['data'].get('detailed_results', {})

    print("Creation Results:")
    print(f"  Successful Tables: {summary.get('successful_tables', 0)}")
    print(f"  Total Records: {summary.get('total_records_verified', 0)}")

    print("\\nTable Details:")
    for table, info in detailed_results.items():
        status = info.get('status', 'unknown').upper()
        verified = info.get('verified', 0)
        working_schema = info.get('working_schema')

        print(f"  {table:<20} | {status:<7} | {verified} records")
        if working_schema:
            schema_str = str(working_schema).replace("'", "")
            print(f"    Schema: {schema_str}")

# Step 3: Try Railway Data endpoint for specific modules
print("\\nSTEP 3: TARGET RAILWAY MODULES DIRECTLY")
print("-" * 50)

railway_result = api_request('POST', '/railway-data/create-railway-modules')

if railway_result['success']:
    summary = railway_result['data'].get('summary', {})
    detailed_results = railway_result['data'].get('detailed_results', {})

    print("Railway Module Results:")
    print(f"  Target Modules: {summary.get('target_modules', 0)}")
    print(f"  Successful: {summary.get('successful_modules', 0)}")

    print("\\nModule Details:")
    for module, info in detailed_results.items():
        status = info.get('status', 'unknown').upper()
        records = info.get('records_verified', 0)
        print(f"  {module:<20} | {status:<7} | {records} records")

# Step 4: Final verification of all data
print("\\nSTEP 4: FINAL VERIFICATION")
print("-" * 50)

final_verify_result = api_request('GET', '/schema-discovery/final-verification')
if final_verify_result['success']:
    summary = final_verify_result['data'].get('summary', {})
    table_verification = final_verify_result['data'].get('table_verification', {})

    print("Final CloudScale Status:")
    print(f"  Total Records: {summary.get('total_records_in_cloudscale', 0)}")
    print(f"  Populated Tables: {summary.get('populated_tables', 0)}")

    print("\\nRailway Module Status:")
    requested_modules = ['trains', 'stations', 'train_inventory', 'train_routes', 'fares', 'quotas']
    successful_modules = []

    for module in requested_modules:
        if module in table_verification:
            count = table_verification[module].get('record_count', 0)
            status = "SUCCESS" if count > 0 else "EMPTY"
            print(f"  {module:<20} | {count:>3} records | {status}")
            if count > 0:
                successful_modules.append(module)
        else:
            print(f"  {module:<20} |   0 records | NOT FOUND")

    print(f"\\nSUCCESS COUNT: {len(successful_modules)}/6 railway modules")
    if successful_modules:
        print(f"Modules with data: {successful_modules}")

    total_records = summary.get('total_records_in_cloudscale', 0)
    if total_records > 0:
        print(f"\\n*** {total_records} RECORDS NOW IN CLOUDSCALE! ***")
        if len(successful_modules) >= 3:
            print("*** GOOD PROGRESS ON RAILWAY MODULES! ***")
    else:
        print("\\n*** Still working on CloudScale data creation ***")

print(f"\\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)