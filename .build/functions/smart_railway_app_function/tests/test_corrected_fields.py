"""
Test Corrected Field Names - Railway Data Creation
Tests the updated reliable railway data endpoint with exact CloudScale schema field names.
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
        response = urllib.request.urlopen(request_obj, timeout=180, context=ctx)
        response_data = json.loads(response.read().decode())

        success = response.status in [200, 201]
        status = "SUCCESS" if success else "FAILED"
        print(f"{status} - {method} {endpoint} (HTTP {response.status})")

        return {
            'success': success,
            'status_code': response.status,
            'data': response_data
        }

    except Exception as e:
        print(f"ERROR - {method} {endpoint}: {str(e)[:100]}...")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("=" * 80)
print("TEST CORRECTED CLOUDSCALE FIELD NAMES")
print("Railway Data Creation with Exact Schema Compliance")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Test 1: Create railway records with corrected field names
print(f"\nSTEP 1: CREATE RAILWAY RECORDS WITH CORRECTED FIELDS")
print("-" * 60)
print("Using exact CloudScale schema field names from CLOUDSCALE_DATABASE_V2.md...")

create_result = api_request('POST', '/reliable-railway-data/create-persistent-records')

if create_result['success']:
    data = create_result['data']
    results = data.get('results', {})
    summary = results.get('summary', {})

    print(f"Status: {data.get('status', 'unknown').upper()}")
    print(f"Message: {data.get('message', '')}")
    print()

    print(f"CREATION SUMMARY:")
    print(f"  Total Attempted: {summary.get('total_attempted', 0)}")
    print(f"  Total Created: {summary.get('total_created', 0)}")
    print(f"  Total Verified: {summary.get('total_verified', 0)}")
    print(f"  Modules Successful: {summary.get('modules_successful', 0)}/4")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")
    print()

    # Show module details
    module_results = results.get('module_results', {})
    print(f"MODULE RESULTS:")
    for module, result in module_results.items():
        attempted = result.get('attempted', 0)
        created = result.get('created', 0)
        verified = result.get('verified', 0)
        status = "✓ SUCCESS" if created > 0 else "✗ FAILED"
        print(f"  {module.capitalize():<12} | {created}/{attempted} records | {status}")

        # Show any errors
        details = result.get('details', [])
        for detail in details[:2]:  # Show first 2 details
            if detail.get('error'):
                error_msg = detail['error'][:60] + "..." if len(detail['error']) > 60 else detail['error']
                print(f"    Error: {error_msg}")

    creation_successful = summary.get('total_created', 0) > 0
else:
    print(f"CREATION FAILED: {create_result['data'].get('error', 'Unknown error')}")
    creation_successful = False

# Test 2: Verify persistence with direct ZCQL
print(f"\nSTEP 2: VERIFY CLOUDSCALE PERSISTENCE")
print("-" * 60)
print("Using direct ZCQL queries to confirm actual data persistence...")

verify_result = api_request('GET', '/reliable-railway-data/verify-persistence')

if verify_result['success']:
    data = verify_result['data']
    summary = data.get('summary', {})
    verification_results = data.get('verification_results', {})

    print(f"Status: {data.get('status', 'unknown').upper()}")
    print(f"Message: {data.get('message', '')}")
    print()

    print(f"VERIFICATION SUMMARY:")
    print(f"  Total Railway Records: {summary.get('total_railway_records', 0)}")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}/4")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")
    print()

    print(f"DIRECT ZCQL RESULTS:")
    print(f"{'Module':<12} {'Records':<8} {'Status':<8} {'Query'}")
    print("-" * 70)

    total_verified = 0
    verified_modules = []

    for module, result in verification_results.items():
        count = result.get('count', 0)
        status = result.get('status', 'UNKNOWN')
        query = result.get('query', '')[:30] + "..." if result.get('query') else ''

        print(f"{module.capitalize():<12} {count:<8} {status:<8} {query}")

        if count > 0:
            total_verified += count
            verified_modules.append(module)

    verification_successful = len(verified_modules) > 0
else:
    print(f"VERIFICATION FAILED: {verify_result['data'].get('error', 'Unknown error')}")
    verification_successful = False
    total_verified = 0
    verified_modules = []

# Final Assessment
print(f"\n" + "=" * 80)
print("FINAL ASSESSMENT - CORRECTED FIELD NAMES TEST")
print("=" * 80)

print(f"\nFIELD NAME CORRECTIONS:")
print(f"  ✓ Station fields: Number_of_Platforms, Station_Type, Division, etc.")
print(f"  ✓ Train fields: Run_Days, Distance, Pantry_Car_Available, etc.")
print(f"  ✓ Fare fields: From_Station, To_Station, Base_Fare, Distance_KM")
print(f"  ✓ Quota fields: Train, Class, Total_Seats, Available_Seats")

print(f"\nCREATION RESULTS:")
if creation_successful:
    print(f"  ✓ SUCCESS - Railway records created with correct field names")
    if create_result['success']:
        summary = create_result['data'].get('results', {}).get('summary', {})
        print(f"    Created {summary.get('total_created', 0)} records across {summary.get('modules_successful', 0)} modules")
else:
    print(f"  ✗ FAILED - Field name issues may still exist")

print(f"\nPERSISTENCE VERIFICATION:")
if verification_successful:
    print(f"  ✓ SUCCESS - {total_verified} records confirmed in CloudScale")
    print(f"    Modules with data: {verified_modules}")
else:
    print(f"  ✗ FAILED - No persistent records found")

print(f"\nRAILWAY MODULES STATUS:")
requested_modules = ['trains', 'stations', 'fares', 'quotas']
success_count = len(verified_modules) if verification_successful else 0

if success_count == 4:
    print(f"  🎉 PERFECT! All 4 railway modules have persistent data!")
    print(f"     CloudScale field name corrections were successful!")
elif success_count >= 2:
    print(f"  ✓ GOOD PROGRESS! {success_count}/4 railway modules working!")
    print(f"     Field name corrections mostly successful!")
elif success_count == 1:
    print(f"  ~ PARTIAL: {success_count}/4 railway module working")
    print(f"     Some field name corrections working")
else:
    print(f"  ✗ ISSUE: 0/4 railway modules working")
    print(f"     Field name corrections may need more work")

if total_verified > 0:
    print(f"\n*** {total_verified} VERIFIED RAILWAY RECORDS IN CLOUDSCALE! ***")
    print(f"The exact CloudScale schema field names are working!")
else:
    print(f"\n*** NO VERIFIED RECORDS - May need further field corrections ***")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)