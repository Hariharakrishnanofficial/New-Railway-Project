# Gemini 3 Flash — Browser Automation Prompts
## Zoho Catalyst Cloud Scale · 14 Tables · Environment Variables · Verification
## Railway Ticketing System

---

## HOW TO USE THIS FILE

Feed these prompts to Gemini 3 Flash with Computer Use enabled.
Run them in order — one prompt at a time.
Wait for "Report:" confirmation before running the next prompt.

**Required setup before running:**
- Gemini 3 Flash with Computer Use (browser environment)
- Playwright or equivalent browser driver connected
- Zoho Catalyst account logged in, or credentials ready
- Project already created: railway-ticketing-system

**Run order:**
1. MASTER ORCHESTRATOR (once, sets context)
2. PROMPTS 1–14 (one per table, in order)
3. PROMPT 15 (environment variables, all 9 functions)
4. PROMPT 16 (verification, run last)

---

## MASTER ORCHESTRATOR PROMPT

```
You are a browser automation agent. Your task is to create all 14 database tables
in the Zoho Catalyst Cloud Scale Data Store console.

STARTING URL: https://console.catalyst.zoho.com

NAVIGATION PATH to reach Data Store:
1. Log in if prompted
2. Click your project name: railway-ticketing-system
3. In the left sidebar click "Cloud Scale"
4. Click "Data Store"
5. You are now on the table list page

HOW TO CREATE ONE TABLE (follow this for every table):
Step 1: Click the "+" or "Create Table" button
Step 2: Type the table name exactly as given — case-sensitive
Step 3: Click "Add Column" for each column in the list
Step 4: For each column:
  a. Type the column name exactly as given
  b. Click the Type dropdown — select the mapped type
  c. If Required = Yes → toggle the Required switch ON
  d. If Unique = Yes → toggle the Unique switch ON
  e. If Default = a value → enter that value in the Default field
Step 5: DO NOT add a primary key column — Catalyst auto-generates ROWID
Step 6: Click "Save" or "Create"
Step 7: Verify the table appears in the table list

TYPE MAPPING — always use the Catalyst UI name:
  STRING / TEXT / VARCHAR → select "Text"
  BIGINT / INT / INTEGER  → select "Number"
  DOUBLE / DECIMAL / FLOAT → select "Number"
  BOOLEAN                 → select "Boolean"
  DATE                    → select "Date"
  DATETIME / TIMESTAMP    → select "DateTime"
  JSON                    → select "Text" (Long text toggle ON)

DRAG AND DROP — for reordering columns:
  Hover over the 6-dot drag handle on the left of each column row
  Hold left mouse button, drag to new position, release

After all 14 tables are created, report:
  - Table name
  - Number of columns created
  - Any column that failed to save

Now start with TABLE 1: Users
```

---

## PROMPT 1 — Table: Users

```
Navigate to: https://console.catalyst.zoho.com
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Users
(Exact case, no spaces)

Click "Add Column" and add these columns in this exact order.
DO NOT add user_id — Catalyst creates ROWID automatically.

COLUMN 1:
  Name: email
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: password_hash
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: full_name
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: phone
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: role
  Type: Text
  Required: NO
  Unique: NO
  Default: passenger

COLUMN 6:
  Name: status
  Type: Text
  Required: NO
  Unique: NO
  Default: active

COLUMN 7:
  Name: date_of_birth
  Type: Date
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: gender
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 10:
  Name: updated_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 11:
  Name: last_login
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

After adding all 11 columns, click Save.
Verify "Users" appears in the table list.
Report: "Users table created — 11 columns"
```

---

## PROMPT 2 — Table: Stations

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Stations

Add these columns. DO NOT add station_id.

COLUMN 1:
  Name: station_code
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: station_name
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: city
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: state
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: country
  Type: Text
  Required: NO
  Unique: NO
  Default: India

COLUMN 6:
  Name: latitude
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: longitude
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: timezone
  Type: Text
  Required: NO
  Unique: NO
  Default: Asia/Kolkata

COLUMN 9:
  Name: platform_count
  Type: Number
  Required: NO
  Unique: NO
  Default: 4

COLUMN 10:
  Name: is_major_station
  Type: Boolean
  Required: NO
  Unique: NO
  Default: false

