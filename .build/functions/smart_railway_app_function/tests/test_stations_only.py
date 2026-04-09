"""
Simple Station Creation Test - Minimal Dependencies
Tests creating stations first with minimal field data to establish success pattern.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

# Test with minimal required fields only
minimal_station = {
    'Station_Code': 'TEST1',
    'Station_Name': 'Test Station One',
    'City': 'Test City',
    'State': 'Test State'
}

# Test with full fields as per our current samples
full_station = {
    'Station_Code': 'TEST2',
    'Station_Name': 'Test Station Two',
    'City': 'Test City',
    'State': 'Test State',
    'Zone': 'TR',
    'Division': 'Test Division',
    'Station_Type': 'Junction',
    'Number_of_Platforms': 4,
    'Latitude': 12.9716,
    'Longitude': 77.5946,
    'Is_Active': 'true'
}

def test_create_station(station_data, description):
    """Test creating a station with specific data."""
    print(f"\nTesting {description}:")
    print(f"Data: {station_data}")

    try:
        # Create a custom request to the reliable endpoint but just for stations
        test_payload = {
            'test_mode': True,
            'station_only': True,
            'station_data': station_data
        }

        # We'll need to create a simple station creation via direct API call
        # For now, let's test using the expand-railway endpoint which might have working station creation
        url = f'{BASE_URL}/expand-railway/create-more-samples'
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({}).encode('utf-8')  # Empty body for now

        request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
        result = json.loads(response.read().decode())

        print(f"Response: {result.get('status', 'unknown')}")
        return result.get('status') == 'success'

    except Exception as e:
        print(f"Error: {str(e)[:100]}...")
        return False

print("=" * 60)
print("SIMPLE STATION CREATION TEST")
print("=" * 60)

# Test 1: Check current state
print("\nSTEP 1: Check current station count")
try:
    url = f'{BASE_URL}/reliable-railway-data/verify-persistence'
    request_obj = urllib.request.Request(url, method='GET')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    data = json.loads(response.read().decode())

    verification_results = data.get('verification_results', {})
    stations_info = verification_results.get('stations', {})
    current_count = stations_info.get('count', 0)

    print(f"Current station count: {current_count}")

except Exception as e:
    print(f"Could not check current count: {e}")
    current_count = 0

# Test 2: Try expand-railway endpoint to see if it works
print("\nSTEP 2: Test expand-railway endpoint (known working pattern)")
expand_success = test_create_station({}, "expand-railway method")

# Test 3: Check if station count changed
print("\nSTEP 3: Check if station count changed")
try:
    request_obj = urllib.request.Request(url, method='GET')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    data = json.loads(response.read().decode())

    verification_results = data.get('verification_results', {})
    stations_info = verification_results.get('stations', {})
    new_count = stations_info.get('count', 0)

    print(f"New station count: {new_count}")
    if new_count > current_count:
        print(f"SUCCESS: Added {new_count - current_count} stations!")
    else:
        print("No new stations added")

except Exception as e:
    print(f"Error checking new count: {e}")

print('\nCompleted station creation test')