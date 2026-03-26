#!/usr/bin/env python
"""Test that all imports work correctly"""

import sys
import os

# Add the functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'catalyst_backend'))

print("Testing imports...")

try:
    print("1. Importing config...")
    from config import TABLES
    print(f"   ✓ TABLES loaded: {list(TABLES.keys())[:3]}...")
    
    print("2. Importing exceptions...")
    from core.exceptions import RailwayException, ValidationError, AuthenticationError
    print("   ✓ Exceptions loaded")
    
    print("3. Importing security...")
    from core.security import hash_password, generate_access_token
    print("   ✓ Security loaded")
    
    print("4. Importing repositories...")
    from repositories.cloudscale_repository import zoho_repo
    print("   ✓ Repositories loaded")
    
    print("5. Importing auth_crud_service...")
    from services.auth_crud_service import auth_crud_service
    print("   ✓ auth_crud_service loaded")
    print(f"   - Service.users_table = {auth_crud_service.users_table}")
    
    print("6. Importing auth_crud routes...")
    from routes.auth_crud import auth_crud_bp
    print("   ✓ auth_crud routes loaded")
    print(f"   - Blueprint: {auth_crud_bp.name}")
    print(f"   - Routes: {[str(rule) for rule in auth_crud_bp.deferred_functions][:3]}...")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
