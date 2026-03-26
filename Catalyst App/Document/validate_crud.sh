#!/bin/bash
# Quick validation script for CRUD Auth Implementation

echo "═══════════════════════════════════════════════════════════"
echo "CATALYST APP - CRUD AUTH VALIDATION SCRIPT"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} Found: $1"
    return 0
  else
    echo -e "${RED}✗${NC} Missing: $1"
    return 1
  fi
}

echo "CHECKING BACKEND FILES..."
echo "────────────────────────────────────────────────────────────"
check_file "functions/catalyst_backend/routes/auth_crud.py"
check_file "functions/catalyst_backend/services/auth_crud_service.py"

echo ""
echo "CHECKING FRONTEND FILES..."
echo "────────────────────────────────────────────────────────────"
check_file "catalyst-frontend/src/services/authApi.js"
check_file "catalyst-frontend/src/pages/AuthPage.jsx"
check_file "catalyst-frontend/src/styles/AuthPage.css"
check_file "catalyst-frontend/src/styles/ProfilePage.css"
check_file "catalyst-frontend/src/pages/ProfilePage_NEW.jsx"

echo ""
echo "CHECKING INTEGRATION..."
echo "────────────────────────────────────────────────────────────"
if grep -q "auth_crud_bp" functions/catalyst_backend/routes/__init__.py; then
  echo -e "${GREEN}✓${NC} Blueprint registered in routes/__init__.py"
else
  echo -e "${RED}✗${NC} Blueprint not registered in routes/__init__.py"
fi

if grep -q "import AuthPage" catalyst-frontend/src/App.jsx; then
  echo -e "${GREEN}✓${NC} AuthPage imported in App.jsx"
else
  echo -e "${RED}✗${NC} AuthPage not imported in App.jsx"
fi

if grep -q "authApi" catalyst-frontend/src/pages/ProfilePage_NEW.jsx; then
  echo -e "${GREEN}✓${NC} authApi imported in ProfilePage_NEW.jsx"
else
  echo -e "${RED}✗${NC} authApi not imported in ProfilePage_NEW.jsx"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "IMPLEMENTATION SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Backend CRUD Endpoints:"
echo "  • POST   /api/auth/register            - CREATE user"
echo "  • POST   /api/auth/signin              - READ + authenticate"
echo "  • GET    /api/auth/profile/<id>        - READ profile"
echo "  • PUT    /api/auth/profile/<id>        - UPDATE profile"
echo "  • POST   /api/auth/change-password     - UPDATE password"
echo "  • POST   /api/auth/delete-account      - DELETE (permanent)"
echo "  • POST   /api/auth/deactivate-account  - DELETE (soft)"
echo ""
echo "Frontend Components:"
echo "  • AuthPage.jsx      - Registration & Sign In (tabbed)"
echo "  • ProfilePage.jsx   - Profile management (3 tabs)"
echo "  • authApi.js        - API service layer"
echo ""
echo "Styling:"
echo "  • AuthPage.css      - Beautiful auth forms"
echo "  • ProfilePage.css   - Modern profile management UI"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "NEXT STEPS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Start the development server:"
echo "   cd \"f:\\Railway Project Backend\\Catalyst App\""
echo "   catalyst serve"
echo ""
echo "2. Navigate to:"
echo "   Frontend: http://localhost:5173/auth"
echo "   Backend:  http://localhost:3000/api/auth/"
echo ""
echo "3. Test registration and sign in flows"
echo ""
echo "4. Check AUTH_CRUD_IMPLEMENTATION_COMPLETE.md for details"
echo ""
echo "═══════════════════════════════════════════════════════════"
