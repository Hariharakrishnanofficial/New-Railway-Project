"""
Test Reliable Railway Data Creation - CloudScale Persistence Fix

Tests the new /reliable-railway-data endpoints to ensure actual CloudScale persistence
using proven cloudscale_repo.create_record() method with ZCQL verification.
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
        response = urllib.request.urlopen(request_obj, timeout=180, context=ctx)  # Longer timeout for data creation
        response_data = json.loads(response.read().decode())

        success = response.status in [200, 201]
        status = "SUCCESS" if success else "FAILED"
        print(f"{status} - {method} {endpoint}")

        return {
            'success': success,
            'status_code': response.status,
            'data': response_data
        }

    except Exception as e:
        print(f"ERROR - {method} {endpoint}: {str(e)[:100]}")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("=" * 80)
print("RELIABLE RAILWAY DATA CREATION TEST")
print("CloudScale Persistence Fix - Using proven create_record() method")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Step 1: Create persistent railway records
print(f"\nSTEP 1: CREATE PERSISTENT RAILWAY RECORDS")
print("-" * 60)
print("Using proven cloudscale_repo.create_record() with immediate ZCQL verification...")

create_result = api_request('POST', '/reliable-railway-data/create-persistent-records')

if create_result['success']:
    data = create_result['data']
    results = data.get('results', {})
    summary = results.get('summary', {})

    print(f"Status: {data.get('status', 'unknown').upper()}")
    print(f"Message: {data.get('message', '')}")
    print()

    print(f"SUMMARY:")
    print(f"  Total Attempted: {summary.get('total_attempted', 0)}")
    print(f"  Total Created: {summary.get('total_created', 0)}")
    print(f"  Total Verified: {summary.get('total_verified', 0)}")
    print(f"  Modules Successful: {summary.get('modules_successful', 0)}/4")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")
    print()

    # Show details for each module
    module_results = results.get('module_results', {})
    print(f"MODULE DETAILS:")
    for module, module_result in module_results.items():
        attempted = module_result.get('attempted', 0)
        created = module_result.get('created', 0)
        verified = module_result.get('verified', 0)
        status = "SUCCESS" if created > 0 else "FAILED"

        print(f"  {module.capitalize():<12} | {created}/{attempted} created, {verified} verified | {status}")

        # Show created items
        if module == 'stations':
            created_items = module_result.get('created_stations', [])
        elif module == 'trains':
            created_items = module_result.get('created_trains', [])
        elif module == 'fares':
            created_items = module_result.get('created_fares', [])
        elif module == 'quotas':
            created_items = module_result.get('created_quotas', [])
        else:
            created_items = []

        if created_items:
            print(f"    Created: {created_items}")

        # Show errors if any
        details = module_result.get('details', [])
        errors = [detail.get('error') for detail in details if detail.get('error')]
        if errors:
            print(f"    Errors: {errors[:2]}{'...' if len(errors) > 2 else ''}")

    creation_successful = summary.get('total_created', 0) > 0
else:
    print(f"FAILED: {create_result['data'].get('error', 'Unknown error')}")
    creation_successful = False

# Step 2: Verify actual persistence using direct ZCQL
print(f"\nSTEP 2: VERIFY ACTUAL CLOUDSCALE PERSISTENCE")
print("-" * 60)
print("Using direct ZCQL queries (bypasses all caching)...")

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
    print(f"  Modules with Data: {summary.get('modules_with_data', [])}")
    print()

    print(f"DIRECT ZCQL VERIFICATION:")
    print(f"{'Module':<12} {'Count':<6} {'Status':<8} {'Query'}")
    print("-" * 80)

    total_verified_records = 0
    verified_modules = []

    for module, result in verification_results.items():
        count = result.get('count', 0)
        status = result.get('status', 'UNKNOWN')
        query = result.get('query', '')

        print(f"{module.capitalize():<12} {count:<6} {status:<8} {query[:40]}...")

        if count > 0:
            total_verified_records += count
            verified_modules.append(module)

    verification_successful = len(verified_modules) > 0
else:
    print(f"FAILED: {verify_result['data'].get('error', 'Unknown error')}")
    verification_successful = False
    total_verified_records = 0
    verified_modules = []

# Step 3: Final Assessment
print(f"\n" + "=" * 80)
print("FINAL ASSESSMENT - CLOUDSCALE PERSISTENCE TEST")
print("=" * 80)

print(f"\nCREATION PROCESS:")
if creation_successful:
    print(f"  ✓ SUCCESS - Railway data creation completed")
    if create_result['success']:
        summary = create_result['data'].get('results', {}).get('summary', {})
        print(f"    Created {summary.get('total_created', 0)} records across {summary.get('modules_successful', 0)} modules")
else:
    print(f"  ✗ FAILED - Railway data creation failed")

print(f"\nPERSISTENCE VERIFICATION:")
if verification_successful:
    print(f"  ✓ SUCCESS - CloudScale records confirmed via direct ZCQL")
    print(f"    Found {total_verified_records} records in {len(verified_modules)} modules")
    print(f"    Verified modules: {verified_modules}")
else:
    print(f"  ✗ FAILED - No persistent records found in CloudScale")

print(f"\nREQUESTED 4 RAILWAY MODULES STATUS:")
requested_modules = ['trains', 'stations', 'fares', 'quotas']
success_count = 0

if verify_result['success'] and verification_results:
    for module in requested_modules:
        if module in verification_results:
            count = verification_results[module].get('count', 0)
            status = "✓ HAS DATA" if count > 0 else "✗ EMPTY"
            print(f"  {module.capitalize():<12} | {count:>3} records | {status}")
            if count > 0:
                success_count += 1
        else:
            print(f"  {module.capitalize():<12} |   ? records | ? NOT VERIFIED")
else:
    for module in requested_modules:
        print(f"  {module.capitalize():<12} |   ? records | ? VERIFICATION FAILED")

print(f"\nOVERALL RESULT:")
if success_count >= 3:
    print(f"🎉 EXCELLENT! {success_count}/4 railway modules now have persistent data!")
    print(f"   CloudScale persistence fix was successful!")
elif success_count >= 1:
    print(f"✓ PROGRESS! {success_count}/4 railway modules have persistent data!")
    print(f"   Partial success - some modules working")
else:
    print(f"✗ ISSUE: 0/4 railway modules have persistent data")
    print(f"   CloudScale persistence still problematic")

if total_verified_records > 0:
    print(f"\n*** {total_verified_records} VERIFIED RECORDS IN CLOUDSCALE ***")
    print(f"Your railway system now has real, persistent data!")
else:
    print(f"\n*** NO VERIFIED RECORDS FOUND ***")
    print(f"CloudScale persistence issue persists")

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)