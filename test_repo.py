import os
import sys
import json
import logging
import bcrypt

# Add functions folder to path to import repository
sys.path.append(os.path.join(str(Get-Location), "functions", "smart_railway_app_function"))

from repositories.cloudscale_repository import CloudScaleRepository
from config import TABLES

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_admin_via_api():
    print("="*80)
    print("INDIRECT ADMIN CREATION VIA REPOSITORY")
    print("="*80)
    
    email = "test@railway.com"
    full_name = "Test Admin"
    password = "test@railway.com"
    
    print(f"Target Email: {email}")
    
    # Generate password hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    repo = CloudScaleRepository()
    
    # Check if user already exists
    print("\nChecking for existing user...")
    user_query = f"SELECT ROWID, Email FROM {TABLES['users']} WHERE Email = '{email}'"
    # Note: This will fail unless we have a Catalyst app instance.
    # We can't easily initialize the SDK here without a project ID and valid auth headers.
    # INSTEAD: We will use the existing catalyst serve session via a new debug endpoint.
    print("Please use the web browser or curl to trigger creation via the server.")

if __name__ == "__main__":
    create_admin_via_api()
