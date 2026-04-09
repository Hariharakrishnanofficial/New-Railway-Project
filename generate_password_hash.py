#!/usr/bin/env python3
"""
Generate password hash for manual record creation.
Prioritizes Argon2 (preferred by current system), fallback to bcrypt.
"""

import os
import sys

# Ensure the core module is in path
sys.path.append(os.path.join(os.getcwd(), 'functions', 'smart_railway_app_function'))

def generate_hash():
    print("=" * 80)
    print("SYSTEM PASSWORD HASH GENERATOR")
    print("=" * 80)
    print("\nUse this to generate a password hash for manual CloudScale INSERT.\n")
    
    try:
        from core.security import hash_password
        
        password = input("Enter password: ").strip()
        if not password:
            print("ERROR: Password required")
            return
            
        if len(password) < 8:
             print("⚠ WARNING: Password is less than 8 characters")
        
        print("\nGenerating hash using system core.security logic...")
        password_hash = hash_password(password)
        
        print("\n" + "-" * 40)
        print(f"PLAIN PASSWORD: {password}")
        print(f"HASHED VALUE:   {password_hash}")
        print("-" * 40)
        
        print("\nInstructions for Catalyst Console:")
        print("1. Copy the HASHED VALUE above.")
        print("2. Go to Catalyst Console -> CloudScale Datastore.")
        print("3. Paste into the 'Password' column for your user/employee record.")
        
    except ImportError as e:
        print(f"Error importing security module: {e}")
        print("Falling back to basic bcrypt...")
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        print(f"BCRYPT HASH: {password_hash}")

if __name__ == "__main__":
    generate_hash()
    
    print("\n" + "=" * 80)
    print("PASSWORD HASH")
    print("=" * 80)
    print(f"\n{password_hash}\n")
    print("Copy this hash and use it in your SQL INSERT statement:")
    print(f"""
INSERT INTO Employees (
  Employee_ID, Full_Name, Email, Password_Hash, Role, 
  Department, Designation, Permissions, Is_Active
) VALUES (
  'ADM001',
  'System Admin',
  'your_email@example.com',
  '{password_hash}',
  'Admin',
  'Administration',
  'System Administrator',
  '{{"users": {{"view": true, "create": true}}, "employees": {{"view": true, "create": true}}}}',
  1
);
""")
    print("=" * 80)

if __name__ == '__main__':
    try:
        generate_hash()
    except KeyboardInterrupt:
        print("\n\nAborted.")
    except Exception as e:
        print(f"\nError: {e}")
