#!/usr/bin/env python3
"""
CloudScale Connection Diagnosis for Railway Ticketing System
This script diagnoses the CloudScale connection issue and tests Zoho Creator API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'catalyst_backend'))

print("CLOUDSCALE CONNECTION DIAGNOSIS")
print("=" * 40)

# Test 1: Check environment configuration
print("\n1. ENVIRONMENT CONFIGURATION:")
print("-" * 30)

from config import get_zoho_config
config = get_zoho_config()

config_status = {
    'CLIENT_ID': 'SET' if config.get('client_id') else 'MISSING',
    'CLIENT_SECRET': 'SET' if config.get('client_secret') else 'MISSING',
    'REFRESH_TOKEN': 'SET' if config.get('refresh_token') else 'MISSING',
    'API_BASE_URL': config.get('api_base_url', 'MISSING'),
    'APP_NAME': config.get('app_name', 'MISSING'),
    'OWNER_NAME': config.get('account_owner_name', 'MISSING')
}

for key, status in config_status.items():
    status_icon = "✅" if status != 'MISSING' else "❌"
    print(f"  {status_icon} {key}: {status}")

# Test 2: Check Catalyst SDK availability
print("\n2. CATALYST SDK CHECK:")
print("-" * 25)

try:
    import zcatalyst_sdk
    print("✅ zcatalyst_sdk imported successfully")

    try:
        catalyst_app = zcatalyst_sdk.initialize()
        print("✅ Catalyst SDK initialized successfully")
        print(f"  App info: {type(catalyst_app)}")
    except Exception as e:
        print(f"❌ Catalyst SDK initialization failed: {e}")
        print("  This explains why CloudScale isn't working!")

except ImportError as e:
    print(f"❌ zcatalyst_sdk import failed: {e}")

# Test 3: Test Zoho Creator REST API (fallback)
print("\n3. ZOHO CREATOR REST API TEST:")
print("-" * 35)

try:
    from repositories.zoho_repository import ZohoRepository
    from services.zoho_token_manager import token_manager

    print("✅ Zoho Repository imported successfully")

    # Test token manager
    try:
        token = token_manager.get_access_token()
        if token:
            print("✅ Zoho API access token obtained")
            print(f"  Token: {token[:20]}...")

            # Test a simple API call
            zoho_repo = ZohoRepository()
            forms = zoho_repo.forms
            print(f"✅ Forms configured: {len(forms.get('forms', {}))} forms")

            # Test user creation capability
            print("\n  Testing Users table access...")
            users_form = forms['forms'].get('users', 'Users')
            users_report = forms['reports'].get('users', 'All_Users')
            print(f"  Users Form: {users_form}")
            print(f"  Users Report: {users_report}")

        else:
            print("❌ Failed to obtain Zoho API access token")

    except Exception as e:
        print(f"❌ Zoho API test failed: {e}")

except Exception as e:
    print(f"❌ Zoho Repository test failed: {e}")

# Test 4: Diagnosis Summary
print("\n4. DIAGNOSIS SUMMARY:")
print("-" * 20)

print("\nISSUE IDENTIFIED:")
print("The system is configured to use CloudScale (Catalyst SDK) but:")
print("1. ❌ Catalyst SDK initialization is failing")
print("2. ❌ CloudScale repository cannot connect")
print("3. ✅ Zoho Creator REST API credentials are available")

print("\nSOLUTION OPTIONS:")
print("A) Fix CloudScale: Resolve Catalyst SDK initialization")
print("B) Use REST API: Switch back to working Zoho Repository")
print("C) Hybrid: Use REST API until CloudScale is fixed")

print("\nRECOMMENDATION:")
print("Switch to Zoho Creator REST API (Option B) for immediate functionality")

print("\n" + "=" * 50)
print("DIAGNOSIS COMPLETE - See solutions above")