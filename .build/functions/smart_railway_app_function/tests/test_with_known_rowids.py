"""
Test Train Creation with Known Station ROWIDs
Uses the discovered station ROWID mapping to test train creation directly.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

print('TESTING TRAIN CREATION WITH KNOWN STATION ROWIDS')
print('=' * 60)

# Known station ROWID mapping from previous verification:
# MMCT → ROWID: 1
# NDLS → ROWID: 2
# BNC → ROWID: 3

print('STEP 1: Test direct train creation with ROWID references')
print('')

# Create test train data with ROWID references instead of station codes
test_train_data = {
    'Train_Number': 'TEST001',
    'Train_Name': 'ROWID Test Express',
    'Train_Type': 'EXPRESS',
    'From_Station': 1,         # MMCT ROWID
    'To_Station': 2,           # NDLS ROWID
    'Departure_Time': '10:00',
    'Arrival_Time': '18:00',
    'Duration': '8:00',
    'Distance': 500.0,
    'Run_Days': 'Mon,Tue,Wed,Thu,Fri',
    'Is_Active': 'true'
}

print(f'Test train data with ROWID references:')
print(f'  Train_Number: {test_train_data["Train_Number"]}')
print(f'  From_Station: {test_train_data["From_Station"]} (MMCT)')
print(f'  To_Station: {test_train_data["To_Station"]} (NDLS)')
print('')

# Test direct CloudScale record creation
try:
    url = f'{BASE_URL}/cloudscale-test/direct-create'

    test_payload = {
        'table': 'Trains',
        'data': test_train_data
    }

    headers = {'Content-Type': 'application/json'}
    body = json.dumps(test_payload).encode('utf-8')

    print('STEP 2: Sending direct create request to CloudScale')
    request_obj = urllib.request.Request(url, data=body, headers=headers, method='POST')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    result = json.loads(response.read().decode())

    print(f'Create response: {result.get("status", "unknown")}')

    if result.get('status') == 'success':
        print('SUCCESS! Train created with ROWID references')
        print(f'Created train data: {result.get("data", {})}')

        # Store the created train ROWID for potential quota creation
        train_rowid = result.get('data', {}).get('ROWID')
        print(f'Train ROWID: {train_rowid}')

    else:
        print('FAILED! Train creation error:')
        print(f'Error: {result.get("error", "Unknown error")}')

except Exception as e:
    print(f'Exception during train creation: {str(e)}')

print('')
print('STEP 3: Verify train exists in database')

# Verify the train was created
try:
    verify_url = f'{BASE_URL}/cloudscale-test/run-zcql-query'

    verify_query = "SELECT Train_Number, Train_Name, From_Station, To_Station, ROWID FROM Trains WHERE Train_Number = 'TEST001'"

    verify_payload = {'sql': verify_query}
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(verify_payload).encode('utf-8')

    request_obj = urllib.request.Request(verify_url, data=body, headers=headers, method='POST')
    response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
    result = json.loads(response.read().decode())

    if result.get('status') == 'success':
        train_records = result.get('data', [])
        if train_records:
            print('VERIFICATION SUCCESS! Train found in database:')
            for record in train_records:
                print(f'  Train: {record.get("Train_Number")} - {record.get("Train_Name")}')
                print(f'  From Station ROWID: {record.get("From_Station")}')
                print(f'  To Station ROWID: {record.get("To_Station")}')
                print(f'  Train ROWID: {record.get("ROWID")}')
        else:
            print('No train records found - creation might have failed silently')
    else:
        print(f'Verification failed: {result.get("error", "Unknown error")}')

except Exception as e:
    print(f'Exception during verification: {str(e)}')

print('')
print('Test completed!')
print('')
print('CONCLUSION:')
print('If this test succeeds, we have proven that trains can be created using ROWID references.')
print('The next step would be to update the reliable_railway_data.py to use ROWIDs instead of station codes.')