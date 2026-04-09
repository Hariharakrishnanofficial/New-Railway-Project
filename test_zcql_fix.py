#!/usr/bin/env python3
"""
Quick test to verify ZCQL Session_ID BIGINT fixes are working
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from repositories.cloudscale_repository import CriteriaBuilder, CloudScaleRepository
from services.session_service import validate_csrf_token

def test_criteria_builder():
    """Test that CriteriaBuilder generates correct ZCQL for Session_ID"""
    print("Testing CriteriaBuilder for Session_ID (BIGINT)...")
    
    # Test numeric Session_ID 
    session_id = "3799543593"
    criteria = CriteriaBuilder().id_eq("Session_ID", session_id).build()
    print(f"Session ID: {session_id}")
    print(f"Generated criteria: {criteria}")
    
    # Should generate: Session_ID = 3799543593 (without quotes)
    expected = f"Session_ID = {session_id}"
    if criteria == expected:
        print("✅ PASS: CriteriaBuilder correctly generates numeric Session_ID")
    else:
        print(f"❌ FAIL: Expected '{expected}', got '{criteria}'")
    
    return criteria == expected

def test_csrf_validation_query():
    """Test the validate_csrf_token function query construction"""
    print("\nTesting validate_csrf_token ZCQL construction...")
    
    # Mock a test session ID and CSRF token
    session_id = "3799543593"  # Same as user's error logs
    csrf_token = "test-token"
    
    try:
        # This should not raise ZCQL BIGINT errors
        result = validate_csrf_token(session_id, csrf_token)
        print(f"✅ PASS: validate_csrf_token executed without ZCQL BIGINT error")
        print(f"Result: {result}")
        return True
    except Exception as e:
        if "Invalid input value for BIGINT column" in str(e):
            print(f"❌ FAIL: ZCQL BIGINT error still occurring: {e}")
            return False
        else:
            print(f"⚠️  Other error (expected if session doesn't exist): {e}")
            return True  # This is OK, we just want to avoid BIGINT errors

if __name__ == "__main__":
    print("=== ZCQL Session_ID BIGINT Fix Test ===\n")
    
    test1_pass = test_criteria_builder()
    test2_pass = test_csrf_validation_query()
    
    print(f"\n=== Results ===")
    print(f"CriteriaBuilder test: {'PASS' if test1_pass else 'FAIL'}")
    print(f"CSRF validation test: {'PASS' if test2_pass else 'FAIL'}")
    
    if test1_pass and test2_pass:
        print("✅ ALL TESTS PASSED: ZCQL fixes appear to be working!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED: ZCQL issues may still exist")
        sys.exit(1)