COLUMN 11:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Stations table created — 11 columns"
```

---

## PROMPT 3 — Table: Trains

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Trains

Add these columns. DO NOT add train_id.

COLUMN 1:
  Name: train_number
  Type: Number
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: train_name
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: train_type
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: source_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: destination_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: departure_time
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: arrival_time
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: duration_minutes
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: total_coaches
  Type: Number
  Required: NO
  Unique: NO
  Default: 16

COLUMN 10:
  Name: status
  Type: Text
  Required: NO
  Unique: NO
  Default: active

COLUMN 11:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Trains table created — 11 columns"
```

---

## PROMPT 4 — Table: Train_Routes

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Train_Routes

Add these columns. DO NOT add route_id.

COLUMN 1:
  Name: train_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: sequence
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: arrival_time
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: departure_time
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: halt_duration_minutes
  Type: Number
  Required: NO
  Unique: NO
  Default: 5

COLUMN 7:
  Name: distance_from_source_km
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: platform_number
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Train_Routes table created — 9 columns"
```

---

## PROMPT 5 — Table: Coach_Layouts

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Coach_Layouts

Add these columns. DO NOT add layout_id.

COLUMN 1:
  Name: coach_type_code
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: coach_type_name
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: total_berths
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: layout_json
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)
  Action: If a "Long Text" toggle is visible, enable it

COLUMN 5:
  Name: amenities_json
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)
  Action: If a "Long Text" toggle is visible, enable it

COLUMN 6:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Coach_Layouts table created — 6 columns"
```

---

## PROMPT 6 — Table: Train_Inventory

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Train_Inventory

Add these columns. DO NOT add inventory_id.

COLUMN 1:
  Name: train_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: coach_type_code
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: coach_number
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: total_seats
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: available_seats
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: is_active
  Type: Boolean
  Required: NO
  Unique: NO
  Default: true

COLUMN 7:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Train_Inventory table created — 7 columns"
```

---

## PROMPT 7 — Table: Fares

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Fares

Add these columns. DO NOT add fare_id.

COLUMN 1:
  Name: train_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: source_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: destination_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: class_code
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: base_fare
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: tatkal_fare
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 7:
  Name: premium_tatkal_fare
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 8:
  Name: concession_percentage
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 9:
  Name: distance_km
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 10:
  Name: effective_from
  Type: Date
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 11:
  Name: effective_to
  Type: Date
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 12:
  Name: is_active
  Type: Boolean
  Required: NO
  Unique: NO
  Default: true

COLUMN 13:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Fares table created — 13 columns"
```

---

## PROMPT 8 — Table: Bookings

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Bookings

Add these columns. DO NOT add booking_id.

COLUMN 1:
  Name: pnr_number
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: user_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: train_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: source_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: destination_station_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: journey_date
  Type: Date
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: class_code
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: quota_type
  Type: Text
  Required: NO
  Unique: NO
  Default: General

COLUMN 9:
  Name: total_fare
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 10:
  Name: booking_status
  Type: Text
  Required: YES
  Unique: NO
  Default: pending

COLUMN 11:
  Name: payment_status
  Type: Text
  Required: NO
  Unique: NO
  Default: pending

COLUMN 12:
  Name: payment_method
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 13:
  Name: refund_amount
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 14:
  Name: booking_date
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 15:
  Name: cancellation_date
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 16:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Bookings table created — 16 columns"
```

---

## PROMPT 9 — Table: Passengers

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Passengers

Add these columns. DO NOT add passenger_id.

COLUMN 1:
  Name: booking_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: passenger_name
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: age
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: gender
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: id_proof_type
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: id_proof_number
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: coach_number
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: berth_number
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: berth_type
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 10:
  Name: status
  Type: Text
  Required: NO
  Unique: NO
  Default: confirmed

COLUMN 11:
  Name: is_child
  Type: Boolean
  Required: NO
  Unique: NO
  Default: false

COLUMN 12:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Passengers table created — 12 columns"
```

---

## PROMPT 10 — Table: Quotas

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Quotas

Add these columns. DO NOT add quota_id.

