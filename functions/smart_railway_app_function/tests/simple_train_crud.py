"""
Simple Train CRUD Test Using Available Methods
Creates a minimal train record using the simplest possible approach.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

print('SIMPLE TRAIN CRUD TEST')
print('=' * 40)

# Step 1: Create stations first if needed
print('STEP 1: Ensuring stations exist')

minimal_stations = [
    {
        'Station_Code': 'TST1',
        'Station_Name': 'Test Station One',
        'City': 'Test City',
        'State': 'Test State',
        'Is_Active': 'true'
    },
    {
        'Station_Code': 'TST2',
        'Station_Name': 'Test Station Two',
        'City': 'Test City 2',
        'State': 'Test State',
        'Is_Active': 'true'
    }
]

# Try to create stations using POST to stations endpoint
station_ids = []

for station in minimal_stations:
    try:
        url = f'{BASE_URL}/stations'
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(station).encode('utf-8')

        request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
        result = json.loads(response.read().decode())

        print(f"Station {station['Station_Code']}: {result.get('status', 'unknown')}")
        if result.get('status') == 'success':
            station_data = result.get('data', {})
            station_id = station_data.get('ID') or station_data.get('ROWID')
            if station_id:
                station_ids.append(station_id)
                print(f"  -> ROWID: {station_id}")
        else:
            print(f"  -> Error: {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"Station {station['Station_Code']}: Error - {str(e)}")

print(f"\nStation IDs collected: {station_ids}")

# Step 2: Create a traffic train
if len(station_ids) >= 2:
    print('\nSTEP 2: Creating minimal train')

    minimal_train = {
        'Train_Number': 'T001',
        'Train_Name': 'Test Express',
        'From_Station': station_ids[0],  # Use actual ROWID
        'To_Station': station_ids[1],     # Use actual ROWID
        'Departure_Time': '10:00',
        'Arrival_Time': '20:00',
        'Is_Active': 'true'
    }

    try:
        url = f'{BASE_URL}/trains'
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(minimal_train).encode('utf-8')

        request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
        result = json.loads(response.read().decode())

        print(f"Train creation: {result.get('status', 'unknown')}")
        if result.get('status') == 'success':
            train_data = result.get('data', {})
            train_id = train_data.get('ID') or train_data.get('ROWID')
            print(f"SUCCESS! Train created with ID: {train_id}")
            print(f"Train data: {train_data}")
        else:
            print(f"FAILED: {result.get('message', 'Unknown error')}")

        print(f"\nRaw response: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"Train creation failed: {str(e)}")

else:
    print('\nSTEP 2: Skipped - not enough station IDs')

# Step 3: Test reading trains
print('\nSTEP 3: Reading all trains')
try:
    url = f'{BASE_URL}/trains'
    request_obj = urllib.request.Request(url, method='GET')
    response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
    result = json.loads(response.read().decode())

    print(f"Read trains: {result.get('status', 'unknown')}")
    if result.get('status') == 'success':
        trains = result.get('data', [])
        print(f"Found {len(trains)} trains:")
        for train in trains:
            print(f"  {train.get('Train_Number', 'N/A')} - {train.get('Train_Name', 'N/A')}")
    else:
        print(f"Read failed: {result.get('message', 'Unknown error')}")

except Exception as e:
    print(f"Read failed: {str(e)}")

print('\nSimple CRUD test completed.')