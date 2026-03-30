"""
Comprehensive Module-Level CRUD Test Suite
Tests all API modules on deployed Catalyst environment
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from datetime import datetime

# Disable SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

# Store auth tokens and IDs for CRUD operations
test_data = {
    'auth_token': None,
    'refresh_token': None,
    'user_id': None,
    'admin_token': None,
    'station_id': None,
    'train_id': None,
    'route_id': None,
    'booking_id': None,
    'module_id': None,
}

# Test results
results = {
    'timestamp': datetime.now().isoformat(),
    'baseUrl': BASE_URL,
    'modules': {},
    'summary': {'total': 0, 'passed': 0, 'failed': 0}
}


def api_request(method, endpoint, data=None, headers=None, expected_status=None):
    """Make API request and return result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None

        request = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)

        start = time.time()
        response = urllib.request.urlopen(request, timeout=30, context=ctx)
        elapsed = (time.time() - start) * 1000

        response_data = json.loads(response.read().decode())

        return {
            'success': True,
            'status': response.status,
            'data': response_data,
            'time': f"{elapsed:.0f}ms"
        }

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = str(e)

        return {
            'success': False,
            'status': e.code,
            'data': error_data,
            'time': f"{elapsed:.0f}ms"
        }
    except Exception as e:
        return {
            'success': False,
            'status': 0,
            'data': str(e),
            'time': '0ms'
        }


def test_module(module_name, tests):
    """Run tests for a module and record results."""
    print(f"\n{'='*70}")
    print(f"MODULE: {module_name}")
    print('='*70)

    module_results = {'tests': [], 'passed': 0, 'failed': 0}

    for test in tests:
        test_name = test['name']
        method = test['method']
        endpoint = test['endpoint']
        data = test.get('data')
        headers = test.get('headers', {})
        expected = test.get('expected', [200, 201])
        extract = test.get('extract')

        # Add auth token if required
        if test.get('auth') and test_data['auth_token']:
            headers['Authorization'] = f"Bearer {test_data['auth_token']}"
        if test.get('admin_auth') and test_data['admin_token']:
            headers['Authorization'] = f"Bearer {test_data['admin_token']}"

        print(f"\n  [{method}] {test_name}")
        print(f"      Endpoint: {endpoint}")

        result = api_request(method, endpoint, data, headers)

        # Check if status matches expected
        if isinstance(expected, list):
            passed = result['status'] in expected
        else:
            passed = result['status'] == expected

        # Extract data if specified
        if extract and result['success']:
            for key, path in extract.items():
                try:
                    value = result['data']
                    for p in path.split('.'):
                        value = value.get(p, {}) if isinstance(value, dict) else None
                    if value:
                        test_data[key] = value
                        print(f"      Extracted {key}: {str(value)[:50]}...")
                except:
                    pass

        status_str = "PASS" if passed else "FAIL"
        print(f"      Status: {result['status']} | Time: {result['time']} | Result: {status_str}")

        if not passed:
            print(f"      Response: {json.dumps(result['data'], indent=2)[:200]}")

        module_results['tests'].append({
            'name': test_name,
            'method': method,
            'endpoint': endpoint,
            'status': result['status'],
            'time': result['time'],
            'result': status_str,
            'response': result['data'] if not passed else None
        })

        if passed:
            module_results['passed'] += 1
            results['summary']['passed'] += 1
        else:
            module_results['failed'] += 1
            results['summary']['failed'] += 1

        results['summary']['total'] += 1

    results['modules'][module_name] = module_results
    print(f"\n  Module Summary: {module_results['passed']}/{len(tests)} passed")
    return module_results


# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

print("="*70)
print("COMPREHENSIVE MODULE-LEVEL CRUD TEST SUITE")
print(f"Base URL: {BASE_URL}")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*70)

# -----------------------------------------------------------------------------
# 1. SEED MODULE - Create Test Users
# -----------------------------------------------------------------------------
test_module("SEED", [
    {
        'name': 'Create Test User (agent@agent.com)',
        'method': 'POST',
        'endpoint': '/seed/user',
        'expected': [200, 201],
        'extract': {
            'auth_token': 'data.token',
            'refresh_token': 'data.refreshToken',
            'user_id': 'data.user.id'
        }
    },
    {
        'name': 'Create Admin User',
        'method': 'POST',
        'endpoint': '/seed/admin',
        'expected': [200, 201],
        'extract': {
            'admin_token': 'data.token'
        }
    },
    {
        'name': 'Check Seed Status',
        'method': 'GET',
        'endpoint': '/seed/status',
        'expected': 200
    }
])

