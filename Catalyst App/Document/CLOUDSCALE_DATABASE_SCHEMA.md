# Zoho Catalyst CloudScale Database Schema
## Railway Ticketing System

---

## TABLE DEFINITIONS

### 1. USERS
Store all user accounts and authentication

```json
{
  "table_name": "Users",
  "fields": [
    {
      "name": "user_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true,
      "description": "Unique user identifier"
    },
    {
      "name": "email",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 255,
      "description": "User email (login username)"
    },
    {
      "name": "password_hash",
      "type": "STRING",
      "required": true,
      "max_length": 512,
      "description": "SHA-256 hash of password"
    },
    {
      "name": "full_name",
      "type": "STRING",
      "max_length": 255,
      "description": "User full name"
    },
    {
      "name": "phone",
      "type": "STRING",
      "max_length": 20,
      "description": "Contact phone number"
    },
    {
      "name": "role",
      "type": "STRING",
      "enum": ["passenger", "admin", "agent"],
      "default": "passenger",
      "description": "User role for access control"
    },
    {
      "name": "status",
      "type": "STRING",
      "enum": ["active", "inactive", "suspended"],
      "default": "active"
    },
    {
      "name": "date_of_birth",
      "type": "DATE",
      "description": "User DOB for identity verification"
    },
    {
      "name": "gender",
      "type": "STRING",
      "enum": ["M", "F", "O"],
      "description": "Gender (required for berth allocation)"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP",
      "description": "Account creation timestamp"
    },
    {
      "name": "updated_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP",
      "on_update": "CURRENT_TIMESTAMP"
    },
    {
      "name": "last_login",
      "type": "DATETIME",
      "description": "Last login timestamp"
    }
  ],
  "indexes": [
    {"columns": ["email"], "unique": true},
    {"columns": ["role"]},
    {"columns": ["status"]},
    {"columns": ["created_at"]}
  ]
}
```

---

### 2. STATIONS
Railway station master data

```json
{
  "table_name": "Stations",
  "fields": [
    {
      "name": "station_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "station_code",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 10,
      "description": "3-letter station code (e.g., MAS, DEL, BOM)"
    },
    {
      "name": "station_name",
      "type": "STRING",
      "required": true,
      "max_length": 255
    },
    {
      "name": "city",
      "type": "STRING",
      "max_length": 100,
      "description": "City name"
    },
    {
      "name": "state",
      "type": "STRING",
      "max_length": 100,
      "description": "State/Province"
    },
    {
      "name": "country",
      "type": "STRING",
      "default": "India",
      "max_length": 100
    },
    {
      "name": "latitude",
      "type": "DOUBLE",
      "description": "GPS latitude"
    },
    {
      "name": "longitude",
      "type": "DOUBLE",
      "description": "GPS longitude"
    },
    {
      "name": "timezone",
      "type": "STRING",
      "default": "Asia/Kolkata",
      "description": "Station timezone"
    },
    {
      "name": "platform_count",
      "type": "INT",
      "default": 4,
      "description": "Number of platforms"
    },
    {
      "name": "is_major_station",
      "type": "BOOLEAN",
      "default": false,
      "description": "Whether it's a major hub"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["station_code"], "unique": true},
    {"columns": ["city"]},
    {"columns": ["state"]}
  ]
}
```

---

### 3. TRAINS
Train master data

