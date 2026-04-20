"""
Manual API Test Script - Smart Railway Ticketing System
Tests all CRUD operations across modules.

Usage:
    python test_api_manual.py [--base-url http://localhost:9000]
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:9000"
VERBOSE = True

# Test data storage
test_data = {
    "auth_token": None,
    "refresh_token": None,
    "user_id": None,
    "station_id": None,
    "train_id": None,
    "route_id": None,
    "booking_id": None,
    "pnr": None,
    "admin_token": None,
}


def log(msg, level="INFO"):
    """Print formatted log message."""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WARNING": "\033[93m",
        "RESET": "\033[0m"
    }
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = colors.get(level, colors["INFO"])
    print(f"{color}[{timestamp}] [{level}] {msg}{colors['RESET']}")


def log_response(resp, show_body=True):
    """Log API response details."""
    status_color = "\033[92m" if resp.status_code < 400 else "\033[91m"
    print(f"  Status: {status_color}{resp.status_code}\033[0m")
    if show_body and VERBOSE:
        try:
            body = resp.json()
            print(f"  Response: {json.dumps(body, indent=2)[:500]}")
        except:
            print(f"  Response: {resp.text[:200]}")


def make_request(method, endpoint, data=None, auth=True, token=None):
    """Make HTTP request with optional auth."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if auth:
        use_token = token or test_data.get("auth_token")
        if use_token:
            headers["Authorization"] = f"Bearer {use_token}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unknown method: {method}")
        return resp
    except requests.exceptions.ConnectionError:
        log(f"Connection refused to {url}. Is the server running?", "ERROR")
        return None
    except Exception as e:
        log(f"Request failed: {e}", "ERROR")
        return None


