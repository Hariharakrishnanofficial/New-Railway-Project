"""
API Testing Agent - Comprehensive Test Suite

Tests all API endpoints with real HTTP requests.
"""

import subprocess
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = 'http://localhost:9000'

# Test results storage
test_results = {
    'timestamp': datetime.now().isoformat(),
    'baseUrl': BASE_URL,
    'tests': [],
    'summary': {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': 0
    }
}


def make_request(method, endpoint, data=None, headers=None, expected_status=200):
    """Make HTTP request and return result."""
    url = f"{BASE_URL}{endpoint}"
    result = {
        'endpoint': f"{method} {endpoint}",
        'url': url,
        'method': method,
        'requestData': data,
        'responseTime': None,
        'statusCode': None,
        'response': None,
        'error': None,
        'result': 'PENDING'
    }

    try:
        start_time = time.time()

        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None

        request = urllib.request.Request(
            url,
            data=data_bytes,
            headers=req_headers,
            method=method
        )

        response = urllib.request.urlopen(request, timeout=10)
        response_data = response.read().decode('utf-8')

        result['responseTime'] = f"{(time.time() - start_time) * 1000:.0f}ms"
        result['statusCode'] = response.status

        try:
            result['response'] = json.loads(response_data)
        except:
            result['response'] = response_data

        if response.status == expected_status:
            result['result'] = 'PASS'
        else:
            result['result'] = 'FAIL'
            result['error'] = f"Expected status {expected_status}, got {response.status}"

    except urllib.error.HTTPError as e:
        result['responseTime'] = f"{(time.time() - start_time) * 1000:.0f}ms"
        result['statusCode'] = e.code
        try:
            result['response'] = json.loads(e.read().decode('utf-8'))
        except:
            result['response'] = str(e)

        if e.code == expected_status:
            result['result'] = 'PASS'
        else:
            result['result'] = 'FAIL'
            result['error'] = f"Expected status {expected_status}, got {e.code}"

    except Exception as e:
        result['responseTime'] = f"{(time.time() - start_time) * 1000:.0f}ms"
        result['result'] = 'ERROR'
        result['error'] = str(e)

    return result


