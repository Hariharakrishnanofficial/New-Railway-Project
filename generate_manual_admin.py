import os
import sys
import json
import logging
import hashlib

# Add paths for security import
BASE_DIR = os.getcwd()
sys.path.insert(0, os.path.join(BASE_DIR, 'functions', 'smart_railway_app_function'))

from core.security import hash_password

def generate_manual_record():
    email = "test_verified_2@railway.com"
    password = "Admin@123"
    
    print("\n" + "="*60)
    print("🚀 SMART RAILWAY: MANUAL ADMIN RECORD GENERATOR")
    print("="*60)
    
    # Generate Hash
    # This will use Argon2 if available in the environment, else fallback
    password_hash = hash_password(password)
    
    print(f"\nCOPY AND PASTE THESE VALUES INTO ZOHO CATALYST DATASTORE:")
    print(f"Table: Employees")
    print(f"-"*60)
    print(f"Employee_ID    : Admin001")
    print(f"Email           : {email}")
    print(f"Full_Name       : System Admin")
    print(f"Password        : {password_hash}")
    print(f"Role            : Admin")
    print(f"Account_Status  : Active")
    print(f"Is_Active       : true")
    print(f"Designation     : ADMIN")
    print(f"Department      : ADMIN")
    print(f"Joined_At       : 2026-04-07 17:06:55")
    print(f"-"*60)
    print(f"\nNote: The Password hash starts with '{password_hash[:15]}...'")
    print("="*60)

if __name__ == "__main__":
    generate_manual_record()
