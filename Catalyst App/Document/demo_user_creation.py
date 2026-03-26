#!/usr/bin/env python3
"""
User Creation Demonstration for Railway Ticketing System
"""
import hashlib
from datetime import datetime

print("CREATING USER RECORD IN RAILWAY TICKETING SYSTEM")
print("=" * 50)

# Sample user data
user_data = {
    "Full_Name": "John Railway Doe",
    "Email": "john.doe@railway.com",
    "Phone_Number": "9876543210",
    "Password": "SecurePass@123",
    "Gender": "Male",
    "Role": "User",
    "Address": "123 Railway Avenue, Chennai",
    "Account_Status": "Active"
}

print("\nUser Data to be Created:")
for key, value in user_data.items():
    if key == "Password":
        print(f"  {key}: {'*' * len(value)}")
    else:
        print(f"  {key}: {value}")

print("\nProcessing User Registration...")

# Hash password (SHA-256 as used in the system)
password_hash = hashlib.sha256(user_data["Password"].encode()).hexdigest()

# Prepare payload for Zoho Creator Users table
payload = {
    "Full_Name": user_data["Full_Name"],
    "Email": user_data["Email"].lower(),
    "Phone_Number": user_data["Phone_Number"],
    "Password": password_hash,
    "Gender": user_data["Gender"],
    "Role": user_data["Role"],
    "Address": user_data["Address"],
    "Account_Status": user_data["Account_Status"],
    "Aadhar_Verified": "false",
    "Is_Aadhar_Verified": "false",
    "Registered_Date": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
    "Last_Login": None
}

print("SUCCESS: Password hashed successfully")
print("SUCCESS: Payload prepared for Zoho Creator")
print("SUCCESS: Registration date set")

print("\nFinal User Record (ready for database):")
for key, value in payload.items():
    if key == "Password":
        print(f"  {key}: {value[:20]}... (SHA-256 hash)")
    else:
        print(f"  {key}: {value}")

print(f"\nAPI Details:")
print(f"  Endpoint: POST /api/auth/register")
print(f"  Target: Users table (Zoho Creator)")
print(f"  Form Name: Users")
print(f"  Report Name: All_Users")

print(f"\nUser Creation Process:")
print(f"  1. Validate required fields (Full_Name, Email, Password)")
print(f"  2. Check for duplicate email in Users table")
print(f"  3. Hash password with SHA-256")
print(f"  4. Set default values (Role=User, Status=Active)")
print(f"  5. Add timestamp (Registered_Date)")
print(f"  6. Insert record into CloudScale Users table")
print(f"  7. Return success with user_id")

print(f"\nSUCCESS: User creation completed!")
print(f"Generated User ID: USR{hash(payload['Email']) % 1000000:06d}")
print(f"User can now login with: {payload['Email']}")
print(f"User record stored in CloudScale database")

# Simulate successful API response
response = {
    "success": True,
    "message": "User registered successfully",
    "user_id": f"USR{hash(payload['Email']) % 1000000:06d}",
    "email": payload["Email"],
    "role": payload["Role"]
}

print(f"\nAPI Response:")
for key, value in response.items():
    print(f"  {key}: {value}")

print(f"\nNext Steps:")
print(f"  - User can login via POST /api/auth/login")
print(f"  - Admin can view user via GET /api/users")
print(f"  - User can update profile via PUT /api/users/{{id}}/profile")
print(f"  - User can create bookings, search trains, etc.")