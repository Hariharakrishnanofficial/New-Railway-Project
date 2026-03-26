# Claude Copilot Skillset – Catalyst Frontend (React + Vite)

## 🤖 Claude Agent Prompt (For Your Tasks)

**Copy & use this prompt when working with Claude:**

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
✅ Local testing
✅ Bug fixing & debugging
✅ Code refactoring

CANNOT DO:
❌ Modify backend (Flask)
❌ Change database schema
❌ Deploy to Catalyst (requires platform access)
❌ Manage environment credentials
❌ Infrastructure setup

WHEN I ASK FOR HELP:
1. Provide working code examples
2. Reference specific files (src/pages/, src/components/, etc)
3. Include testing/verification steps
4. Suggest performance optimizations
5. Link to relevant documentation

SAMPLE TASKS:
- Create a new CRUD page
- Fix API call errors
- Add form validation
- Debug component state
- Optimize performance
- Update styling
```

---

## 🎯 Quick Overview

**Project**: Railway Ticketing System - Catalyst Client  
**Framework**: React 18.2.0 + Vite 5.1.0  
**Type**: Single Page Application (SPA)  
**Location**: `f:\Railway Project Backend\Catalyst App\catalyst-frontend`  
**Build Output**: `build/` folder (for Catalyst Client deployment)

---

## 📋 Quick Ask Examples

**"Create a new train search page"**
```
I need a new search page with:
- Form: from/to stations, date, class
- Results: display available trains in table
- Integration: call GET /api/search/trains

Can you provide SearchPage.jsx component?
```

**"Fix API call errors in booking page"**
```
BookingsPage is showing 401 errors when creating bookings.
Backend is at http://localhost:9000
Token is stored in sessionStorage.rail_access_token

Can you check the API setup and auth headers?
```

**"Add form validation to user creation"**
```
I'm adding email validation to the create user form.
Using Formik + Yup.

Requirements:
- Email must be valid format
- Phone must be 10 digits
- Role must be selected

Can you write the validation schema?
```

**"Optimize component performance"**
```
TrainsTable with 1000+ rows is slow.
Currently using .map() to render all rows.

Can you suggest optimizations (pagination, lazy load, etc)?
```

---

## 🏗️ Technology Stack

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| **Framework** | React | 18.2.0 | Component-based UI |
| **Bundler** | Vite | 5.1.0 | Lightning-fast build |
| **Router** | React Router | 6.22.0 | Client-side navigation |
| **HTTP** | Axios | 1.6.7 | API calls to backend |
| **Forms** | Formik + Yup | 2.4.5 + 1.3.3 | Form validation |
| **Dates** | date-fns | 3.3.1 | Date handling |
| **Styling** | CSS Variables | - | Custom design system |

---

## 📁 Project Structure

```
catalyst-frontend/
│
├── src/
│   ├── main.jsx                 # React entry point
│   ├── App.jsx                  # Root component + routing
│   │
│   ├── components/
│   │   ├── UI.jsx               # Design system (Icon, Badge, Button, Modal, etc)
│   │   ├── Layout.jsx           # App layout (Sidebar, TopBar, Breadcrumb)
│   │   ├── CRUDTable.jsx        # Reusable CRUD table
│   │   └── [other components]
│   │
│   ├── context/
│   │   ├── ToastContext.jsx     # Global notifications
│   │   └── [other contexts]
│   │
│   ├── hooks/
│   │   ├── useApi.js            # Fetch data hook
│   │   ├── useMutation.js       # Mutate data hook
│   │   └── [other hooks]
│   │
│   ├── pages/
│   │   ├── LoginPage.jsx        # Authentication
│   │   ├── DashboardPage.jsx    # Overview/home
│   │   ├── TrainsPage.jsx       # Train management
│   │   ├── StationsPage.jsx     # Station management
│   │   ├── UsersPage.jsx        # User management
│   │   ├── BookingsPage.jsx     # Booking management
│   │   ├── SearchPage.jsx       # Train search + booking
│   │   ├── ReportsPage.jsx      # Analytics
│   │   ├── AIPage.jsx           # Chatbot & AI features
│   │   └── [40+ pages total]
│   │
│   ├── services/
│   │   └── api.js               # Axios setup + endpoints
│   │
│   └── styles/
│       └── global.css           # CSS variables, animations
│
├── public/
│   ├── index.html               # Main HTML
│   ├── favicon.ico
│   └── [assets]
│
├── build/                       # Production output (after `vite build`)
│   ├── index.html
│   ├── 404.html                 # SPA fallback
│   ├── assets/
│   │   ├── index-*.js
│   │   └── index-*.css
│   └── favicon.ico
│
├── package.json                 # Dependencies & scripts
├── vite.config.js               # Vite configuration
├── .env.development             # Dev environment
├── .env.production              # Production environment
└── README.md
```

---

## 🚀 Development & Build

### Scripts

```json
{
  "scripts": {
    "dev": "vite",                  // Start dev server
    "build": "vite build && ...",   // Build for production
    "preview": "vite preview"       // Preview built app
  }
}
```

### Workflows

**Development**:
```bash
cd catalyst-frontend
npm install              # First time only
npm run dev             # Starts http://localhost:5173
# Edit files, HMR reloads instantly
```

**Production Build**:
```bash
npm run build
# Generates optimized build in build/ folder
# Also creates build/404.html for SPA routing
```

**Preview Built App**:
```bash
npm run preview
# Serves build/ locally for testing
```

---

## 🔌 API Integration

### API Configuration

**File**: `src/services/api.js`

```javascript
// Axios client configured with:
// 1. Base URL from environment
// 2. JWT token from sessionStorage
// 3. Default headers (Content-Type, Authorization)
// 4. Error interceptors
```

### Environment Setup

**`.env.development`**:
```
VITE_API_BASE_URL=http://localhost:9000
```

**`.env.production`**:
```
VITE_API_BASE_URL=https://railway-project-backend-*.catalystappsail.in
```

### Using API in Components

```javascript
// In any page/component:
import { useApi, useMutation } from '../hooks/useApi'

