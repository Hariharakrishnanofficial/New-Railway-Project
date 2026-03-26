# ✅ Agent Prompt Updates – Catalyst App Skillset Files

## 📋 Summary

Updated both Claude skillset documents with comprehensive **agent prompt sections** to guide AI-assisted development. These prompts define scope, capabilities, and best practices for working with Claude.

---

## 📄 Files Updated

### 1. **CLAUDE_CATALYST_SKILLSET.md** (Main Reference)
📍 **Location**: `f:\Railway Project Backend\Catalyst App\CLAUDE_CATALYST_SKILLSET.md`

#### New Sections Added:

**Section 2: 🤖 Claude Agent Prompt (System Instructions)**
- Copy-paste prompt for Claude
- Defines project context
- Lists capabilities (✅ what Claude can do)
- Lists limitations (❌ what Claude cannot do)
- Explains response format
- Links reference documents

**Section 7.2: 🤖 Extended Agent Instructions (Detailed Guidance)**
- How to ask Claude for help
- Effective prompt templates
- Example prompts (Frontend, Backend, Database)
- Response format expectations
- Task categories & expected responses
- Best practices (DO's and DON'Ts)
- Reference files to share
- Typical development workflow

---

### 2. **catalyst-frontend/claude.md** (Frontend Quick Guide)
📍 **Location**: `f:\Railway Project Backend\Catalyst App\catalyst-frontend\claude.md`

#### New Sections Added:

**Section 1: 🤖 Claude Agent Prompt (For Your Tasks)**
- Copy-paste prompt for frontend-specific work
- Project context
- Frontend capabilities
- Frontend limitations
- Sample tasks

**Section 2: 📋 Quick Ask Examples**
- Real examples of asking for help
- "Create a new train search page"
- "Fix API call errors"
- "Add form validation"
- "Optimize component performance"

**Section 3: 💬 How to Ask Claude for Help**
- Effective prompt structure with template
- Real-world examples (4 detailed scenarios)
- What to include in prompts
- What NOT to include
- What Claude will provide
- When Claude cannot help

---

## 🤖 Agent Prompt Overview

### Main Catalyst Prompt

```
You are a specialized AI assistant for the Railway Ticketing System - Catalyst App project.

CONTEXT:
- Full-stack Zoho Catalyst application (Client + Functions + CloudScale Database)
- Frontend: React 18.2.0 + Vite 5.1.0 (React SPA)
- Backend: Flask 2.3.2 wrapped in Catalyst Functions
- Database: Zoho CloudScale (14 tables, fully migrated)
- Current Status: Phase 4 testing/cutover (production deployment imminent)

YOUR CAPABILITIES:
✅ Frontend Development: React components, hooks, routing, forms, state management
✅ Backend Development: Flask routes, services, repositories, business logic
✅ Database: CloudScale queries, data models, table relationships
✅ API Integration: Axios calls, error handling, JWT authentication
✅ Build & Deployment: Vite config, Catalyst CLI, environment setup
✅ Troubleshooting: Debug code issues, CORS errors, API failures
✅ Code Examples: Provide working code for common tasks
✅ Refactoring: Optimize code, improve architecture

YOUR LIMITATIONS:
❌ Cannot access Zoho Catalyst platform directly (no credentials)
❌ Cannot modify production environment (requires platform access)
❌ Cannot handle infrastructure/DevOps tasks (AppSail configuration)
❌ Cannot make security policy decisions
❌ Cannot access actual database (only advise on schema/queries)
```

### Frontend Prompt

```
You are an AI assistant for the Catalyst Frontend project.

PROJECT:
- Railway Ticketing System - Catalyst App
- React 18.2.0 + Vite 5.1.0 SPA
- Location: catalyst-frontend/
- Build: produces build/ folder for Catalyst Client

YOUR ROLE:
Help with frontend development, debugging, and optimization.

CAN DO:
✅ Create/modify React components
✅ Set up routing with React Router
✅ API integration with Axios
✅ Form handling (Formik + Yup)
✅ Styling with CSS Variables
✅ State management (hooks, context)
✅ Build optimization (Vite)
✅ Local testing & debugging

CANNOT DO:
❌ Modify backend (Flask)
❌ Change database schema
❌ Deploy to Catalyst (requires platform access)
❌ Manage environment credentials
```

---

## 💬 How to Use These Prompts

### Method 1: Copy-Paste at Start of Conversation
When beginning work on the Catalyst App:
1. Open `CLAUDE_CATALYST_SKILLSET.md` → Find agent prompt section
2. Copy the prompt text
3. Paste into your conversation with Claude
4. Claude now has full context

### Method 2: Reference in Your Question
```
"Based on the Claude Agent Prompt in CLAUDE_CATALYST_SKILLSET.md:
[your question]"
```

### Method 3: Use Template
Follow the "How to Ask Claude" section:
```
I'm working on [Feature] in the Catalyst App.

Context:
- File: [path]
- What I'm trying: [description]
- What I've tried: [previous attempts]

Can you help with [specific ask]?
```

---

## 📝 Example Prompts for Common Tasks

### Create a New React Component
```
I need help creating a new component in catalyst-frontend.

File: src/pages/NewFeaturePage.jsx

Requirements:
- Display a list of [items]
- Add search/filter functionality
- Include create/edit modal
- Use Formik + Yup for validation
- Call GET /api/new-feature endpoint

Based on the Claude Agent Prompt: Can you provide the component code?
```