```json
{
  "table_name": "Trains",
  "fields": [
    {
      "name": "train_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_number",
      "type": "INT",
      "unique": true,
      "required": true,
      "description": "Unique train number (e.g., 12621)"
    },
    {
      "name": "train_name",
      "type": "STRING",
      "required": true,
      "max_length": 255,
      "description": "Train name (e.g., Tamil Nadu Express)"
    },
    {
      "name": "train_type",
      "type": "STRING",
      "enum": ["Express", "Superfast", "Local", "Suburban", "Shatabdi", "Rajdhani"],
      "description": "Type of train"
    },
    {
      "name": "source_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "destination_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "departure_time",
      "type": "TIME",
      "required": true,
      "description": "Departure time from source"
    },
    {
      "name": "arrival_time",
      "type": "TIME",
      "required": true,
      "description": "Arrival time at destination"
    },
    {
      "name": "duration_minutes",
      "type": "INT",
      "description": "Journey duration in minutes"
    },
    {
      "name": "total_coaches",
      "type": "INT",
      "default": 16,
      "description": "Total number of coaches"
    },
    {
      "name": "status",
      "type": "STRING",
      "enum": ["active", "inactive", "seasonal"],
      "default": "active"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_number"], "unique": true},
    {"columns": ["source_station_id", "destination_station_id"]},
    {"columns": ["status"]}
  ]
}
```

---

### 4. TRAIN_ROUTES
Route stops for trains (many-to-many between trains and stations)

```json
{
  "table_name": "Train_Routes",
  "fields": [
    {
      "name": "route_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id",
      "required": true
    },
    {
      "name": "station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "sequence",
      "type": "INT",
      "required": true,
      "description": "Stop sequence (1 = source, n = destination)"
    },
    {
      "name": "arrival_time",
      "type": "TIME",
      "description": "Arrival time at this stop"
    },
    {
      "name": "departure_time",
      "type": "TIME",
      "description": "Departure time from this stop"
    },
    {
      "name": "halt_duration_minutes",
      "type": "INT",
      "default": 5,
      "description": "Halt duration in minutes"
    },
    {
      "name": "distance_from_source_km",
      "type": "DOUBLE",
      "description": "Distance from source in km"
    },
    {
      "name": "platform_number",
      "type": "INT",
      "description": "Platform number at this station"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_id", "sequence"]},
    {"columns": ["station_id"]},
    {"columns": ["train_id", "station_id"]}
  ],
  "unique_constraint": ["train_id", "station_id", "sequence"]
}
```

---

### 5. COACH_LAYOUTS
Coach configuration (SL=Sleeper, 1A=1st AC, 2A=2nd AC, etc.)

```json
{
  "table_name": "Coach_Layouts",
  "fields": [
    {
      "name": "layout_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "car_type_code",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 10,
      "enum": ["1A", "2A", "3A", "SL", "UR", "FC"],
      "description": "Coach type code"
    },
    {
      "name": "car_type_name",
      "type": "STRING",
      "required": true,
      "max_length": 100,
      "description": "Full name (1st AC, 2nd AC, Sleeper, etc.)"
    },
    {
      "name": "total_berths",
      "type": "INT",
      "required": true,
      "description": "Total berths in coach"
    },
    {
      "name": "layout_pattern",
      "type": "JSON",
      "description": "Berth layout (unicode, side-lower, side-upper)"
    },
    {
      "name": "seat_configuration",
      "type": "JSON",
      "description": "Detailed seat/berth layout"
    },
    {
      "name": "amenities",
      "type": "JSON",
      "description": "Coach amenities (charging, wifi, etc.)"
    },
    {
      "name": "is_active",
      "type": "BOOLEAN",
      "default": true
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["car_type_code"], "unique": true}
  ]
}
```

**Layout Pattern Example:**
```json
{
  "layout_pattern": {
    "1": "SU", "2": "SL", "3": "MU", "4": "ML",
    "5": "LU", "6": "LL", "7": "SU", "8": "SL"
  },
  "berth_cycle": 8,
  "side_berths": ["1", "2", "3", "4", "7", "8"],
  "mid_berths": ["5", "6"],
  "lower_berths": ["2", "4", "6", "8"],
  "upper_berths": ["1", "3", "5", "7"]
}
```

---

### 6. TRAIN_INVENTORY
Coach allocation per train