// Fetch data
const { data, loading, error, refetch } = useApi('/api/trains')

// Mutate data
const { mutate, loading } = useMutation('POST', '/api/bookings')

// Call it
await mutate({ train_id: 123, date: '2026-03-22' })
```

---

## 🎨 UI Components

### Available in `UI.jsx`

```javascript
// All imported from components/UI.jsx
<Icon name="search" />
<Badge label="Active" variant="success" />
<Button onClick={handler}>Click me</Button>
<Input placeholder="Search..." />
<Modal isOpen={true}>Content</Modal>
<Toast message="Success!" type="success" />
// ... and more
```

### Design System

CSS Variables (in `styles/global.css`):
```css
--primary: #2563eb          /* Blues */
--success: #10b981          /* Greens */
--danger: #ef4444           /* Reds */
--warning: #f59e0b          /* Ambers */
--gray-50 to --gray-900     /* Grays */
```

---

## 💬 How to Ask Claude for Help

### Effective Prompt Structure

**Template:**
```
I need help with [component/feature/issue] in catalyst-frontend.

Context:
- File: [src/pages/... or src/components/...]
- What I'm trying to do: [clear description]
- Current behavior: [what's happening]
- Expected behavior: [what should happen]
- Tech used: [React hooks, Formik, Axios, etc]

Can you [specific request]?
```

### Real Examples

**Example 1: Create Component**
```
I need help creating a new booking confirmation page.

Context:
- File: src/pages/BookingConfirmPage.jsx
- Need to: Display booking details, show fare breakdown, confirm booking
- Should call: POST /api/bookings/:id/confirm
- Display: Train details, passenger list, total price

Can you provide the component code with loading states and error handling?
```

**Example 2: Debug Issue**
```
My login page isn't saving the JWT token.

Context:
- File: src/pages/LoginPage.jsx
- Using: axios.post('/api/auth/login', credentials)
- Backend returns: { token: "jwt..." }
- Token should be in: sessionStorage.rail_access_token
- Problem: Token not persisting after refresh

Console error: None (silent failure)

Can you check the token storage code and fix it?
```

**Example 3: Optimize Code**
```
TrainsTable is rendering 500 rows and it's slow.

Context:
- File: src/pages/TrainsPage.jsx
- Using: .map() to render all rows
- No pagination
- API returns all results at once

Can you suggest optimization (pagination, lazy load, or virtual scroll)?
```

**Example 4: Styling Issue**
```
Button styling isn't responsive on mobile.

Context:
- File: src/components/UI.jsx or specific page
- Current: Fixed button width 200px
- Problem: Overlaps on mobile screens
- Using: CSS Variables (--primary, --danger, etc)

Can you make buttons responsive and provide the CSS?
```

### What to Include

✅ **DO INCLUDE:**
- Exact file path
- What you're trying to accomplish
- Relevant code (if available)
- Error messages or console output
- What you've already tried
- Constraints (must use Formik, must be accessible, etc)

❌ **DON'T INCLUDE:**
- Backend changes (that's backend team)
- Database schema changes
- Environment credentials
- Production deployment requests
- Infrastructure setup

### What Claude Will Provide

When you ask for help, expect:

1. **Explanation** - Why/how the solution works
2. **Code** - Working implementation ready to use
3. **Integration** - Where/how to add to your project
4. **Testing** - How to verify it works
5. **Troubleshooting** - Common issues & fixes
6. **Performance** - Optimization notes if applicable

### When Claude Can't Help

🚫 **Backend Issues** → Ask backend team  
🚫 **Database Changes** → Ask database team  
🚫 **Deployment** → Requires Catalyst platform access  
🚫 **Credentials** → Security team only  
🚫 **Infrastructure** → DevOps/Catalyst admin only  

---

## 📝 Common Tasks

### Create New Page

**Step 1**: Create file `src/pages/NewFeaturePage.jsx`

```javascript
import { useApi, useMutation } from '../hooks/useApi'
import { useToast } from '../context/ToastContext'
import CRUDTable from '../components/CRUDTable'
import Modal from '../components/Modal'
import Button from '../components/Button'

export default function NewFeaturePage() {
  const { data, loading, refetch } = useApi('/api/new-feature')
  const { mutate: create } = useMutation('POST', '/api/new-feature')
  const { toast } = useToast()

  return (
    <div>
      {/* Header */}
      <h1>New Feature</h1>
      
      {/* Table */}
      <CRUDTable data={data} loading={loading} />
      
      {/* Actions */}
      <Button onClick={() => {/* show modal */}}>Create</Button>
    </div>
  )
}
```

**Step 2**: Add route in `src/App.jsx`
```javascript
import NewFeaturePage from './pages/NewFeaturePage'

// In <Routes>:
<Route path="/new-feature" element={<NewFeaturePage />} />
```

**Step 3**: Add navigation link in `src/components/Layout.jsx`
```javascript
{ path: '/new-feature', label: 'New Feature', icon: 'icon-name' }
```

### Add New API Endpoint Call

**File**: `src/services/api.js`

```javascript
export const endpoints = {
  // Existing...
  
  // New:
  newFeature: {
    list: '/new-feature',
    get: (id) => `/new-feature/${id}`,
    create: '/new-feature',
    update: (id) => `/new-feature/${id}`,
    delete: (id) => `/new-feature/${id}`,
  }
}
```

### Handle Form Submission

Using Formik + Yup:

```javascript
import { Formik, Form, Field, ErrorMessage } from 'formik'
import * as Yup from 'yup'

const validationSchema = Yup.object({
  email: Yup.string().email().required(),
  name: Yup.string().required(),
})

<Formik
  initialValues={{ email: '', name: '' }}
  validationSchema={validationSchema}
  onSubmit={async (values) => {
    await mutate(values)
    toast.success('Created!')
  }}
>
  {({ errors, touched }) => (
    <Form>
      <Field name="email" type="email" />
      <ErrorMessage name="email" />
      
      <Field name="name" />
      <ErrorMessage name="name" />
      
      <button type="submit">Submit</button>
    </Form>
  )}
</Formik>
```

---

## 🧪 Testing Locally

```bash
# 1. Make sure backend is running
# Backend: http://localhost:9000

# 2. Start frontend dev server
npm run dev

# 3. Navigate to http://localhost:5173

# 4. Test features:
# - Login works
# - Pages load
# - API calls succeed
# - Forms submit
# - Error handling works
```

---

## 📦 Building for Deployment

```bash
npm run build

# Output structure:
build/
├── index.html           # SPA entry (served for all routes)
├── 404.html             # Fallback for client-side routing
├── assets/
│   ├── index-abc123.js  # Minified React bundle
│   ├── index-def456.css # Minified styles
│   └── ...
└── favicon.ico
```

### Upload to Catalyst Client

1. Build: `npm run build`
2. Go to Catalyst Dashboard → Client app
3. Upload `build/` folder
4. Wait 2-5 minutes
5. Access at Catalyst domain

---

## ⚡ Performance Tips

### Optimization Checklist

- [ ] Code splitting (lazy load pages with `React.lazy`)
- [ ] Image optimization (use `<picture>` or next-gen formats)
- [ ] Caching headers (configured in Catalyst Client)
- [ ] Bundle size (check with `vite build --stats`)
- [ ] Unused dependencies (run `npm audit`)

### Common Optimizations

```javascript
// Lazy load pages
import { lazy, Suspense } from 'react'

const TrainsPage = lazy(() => import('./pages/TrainsPage'))

// In routes:
<Suspense fallback={<Loading />}>
  <TrainsPage />
</Suspense>

// Memoize expensive components
import { memo } from 'react'
export default memo(MyComponent)

// Use useCallback for handlers
const handleClick = useCallback(() => {
  // handler code
}, [dependencies])
```

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| **"Cannot find module"** | Run `npm install` |
| **Blank page** | Check browser console, verify 404.html exists |
| **API calls fail** | Verify backend URL in .env, check CORS |
| **HMR not working** | Restart dev server, clear cache |
| **Build fails** | Check for TypeScript errors, fix imports |
| **Slow build** | Check bundle size, remove unused dependencies |

---

## 📚 Key Files Reference

| File | Purpose | Edit When |
|------|---------|-----------|
| `src/App.jsx` | Routing setup | Adding new routes |
| `src/services/api.js` | API client | Adding new endpoints |
| `src/components/Layout.jsx` | App layout | Changing navigation |
| `src/context/ToastContext.jsx` | Notifications | Modifying toast behavior |
| `src/hooks/useApi.js` | Data fetching | Adding new hook features |
| `vite.config.js` | Build config | Changing build settings |
| `.env.production` | Prod settings | Before production build |

---

## 🔗 Related Files

- **Backend**: `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend\`
- **Main Skillset**: `f:\Railway Project Backend\Catalyst App\CLAUDE_CATALYST_SKILLSET.md`
- **Database Schema**: `f:\Railway Project Backend\Catalyst App\CLOUDSCALE_DATABASE_SCHEMA.md`

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-22  
**Status**: Production-Ready  
**Maintained By**: Railway Ticketing System Team
