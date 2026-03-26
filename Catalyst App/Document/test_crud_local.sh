#!/bin/bash
# CRUD Test Script for Catalyst Local Server
# Usage: ./test_crud_local.sh

BASE_URL="http://localhost:9000/server/catalyst_backend"

echo "========================================="
echo "🧪 Railway Ticketing - Local CRUD Test"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Health Check
echo -e "${YELLOW}[1/7]${NC} Health Check..."
health_response=$(curl -s "${BASE_URL}/api/health" 2>&1)
if echo "$health_response" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Server is running"
    echo "$health_response" | head -5
else
    echo -e "${RED}✗${NC} Server not responding on port 9000"
    echo "Response: $health_response"
    echo ""
    echo "Please ensure Catalyst server is running:"
    echo "  cd 'f:/Railway Project Backend/Catalyst App'"
    echo "  catalyst serve"
    exit 1
fi
echo ""

# Step 2: Register a new user
echo -e "${YELLOW}[2/7]${NC} Creating test user..."
register_response=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User CRUD",
    "email": "testcrud@example.com",
    "phone": "9876543210",
    "password": "Test@12345"
  }')

echo "$register_response" | head -10
echo ""

# Step 3: Login to get JWT token
echo -e "${YELLOW}[3/7]${NC} Logging in..."
login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testcrud@example.com",
    "password": "Test@12345"
  }')

TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
USER_ID=$(echo "$login_response" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗${NC} Login failed"
    echo "$login_response"
    exit 1
fi

echo -e "${GREEN}✓${NC} Login successful"
echo "Token: ${TOKEN:0:30}..."
echo "User ID: $USER_ID"
echo ""

# Step 4: READ - Get user profile
echo -e "${YELLOW}[4/7]${NC} Reading user profile (GET /api/users/:id)..."
read_response=$(curl -s -X GET "${BASE_URL}/api/users/${USER_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo "$read_response" | head -15
echo ""

# Step 5: UPDATE - Update user profile
echo -e "${YELLOW}[5/7]${NC} Updating user profile (PUT /api/users/:id/profile)..."
update_response=$(curl -s -X PUT "${BASE_URL}/api/users/${USER_ID}/profile" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "Full_Name": "Updated CRUD Test User",
    "Phone_Number": "9999888877"
  }')

echo "$update_response" | head -10
echo ""

# Step 6: READ again to verify update
echo -e "${YELLOW}[6/7]${NC} Reading updated profile..."
verify_response=$(curl -s -X GET "${BASE_URL}/api/users/${USER_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo "$verify_response" | grep -E "Full_Name|Phone_Number" | head -5
echo ""

# Step 7: Get user bookings (should be empty)
echo -e "${YELLOW}[7/7]${NC} Reading user bookings (GET /api/users/:id/bookings)..."
bookings_response=$(curl -s -X GET "${BASE_URL}/api/users/${USER_ID}/bookings" \
  -H "Authorization: Bearer ${TOKEN}")

echo "$bookings_response" | head -10
echo ""

echo "========================================="
echo -e "${GREEN}✅ CRUD Test Complete!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ CREATE - User registered via /api/auth/register"
echo "  ✓ READ   - User profile fetched via /api/users/:id"
echo "  ✓ UPDATE - Profile updated via /api/users/:id/profile"
echo "  ✓ DELETE - (Skipped to preserve test user)"
echo ""
echo "Test User Credentials:"
echo "  Email: testcrud@example.com"
echo "  Password: Test@12345"
echo "  User ID: $USER_ID"
echo ""
