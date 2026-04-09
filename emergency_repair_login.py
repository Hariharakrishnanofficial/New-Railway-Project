
import os
import sys
import hashlib
import logging

# Add the function directory to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'functions', 'smart_railway_app_function'))

# Try to import bcrypt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("WARNING: bcrypt not available. Using SHA-256 fallback.")

def generate_emergency_hashes(password):
    """Generate hashes that cover the environment types in your project."""
    
    # Force fresh hash generation specifically for your local environment
    if BCRYPT_AVAILABLE:
        # We MUST generate a fresh hash for YOUR environment to ensure verify_password works
        bcrypt_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
    else:
        bcrypt_hash = "Bcrypt not installed locally"
    
    # SHA-256 (Used as fallback in security.py when bcrypt/argon2 fail)
    sha_hash = hashlib.sha256(password.encode()).hexdigest()
    
    return bcrypt_hash, sha_hash

def repair_login():
    email = "test_verified_2@railway.com"
    password = "Admin@123"
    
    b_hash, s_hash = generate_emergency_hashes(password)
    
    print("\n" + "="*80)
    print("🔐 EMERGENCY REPAIR: ADMIN LOGIN FAILURE")
    print("="*80)
    print(f"\nYour login for '{email}' failed with 'Invalid email or password'.")
    print("This means the hash in the Employees table does not match 'Admin@123'.")
    
    print(f"\n[ACTION 1] Try this RECOMMENDED (Bcrypt) hash first:")
    print(f"  {b_hash}")
    
    print(f"\n[ACTION 2] If that fails, try this FALLBACK (SHA-256) hash:")
    print(f"  {s_hash}")
    
    print("\n[STEP-BY-STEP INSTRUCTIONS]:")
    print(f"  1. Go to Catalyst Console -> CloudScale -> Tables -> Employees.")
    print(f"  2. Find the row for {email}.")
    print(f"  3. Replace the 'Password' field with ACTION 1 (RECOMMENDED) hash.")
    print(f"  4. Set 'Account_Status' to exactly: Active")
    print(f"  5. Set 'Role' to exactly: Admin")
    print(f"  6. Set 'Is_Active' to true (boolean check).")
    print("  7. SAVE changes and try the login again.")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    repair_login()
