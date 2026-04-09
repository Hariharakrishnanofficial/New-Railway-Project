"""
Token Debug Test - Analyze JWT token validation issues
"""

import sys
import os
sys.path.append('f:\\New Railway Project\\functions\\smart_railway_app_function')

from core.security import decode_token, JWT_SECRET, JWT_ALGO
import json
import base64

# Sample token from our debug test (user token)
user_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMTIwNzAwMDAwMDExMjAwMiIsImVtYWlsIjoiYWdlbnRAYWdlbnQuY29tIiwicm9sZSI6IlVzZXIiLCJpYXQiOjE3NzQ2MDE2NjQsImV4cCI6MTc3NDYwNTI2NCwidHlwZSI6ImFjY2VzcyJ9.sBZbocMyWPMtiFOM_XMI1Yn2cTRh4Wxw7lWWeGH75QE"

print("="*80)
print("TOKEN DEBUG ANALYSIS")
print("="*80)

print(f"\n1. JWT_SECRET from config: {JWT_SECRET[:20]}...")
print(f"2. JWT_ALGO from config: {JWT_ALGO}")

print(f"\n3. Token to decode: {user_token[:50]}...")

# Try to decode manually with PyJWT
try:
    import jwt
    print(f"\n4. PyJWT Available: YES")

    # Try decoding
    try:
        payload = jwt.decode(user_token, JWT_SECRET, algorithms=[JWT_ALGO])
        print(f"5. PyJWT decode SUCCESS:")
        print(f"   Payload: {json.dumps(payload, indent=2, default=str)}")
    except jwt.ExpiredSignatureError:
        print(f"5. PyJWT decode FAILED: Token expired")
        # Try without expiry check
        try:
            payload = jwt.decode(user_token, JWT_SECRET, algorithms=[JWT_ALGO], options={"verify_exp": False})
            print(f"   Payload (ignoring expiry): {json.dumps(payload, indent=2, default=str)}")
        except Exception as e:
            print(f"   Still failed: {e}")
    except Exception as e:
        print(f"5. PyJWT decode FAILED: {e}")

except ImportError:
    print(f"\n4. PyJWT Available: NO")

# Try using our security module's decode function
print(f"\n6. Using core.security.decode_token:")
try:
    payload = decode_token(user_token)
    if payload:
        print(f"   SUCCESS: {json.dumps(payload, indent=2, default=str)}")
    else:
        print(f"   FAILED: decode_token returned None")
except Exception as e:
    print(f"   ERROR: {e}")

# Manual JWT parsing
print(f"\n7. Manual JWT parsing:")
try:
    parts = user_token.split('.')
    if len(parts) == 3:
        header_b64, payload_b64, signature = parts

        # Decode header
        header_padded = header_b64 + '=' * (4 - len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_padded))
        print(f"   Header: {json.dumps(header, indent=2)}")

        # Decode payload
        payload_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_padded))
        print(f"   Payload: {json.dumps(payload, indent=2, default=str)}")

        print(f"   Signature: {signature[:20]}...")

        # Check times
        from datetime import datetime
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            now = datetime.now()
            print(f"   Expires: {exp_time}")
            print(f"   Now: {now}")
            print(f"   Expired: {now > exp_time}")
    else:
        print(f"   Invalid JWT format: {len(parts)} parts instead of 3")
except Exception as e:
    print(f"   Manual parsing failed: {e}")

print("\n" + "="*80)