```json
{
  "table_name": "Train_Inventory",
  "fields": [
    {
      "name": "inventory_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id",
      "required": true
    },
    {
      "name": "coach_type_code",
      "type": "STRING",
      "foreign_key": "Coach_Layouts.car_type_code",
      "required": true
    },
    {
      "name": "coach_count",
      "type": "INT",
      "required": true,
      "description": "Number of coaches of this type"
    },
    {
      "name": "total_capacity",
      "type": "INT",
      "required": true,
      "description": "Total berths (coach_count * berths_per_coach)"
    },
    {
      "name": "sequence_start",
      "type": "INT",
      "description": "Coach sequence start position"
    },
    {
      "name": "sequence_end",
      "type": "INT",
      "description": "Coach sequence end position"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_id", "coach_type_code"]},
    {"columns": ["train_id"]}
  ]
}
```

---

### 7. FARES
Fare rules between stations for different classes

```json
{
  "table_name": "Fares",
  "fields": [
    {
      "name": "fare_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id",
      "required": true
    },
    {
      "name": "source_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "destination_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "class_code",
      "type": "STRING",
      "enum": ["1A", "2A", "3A", "SL", "UR", "FC"],
      "required": true
    },
    {
      "name": "base_fare",
      "type": "DECIMAL(10,2)",
      "required": true,
      "description": "Base fare in rupees"
    },
    {
      "name": "reservation_charge",
      "type": "DECIMAL(10,2)",
      "default": 0,
      "description": "Reservation charge"
    },
    {
      "name": "gst_percentage",
      "type": "DECIMAL(5,2)",
      "default": 5.00,
      "description": "GST percentage"
    },
    {
      "name": "total_fare",
      "type": "DECIMAL(10,2)",
      "description": "Total fare including all charges"
    },
    {
      "name": "effective_from",
      "type": "DATE",
      "description": "Fare effective from date"
    },
    {
      "name": "effective_to",
      "type": "DATE",
      "description": "Fare effective to date"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_id", "source_station_id", "destination_station_id", "class_code"]},
    {"columns": ["effective_from", "effective_to"]}
  ]
}
```

---

### 8. BOOKINGS
Main booking records

```json
{
  "table_name": "Bookings",
  "fields": [
    {
      "name": "booking_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "pnr_number",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 20,
      "description": "Passenger Name Record (10 digits)"
    },
    {
      "name": "user_id",
      "type": "BIGINT",
      "foreign_key": "Users.user_id",
      "required": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id",
      "required": true
    },
    {
      "name": "journey_date",
      "type": "DATE",
      "required": true,
      "description": "Date of journey"
    },
    {
      "name": "source_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "destination_station_id",
      "type": "BIGINT",
      "foreign_key": "Stations.station_id",
      "required": true
    },
    {
      "name": "class_code",
      "type": "STRING",
      "enum": ["1A", "2A", "3A", "SL", "UR", "FC"],
      "required": true
    },
    {
      "name": "quota_type",
      "type": "STRING",
      "enum": ["General", "Tatkal", "Premium", "Senior_Citizen"],
      "default": "General"
    },
    {
      "name": "passenger_count",
      "type": "INT",
      "required": true,
      "description": "Number of passengers"
    },
    {
      "name": "total_fare",
      "type": "DECIMAL(10,2)",
      "required": true
    },
    {
      "name": "payment_status",
      "type": "STRING",
      "enum": ["pending", "confirmed", "failed", "refunded"],
      "default": "pending"
    },
    {
      "name": "booking_status",
      "type": "STRING",
      "enum": ["confirmed", "waitlist", "cancelled", "rescheduled"],
      "default": "confirmed"
    },
    {
      "name": "posted_status",
      "type": "STRING",
      "enum": ["reserved", "confirmed", "RAC", "waitlist"],
      "default": "reserved"
    },
    {
      "name": "booking_date",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    },
    {
      "name": "confirmation_date",
      "type": "DATETIME",
      "description": "When booking was confirmed"
    },
    {
      "name": "cancelled_date",
      "type": "DATETIME",
      "description": "When booking was cancelled"
    },
    {
      "name": "cancellation_charge",
      "type": "DECIMAL(10,2)",
      "default": 0
    },
    {
      "name": "refund_amount",
      "type": "DECIMAL(10,2)",
      "default": 0
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["pnr_number"], "unique": true},
    {"columns": ["user_id", "booking_date"]},
    {"columns": ["train_id", "journey_date"]},
    {"columns": ["booking_status"]},
    {"columns": ["payment_status"]}
  ]
}
```