def run_test(name, method, endpoint, data=None, headers=None, expected_status=200, validations=None):
    """Run a single test and record results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"  {method} {endpoint}")

    result = make_request(method, endpoint, data, headers, expected_status)
    result['testName'] = name
    result['validations'] = {}

    # Run validations
    if validations and result['response']:
        for val_name, val_func in validations.items():
            try:
                val_result = val_func(result['response'])
                result['validations'][val_name] = 'PASS' if val_result else 'FAIL'
            except Exception as e:
                result['validations'][val_name] = f'ERROR: {e}'

    # Print result
    print(f"  Status: {result['statusCode']}")
    print(f"  Response Time: {result['responseTime']}")
    print(f"  Result: {result['result']}")

    if result['response']:
        resp_str = json.dumps(result['response'], indent=2)
        if len(resp_str) > 500:
            resp_str = resp_str[:500] + '...'
        print(f"  Response: {resp_str}")

    if result['error']:
        print(f"  Error: {result['error']}")

    # Update summary
    test_results['tests'].append(result)
    test_results['summary']['total'] += 1
    if result['result'] == 'PASS':
        test_results['summary']['passed'] += 1
    elif result['result'] == 'FAIL':
        test_results['summary']['failed'] += 1
    else:
        test_results['summary']['errors'] += 1

    return result


def main():
    print("=" * 70)
    print("API TESTING AGENT - Smart Railway Ticketing System")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # =========================================================================
    # TEST 1: Root Endpoint
    # =========================================================================
    run_test(
        name="Root Endpoint",
        method="GET",
        endpoint="/",
        expected_status=200,
        validations={
            'has_status': lambda r: r.get('status') == 'success',
            'has_version': lambda r: 'version' in r,
            'has_endpoints': lambda r: 'endpoints' in r,
        }
    )

    # =========================================================================
    # TEST 2: Health Check
    # =========================================================================
    run_test(
        name="Health Check",
        method="GET",
        endpoint="/health",
        expected_status=200,
        validations={
            'has_status': lambda r: 'status' in r,
            'has_timestamp': lambda r: 'timestamp' in r,
        }
    )

    # =========================================================================
    # TEST 3: Debug Config
    # =========================================================================
    run_test(
        name="Debug Config",
        method="GET",
        endpoint="/debug/config",
        expected_status=200,
        validations={
            'has_tables': lambda r: 'tables' in r,
            'has_database': lambda r: 'database' in r,
        }
    )

    # =========================================================================
    # TEST 4: Register - Valid User
    # =========================================================================
    register_result = run_test(
        name="Register - Valid User (agent@agent.com)",
        method="POST",
        endpoint="/auth/register",
        data={
            'fullName': 'Agent User',
            'email': 'agent@agent.com',
            'password': 'agent@agent.com',
            'phoneNumber': '9876543210'
        },
        expected_status=201,
        validations={
            'has_status': lambda r: 'status' in r,
        }
    )

    # Extract token if available
    auth_token = None
    if register_result.get('response', {}).get('data', {}).get('token'):
        auth_token = register_result['response']['data']['token']
        print(f"  Token obtained: {auth_token[:50]}...")

    # =========================================================================
    # TEST 5: Register - Duplicate Email (should fail with 409)
    # =========================================================================
    run_test(
        name="Register - Duplicate Email (Negative Test)",
        method="POST",
        endpoint="/auth/register",
        data={
            'fullName': 'Agent User 2',
            'email': 'agent@agent.com',
            'password': 'agent@agent.com',
            'phoneNumber': '9876543211'
        },
        expected_status=409,
        validations={
            'has_error': lambda r: r.get('status') == 'error',
        }
    )

    # =========================================================================
    # TEST 6: Register - Missing Fields (should fail with 400)
    # =========================================================================
    run_test(
        name="Register - Missing Required Fields (Negative Test)",
        method="POST",
        endpoint="/auth/register",
        data={
            'fullName': 'Test User'
            # Missing email and password
        },
        expected_status=400,
        validations={
            'has_error': lambda r: r.get('status') == 'error',
        }
    )

    # =========================================================================
    # TEST 7: Login - Valid Credentials
    # =========================================================================
    login_result = run_test(
        name="Login - Valid Credentials",
        method="POST",
        endpoint="/auth/login",
        data={
            'email': 'agent@agent.com',
            'password': 'agent@agent.com'
        },
        expected_status=200,
        validations={
            'has_status': lambda r: r.get('status') == 'success',
            'has_token': lambda r: r.get('data', {}).get('token') is not None,
            'has_user': lambda r: r.get('data', {}).get('user') is not None,
        }
    )

    # Extract token from login
    if login_result.get('response', {}).get('data', {}).get('token'):
        auth_token = login_result['response']['data']['token']
        print(f"  Login Token: {auth_token[:50]}...")

    # =========================================================================
    # TEST 8: Login - Invalid Password (should fail with 401)
    # =========================================================================
    run_test(
        name="Login - Invalid Password (Negative Test)",
        method="POST",
        endpoint="/auth/login",
        data={
            'email': 'agent@agent.com',
            'password': 'wrongpassword'
        },
        expected_status=401,
        validations={
            'has_error': lambda r: r.get('status') == 'error',
        }
    )

    # =========================================================================
    # TEST 9: Login - Non-existent User (should fail with 401)
    # =========================================================================
    run_test(
        name="Login - Non-existent User (Negative Test)",
        method="POST",
        endpoint="/auth/login",
        data={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        },
        expected_status=401,
        validations={
            'has_error': lambda r: r.get('status') == 'error',
        }
    )

    # =========================================================================
    # TEST 10: Validate Session - With Token
    # =========================================================================
    if auth_token:
        run_test(
            name="Validate Session - With Valid Token",
            method="GET",
            endpoint="/auth/validate",
            headers={'Authorization': f'Bearer {auth_token}'},
            expected_status=200,
            validations={
                'has_user': lambda r: r.get('data', {}).get('user') is not None,
            }
        )

    # =========================================================================
    # TEST 11: Validate Session - Without Token (should fail with 401)
    # =========================================================================
    run_test(
        name="Validate Session - Without Token (Negative Test)",
        method="GET",
        endpoint="/auth/validate",
        expected_status=401,
        validations={
            'has_error': lambda r: r.get('status') == 'error' or r.get('message'),
        }
    )

    # =========================================================================
    # TEST 12: Get Users - Without Auth (should fail)
    # =========================================================================
    run_test(
        name="Get Users - Without Auth (Negative Test)",
        method="GET",
        endpoint="/users",
        expected_status=401,
        validations={
            'has_error': lambda r: 'error' in str(r).lower() or 'unauthorized' in str(r).lower(),
        }
    )

    # =========================================================================
    # TEST 13: Logout
    # =========================================================================
    run_test(
        name="Logout",
        method="POST",
        endpoint="/auth/logout",
        expected_status=200,
        validations={
            'has_status': lambda r: r.get('status') == 'success',
        }
    )

    # =========================================================================
    # TEST 14: SQL Injection Test
    # =========================================================================
    run_test(
        name="SQL Injection Test - Login",
        method="POST",
        endpoint="/auth/login",
        data={
            'email': "'; DROP TABLE Users; --",
            'password': "' OR '1'='1"
        },
        expected_status=401,  # Should reject, not crash
        validations={
            'no_crash': lambda r: 'status' in r or 'error' in str(r).lower(),
        }
    )

    # =========================================================================
    # TEST 15: 404 Not Found
    # =========================================================================
    run_test(
        name="404 Not Found",
        method="GET",
        endpoint="/nonexistent/endpoint",
        expected_status=404,
        validations={
            'has_error': lambda r: 'error' in str(r).lower() or 'not found' in str(r).lower(),
        }
    )

    # =========================================================================
    # PRINT FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {test_results['summary']['total']}")
    print(f"Passed: {test_results['summary']['passed']}")
    print(f"Failed: {test_results['summary']['failed']}")
    print(f"Errors: {test_results['summary']['errors']}")

    pass_rate = (test_results['summary']['passed'] / test_results['summary']['total'] * 100) if test_results['summary']['total'] > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")

    # Print failed tests
    failed_tests = [t for t in test_results['tests'] if t['result'] != 'PASS']
    if failed_tests:
        print("\nFailed Tests:")
        for t in failed_tests:
            print(f"  - {t['testName']}: {t['result']} ({t.get('error', 'N/A')})")

    print("\n" + "=" * 70)

    # Save results to file
    with open('tests/api_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"Results saved to: tests/api_test_results.json")

    return test_results


if __name__ == '__main__':
    main()