COLUMN 1:
  Name: train_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: class_code
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: quota_type
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: journey_date
  Type: Date
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: total_capacity
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 6:
  Name: booked_seats
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 7:
  Name: available_seats
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: waitlist_count
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 9:
  Name: rac_count
  Type: Number
  Required: NO
  Unique: NO
  Default: 0

COLUMN 10:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Quotas table created — 10 columns"
```

---

## PROMPT 11 — Table: Announcements

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Announcements

Add these columns. DO NOT add announcement_id.

COLUMN 1:
  Name: train_id
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: announcement_type
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: title
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: message
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)
  Action: If a "Long Text" toggle is visible, enable it

COLUMN 5:
  Name: severity
  Type: Text
  Required: NO
  Unique: NO
  Default: info

COLUMN 6:
  Name: effective_from
  Type: DateTime
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: effective_to
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: created_by
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Announcements table created — 9 columns"
```

---

## PROMPT 12 — Table: Admin_Logs

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Admin_Logs

Add these columns. DO NOT add log_id.

COLUMN 1:
  Name: admin_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: action
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 3:
  Name: entity_type
  Type: Text
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: entity_id
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: old_value
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)
  Action: Enable Long Text toggle — stores JSON

COLUMN 6:
  Name: new_value
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)
  Action: Enable Long Text toggle — stores JSON

COLUMN 7:
  Name: ip_address
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 8:
  Name: user_agent
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 9:
  Name: status
  Type: Text
  Required: NO
  Unique: NO
  Default: success

COLUMN 10:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Admin_Logs table created — 10 columns"
```

---

## PROMPT 13 — Table: Settings

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Settings

Add these columns. DO NOT add setting_id.

COLUMN 1:
  Name: key
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 2:
  Name: value
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)
  Action: Enable Long Text toggle — stores JSON for complex values

COLUMN 3:
  Name: setting_type
  Type: Text
  Required: NO
  Unique: NO
  Default: string

COLUMN 4:
  Name: description
  Type: Text
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 5:
  Name: is_system
  Type: Boolean
  Required: NO
  Unique: NO
  Default: false

COLUMN 6:
  Name: updated_by
  Type: Number
  Required: NO
  Unique: NO
  Default: (leave empty)

COLUMN 7:
  Name: updated_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Settings table created — 7 columns"
```

---

## PROMPT 14 — Table: Password_Reset_Tokens

```
Go to: Cloud Scale → Data Store → Create Table

TABLE NAME: Password_Reset_Tokens

Add these columns. DO NOT add token_id.

COLUMN 1:
  Name: user_id
  Type: Number
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 2:
  Name: token
  Type: Text
  Required: YES
  Unique: YES
  Default: (leave empty)

COLUMN 3:
  Name: expires_at
  Type: DateTime
  Required: YES
  Unique: NO
  Default: (leave empty)

COLUMN 4:
  Name: used
  Type: Boolean
  Required: NO
  Unique: NO
  Default: false

COLUMN 5:
  Name: created_at
  Type: DateTime
  Required: NO
  Unique: NO
  Default: (leave empty)

Save. Report: "Password_Reset_Tokens table created — 5 columns"
```

---

## PROMPT 15 — Environment Variables (all 9 Functions)

```
Navigate to: https://console.catalyst.zoho.com
Go to: Serverless → Functions

You will repeat the same steps for each of these 9 functions:
  1. auth_function
  2. bookings_function
  3. trains_function
  4. stations_function
  5. users_function
  6. fares_function
  7. train_routes_function
  8. admin_function
  9. ai_agent_function

FOR EACH FUNCTION — follow these steps:
1. Click the function name in the list
2. Click the "Variables" or "Environment Variables" tab
3. Click "Add Variable" for each variable below
4. Type the Key exactly, then the Value
5. Click Save after all variables are added for that function
6. Go back to the function list and repeat for the next function

VARIABLES TO ADD (add these 6 to all 9 functions):

Variable 1:
  Key:   CATALYST_PROJECT_ID
  Value: (copy your project ID from the Catalyst console URL)

Variable 2:
  Key:   CATALYST_ORG
  Value: (copy your org ID from Catalyst console settings)

Variable 3:
  Key:   CATALYST_MODEL
  Value: crm-di-qwen_text_14b-fp8-it

Variable 4:
  Key:   ADMIN_DOMAIN
  Value: admin.com

Variable 5:
  Key:   BOOKING_ADVANCE_DAYS
  Value: 90

Variable 6:
  Key:   MAX_PASSENGERS
  Value: 6

ADDITIONAL VARIABLES — add only to ai_agent_function (2 extra):

Variable 7:
  Key:   CATALYST_AI_MODEL
  Value: crm-di-qwen_text_14b-fp8-it

Variable 8:
  Key:   CATALYST_CODER_MODEL
  Value: crm-di-qwen_coder_7b-fp8-it

After completing all 9 functions report:
  "Environment variables set:
   - 8 functions × 6 variables = 48 variables
   - ai_agent_function × 8 variables = 8 variables
   - Total: 56 variables across 9 functions"
```

