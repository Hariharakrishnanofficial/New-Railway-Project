# 🤖 Smart Railway AI Agents Guide

> **Your specialized AI assistants for the Smart Railway Ticketing System**

## Quick Start

In VS Code Copilot Chat, type `@agent-name` followed by your request:

```
@api-developer Create an endpoint for train search
@debugger Fix the 500 error on /employees
```

---

## 📋 Agent Overview

| Agent | Best For | Tools |
|-------|----------|-------|
| [@architect](#architect) | Planning features, designing systems | read, search |
| [@explore](#explore) | Finding code, understanding patterns | read, search |
| [@api-developer](#api-developer) | Building Flask APIs | read, edit, create, run |
| [@react-developer](#react-developer) | Building React UI | read, edit, create, run |
| [@database-expert](#database-expert) | ZCQL queries, schemas | read, edit, search, run |
| [@security-reviewer](#security-reviewer) | Security audits | read, search |
| [@tester](#tester) | Writing tests | read, edit, create, run |
| [@debugger](#debugger) | Fixing bugs | read, edit, search, run |

---

## 🏗️ @architect

**Senior Architecture Engineer** - Plans features without implementing them.

### When to Use
- Planning a new feature
- Designing database schemas
- Creating API specifications
- Breaking down complex tasks
- Reviewing technical decisions

### Example Prompts
```
@architect Plan the ticket cancellation and refund system

@architect Design the database schema for train scheduling

@architect Break down the employee management feature into tasks

@architect Review the booking flow architecture
```

### Output
- Architecture diagrams (ASCII/Mermaid)
- Database schema designs
- API endpoint specifications
- Ordered task breakdowns
- Security considerations

---

## 🔍 @explore

**Fast Read-Only Explorer** - Finds code and explains how things work.

### When to Use
- Finding where something is implemented
- Understanding existing patterns
- Locating specific files
- Learning how a feature works

### Example Prompts
```
@explore How does session authentication work?

@explore Find all API endpoints for bookings

@explore Where is password hashing implemented?

@explore What tables are used for train management?
```

### Output
- File locations with descriptions
- Key findings summary
- Relevant code snippets

---

## 🔧 @api-developer

**Senior Flask API Developer** - Builds backend features.

### When to Use
- Creating new API endpoints
- Adding business logic to services
- Building validators
- Modifying existing routes

### Example Prompts
```
@api-developer Create a train search API with filters for date, source, destination

@api-developer Add a booking cancellation endpoint with refund calculation

@api-developer Create a service to calculate dynamic fares

@api-developer Add pagination to the /admin/employees endpoint
```

### Key Patterns It Follows
```python
# Standard route pattern
@blueprint.route('/endpoint', methods=['POST'])
@require_session_admin
def handler():
    try:
        data = request.get_json()
        result = service.process(data)
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

---

## ⚛️ @react-developer

**Senior React Developer** - Builds frontend features.

### When to Use
- Creating new pages
- Building UI components
- Integrating APIs
- Managing state with hooks
- Styling with Tailwind CSS

### Example Prompts
```
@react-developer Create an admin dashboard page showing employee statistics

@react-developer Build a train search form with autocomplete for stations

@react-developer Create a booking confirmation component

@react-developer Add a dark mode toggle to the app
```

### Key Patterns It Follows
```jsx
// Standard component pattern
const ComponentName = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  
  useEffect(() => { loadData(); }, []);
  
  if (loading) return <div>Loading...</div>;
  
  return <div className="p-4">...</div>;
};
```

---

## 🗄️ @database-expert

**CloudScale ZCQL Specialist** - Handles all database work.

### When to Use
- Writing ZCQL queries
- Designing table schemas
- Debugging database errors
- Optimizing slow queries
- Planning data migrations

### Example Prompts
```
@database-expert Write a query to find available seats for a train on a date

@database-expert Design a schema for the Reviews table

@database-expert Why am I getting "Column not found" error?

@database-expert Optimize this booking search query
```

### ZCQL Quick Reference
```sql
-- Always use ROWID for primary key
SELECT ROWID, Column1 FROM TableName WHERE Condition

-- Pagination
SELECT * FROM TableName ORDER BY CREATEDTIME DESC LIMIT 20 OFFSET 0

-- Count
SELECT COUNT(ROWID) as cnt FROM TableName WHERE Status = 'Active'
```

---

## 🔒 @security-reviewer

**Security Auditor** - Reviews code for vulnerabilities (read-only).

### When to Use
- Auditing authentication logic
- Reviewing authorization checks
- Finding injection vulnerabilities
- Checking sensitive data handling
- Pre-deployment security review

### Example Prompts
```
@security-reviewer Review the session_auth.py for vulnerabilities

@security-reviewer Audit the admin employee endpoints

@security-reviewer Check the booking flow for security issues

@security-reviewer Review password handling in employee_service.py
```

### Output Format
```markdown
## Security Review: [Feature]

### Summary
Risk Level: LOW | MEDIUM | HIGH | CRITICAL

### Findings
#### [SEVERITY] Finding Title
- Location: file.py:line
- Issue: Description
- Impact: What could happen
- Fix: Recommendation
```

---

## 🧪 @tester

**QA Tester** - Writes tests and validates features.

### When to Use
- Writing pytest unit tests
- Creating integration tests
- Testing APIs with curl
- Generating test data
- Validating feature requirements

### Example Prompts
```
@tester Write tests for the employee CRUD endpoints

@tester Create curl commands to test the booking flow

@tester Generate test data for the trains table

@tester Write pytest tests for session_service.py
```

### Test Patterns
```bash
# Quick API test with curl
curl -X POST "http://localhost:3000/server/smart_railway_app_function/endpoint" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"field": "value"}'
```

```python
# Pytest pattern
def test_create_success():
    result = service.create({'name': 'Test'})
    assert result['status'] == 'success'
```

---

## 🐛 @debugger

**Bug Hunter** - Investigates and fixes errors.

### When to Use
- Fixing 500 Internal Server Errors
- Debugging authentication issues
- Tracing database failures
- Fixing validation errors
- Understanding error logs

### Example Prompts
```
@debugger Fix: POST /admin/employees returns 500

@debugger Why is login returning "Invalid credentials" for a valid user?

@debugger Debug: "MANDATORY_MISSING: Column Employee_ID" error

@debugger The session is not persisting between requests
```

### Common Error Patterns
| Error | Typical Cause |
|-------|--------------|
| 400 Bad Request | Missing required field |
| 401 Unauthorized | Missing/invalid session |
| 403 Forbidden | User lacks permission |
| 404 Not Found | Wrong URL or missing record |
| 500 Server Error | Unhandled exception |

---

## 🎯 Agent Selection Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                     What do you need to do?                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   UNDERSTAND            IMPLEMENT              FIX/TEST
        │                     │                     │
   ┌────┴────┐           ┌────┴────┐           ┌────┴────┐
   │         │           │         │           │         │
   ▼         ▼           ▼         ▼           ▼         ▼
@explore  @architect  @api-dev  @react-dev  @debugger  @tester
   │         │           │         │           │         │
   │         │           │         │           │         │
"Find     "Plan      "Build    "Build      "Fix      "Test
 code"    feature"   backend"  frontend"   bugs"     this"
```

---

## 💡 Pro Tips

### 1. Chain Agents for Complex Tasks
```
1. @architect Plan the feature first
2. @api-developer Build the backend
3. @react-developer Build the frontend
4. @tester Write tests
5. @security-reviewer Audit the code
```

### 2. Be Specific in Prompts
```
❌ Bad:  @api-developer Create booking API
✅ Good: @api-developer Create POST /bookings endpoint that accepts trainId, 
         date, passengers array, and returns PNR with seat assignments
```

### 3. Provide Context
```
@debugger Fix this error:
POST /admin/employees returns 500
Error: "MANDATORY_MISSING: Column Department is mandatory"
I'm trying to create an employee with {fullName, email, role}
```

### 4. Use @explore First When Unsure
```
@explore How are employees created in this project?
# Then use @api-developer with that knowledge
```

---

## 📁 Agent Files Location

```
.github/agents/
├── architect.agent.md       # Feature planning
├── explore.agent.md         # Code exploration
├── api-developer.agent.md   # Flask backend
├── react-developer.agent.md # React frontend
├── database-expert.agent.md # ZCQL/CloudScale
├── security-reviewer.agent.md # Security audits
├── tester.agent.md          # Testing
└── debugger.agent.md        # Bug fixing
```

---

## 🔄 Workflow Examples

### Example 1: Add New Feature
```
@architect Plan a train review/rating feature
    ↓
@database-expert Design the Reviews table schema
    ↓
@api-developer Create CRUD endpoints for reviews
    ↓
@react-developer Build the review submission UI
    ↓
@tester Write tests for the review feature
    ↓
@security-reviewer Audit the review endpoints
```

### Example 2: Fix Production Bug
```
@debugger Investigate: Users getting 403 on /bookings
    ↓
@explore Find how booking authorization works
    ↓
@debugger Fix the authorization check
    ↓
@tester Verify the fix with test cases
```

### Example 3: Understand Codebase
```
@explore How does OTP verification work?
    ↓
@explore Where are emails sent from?
    ↓
@architect Document the authentication flow
```

---

**Happy Coding! 🚀**