### Debug Backend Issue
```
My Flask endpoint is returning 500 errors.

Context:
- File: functions/catalyst_backend/routes/bookings.py
- Endpoint: POST /api/bookings/:id/confirm
- Error: "CloudScale query failed"
- Using: zcatalyst-sdk

Console error:
```
[paste error here]
```

Based on the Catalyst App architecture: Can you help debug?
```

### Fix CORS Error
```
Getting CORS error in frontend when calling backend.

Context:
- Frontend: http://localhost:5173 (dev)
- Backend: http://localhost:9000
- Error: Access-Control-Allow-Origin missing

Based on the skillset: Can you check what's misconfigured?
```

---

## ✨ Key Features of Updated Prompts

### Clear Scope Definition
✅ Explicitly states what Claude can/cannot do  
✅ Prevents out-of-scope requests  
✅ Saves time and confusion

### Context Provided
✅ Tech stack explicitly stated  
✅ Project structure explained  
✅ File locations clear
✅ Current status noted

### Guidance for Interactions
✅ How to format questions  
✅ What to include in prompts  
✅ What Claude will provide  
✅ When to escalate

### Practical Examples
✅ Real-world prompts  
✅ Common task templates  
✅ Troubleshooting scenarios  
✅ Integration steps

---

## 🎯 Usage Scenarios

### Scenario 1: Frontend Development
1. Read `catalyst-frontend/claude.md` → Agent Prompt section
2. Use prompt when asking for React component help
3. Reference "Quick Ask Examples" for inspiration
4. Follow "How to Ask Claude" guidelines

### Scenario 2: Backend Development
1. Read `CLAUDE_CATALYST_SKILLSET.md` → Agent Prompt section
2. Use prompt for Flask endpoint creation
3. Reference "Extended Agent Instructions"
4. Include file path and requirements

### Scenario 3: Debugging Issues
1. Read "When Claude Cannot Help" section
2. Check scope (is it in Claude's capabilities?)
3. Format question using template
4. Include error messages and context

### Scenario 4: Code Review/Refactoring
1. Share relevant code snippet
2. Ask specific question (performance, style, etc)
3. Reference applicable guidelines
4. Accept Claude's suggestions with reasoning

---

## 📚 Reference Links

| Purpose | File | Section |
|---------|------|---------|
| **Full Context** | CLAUDE_CATALYST_SKILLSET.md | Section 2: Agent Prompt |
| **Frontend Help** | catalyst-frontend/claude.md | Section 1: Agent Prompt |
| **How to Ask** | catalyst-frontend/claude.md | Section 3: How to Ask Claude |
| **Extended Guidance** | CLAUDE_CATALYST_SKILLSET.md | Section 7.2: Extended Instructions |
| **Scope Definition** | CLAUDE_CATALYST_SKILLSET.md | Section 8: What Claude Can Help |
| **Examples** | catalyst-frontend/claude.md | Section 2: Quick Ask Examples |

---

## ✅ What Changed

### Before
- ❌ Minimal guidance on interacting with Claude
- ❌ No explicit scope boundaries
- ❌ Limited examples of how to ask
- ❌ No prompt template provided

### After
- ✅ Comprehensive agent prompts (copy-paste ready)
- ✅ Clear capabilities & limitations defined
- ✅ Multiple real-world examples
- ✅ Prompt templates provided
- ✅ Guidelines for effective collaboration
- ✅ Integration instructions
- ✅ Troubleshooting guidance
- ✅ Best practices documented

---

## 🚀 Next Steps

1. **Copy Agent Prompt**: When starting new work, copy relevant prompt
2. **Use Templates**: Follow "How to Ask" templates for consistency
3. **Reference Examples**: Use quick examples to inspire prompts
4. **Follow Guidelines**: Adhere to DO's and DON'Ts
5. **Share Context**: Include file paths, requirements, error messages
6. **Iterate**: Refine questions based on Claude's responses

---

## 📍 File Locations

| Document | Path |
|----------|------|
| **Main Skillset** | `f:\Railway Project Backend\Catalyst App\CLAUDE_CATALYST_SKILLSET.md` |
| **Frontend Skillset** | `f:\Railway Project Backend\Catalyst App\catalyst-frontend\claude.md` |
| **This Summary** | `f:\Railway Project Backend\Catalyst App\AGENT_PROMPT_UPDATES.md` |

---

## 🎓 Quick Tips

**For Best Results:**
1. Start with agent prompt → Sets context
2. Include specific file paths → Helps Claude locate code
3. Share error messages → Speeds debugging
4. Mention constraints → Clarifies requirements
5. Ask for test steps → Validates solutions
6. Request explanations → Builds understanding

**Common Questions:**
- **"How detailed should my prompt be?"** → Very! More context = better answers
- **"Should I include code?"** → Yes, if it helps explain the issue
- **"Can Claude make production changes?"** → No, requires platform access
- **"What if Claude's answer doesn't work?"** → Refine the prompt with more details

---

**Update Date**: 2026-03-22  
**Status**: ✅ Complete  
**Files Modified**: 2  
**New Sections Added**: 5  
**Audience**: Developers, AI/Claude Users  
**Maintained By**: Railway Ticketing System Team
