# Architecture Documentation

**Smart Railway Ticketing System - Technical Architecture**

---

## 📖 Quick Navigation

### Start Here

1. **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - Complete system overview
   - High-level architecture diagram
   - Technology stack
   - Core components
   - Security features
   - API endpoints reference

2. **[AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md)** - Visual flow diagrams
   - Dual authentication system flows
   - Passenger vs Employee login paths
   - Session creation and validation
   - Polymorphic reference pattern visualization
   - Error handling flows

### Database

3. **[CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md)** - Database schema reference
   - Complete table definitions
   - Field specifications and constraints
   - **Migration warnings** (Sessions FK issue)
   - Polymorphic reference patterns
   - Application-level validation examples

### Authentication System

4. **[USER_EMPLOYEE_RESTRUCTURE_PLAN.md](USER_EMPLOYEE_RESTRUCTURE_PLAN.md)** - Dual auth implementation
   - Passenger authentication flow
   - Employee/Admin authentication flow
   - Separate login endpoints
   - Role-based access control
   - Production schema

5. **[SESSION_ARCHITECTURE_GUIDE.md](SESSION_ARCHITECTURE_GUIDE.md)** - Session management details
   - Session ID generation
   - Cookie configuration
   - Session lifecycle
   - Security best practices

### Implementation

6. **[IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)** - Code changes and patterns
   - Recent implementation updates
   - Polymorphic session pattern
   - Migration requirements
   - Validation code examples

### Frontend

7. **[ROUTING_GUIDE.md](ROUTING_GUIDE.md)** - Frontend routing configuration
   - React Router setup
   - Clean URL standards
   - Admin route protection
   - Deployment considerations

### Planning

8. **[FEATURE_GAP_ANALYSIS.md](FEATURE_GAP_ANALYSIS.md)** - Feature planning
   - Implemented features
   - Planned features
   - Gap analysis

---

## 🎯 Read by Goal

### I want to understand the system architecture
→ Start with [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)  
→ Then review [AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md) for visual flows

### I need to fix employee login errors
→ Review [AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md) (Error Handling section)  
→ Check [../CRITICAL_DATABASE_MIGRATION_REQUIRED.md](../CRITICAL_DATABASE_MIGRATION_REQUIRED.md)  
→ Consult [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) (Database Migration section)

### I'm implementing a new feature
→ Review [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) for system constraints  
→ Check [CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md) for database access  
→ Follow patterns in [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)

### I'm deploying to production
→ **CRITICAL**: Complete [../CRITICAL_DATABASE_MIGRATION_REQUIRED.md](../CRITICAL_DATABASE_MIGRATION_REQUIRED.md) FIRST  
→ Review [SESSION_ARCHITECTURE_GUIDE.md](SESSION_ARCHITECTURE_GUIDE.md) for security checklist  
→ Verify [CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md) schema matches production

### I'm onboarding to the team
→ Day 1: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)  
→ Day 2: [AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md)  
→ Day 3: [CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md)  
→ Day 4: [USER_EMPLOYEE_RESTRUCTURE_PLAN.md](USER_EMPLOYEE_RESTRUCTURE_PLAN.md)  
→ Ongoing: [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for latest changes

---

## 🚨 Critical Concepts

### Polymorphic Reference Pattern

**What**: Sessions.User_ID can reference either Users.ROWID OR Employees.ROWID

**Why**: Single session system for two user types (passengers vs employees)

**Implementation**: 
- No database FK constraint (removed in migration)
- User_Type field indicates which table ('user' or 'employee')
- Application validates references before insert

**Read More**:
- [AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md) - "Polymorphic Reference Pattern" section
- [CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md) - Sessions table documentation

### Dual Authentication System

**What**: Completely separate login flows for passengers and employees

**Endpoints**:
- Passengers: `POST /session/login` → checks Users table
- Employees: `POST /session/employee/login` → checks Employees table

**Why**: Different security requirements, audit trails, and data models

**Read More**:
- [AUTHENTICATION_SESSION_FLOWS.md](AUTHENTICATION_SESSION_FLOWS.md) - Full flow diagrams
- [USER_EMPLOYEE_RESTRUCTURE_PLAN.md](USER_EMPLOYEE_RESTRUCTURE_PLAN.md) - Implementation plan

### Session Security

**Key Features**:
- HttpOnly, Secure, SameSite=Strict cookies
- 256-bit cryptographically secure session IDs
- CSRF token protection
- 90-day absolute expiration
- 24-hour idle timeout (sliding window)
- Device fingerprinting
- Comprehensive audit logging

**Read More**:
- [SESSION_ARCHITECTURE_GUIDE.md](SESSION_ARCHITECTURE_GUIDE.md)
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - Security section

---

## 📊 Documentation Status

| Document | Status | Last Updated | Coverage |
|----------|--------|--------------|----------|
| ARCHITECTURE_OVERVIEW.md | ✅ Complete | April 8, 2026 | 100% |
| AUTHENTICATION_SESSION_FLOWS.md | ✅ Complete | April 8, 2026 | 100% |
| CLOUDSCALE_DATABASE_SCHEMA_V2.md | ✅ Updated | April 8, 2026 | 100% |
| USER_EMPLOYEE_RESTRUCTURE_PLAN.md | ✅ Updated | April 8, 2026 | 100% |
| IMPLEMENTATION_NOTES.md | ✅ Updated | April 8, 2026 | 100% |
| SESSION_ARCHITECTURE_GUIDE.md | ⚠️ Needs Update | March 2026 | 80% |
| ROUTING_GUIDE.md | ✅ Current | March 2026 | 100% |
| FEATURE_GAP_ANALYSIS.md | ⚠️ Needs Update | February 2026 | 70% |

---

## 🔗 Related Documentation

- [../CRITICAL_DATABASE_MIGRATION_REQUIRED.md](../CRITICAL_DATABASE_MIGRATION_REQUIRED.md) - **Required before production**
- [../00_START_HERE.md](../00_START_HERE.md) - Quick start guide
- [../security/SECURITY_IMPLEMENTATION_SUMMARY.md](../security/SECURITY_IMPLEMENTATION_SUMMARY.md) - Security features
- [../DOCUMENTATION_UPDATE_APRIL_8_2026.md](../DOCUMENTATION_UPDATE_APRIL_8_2026.md) - Recent doc changes

---

## 📝 Document Maintenance

### When to Update

- **ARCHITECTURE_OVERVIEW.md**: Any major system design change
- **AUTHENTICATION_SESSION_FLOWS.md**: Changes to login flows or session logic
- **CLOUDSCALE_DATABASE_SCHEMA_V2.md**: Any table/field modifications
- **IMPLEMENTATION_NOTES.md**: Every significant code change
- **SESSION_ARCHITECTURE_GUIDE.md**: Session management changes

### How to Update

1. Edit the relevant document
2. Update "Last Updated" date
3. Add entry to IMPLEMENTATION_NOTES.md if code changed
4. Update this README's status table
5. Consider updating flow diagrams if logic changed

---

**Last Updated**: April 8, 2026  
**Maintained By**: Development Team
