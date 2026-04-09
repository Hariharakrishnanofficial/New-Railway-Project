# Smart Railway Ticketing System - Workspace Instructions

## Project Overview
A comprehensive railway ticketing system built on Zoho Catalyst using a modular Flask backend and React frontend.

## Key Directories
- [functions/](functions/): Active Backend (Flask + Catalyst Serverless)
- [railway-app/](railway-app/): Active Frontend (React)
- [docs/](docs/): Centralized documentation hub
- **REFERENCE ONLY**: `Catalyst App/` is a legacy reference folder. DO NOT MODIFY FILES HERE.

## Architecture
- **Backend**: Modular Flask architecture using Blueprints for separation of concerns.
- **Frontend**: Standard React and Tailwind CSS, using `BrowserRouter` with `basename="/app"`.
- **Database**: Zoho CloudScale with ZCQL for queries. Schema is documented in [docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md](docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md).
- **Security**: Hardened implementation with HMAC signing, CORS, and full session audit logging. See [docs/security/SECURITY_IMPLEMENTATION_SUMMARY.md](docs/security/SECURITY_IMPLEMENTATION_SUMMARY.md).

## Build and Test
- **Local Dev Server**: `catalyst serve` (from root) for the integrated environment.
- **Backend Setup**: `pip install -r functions/requirements.txt`. Main entry point is [functions/smart_railway_app_function/main.py](functions/smart_railway_app_function/main.py).
- **Frontend Startup**: `npm start` (from [railway-app/](railway-app/)).
- **Utility Scripts**: 
  - [seed_sample_data.bat](seed_sample_data.bat) for sample data.
  - [diagnose_and_fix_db.py](diagnose_and_fix_db.py) for database maintenance.
  - [provision_admin_employee.py](provision_admin_employee.py) for admin setup.

## Development Conventions
- **Routing**: Follow clean URL standards (no hash fragments). See [docs/architecture/ROUTING_GUIDE.md](docs/architecture/ROUTING_GUIDE.md).
- **Agent Roles**: Specialized subagents (API Developer, React Developer, Database Expert, etc.) are used for focused tasks. Refer to [docs/AGENTS_GUIDE.md](docs/AGENTS_GUIDE.md).
- **Exemplar Patterns**:
  - API Route Blueprint: [functions/smart_railway_app_function/routes/auth.py](functions/smart_railway_app_function/routes/auth.py)
  - React Component: [railway-app/src/components/OTPVerification.jsx](railway-app/src/components/OTPVerification.jsx)

## Common Pitfalls
- **Reference Folder**: Accidentally editing `Catalyst App/`. Always check the parent directory before saving.
- **Database Migration**: Large schema changes require manual ZCQL migration. See [docs/development/CRITICAL_DATABASE_MIGRATION_REQUIRED.md](docs/development/CRITICAL_DATABASE_MIGRATION_REQUIRED.md).
- **OTP Validation**: 400 errors during login are often related to session synchronization. Refer to [docs/guides/FIX_400_OTP_VALIDATION.md](docs/guides/FIX_400_OTP_VALIDATION.md).

---
See [docs/00_START_HERE.md](docs/00_START_HERE.md) for full documentation.