---

### 9. PASSENGERS
Passenger details for each booking

```json
{
  "table_name": "Passengers",
  "fields": [
    {
      "name": "passenger_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "booking_id",
      "type": "BIGINT",
      "foreign_key": "Bookings.booking_id",
      "required": true
    },
    {
      "name": "first_name",
      "type": "STRING",
      "required": true,
      "max_length": 100
    },
    {
      "name": "last_name",
      "type": "STRING",
      "max_length": 100
    },
    {
      "name": "age",
      "type": "INT",
      "required": true
    },
    {
      "name": "gender",
      "type": "STRING",
      "enum": ["M", "F", "O"],
      "required": true,
      "description": "For berth allocation"
    },
    {
      "name": "concession_type",
      "type": "STRING",
      "enum": ["None", "Student", "Senior_Citizen", "PWD", "Armed_Forces"],
      "default": "None"
    },
    {
      "name": "coach_number",
      "type": "INT",
      "description": "Allocated coach number"
    },
    {
      "name": "berth_number",
      "type": "STRING",
      "description": "Allocated berth/seat number"
    },
    {
      "name": "berth_type",
      "type": "STRING",
      "enum": ["lower", "middle", "upper", "side-lower", "side-upper"],
      "description": "Type of berth allocated"
    },
    {
      "name": "status",
      "type": "STRING",
      "enum": ["confirmed", "waitlist", "RAC", "cancelled"],
      "default": "confirmed"
    },
    {
      "name": "document_type",
      "type": "STRING",
      "enum": ["Aadhaar", "PAN", "Passport", "DL", "Voter_ID"],
      "description": "ID proof type"
    },
    {
      "name": "document_number",
      "type": "STRING",
      "max_length": 50,
      "description": "ID proof number"
    },
    {
      "name": "ticket_number",
      "type": "STRING",
      "unique": true,
      "description": "eTicket number"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["booking_id"]},
    {"columns": ["ticket_number"], "unique": true},
    {"columns": ["coach_number", "berth_number"]},
    {"columns": ["status"]}
  ]
}
```

---

### 10. QUOTAS
Seat quota distribution (General, Tatkal, Senior, etc.)

```json
{
  "table_name": "Quotas",
  "fields": [
    {
      "name": "quota_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id",
      "required": true
    },
    {
      "name": "class_code",
      "type": "STRING",
      "enum": ["1A", "2A", "3A", "SL", "UR", "FC"],
      "required": true
    },
    {
      "name": "quota_type",
      "type": "STRING",
      "enum": ["General", "Tatkal", "Senior_Citizen", "PWD", "Cancellation", "VIP"],
      "required": true
    },
    {
      "name": "percentage",
      "type": "DECIMAL(5,2)",
      "required": true,
      "description": "Percentage of capacity"
    },
    {
      "name": "actual_capacity",
      "type": "INT",
      "description": "Actual seat count for this quota"
    },
    {
      "name": "available_seats",
      "type": "INT",
      "description": "Currently available seats"
    },
    {
      "name": "booked_seats",
      "type": "INT",
      "default": 0
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_id", "class_code", "quota_type"]}
  ],
  "unique_constraint": ["train_id", "class_code", "quota_type"]
}
```

---

### 11. ANNOUNCEMENTS
Train announcements and alerts

