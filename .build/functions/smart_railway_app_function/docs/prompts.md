🔹 Prompt 1: Analyze Existing Catalyst App

Task:
Analyze a Zoho Catalyst application folder.

Instructions:

The project contains:
Frontend
Backend
Database (Zoho Creator)
Ignore standard/framework-generated folders such as:
Node.js-related folders (e.g., node_modules)
Python-related folders (e.g., venv, __pycache__)
Focus only on:
Custom business logic
API structure
Database interactions
Folder architecture

Output अपेक्षित:

High-level architecture overview
Key modules and their responsibilities
Data flow between frontend, backend, and database
Any inefficiencies or optimization opportunities
🔹 Prompt 2: Migration Architecture Design

Task:
Design a new architecture based on an existing Catalyst app.

Target Stack:

Frontend: React.js
Backend: Flask
Database: Cloudscale

References Provided:

cloudscale_database_scheme.md (sample schema)
Sample frontend working code

Instructions:

Map existing Catalyst components to the new stack:
Catalyst backend → Flask APIs
Zoho Creator DB → Cloudscale schema
Existing frontend → React structure
Suggest:
Folder structure for both frontend and backend
API design (REST endpoints)
Database integration approach
Keep the design scalable and modular

Output अपेक्षित:

Proposed system architecture
Folder structure (frontend + backend)
API endpoint list
Database mapping strategy
🔹 Prompt 3: Code-Level Guidance

Task:
Provide implementation guidance for the new stack.

Instructions:

Use:
React for frontend
Flask for backend
Cloudscale as database
Refer to:
Sample frontend code (for structure/style)
cloudscale_database_scheme.md (for DB design)

Focus Areas:

API integration (React ↔ Flask)
Database CRUD operations
Environment configuration
Best practices for performance and scalability

Output अपेक्षित:

Sample code snippets (API + frontend calls)
Integration workflow
Recommended libraries/tools
🔹 Prompt 4: Optimization & Improvements

Task:
Suggest improvements over the original Catalyst implementation.

Instructions:

Compare:
Catalyst architecture vs new stack
Identify:
Bottlenecks
Redundant logic
Performance issues

Output अपेक्षित:

Optimization suggestions
Improved design patterns
Scalability recommendations