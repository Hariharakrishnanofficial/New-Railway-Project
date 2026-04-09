"""
Focused Train Creation Test
Tests creating a single minimal train using the reliable railway data endpoint.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

print('FOCUSED TRAIN CREATION TEST')
print('=' * 50)

# Test the reliable railway data creation endpoint
print('Calling reliable-railway-data/create-persistent-records to see current behavior...')

try:
    url = f'{BASE_URL}/reliable-railway-data/create-persistent-records'
    request_obj = urllib.request.Request(url, method='POST')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    result = json.loads(response.read().decode())

    print('\n=== RESPONSE ===')
    print(json.dumps(result, indent=2))

    # Focus on the trains module results
    trains_result = result.get('results', {}).get('module_results', {}).get('trains', {})

    print('\n=== TRAINS MODULE ANALYSIS ===')
    print(f"Attempted: {trains_result.get('attempted', 0)}")
    print(f"Created: {trains_result.get('created', 0)}")
    print(f"Station ROWID mapping available: {'station_rowid_map' in result.get('results', {}).get('module_results', {}).get('stations', {})}")

    # Show specific train errors
    train_details = trains_result.get('details', [])
    for i, detail in enumerate(train_details):
        print(f"\nTrain {i+1} ({detail.get('train_number', 'unknown')}):")
        print(f"  From: {detail.get('from_station')}")
        print(f"  To: {detail.get('to_station')}")
        print(f"  Success: {detail.get('success')}")
        print(f"  Error: {detail.get('error')}")

    # Show station ROWID mapping
    station_details = result.get('results', {}).get('module_results', {}).get('stations', {})
    if 'station_rowid_map' in station_details:
        print(f"\n=== STATION ROWID MAP ===")
        station_map = station_details['station_rowid_map']
        for code, rowid in station_map.items():
            print(f"  {code} -> ROWID {rowid}")

        print(f"\n=== CONCLUSION ===")
        if len(station_map) >= 2:
            print("✅ Station ROWIDs are available for foreign key mapping")
            print("❌ Train creation is still failing despite correct ROWID mapping")
            print("\nNext steps:")
            print("1. The error 'Invalid input value for column name' suggests field name mismatch")
            print("2. May need to check train data structure against exact CloudScale schema")
            print("3. Could be data type mismatch (string vs number vs boolean)")
        else:
            print("❌ Insufficient station ROWIDs for train creation")

except Exception as e:
    print(f'Error calling endpoint: {str(e)}')

    # If the main endpoint fails, check basic connectivity
    try:
        basic_url = f'{BASE_URL}/reliable-railway-data/verify-persistence'
        request_obj = urllib.request.Request(basic_url, method='GET')
        response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
        print('✅ Basic connectivity to reliable-railway-data endpoint works')
    except Exception as basic_e:
        print(f'❌ Basic connectivity failed: {str(basic_e)}')

print('\nFocused test completed.')