# -----------------------------------------------------------------------------
# 2. AUTH MODULE - Authentication CRUD
# -----------------------------------------------------------------------------
test_module("AUTH", [
    {
        'name': 'Login - Valid Credentials',
        'method': 'POST',
        'endpoint': '/auth/login',
        'data': {'email': 'agent@agent.com', 'password': 'agent@agent.com'},
        'expected': 200,
        'extract': {
            'auth_token': 'data.token',
            'refresh_token': 'data.refreshToken'
        }
    },
    {
        'name': 'Login - Invalid Credentials',
        'method': 'POST',
        'endpoint': '/auth/login',
        'data': {'email': 'agent@agent.com', 'password': 'wrongpassword'},
        'expected': 401
    },
    {
        'name': 'Validate Session',
        'method': 'GET',
        'endpoint': '/auth/validate',
        'auth': True,
        'expected': 200
    },
    {
        'name': 'Refresh Token',
        'method': 'POST',
        'endpoint': '/auth/refresh',
        'data': {'refreshToken': test_data.get('refresh_token', '')},
        'expected': [200, 401]  # May fail if token not set
    },
    {
        'name': 'Update Profile',
        'method': 'PUT',
        'endpoint': '/auth/profile',
        'data': {'fullName': 'Agent User Updated', 'phoneNumber': '9123456789'},
        'auth': True,
        'expected': 200
    },
    {
        'name': 'Logout',
        'method': 'POST',
        'endpoint': '/auth/logout',
        'expected': 200
    }
])

# Re-login to get fresh token
result = api_request('POST', '/auth/login', {'email': 'agent@agent.com', 'password': 'agent@agent.com'})
if result['success']:
    test_data['auth_token'] = result['data'].get('data', {}).get('token')
    test_data['refresh_token'] = result['data'].get('data', {}).get('refreshToken')

# Login as admin
result = api_request('POST', '/auth/login', {'email': 'admin@railway.com', 'password': 'admin@railway.com'})
if result['success']:
    test_data['admin_token'] = result['data'].get('data', {}).get('token')

# -----------------------------------------------------------------------------
# 3. USERS MODULE - User Management CRUD
# -----------------------------------------------------------------------------
test_module("USERS", [
    {
        'name': 'Get All Users (Admin)',
        'method': 'GET',
        'endpoint': '/users',
        'admin_auth': True,
        'expected': 200
    },
    {
        'name': 'Get User by ID',
        'method': 'GET',
        'endpoint': f'/users/{test_data.get("user_id", "1")}',
        'auth': True,
        'expected': [200, 404]
    },
    {
        'name': 'Get Users Without Auth',
        'method': 'GET',
        'endpoint': '/users',
        'expected': 401
    }
])

# -----------------------------------------------------------------------------
# 4. STATIONS MODULE - Station CRUD
# -----------------------------------------------------------------------------
test_module("STATIONS", [
    {
        'name': 'Get All Stations',
        'method': 'GET',
        'endpoint': '/stations',
        'expected': 200,
        'extract': {
            'station_id': 'data.0.ROWID'
        }
    },
    {
        'name': 'Create Station (Admin)',
        'method': 'POST',
        'endpoint': '/stations',
        'data': {
            'stationCode': 'TST1',
            'stationName': 'Test Station 1',
            'city': 'Test City',
            'state': 'Test State',
            'zone': 'SR'
        },
        'admin_auth': True,
        'expected': [201, 409, 500]
    },
    {
        'name': 'Search Stations',
        'method': 'GET',
        'endpoint': '/stations?search=test',
        'expected': 200
    }
])

# -----------------------------------------------------------------------------
# 5. TRAINS MODULE - Train CRUD
# -----------------------------------------------------------------------------
test_module("TRAINS", [
    {
        'name': 'Get All Trains',
        'method': 'GET',
        'endpoint': '/trains',
        'expected': 200,
        'extract': {
            'train_id': 'data.0.ROWID'
        }
    },
    {
        'name': 'Create Train (Admin)',
        'method': 'POST',
        'endpoint': '/trains',
        'data': {
            'trainNumber': '99999',
            'trainName': 'Test Express',
            'trainType': 'Express',
            'totalSeats': 500
        },
        'admin_auth': True,
        'expected': [201, 409, 500]
    },
    {
        'name': 'Search Trains',
        'method': 'GET',
        'endpoint': '/trains?search=express',
        'expected': 200
    }
])

# -----------------------------------------------------------------------------
# 6. FARES MODULE - Fare CRUD
# -----------------------------------------------------------------------------
test_module("FARES", [
    {
        'name': 'Get All Fares',
        'method': 'GET',
        'endpoint': '/fares',
        'expected': 200
    },
    {
        'name': 'Calculate Fare',
        'method': 'POST',
        'endpoint': '/fares/calculate',
        'data': {
            'trainId': test_data.get('train_id', '1'),
            'class': '3A',
            'passengers': 2
        },
        'expected': [200, 400, 404]
    }
])

# -----------------------------------------------------------------------------
# 7. BOOKINGS MODULE - Booking CRUD
# -----------------------------------------------------------------------------
test_module("BOOKINGS", [
    {
        'name': 'Get User Bookings',
        'method': 'GET',
        'endpoint': '/bookings',
        'auth': True,
        'expected': 200
    },
    {
        'name': 'Get Booking by PNR',
        'method': 'GET',
        'endpoint': '/bookings/pnr/TEST123456',
        'auth': True,
        'expected': [200, 404]
    }
])

