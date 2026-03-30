"""
Direct Station ROWID Solution
Bypasses SELECT * issues by creating a hardcoded mapping and direct testing.
"""

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

print('DIRECT STATION ROWID SOLUTION - BYPASSING SELECT * ISSUES')
print('=' * 65)

# Strategy: Create a simple endpoint that creates one train at a time with hardcoded station references
print('STEP 1: Testing simple train creation approach')

# First, let's confirm we still have stations in the database
try:
    url = f'{BASE_URL}/schema-discovery/final-verification'
    request_obj = urllib.request.Request(url)
    response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
    data = json.loads(response.read().decode())

    if 'table_verification' in data:
        verification = data['table_verification']
        stations_count = verification.get('stations', {}).get('record_count', 0)
        trains_count = verification.get('trains', {}).get('record_count', 0)
        fares_count = verification.get('fares', {}).get('record_count', 0)

        print(f'Database Status:')
        print(f'  Stations: {stations_count} records ✅' if stations_count > 0 else f'  Stations: {stations_count} records ❌')
        print(f'  Trains: {trains_count} records' + (' ✅' if trains_count > 0 else ' (needs creation)'))
        print(f'  Fares: {fares_count} records' + (' ✅' if fares_count > 0 else ' (needs creation)'))

        if stations_count >= 3:
            print(f'\\nSTRATEGY: Use direct ROWID creation approach')
            print(f'Since we have {stations_count} stations, try creating trains with typical ROWID patterns')

            # CloudScale typically uses sequential ROWIDs starting from a base number
            # Common patterns: 1804000000000000000, 1805000000000000000, etc.
            # Let's try a range of likely ROWIDs

            estimated_rowids = [
                '1804000000000000000',  # Typical CloudScale ROWID pattern
                '1805000000000000000',
                '1806000000000000000',
                '1807000000000000000',
                '1808000000000000000',
            ]

            print(f'\\nEstimated Station ROWIDs to try: {estimated_rowids[:3]}')

            # Create a test payload for manual train creation
            test_train = {
                'Train_Number': '99998',  # Use unique number
                'Train_Name': 'Test Express Direct',
                'Train_Type': 'EXPRESS',
                'From_Station': estimated_rowids[0],  # Try first estimated ROWID
                'To_Station': estimated_rowids[1],    # Try second estimated ROWID
                'Departure_Time': '10:00',
                'Arrival_Time': '18:00',
                'Duration': '8:00',
                'Distance': 500.0,
                'Run_Days': 'Mon,Tue,Wed,Thu,Fri',
                'Is_Active': 'true'
            }

            print(f'\\nTest train payload:')
            print(f'  Train_Number: {test_train[\"Train_Number\"]}')
            print(f'  From_Station ROWID: {test_train[\"From_Station\"]}')
            print(f'  To_Station ROWID: {test_train[\"To_Station\"]}')

            print(f'\\nNEXT STEPS:')
            print(f'1. Create a simple train creation endpoint that accepts ROWID directly')
            print(f'2. Test with estimated ROWIDs until one works')
            print(f'3. Use working ROWIDs for remaining trains')
            print(f'4. Complete quotas creation with train ROWIDs')

            # Show current approach limitations
            print(f'\\nCURRENT LIMITATION:')
            print(f'Multiple SELECT * queries in codebase still causing ZCQL errors')
            print(f'Need direct ROWID approach or complete SELECT * audit')

        else:
            print(f'\\nNeed to create stations first')

    else:
        print('Cannot verify database status')

except Exception as e:
    print(f'Error checking database: {e}')

print(f'\\nDirect solution analysis completed')
print(f'\\nRECOMMENDATION: Create simple hardcoded ROWID approach to complete trains')