```json
{
  "table_name": "Announcements",
  "fields": [
    {
      "name": "announcement_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "train_id",
      "type": "BIGINT",
      "foreign_key": "Trains.train_id"
    },
    {
      "name": "title",
      "type": "STRING",
      "required": true,
      "max_length": 500
    },
    {
      "name": "content",
      "type": "TEXT",
      "required": true
    },
    {
      "name": "announcement_type",
      "type": "STRING",
      "enum": ["delay", "cancellation", "maintenance", "update", "alert", "general"],
      "required": true
    },
    {
      "name": "severity",
      "type": "STRING",
      "enum": ["info", "warning", "critical"],
      "default": "info"
    },
    {
      "name": "effective_from",
      "type": "DATETIME",
      "required": true
    },
    {
      "name": "effective_to",
      "type": "DATETIME"
    },
    {
      "name": "created_by",
      "type": "BIGINT",
      "foreign_key": "Users.user_id"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["train_id"]},
    {"columns": ["announcement_type"]},
    {"columns": ["effective_from", "effective_to"]}
  ]
}
```

---

### 12. ADMIN_LOGS
Admin activity audit trail

```json
{
  "table_name": "Admin_Logs",
  "fields": [
    {
      "name": "log_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "admin_id",
      "type": "BIGINT",
      "foreign_key": "Users.user_id",
      "required": true
    },
    {
      "name": "action",
      "type": "STRING",
      "required": true,
      "max_length": 100,
      "description": "Action performed"
    },
    {
      "name": "entity_type",
      "type": "STRING",
      "enum": ["Train", "Station", "Booking", "User", "Fare", "Quota", "Announcement"],
      "required": true
    },
    {
      "name": "entity_id",
      "type": "BIGINT",
      "description": "ID of the entity modified"
    },
    {
      "name": "old_value",
      "type": "JSON",
      "description": "Previous value"
    },
    {
      "name": "new_value",
      "type": "JSON",
      "description": "New value"
    },
    {
      "name": "ip_address",
      "type": "STRING",
      "max_length": 50
    },
    {
      "name": "user_agent",
      "type": "STRING",
      "max_length": 500
    },
    {
      "name": "status",
      "type": "STRING",
      "enum": ["success", "failure", "pending"],
      "default": "success"
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["admin_id", "created_at"]},
    {"columns": ["entity_type", "entity_id"]},
    {"columns": ["created_at"]}
  ]
}
```

---

### 13. SETTINGS
System settings and configuration

```json
{
  "table_name": "Settings",
  "fields": [
    {
      "name": "setting_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "key",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 100
    },
    {
      "name": "value",
      "type": "TEXT",
      "description": "Setting value (JSON for complex values)"
    },
    {
      "name": "setting_type",
      "type": "STRING",
      "enum": ["string", "integer", "boolean", "json", "decimal"],
      "default": "string"
    },
    {
      "name": "description",
      "type": "STRING",
      "max_length": 500
    },
    {
      "name": "is_system",
      "type": "BOOLEAN",
      "default": false,
      "description": "Whether this is a system setting"
    },
    {
      "name": "updated_by",
      "type": "BIGINT",
      "foreign_key": "Users.user_id"
    },
    {
      "name": "updated_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP",
      "on_update": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["key"], "unique": true}
  ]
}
```

**Common Settings:**
```json
{
  "booking_advance_days": "90",
  "tatkal_booking_hours": "4",
  "tatkal_open_time": "11:00",
  "cancellation_min_deduction": "5% + INR 10",
  "min_booking_age": "5",
  "max_passengers_per_booking": "6"
}
```

---

### 14. PASSWORD_RESET_TOKENS
Password reset link tokens (temporary)

```json
{
  "table_name": "Password_Reset_Tokens",
  "fields": [
    {
      "name": "token_id",
      "type": "BIGINT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "user_id",
      "type": "BIGINT",
      "foreign_key": "Users.user_id",
      "required": true
    },
    {
      "name": "token",
      "type": "STRING",
      "unique": true,
      "required": true,
      "max_length": 512,
      "description": "Reset token (UUID)"
    },
    {
      "name": "expires_at",
      "type": "DATETIME",
      "required": true,
      "description": "Token expiration (typically 24 hours)"
    },
    {
      "name": "used",
      "type": "BOOLEAN",
      "default": false
    },
    {
      "name": "created_at",
      "type": "DATETIME",
      "default": "CURRENT_TIMESTAMP"
    }
  ],
  "indexes": [
    {"columns": ["token"], "unique": true},
    {"columns": ["user_id", "expires_at"]},
    {"columns": ["expires_at"]}
  ]
}
```