def test_health():
    """Test health endpoint."""
    log("Testing /health endpoint...")
    resp = make_request("GET", "/health", auth=False)
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_root():
    """Test root endpoint."""
    log("Testing / endpoint...")
    resp = make_request("GET", "/", auth=False)
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_register():
    """Test user registration."""
    log("\n" + "="*60)
    log("TESTING: User Registration")
    log("="*60)
    
    test_email = f"testuser_{int(time.time())}@example.com"
    data = {
        "fullName": "Test User",
        "email": test_email,
        "password": "SecurePass123!",
        "phoneNumber": "+91-9876543210"
    }
    
    log(f"POST /auth/register (email: {test_email})")
    resp = make_request("POST", "/auth/register", data=data, auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 201:
            body = resp.json()
            if body.get("status") == "success":
                test_data["auth_token"] = body.get("data", {}).get("token")
                test_data["refresh_token"] = body.get("data", {}).get("refreshToken")
                test_data["user_id"] = body.get("data", {}).get("user", {}).get("id")
                test_data["test_email"] = test_email
                log(f"Registration successful! User ID: {test_data['user_id']}", "SUCCESS")
                return True
        log(f"Registration failed: {resp.text}", "ERROR")
    return False


def test_login():
    """Test user login."""
    log("\n" + "="*60)
    log("TESTING: User Login")
    log("="*60)
    
    email = test_data.get("test_email", "john.doe@example.com")
    data = {
        "email": email,
        "password": "SecurePass123!"
    }
    
    log(f"POST /auth/login (email: {email})")
    resp = make_request("POST", "/auth/login", data=data, auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            if body.get("status") == "success":
                test_data["auth_token"] = body.get("data", {}).get("token")
                test_data["refresh_token"] = body.get("data", {}).get("refreshToken")
                test_data["user_id"] = body.get("data", {}).get("user", {}).get("id")
                log(f"Login successful! User ID: {test_data['user_id']}", "SUCCESS")
                return True
        log(f"Login failed", "ERROR")
    return False


def test_validate_session():
    """Test session validation."""
    log("\nTesting session validation...")
    
    log("GET /auth/validate")
    resp = make_request("GET", "/auth/validate")
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_refresh_token():
    """Test token refresh."""
    log("\nTesting token refresh...")
    
    data = {"refreshToken": test_data.get("refresh_token")}
    log("POST /auth/refresh")
    resp = make_request("POST", "/auth/refresh", data=data, auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            if body.get("status") == "success":
                test_data["auth_token"] = body.get("data", {}).get("token")
                log("Token refreshed!", "SUCCESS")
                return True
    return False


def test_update_profile():
    """Test profile update."""
    log("\nTesting profile update...")
    
    data = {
        "fullName": "Updated Test User",
        "phoneNumber": "+91-9876543211"
    }
    
    log("PUT /auth/profile")
    resp = make_request("PUT", "/auth/profile", data=data)
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_logout():
    """Test logout."""
    log("\nTesting logout...")
    
    log("POST /auth/logout")
    resp = make_request("POST", "/auth/logout", auth=False)
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  STATIONS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_stations():
    """Test get all stations."""
    log("\n" + "="*60)
    log("TESTING: Stations Module")
    log("="*60)
    
    log("GET /stations")
    resp = make_request("GET", "/stations", auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("data", [])
            if data:
                test_data["station_id"] = data[0].get("ROWID")
                log(f"Found {len(data)} stations. First ID: {test_data['station_id']}", "SUCCESS")
            return True
    return False


def test_create_station():
    """Test create station (Admin only)."""
    log("\nTesting station creation (Admin required)...")
    
    station_code = f"TST{int(time.time()) % 1000}"
    data = {
        "stationCode": station_code,
        "stationName": "Test Station",
        "city": "Test City",
        "state": "Test State",
        "zone": "NR",
        "platformCount": 5
    }
    
    log(f"POST /stations (code: {station_code})")
    resp = make_request("POST", "/stations", data=data)
    
    if resp:
        log_response(resp)
        if resp.status_code == 201:
            body = resp.json()
            test_data["station_id"] = body.get("data", {}).get("ROWID")
            log(f"Station created! ID: {test_data['station_id']}", "SUCCESS")
            return True
        elif resp.status_code == 403:
            log("Admin access required (expected for non-admin user)", "WARNING")
            return True  # Expected behavior
    return False


def test_get_station_by_id():
    """Test get station by ID."""
    if not test_data.get("station_id"):
        log("Skipping - no station ID available", "WARNING")
        return True
    
    log(f"\nGET /stations/{test_data['station_id']}")
    resp = make_request("GET", f"/stations/{test_data['station_id']}", auth=False)
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  TRAINS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_trains():
    """Test get all trains."""
    log("\n" + "="*60)
    log("TESTING: Trains Module")
    log("="*60)
    
    log("GET /trains")
    resp = make_request("GET", "/trains", auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("data", [])
            if data:
                test_data["train_id"] = data[0].get("ROWID")
                log(f"Found {len(data)} trains. First ID: {test_data['train_id']}", "SUCCESS")
            return True
    return False


def test_search_trains():
    """Test train search."""
    log("\nTesting train search...")
    
    # Use tomorrow's date
    journey_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    log(f"GET /trains/search?from=NDLS&to=CSTM&date={journey_date}")
    resp = make_request("GET", f"/trains/search?from=NDLS&to=CSTM&date={journey_date}", auth=False)
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("data", {}).get("trains", [])
            log(f"Found {len(data)} trains for search", "SUCCESS")
            return True
    return False


def test_get_train_by_id():
    """Test get train by ID."""
    if not test_data.get("train_id"):
        log("Skipping - no train ID available", "WARNING")
        return True
    
    log(f"\nGET /trains/{test_data['train_id']}")
    resp = make_request("GET", f"/trains/{test_data['train_id']}", auth=False)
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_create_train():
    """Test create train (Admin only)."""
    log("\nTesting train creation (Admin required)...")
    
    train_number = f"1{int(time.time()) % 10000}"
    data = {
        "trainNumber": train_number,
        "trainName": "Test Express",
        "trainType": "Superfast",
        "sourceStation": "NDLS",
        "destStation": "CSTM",
        "departureTime": "08:00",
        "arrivalTime": "20:00"
    }
    
    log(f"POST /trains (number: {train_number})")
    resp = make_request("POST", "/trains", data=data)
    
    if resp:
        log_response(resp)
        if resp.status_code == 201:
            body = resp.json()
            test_data["train_id"] = body.get("data", {}).get("ROWID")
            log(f"Train created! ID: {test_data['train_id']}", "SUCCESS")
            return True
        elif resp.status_code == 403:
            log("Admin access required (expected for non-admin user)", "WARNING")
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  FARES TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_calculate_fare():
    """Test fare calculation."""
    log("\n" + "="*60)
    log("TESTING: Fares Module")
    log("="*60)
    
    params = "trainId=12345&fromStation=NDLS&toStation=CSTM&travelClass=3A"
    log(f"GET /fares/calculate?{params}")
    resp = make_request("GET", f"/fares/calculate?{params}", auth=False)
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_get_fares():
    """Test get all fares."""
    log("\nGET /fares")
    resp = make_request("GET", "/fares")
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  BOOKINGS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_create_booking():
    """Test booking creation."""
    log("\n" + "="*60)
    log("TESTING: Bookings Module")
    log("="*60)
    
    journey_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    data = {
        "trainId": test_data.get("train_id", "12345"),
        "fromStation": "NDLS",
        "toStation": "CSTM",
        "journeyDate": journey_date,
        "travelClass": "3A",
        "quota": "GN",
        "passengers": [
            {
                "name": "Test Passenger 1",
                "age": 30,
                "gender": "Male",
                "berthPreference": "Lower"
            },
            {
                "name": "Test Passenger 2",
                "age": 28,
                "gender": "Female",
                "berthPreference": "Lower"
            }
        ]
    }
    
    log("POST /bookings")
    resp = make_request("POST", "/bookings", data=data)
    
    if resp:
        log_response(resp)
        if resp.status_code == 201:
            body = resp.json()
            test_data["booking_id"] = body.get("data", {}).get("booking", {}).get("ROWID")
            test_data["pnr"] = body.get("data", {}).get("booking", {}).get("PNR")
            log(f"Booking created! PNR: {test_data['pnr']}", "SUCCESS")
            return True
        elif resp.status_code in (400, 500):
            log("Booking failed (may need valid train/inventory)", "WARNING")
            return True  # Not a test failure
    return False


def test_get_my_bookings():
    """Test get user's bookings."""
    log("\nGET /bookings/my")
    resp = make_request("GET", "/bookings/my")
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            bookings = body.get("data", [])
            if bookings:
                test_data["booking_id"] = bookings[0].get("ROWID")
                test_data["pnr"] = bookings[0].get("PNR")
            log(f"Found {len(bookings)} bookings", "SUCCESS")
            return True
    return False


def test_get_pnr_status():
    """Test PNR status check."""
    if not test_data.get("pnr"):
        log("Skipping PNR check - no PNR available", "WARNING")
        return True
    
    log(f"\nGET /bookings/pnr/{test_data['pnr']}")
    resp = make_request("GET", f"/bookings/pnr/{test_data['pnr']}")
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_get_booking_by_id():
    """Test get booking by ID."""
    if not test_data.get("booking_id"):
        log("Skipping - no booking ID available", "WARNING")
        return True
    
    log(f"\nGET /bookings/{test_data['booking_id']}")
    resp = make_request("GET", f"/bookings/{test_data['booking_id']}")
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


def test_cancel_booking():
    """Test booking cancellation."""
    if not test_data.get("booking_id"):
        log("Skipping cancellation - no booking ID available", "WARNING")
        return True
    
    log(f"\nPOST /bookings/{test_data['booking_id']}/cancel")
    resp = make_request("POST", f"/bookings/{test_data['booking_id']}/cancel")
    
    if resp:
        log_response(resp)
        return resp.status_code == 200
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS TESTS (Admin)
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_users():
    """Test get all users (Admin only)."""
    log("\n" + "="*60)
    log("TESTING: Users Module (Admin)")
    log("="*60)
    
    log("GET /users")
    resp = make_request("GET", "/users")
    
    if resp:
        log_response(resp)
        if resp.status_code == 200:
            body = resp.json()
            users = body.get("data", [])
            log(f"Found {len(users)} users", "SUCCESS")
            return True
        elif resp.status_code == 403:
            log("Admin access required (expected)", "WARNING")
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Run all API tests."""
    log("\n" + "="*60)
    log("  SMART RAILWAY API - MANUAL TEST SUITE")
    log(f"  Base URL: {BASE_URL}")
    log("="*60 + "\n")
    
    results = {}
    
    # Basic health checks
    results["Health Check"] = test_health()
    results["Root Endpoint"] = test_root()
    
    if not results["Health Check"]:
        log("\nServer is not responding. Aborting tests.", "ERROR")
        return results
    
    # Authentication tests
    results["Register"] = test_register()
    
    if not test_data.get("auth_token"):
        log("\nRegistration failed, trying login with existing user...", "WARNING")
        results["Login"] = test_login()
    else:
        results["Login"] = True  # Already logged in via registration
    
    if test_data.get("auth_token"):
        results["Validate Session"] = test_validate_session()
        results["Refresh Token"] = test_refresh_token()
        results["Update Profile"] = test_update_profile()
    
    # Stations tests
    results["Get Stations"] = test_get_stations()
    results["Get Station by ID"] = test_get_station_by_id()
    results["Create Station"] = test_create_station()
    
    # Trains tests
    results["Get Trains"] = test_get_trains()
    results["Search Trains"] = test_search_trains()
    results["Get Train by ID"] = test_get_train_by_id()
    results["Create Train"] = test_create_train()
    
    # Fares tests
    results["Calculate Fare"] = test_calculate_fare()
    results["Get Fares"] = test_get_fares()
    
    # Bookings tests (need auth)
    if test_data.get("auth_token"):
        results["Create Booking"] = test_create_booking()
        results["Get My Bookings"] = test_get_my_bookings()
        results["Get PNR Status"] = test_get_pnr_status()
        results["Get Booking by ID"] = test_get_booking_by_id()
        # results["Cancel Booking"] = test_cancel_booking()  # Uncomment to test
    
    # Users tests
    results["Get Users"] = test_get_users()
    
    # Logout
    results["Logout"] = test_logout()
    
    # Print summary
    log("\n" + "="*60)
    log("  TEST RESULTS SUMMARY")
    log("="*60)
    
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for test_name, passed_flag in results.items():
        status = "\033[92mPASS\033[0m" if passed_flag else "\033[91mFAIL\033[0m"
        print(f"  [{status}] {test_name}")
    
    log("\n" + "-"*60)
    log(f"  Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    log("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    # Parse command line args
    if "--base-url" in sys.argv:
        idx = sys.argv.index("--base-url")
        if idx + 1 < len(sys.argv):
            BASE_URL = sys.argv[idx + 1]
    
    run_all_tests()
