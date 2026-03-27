"""
Step-by-step Railway Data Fix Test
Tests each component separately to identify the exact failure point.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

def test_direct_zcql(query_name, query):
    """Test direct ZCQL queries."""
    print(f"\nTesting {query_name}:")
    print(f"Query: {query}")

    try:
        test_data = {'sql': query}
        url = f'{BASE_URL}/cloudscale-test/run-zcql-query'

        headers = {'Content-Type': 'application/json'}
        body = json.dumps(test_data).encode('utf-8')

        request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
        response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
        result = json.loads(response.read().decode())

        if result.get('status') == 'success':
            data = result.get('data', [])
            print(f"SUCCESS: Found {len(data)} records")
            for i, record in enumerate(data[:3]):
                print(f"  {i+1}. {record}")
            return True, data
        else:
            print(f"FAILED: {result.get('error', 'Unknown error')}")
            return False, []

    except Exception as e:
        print(f"ERROR: {str(e)[:100]}...")
        return False, []

def test_single_train_creation():
    """Test creating a single train with minimal data."""
    print(f"\nTesting single train creation with minimal data:")

    # Minimal train data - just required fields
    minimal_train = {
        'Train_Number': '99999',  # Use unique number to avoid conflicts
        'Train_Name': 'Test Express',
        'From_Station': 'TEST1',  # Will need to replace with actual ROWID
        'To_Station': 'TEST2',    # Will need to replace with actual ROWID
        'Departure_Time': '10:00',
        'Arrival_Time': '20:00'
    }

    print(f"Minimal train data: {minimal_train}")
    print("Note: From_Station and To_Station need to be actual ROWIDs")

print('STEP-BY-STEP RAILWAY DATA DEBUG TEST')
print('=' * 60)

# Step 1: Test if we can query existing stations
success, stations = test_direct_zcql(
    "Get existing stations",
    "SELECT Station_Code, Station_Name, ROWID FROM Stations LIMIT 5"
)

if success and stations:
    print(f"\\nFound {len(stations)} stations - can proceed with ROWID mapping")

    # Try to get the specific stations we need
    required_success, required_stations = test_direct_zcql(
        "Get required stations",
        "SELECT Station_Code, ROWID FROM Stations WHERE Station_Code IN ('MMCT', 'NDLS', 'BNC')"
    )

    if required_success and required_stations:
        print(f"\\nAll required stations exist:")
        station_map = {}
        for station in required_stations:
            code = station.get('Station_Code')
            rowid = station.get('ROWID')
            if code and rowid:
                station_map[code] = rowid
                print(f"  {code} -> ROWID {rowid}")

        print(f"\\nStation ROWID mapping: {station_map}")

        if len(station_map) >= 2:
            print("\\nWe have enough station ROWIDs to test train creation!")
            print("The foreign key references should work now.")
        else:
            print("\\nInsufficient station ROWIDs for train creation test")
    else:
        print("\\nRequired stations (MMCT, NDLS, BNC) not found")

else:
    print("\\nCannot query existing stations - this might be the core issue")

# Step 2: Check current trains
train_success, trains = test_direct_zcql(
    "Check existing trains",
    "SELECT Train_Number, Train_Name, ROWID FROM Trains LIMIT 5"
)

if train_success:
    print(f"\\nTrain query successful - found {len(trains)} trains")
    if trains:
        print("Some trains already exist:")
        for train in trains:
            print(f"  {train.get('Train_Number')} - {train.get('Train_Name')}")
else:
    print("\\nTrain query failed - table might have schema issues")

# Step 3: Test the simple train creation idea
test_single_train_creation()

print('\\nTest completed - this should help identify the exact failure point')