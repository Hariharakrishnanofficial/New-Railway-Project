"""
Create Remaining Railway Modules - Very Simple Field Approach
Uses the simplest possible field names to create records for the 5 missing modules.
"""

import urllib.request
import urllib.error
import json
import ssl

# Disable SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

def test_create_record(table_name, record_data):
    """Test creating a single record in a table."""
    try:
        url = f"{BASE_URL}/cloudscale-test/test-table-insert"

        test_data = {
            'table_name': table_name,
            'record_data': record_data
        }

        headers = {'Content-Type': 'application/json'}
        body = json.dumps(test_data).encode('utf-8')

        request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
        response_data = json.loads(response.read().decode())

        return {
            'success': response.status in [200, 201],
            'data': response_data
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

print("SIMPLE FIELD TESTING FOR REMAINING RAILWAY MODULES")
print("=" * 60)

# Test patterns based on the successful fares pattern: Base_Fare + Class
# Fares working pattern: {'Base_Fare': '500', 'Class': 'SL'}

test_patterns = {
    'Trains': [
        {'Name': 'Express', 'Number': '12345'},
        {'Train_Name': 'Rajdhani', 'Train_Number': '12951'},
        {'Name': 'Superfast'},
        {'Number': '12002'}
    ],

    'Stations': [
        {'Name': 'Mumbai', 'Code': 'MMCT'},
        {'Station_Name': 'Delhi', 'Station_Code': 'NDLS'},
        {'Name': 'Bangalore'},
        {'Code': 'BNC'}
    ],

    'Train_Inventory': [
        {'Name': 'Inventory', 'Count': '100'},
        {'Type': 'Seats', 'Available': '50'},
        {'Name': 'Coach'},
        {'Count': '200'}
    ],

    'Train_Routes': [
        {'Name': 'Mumbai-Delhi', 'Distance': '1400'},
        {'Route_Name': 'Express Route', 'Duration': '16hrs'},
        {'Name': 'Main Route'},
        {'Distance': '500'}
    ],

    'Quotas': [
        {'Name': 'General', 'Amount': '100'},
        {'Type': 'TATKAL', 'Limit': '50'},
        {'Name': 'Ladies'},
        {'Amount': '25'}
    ]
}

results = {}

for table_name, patterns in test_patterns.items():
    print(f"\\nTesting {table_name}...")
    results[table_name] = {'created': False, 'working_pattern': None}

    for i, pattern in enumerate(patterns):
        print(f"  Pattern {i+1}: {pattern}")

        result = test_create_record(table_name, pattern)

        if result['success']:
            if result['data'].get('status') == 'success':
                print(f"    SUCCESS! Record created")
                results[table_name]['created'] = True
                results[table_name]['working_pattern'] = pattern
                break
            else:
                error_msg = result['data'].get('error', 'Unknown error')
                print(f"    FAILED: {error_msg[:50]}")
        else:
            print(f"    ERROR: {result['error'][:50]}")

print("\\n" + "=" * 60)
print("SIMPLE FIELD TESTING RESULTS")
print("=" * 60)

successful_modules = []
for table_name, result in results.items():
    status = "SUCCESS" if result['created'] else "FAILED"
    print(f"{table_name:<20} | {status}")

    if result['created']:
        successful_modules.append(table_name.lower())
        pattern = result['working_pattern']
        print(f"  Working pattern: {pattern}")

print(f"\\nSUCCESSFUL MODULES: {len(successful_modules)}/5")
if successful_modules:
    print(f"New working modules: {successful_modules}")

# Final verification
print(f"\\nFINAL VERIFICATION...")

try:
    url = f"{BASE_URL}/schema-discovery/final-verification"
    request_obj = urllib.request.Request(url, method='GET')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    verify_data = json.loads(response.read().decode())

    if 'table_verification' in verify_data:
        summary = verify_data.get('summary', {})
        table_verification = verify_data['table_verification']

        total_records = summary.get('total_records_in_cloudscale', 0)
        print(f"Total Records in CloudScale: {total_records}")

        # Check the 6 requested modules
        requested_modules = ['trains', 'stations', 'train_inventory', 'train_routes', 'fares', 'quotas']
        railway_success = []

        for module in requested_modules:
            if module in table_verification:
                count = table_verification[module].get('record_count', 0)
                if count > 0:
                    railway_success.append(module)

        print(f"Railway Modules with Data: {len(railway_success)}/6")
        if railway_success:
            print(f"Successful modules: {railway_success}")

        if len(railway_success) >= 2:
            print(f"\\n*** PROGRESS! {len(railway_success)} railway modules now have data! ***")
        elif len(railway_success) == 1:
            print(f"\\n*** Still working on more railway modules... ***")

except Exception as e:
    print(f"Verification error: {e}")

print("\\nCompleted!")