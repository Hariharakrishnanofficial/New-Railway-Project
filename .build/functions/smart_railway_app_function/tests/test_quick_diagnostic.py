"""
Quick API Diagnostic Script - Test backend connectivity and authentication.

Usage:
    python test_quick_diagnostic.py [base_url]

Examples:
    python test_quick_diagnostic.py http://localhost:9000
    python test_quick_diagnostic.py http://localhost:3000/server/smart_railway_app_function
"""

import sys
import requests
import json
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log(msg, color=Colors.BLUE):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Colors.RESET}")

def test_endpoint(base_url, method, endpoint, data=None, auth=False, token=None):
    """Test a single endpoint."""
    url = f"{base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if auth and token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=15)
        else:
            resp = None
        
        return resp
    except requests.exceptions.ConnectionError:
        return {"error": "Connection refused", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}

def main():
    # Determine base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000"
    
    print("\n" + "="*70)
    print(f"{Colors.BLUE}  SMART RAILWAY API - QUICK DIAGNOSTIC{Colors.RESET}")
    print(f"  Base URL: {base_url}")
    print("="*70 + "\n")
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 1: Health Check
    # ─────────────────────────────────────────────────────────────────────
    log("Test 1: Health Check (/health)")
    resp = test_endpoint(base_url, "GET", "/health")
    
    if isinstance(resp, dict) and resp.get("error"):
        log(f"FAILED: {resp['error']}", Colors.RED)
        log(f"URL tried: {resp.get('url')}", Colors.YELLOW)
        log("\nPossible causes:", Colors.YELLOW)
        log("  1. Backend server is not running", Colors.YELLOW)
        log("  2. Wrong base URL (try: http://localhost:9000 or http://localhost:3000/server/smart_railway_app_function)", Colors.YELLOW)
        log("  3. Firewall blocking the connection", Colors.YELLOW)
        return
    
    if resp.status_code == 200:
        log(f"PASSED: Status {resp.status_code}", Colors.GREEN)
        try:
            body = resp.json()
            print(f"  Response: {json.dumps(body, indent=2)}")
        except:
            print(f"  Response: {resp.text[:200]}")
    else:
        log(f"WARNING: Status {resp.status_code}", Colors.YELLOW)
        print(f"  Response: {resp.text[:200]}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 2: CloudScale Status (if available)
    # ─────────────────────────────────────────────────────────────────────
    log("\nTest 2: CloudScale Status (/cloudscale-test/status)")
    resp = test_endpoint(base_url, "GET", "/cloudscale-test/status")
    
    if isinstance(resp, dict) and resp.get("error"):
        log(f"SKIPPED: {resp['error']}", Colors.YELLOW)
    elif resp.status_code == 200:
        log(f"PASSED: CloudScale connection OK", Colors.GREEN)
        try:
            body = resp.json()
            print(f"  Catalyst Initialized: {body.get('catalyst_initialized')}")
            print(f"  ZCQL Test: {body.get('zcql_test')}")
            print(f"  Datastore Test: {body.get('datastore_test')}")
        except:
            print(f"  Response: {resp.text[:200]}")
    else:
        log(f"WARNING: Status {resp.status_code}", Colors.YELLOW)
        try:
            body = resp.json()
            print(f"  Error: {body.get('message', body.get('error', resp.text[:200]))}")
        except:
            print(f"  Response: {resp.text[:200]}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 3: Root Endpoint
    # ─────────────────────────────────────────────────────────────────────
    log("\nTest 3: Root Endpoint (/)")
    resp = test_endpoint(base_url, "GET", "/")
    
    if isinstance(resp, dict) and resp.get("error"):
        log(f"FAILED: {resp['error']}", Colors.RED)
    elif resp.status_code == 200:
        log(f"PASSED: API info retrieved", Colors.GREEN)
        try:
            body = resp.json()
            print(f"  Version: {body.get('version')}")
            print(f"  Runtime: {body.get('runtime')}")
        except:
            pass
    else:
        log(f"FAILED: Status {resp.status_code}", Colors.RED)
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 4: Registration
    # ─────────────────────────────────────────────────────────────────────
    import time
    test_email = f"test_{int(time.time())}@example.com"
    
    log(f"\nTest 4: Register User (/auth/register)")
    log(f"  Email: {test_email}")
    
    reg_data = {
        "fullName": "Test User",
        "email": test_email,
        "password": "TestPass123!",
        "phoneNumber": "+91-9876543210"
    }
    
    resp = test_endpoint(base_url, "POST", "/auth/register", data=reg_data)
    
    token = None
    if isinstance(resp, dict) and resp.get("error"):
        log(f"FAILED: {resp['error']}", Colors.RED)
    elif resp.status_code == 201:
        log(f"PASSED: Registration successful!", Colors.GREEN)
        try:
            body = resp.json()
            token = body.get("data", {}).get("token")
            user_id = body.get("data", {}).get("user", {}).get("id")
            print(f"  User ID: {user_id}")
            print(f"  Token received: {'Yes' if token else 'No'}")
        except:
            pass
    elif resp.status_code == 409:
        log(f"INFO: Email already registered (expected for repeat tests)", Colors.YELLOW)
    elif resp.status_code == 500:
        log(f"FAILED: Internal Server Error", Colors.RED)
        try:
            body = resp.json()
            print(f"  Error Message: {body.get('message')}")
            print(f"  Details: {body.get('details', 'None')}")
            
            # Provide specific troubleshooting
            if "oauth" in str(body).lower() or "invalid_token" in str(body).lower():
                log("\n  DIAGNOSIS: Catalyst OAuth token issue", Colors.YELLOW)
                log("  SOLUTION: Run 'catalyst login' and restart 'catalyst serve'", Colors.YELLOW)
            elif "tls" in str(body).lower() or "certificate" in str(body).lower():
                log("\n  DIAGNOSIS: TLS/SSL certificate bundle issue", Colors.YELLOW)
                log("  SOLUTION: Delete .build folder and restart 'catalyst serve'", Colors.YELLOW)
            elif "cloudscale" in str(body).lower() or "zcql" in str(body).lower():
                log("\n  DIAGNOSIS: CloudScale database connection issue", Colors.YELLOW)
                log("  SOLUTION: Check CloudScale table configuration in Catalyst console", Colors.YELLOW)
        except:
            print(f"  Response: {resp.text[:500]}")
    elif resp.status_code == 503:
        log(f"FAILED: Service Unavailable (Backend setup issue)", Colors.RED)
        try:
            body = resp.json()
            print(f"  Error Message: {body.get('message')}")
            log("\n  SOLUTION: Run 'catalyst login' and restart 'catalyst serve'", Colors.YELLOW)
        except:
            print(f"  Response: {resp.text[:300]}")
    else:
        log(f"FAILED: Status {resp.status_code}", Colors.RED)
        print(f"  Response: {resp.text[:300]}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 5: Login (if registration failed, try existing user)
    # ─────────────────────────────────────────────────────────────────────
    if not token:
        log(f"\nTest 5: Login (/auth/login)")
        
        login_data = {
            "email": test_email,
            "password": "TestPass123!"
        }
        
        resp = test_endpoint(base_url, "POST", "/auth/login", data=login_data)
        
        if isinstance(resp, dict) and resp.get("error"):
            log(f"FAILED: {resp['error']}", Colors.RED)
        elif resp.status_code == 200:
            log(f"PASSED: Login successful!", Colors.GREEN)
            try:
                body = resp.json()
                token = body.get("data", {}).get("token")
                print(f"  Token received: {'Yes' if token else 'No'}")
            except:
                pass
        elif resp.status_code == 401:
            log(f"INFO: Invalid credentials (user may not exist yet)", Colors.YELLOW)
        elif resp.status_code == 500:
            log(f"FAILED: Internal Server Error", Colors.RED)
            try:
                body = resp.json()
                print(f"  Error: {body.get('message')}")
            except:
                print(f"  Response: {resp.text[:200]}")
        else:
            log(f"FAILED: Status {resp.status_code}", Colors.RED)
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 6: Get Stations (public endpoint)
    # ─────────────────────────────────────────────────────────────────────
    log(f"\nTest 6: Get Stations (/stations)")
    resp = test_endpoint(base_url, "GET", "/stations")
    
    if isinstance(resp, dict) and resp.get("error"):
        log(f"FAILED: {resp['error']}", Colors.RED)
    elif resp.status_code == 200:
        log(f"PASSED: Stations endpoint works", Colors.GREEN)
        try:
            body = resp.json()
            stations = body.get("data", [])
            print(f"  Found {len(stations)} stations")
            if stations:
                print(f"  Sample: {stations[0].get('Station_Name', stations[0])}")
        except:
            pass
    else:
        log(f"INFO: Status {resp.status_code}", Colors.YELLOW)
    
    # ─────────────────────────────────────────────────────────────────────
    # Test 7: Get Trains (public endpoint)
    # ─────────────────────────────────────────────────────────────────────
    log(f"\nTest 7: Get Trains (/trains)")
    resp = test_endpoint(base_url, "GET", "/trains")
    
    if isinstance(resp, dict) and resp.get("error"):
        log(f"FAILED: {resp['error']}", Colors.RED)
    elif resp.status_code == 200:
        log(f"PASSED: Trains endpoint works", Colors.GREEN)
        try:
            body = resp.json()
            trains = body.get("data", [])
            print(f"  Found {len(trains)} trains")
            if trains:
                print(f"  Sample: {trains[0].get('Train_Name', trains[0])}")
        except:
            pass
    else:
        log(f"INFO: Status {resp.status_code}", Colors.YELLOW)
    
    # ─────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print(f"{Colors.BLUE}  DIAGNOSTIC SUMMARY{Colors.RESET}")
    print("="*70)
    
    if token:
        log("Authentication is WORKING", Colors.GREEN)
    else:
        log("Authentication has ISSUES - check error messages above", Colors.RED)
        log("\nCommon fixes:", Colors.YELLOW)
        log("  1. Run: catalyst login", Colors.YELLOW)
        log("  2. Restart: catalyst serve", Colors.YELLOW)
        log("  3. If using standalone Flask: python main.py", Colors.YELLOW)
        log("  4. Check CloudScale tables exist in Catalyst console", Colors.YELLOW)
    
    print()

if __name__ == "__main__":
    main()