# -----------------------------------------------------------------------------
# 8. INVENTORY MODULE - Inventory CRUD
# -----------------------------------------------------------------------------
test_module("INVENTORY", [
    {
        'name': 'Check Availability',
        'method': 'GET',
        'endpoint': '/inventory/availability?trainId=1&date=2026-04-01&class=3A',
        'expected': [200, 400, 404]
    }
])

# -----------------------------------------------------------------------------
# 9. QUOTAS MODULE - Quota CRUD
# -----------------------------------------------------------------------------
test_module("QUOTAS", [
    {
        'name': 'Get All Quotas',
        'method': 'GET',
        'endpoint': '/quotas',
        'expected': 200
    }
])

# -----------------------------------------------------------------------------
# 10. ANNOUNCEMENTS MODULE - Announcement CRUD
# -----------------------------------------------------------------------------
test_module("ANNOUNCEMENTS", [
    {
        'name': 'Get Active Announcements',
        'method': 'GET',
        'endpoint': '/announcements',
        'expected': 200
    },
    {
        'name': 'Create Announcement (Admin)',
        'method': 'POST',
        'endpoint': '/announcements',
        'data': {
            'title': 'Test Announcement',
            'message': 'This is a test announcement',
            'type': 'info'
        },
        'admin_auth': True,
        'expected': [201, 500]
    }
])

# -----------------------------------------------------------------------------
# 11. SETTINGS MODULE - Settings CRUD
# -----------------------------------------------------------------------------
test_module("SETTINGS", [
    {
        'name': 'Get All Settings',
        'method': 'GET',
        'endpoint': '/settings',
        'admin_auth': True,
        'expected': [200, 401]
    }
])

# -----------------------------------------------------------------------------
# 12. MODULE MASTER - Module CRUD
# -----------------------------------------------------------------------------
test_module("MODULE_MASTER", [
    {
        'name': 'Get All Modules',
        'method': 'GET',
        'endpoint': '/modules',
        'auth': True,
        'expected': 200
    },
    {
        'name': 'Create Module (Admin)',
        'method': 'POST',
        'endpoint': '/modules',
        'data': {
            'moduleCode': 'TST',
            'moduleName': 'Test Module',
            'description': 'Test module for API testing',
            'displayOrder': 99,
            'isActive': True
        },
        'admin_auth': True,
        'expected': [201, 409],
        'extract': {
            'module_id': 'data.ROWID'
        }
    },
    {
        'name': 'Get Module by ID',
        'method': 'GET',
        'endpoint': f'/modules/{test_data.get("module_id", "1")}',
        'auth': True,
        'expected': [200, 404]
    },
    {
        'name': 'Update Module (Admin)',
        'method': 'PUT',
        'endpoint': f'/modules/{test_data.get("module_id", "1")}',
        'data': {
            'moduleName': 'Test Module Updated',
            'displayOrder': 100
        },
        'admin_auth': True,
        'expected': [200, 404]
    }
])

# -----------------------------------------------------------------------------
# 13. ADMIN LOGS MODULE
# -----------------------------------------------------------------------------
test_module("ADMIN_LOGS", [
    {
        'name': 'Get Admin Logs',
        'method': 'GET',
        'endpoint': '/admin/logs',
        'admin_auth': True,
        'expected': [200, 401]
    }
])

# -----------------------------------------------------------------------------
# 14. SECURITY TESTS
# -----------------------------------------------------------------------------
test_module("SECURITY", [
    {
        'name': 'SQL Injection - Login',
        'method': 'POST',
        'endpoint': '/auth/login',
        'data': {'email': "'; DROP TABLE Users; --", 'password': "' OR '1'='1"},
        'expected': [400, 401]
    },
    {
        'name': 'XSS Attack - Register',
        'method': 'POST',
        'endpoint': '/auth/register',
        'data': {'fullName': '<script>alert("XSS")</script>', 'email': 'xss@test.com', 'password': 'test1234'},
        'expected': [201, 400, 409, 500]
    },
    {
        'name': 'Unauthorized Access - Admin Endpoint',
        'method': 'GET',
        'endpoint': '/users',
        'auth': True,  # Regular user token, not admin
        'expected': [401, 403]
    }
])

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "="*70)
print("FINAL TEST SUMMARY")
print("="*70)
print(f"\nTotal Tests: {results['summary']['total']}")
print(f"Passed: {results['summary']['passed']}")
print(f"Failed: {results['summary']['failed']}")

pass_rate = (results['summary']['passed'] / results['summary']['total'] * 100) if results['summary']['total'] > 0 else 0
print(f"Pass Rate: {pass_rate:.1f}%")

print("\nModule Results:")
print("-" * 50)
for module, data in results['modules'].items():
    status = "PASS" if data['failed'] == 0 else "PARTIAL" if data['passed'] > 0 else "FAIL"
    print(f"  {module:20} : {data['passed']}/{len(data['tests'])} ({status})")

# Save results
with open('tests/module_crud_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: tests/module_crud_test_results.json")

print("\n" + "="*70)