---

## RELATIONSHIPS (Foreign Keys)

```
Users
  ├─> Admin_Logs (admin_id)
  ├─> Bookings (user_id)
  └─> Password_Reset_Tokens (user_id)

Stations
  ├─> Trains (source_station_id, destination_station_id)
  ├─> Train_Routes (station_id)
  └─> Bookings (source_station_id, destination_station_id)

Trains
  ├─> Train_Routes (train_id)
  ├─> Train_Inventory (train_id)
  ├─> Fares (train_id)
  ├─> Quotas (train_id)
  ├─> Bookings (train_id)
  └─> Announcements (train_id)

Coach_Layouts
  └─> Train_Inventory (coach_type_code)

Bookings
  ├─> Passengers (booking_id)
  ├─> Users (user_id)
  ├─> Trains (train_id)
  └─> Stations (source_station_id, destination_station_id)
```

---

## INDEXES (Performance Tuning)

**High-Priority Indexes:**
```sql
-- Search trains by route
CREATE INDEX idx_trains_route ON Trains(source_station_id, destination_station_id);

-- Find bookings by user
CREATE INDEX idx_bookings_user ON Bookings(user_id, booking_date);

-- PNR lookup
CREATE INDEX idx_bookings_pnr ON Bookings(pnr_number);

-- Check availability on journey date
CREATE INDEX idx_bookings_availability ON Bookings(train_id, journey_date, booking_status);

-- Passenger lookup in booking
CREATE INDEX idx_passengers_booking ON Passengers(booking_id, status);

-- Audit trail queries
CREATE INDEX idx_logs_admin_time ON Admin_Logs(admin_id, created_at);
```

---

## DATA TYPE MAPPING (Catalyst CloudScale)

```
Python Type  → Catalyst Type  → Database
int          → INT/BIGINT     → 64-bit integer
float        → DOUBLE         → 64-bit float
bool         → BOOLEAN        → true/false
str          → STRING/TEXT    → variable length
datetime     → DATETIME       → ISO 8601
date         → DATE           → YYYY-MM-DD
decimal      → DECIMAL(10,2)  → fixed point
list         → JSON           → array
dict         → JSON           → object
```

---

## SAMPLE QUERIES (ZCQL)

```zcql
-- Search trains between two cities
SELECT * FROM Trains
WHERE source_station_id = ? AND destination_station_id = ?;

-- Check availability for a route
SELECT SUM(total_capacity) as capacity, SUM(booked_seats) as booked
FROM Quotas
WHERE train_id = ? AND class_code = ? AND journey_date = ?;

-- Get user bookings
SELECT * FROM Bookings
WHERE user_id = ? ORDER BY booking_date DESC;

-- Audit admin actions
SELECT * FROM Admin_Logs
WHERE admin_id = ? AND created_at BETWEEN ? AND ?
ORDER BY created_at DESC;

-- Check waitlist for train
SELECT COUNT(*) as waitlist_count FROM Passengers
WHERE booking_id IN (SELECT booking_id FROM Bookings WHERE train_id = ? AND status = 'waitlist');
```

---

## MIGRATION CHECKLIST

- [ ] Create all 14 tables in Catalyst CloudScale
- [ ] Add primary keys and indexes
- [ ] Configure foreign key constraints
- [ ] Set default values and timestamps
- [ ] Add data validation rules
- [ ] Create sample data (test trains, stations)
- [ ] Verify relationships and constraints
- [ ] Performance test with 100K+ records
- [ ] Set up backup strategy
- [ ] Document access control (row-level security)