---

## PROMPT 16 — Verification (run last)

```
Navigate to: https://console.catalyst.zoho.com
Go to: Cloud Scale → Data Store

Count all tables visible in the table list.

Click into each table and count the columns (excluding ROWID which Catalyst adds automatically).

Verify against this expected checklist:

  Table Name               Expected Columns
  ─────────────────────────────────────────
  Users                  → 11 columns
  Stations               → 11 columns
  Trains                 → 11 columns
  Train_Routes           → 9  columns
  Coach_Layouts          → 6  columns
  Train_Inventory        → 7  columns
  Fares                  → 13 columns
  Bookings               → 16 columns
  Passengers             → 12 columns
  Quotas                 → 10 columns
  Announcements          → 9  columns
  Admin_Logs             → 10 columns
  Settings               → 7  columns
  Password_Reset_Tokens  → 5  columns
  ─────────────────────────────────────────
  TOTAL                  → 14 tables, 137 columns

Also verify Unique columns are marked correctly:
  Users.email                   → Unique
  Stations.station_code         → Unique
  Trains.train_number           → Unique
  Coach_Layouts.coach_type_code → Unique
  Bookings.pnr_number           → Unique
  Settings.key                  → Unique
  Password_Reset_Tokens.token   → Unique

Also verify Default values are saved:
  Users.role              → passenger
  Users.status            → active
  Stations.country        → India
  Stations.timezone       → Asia/Kolkata
  Stations.platform_count → 4
  Trains.total_coaches    → 16
  Trains.status           → active
  Train_Routes.halt_duration_minutes → 5
  Fares.tatkal_fare       → 0
  Fares.is_active         → true
  Bookings.quota_type     → General
  Bookings.booking_status → pending
  Bookings.refund_amount  → 0
  Passengers.status       → confirmed
  Passengers.is_child     → false
  Quotas.booked_seats     → 0
  Quotas.waitlist_count   → 0
  Quotas.rac_count        → 0
  Announcements.severity  → info
  Admin_Logs.status       → success
  Settings.setting_type   → string
  Settings.is_system      → false
  Password_Reset_Tokens.used → false

IF ALL MATCH:
  Report: "Verification complete — all 14 tables created successfully.
           137 columns verified. 7 unique constraints confirmed.
           22 default values confirmed. Database ready for migration."

IF ANY MISMATCH:
  Report exactly:
  - Which table has wrong column count
  - Which columns are missing
  - Which unique/default values are wrong
  Then re-run only the affected prompt number to fix it.
```

---

## QUICK REFERENCE — Table Summary

| Prompt | Table | Columns | Key Uniques |
|--------|-------|---------|-------------|
| 1 | Users | 11 | email |
| 2 | Stations | 11 | station_code |
| 3 | Trains | 11 | train_number |
| 4 | Train_Routes | 9 | — |
| 5 | Coach_Layouts | 6 | coach_type_code |
| 6 | Train_Inventory | 7 | — |
| 7 | Fares | 13 | — |
| 8 | Bookings | 16 | pnr_number |
| 9 | Passengers | 12 | — |
| 10 | Quotas | 10 | — |
| 11 | Announcements | 9 | — |
| 12 | Admin_Logs | 10 | — |
| 13 | Settings | 7 | key |
| 14 | Password_Reset_Tokens | 5 | token |
| 15 | Env Variables | — | 9 functions |
| 16 | Verification | — | Run last |
| **TOTAL** | **14 tables** | **137 columns** | |
