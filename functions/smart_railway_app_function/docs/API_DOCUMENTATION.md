# Smart Railway Ticketing System - Complete API Documentation

> **Version:** 2.0.0
> **Base URL:** `http://localhost:9000` (Local) | `https://smart-railway-app.onslate.in/server/smart_railway_app_function/724...` (Production)
> **Content-Type:** `application/json`
> **Authentication:** Bearer Token (JWT)

---

## Table of Contents

1. [Authentication API](#1-authentication-api)
2. [Users API](#2-users-api)
3. [Stations API](#3-stations-api)
4. [Trains API](#4-trains-api)
5. [Train Routes API](#5-train-routes-api)
6. [Bookings API](#6-bookings-api)
7. [Fares API](#7-fares-api)
8. [Inventory API](#8-inventory-api)
9. [Quotas API](#9-quotas-api)
10. [Announcements API](#10-announcements-api)
11. [Settings API](#11-settings-api)
12. [Admin Logs API](#12-admin-logs-api)
13. [Admin Users API](#13-admin-users-api)
14. [Module Master API](#14-module-master-api)

---

## Lookup Reference Table

| Field | References Table | Description |
|-------|------------------|-------------|
| `User_ID` | Users.ROWID | User reference |
| `Train_ID` | Trains.ROWID | Train reference |
| `Station_ID` | Stations.ROWID | Station reference |
| `Route_ID` | Train_Routes.ROWID | Route reference |
| `Booking_ID` | Bookings.ROWID | Booking reference |
| `Parent_Module_ID` | Module_Master.ROWID | Parent module reference |

---

## 1. Authentication API

### 1.1 Register User

**Endpoint:** `POST /auth/register`
**Auth Required:** No
**Rate Limit:** 10 requests/hour

**Request:**
```json
{
    "fullName": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "phoneNumber": "+91-9876543210"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "message": "Registration successful",
    "data": {
        "user": {
            "id": "1001",
            "fullName": "John Doe",
            "email": "john.doe@example.com",
            "phoneNumber": "+91-9876543210",
            "role": "User",
            "accountStatus": "Active"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

**Error Response (409 - Duplicate Email):**
```json
{
    "status": "error",
    "message": "Email already registered"
}
```

---

### 1.2 Login

**Endpoint:** `POST /auth/login`
**Auth Required:** No
**Rate Limit:** 10 requests/15 minutes

**Request:**
```json
{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Login successful",
    "data": {
        "user": {
            "id": "1001",
            "fullName": "John Doe",
            "email": "john.doe@example.com",
            "phoneNumber": "+91-9876543210",
            "role": "User",
            "accountStatus": "Active",
            "dateOfBirth": "1990-05-15",
            "address": "123 Main St, Mumbai"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

**Error Response (401):**
```json
{
    "status": "error",
    "message": "Invalid email or password"
}
```

---

### 1.3 Validate Session

**Endpoint:** `GET /auth/validate`
**Auth Required:** Yes (Bearer Token)

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "user": {
            "id": "1001",
            "fullName": "John Doe",
            "email": "john.doe@example.com",
            "phoneNumber": "+91-9876543210",
            "role": "User",
            "accountStatus": "Active"
        }
    }
}
```

---

### 1.4 Refresh Token

**Endpoint:** `POST /auth/refresh`
**Auth Required:** No

**Request:**
```json
{
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "tokenType": "Bearer",
        "expiresIn": 3600
    }
}
```

---

### 1.5 Update Profile

**Endpoint:** `PUT /auth/profile`
**Auth Required:** Yes

**Request:**
```json
{
    "fullName": "John D. Doe",
    "phoneNumber": "+91-9876543211",
    "dateOfBirth": "1990-05-15",
    "address": "456 New St, Delhi"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Profile updated successfully",
    "data": {
        "user": {
            "id": "1001",
            "fullName": "John D. Doe",
            "email": "john.doe@example.com",
            "phoneNumber": "+91-9876543211",
            "role": "User",
            "accountStatus": "Active",
            "dateOfBirth": "1990-05-15",
            "address": "456 New St, Delhi"
        }
    }
}
```

---

### 1.6 Change Password

**Endpoint:** `POST /auth/change-password`
**Auth Required:** Yes

**Request:**
```json
{
    "currentPassword": "SecurePass123!",
    "newPassword": "NewSecurePass456!"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Password changed successfully",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

---

### 1.7 Logout

**Endpoint:** `POST /auth/logout`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Logged out successfully"
}
```

---

## 2. Users API

### 2.1 Get All Users (Admin)

**Endpoint:** `GET /users`
**Auth Required:** Yes (Admin)
**Query Params:** `limit`, `offset`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1001",
            "Full_Name": "John Doe",
            "Email": "john.doe@example.com",
            "Phone_Number": "+91-9876543210",
            "Role": "User",
            "Account_Status": "Active",
            "Date_of_Birth": "1990-05-15",
            "Address": "123 Main St, Mumbai"
        },
        {
            "ROWID": "1002",
            "Full_Name": "Jane Smith",
            "Email": "jane.smith@example.com",
            "Phone_Number": "+91-9876543211",
            "Role": "Admin",
            "Account_Status": "Active"
        }
    ]
}
```

---

### 2.2 Get User by ID

**Endpoint:** `GET /users/:user_id`
**Auth Required:** Yes

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1001",
        "Full_Name": "John Doe",
        "Email": "john.doe@example.com",
        "Phone_Number": "+91-9876543210",
        "Role": "User",
        "Account_Status": "Active"
    }
}
```

---

### 2.3 Create User (Admin)

**Endpoint:** `POST /users`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "fullName": "New User",
    "email": "newuser@example.com",
    "password": "TempPass123!",
    "phoneNumber": "+91-9876543212",
    "role": "User"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1003",
        "Full_Name": "New User",
        "Email": "newuser@example.com",
        "Phone_Number": "+91-9876543212",
        "Role": "User",
        "Account_Status": "Active"
    }
}
```

---

### 2.4 Update User (Admin)

**Endpoint:** `PUT /users/:user_id`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "fullName": "Updated User Name",
    "phoneNumber": "+91-9876543213",
    "role": "Admin",
    "accountStatus": "Active"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "User updated"
}
```

---

### 2.5 Delete User (Admin)

**Endpoint:** `DELETE /users/:user_id`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "message": "User deleted"
}
```

---

### 2.6 Update User Status (Admin)

**Endpoint:** `PUT /users/:user_id/status`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "status": "Blocked"
}
```

**Allowed Values:** `Active`, `Blocked`, `Suspended`

**Success Response (200):**
```json
{
    "status": "success",
    "message": "User status updated to Blocked"
}
```

---

## 3. Stations API

### 3.1 Get All Stations

**Endpoint:** `GET /stations`
**Auth Required:** No (Cached 24 hours)

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "101",
            "Station_Code": "NDLS",
            "Station_Name": "New Delhi",
            "City": "New Delhi",
            "State": "Delhi",
            "Zone": "NR",
            "Platform_Count": 16,
            "Is_Active": "true"
        },
        {
            "ROWID": "102",
            "Station_Code": "CSTM",
            "Station_Name": "Chhatrapati Shivaji Maharaj Terminus",
            "City": "Mumbai",
            "State": "Maharashtra",
            "Zone": "CR",
            "Platform_Count": 18,
            "Is_Active": "true"
        },
        {
            "ROWID": "103",
            "Station_Code": "HWH",
            "Station_Name": "Howrah Junction",
            "City": "Kolkata",
            "State": "West Bengal",
            "Zone": "ER",
            "Platform_Count": 23,
            "Is_Active": "true"
        }
    ]
}
```

---

### 3.2 Get Station by ID

**Endpoint:** `GET /stations/:station_id`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "101",
        "Station_Code": "NDLS",
        "Station_Name": "New Delhi",
        "City": "New Delhi",
        "State": "Delhi",
        "Zone": "NR",
        "Platform_Count": 16,
        "Is_Active": "true"
    }
}
```

---

### 3.3 Create Station (Admin)

**Endpoint:** `POST /stations`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "stationCode": "MAS",
    "stationName": "Chennai Central",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "zone": "SR",
    "platformCount": 17
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "104",
        "Station_Code": "MAS",
        "Station_Name": "Chennai Central",
        "City": "Chennai",
        "State": "Tamil Nadu",
        "Zone": "SR",
        "Platform_Count": 17,
        "Is_Active": "true"
    }
}
```

---

### 3.4 Update Station (Admin)

**Endpoint:** `PUT /stations/:station_id`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "stationName": "Chennai Central Railway Station",
    "platformCount": 18
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Station updated"
}
```

---

### 3.5 Delete Station (Admin)

**Endpoint:** `DELETE /stations/:station_id`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Station deleted"
}
```

---

## 4. Trains API

### 4.1 Get All Trains

**Endpoint:** `GET /trains`
**Auth Required:** No
**Query Params:** `limit`, `offset`, `active` (true/false), `source`, `destination`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "201",
            "Train_Number": "12301",
            "Train_Name": "Howrah Rajdhani Express",
            "Train_Type": "Rajdhani",
            "From_Station": "NDLS",
            "To_Station": "HWH",
            "Departure_Time": "16:55",
            "Arrival_Time": "09:55",
            "Duration": "17h 00m",
            "Days_Of_Operation": "All Days",
            "Is_Active": "true",
            "Total_Seats_SL": 0,
            "Total_Seats_3A": 384,
            "Total_Seats_2A": 92,
            "Total_Seats_1A": 36,
            "Total_Seats_CC": 0
        },
        {
            "ROWID": "202",
            "Train_Number": "12951",
            "Train_Name": "Mumbai Rajdhani Express",
            "Train_Type": "Rajdhani",
            "From_Station": "NDLS",
            "To_Station": "CSTM",
            "Departure_Time": "16:25",
            "Arrival_Time": "08:35",
            "Duration": "16h 10m",
            "Days_Of_Operation": "All Days",
            "Is_Active": "true"
        }
    ]
}
```

---

### 4.2 Get Train by ID

**Endpoint:** `GET /trains/:train_id`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "201",
        "Train_Number": "12301",
        "Train_Name": "Howrah Rajdhani Express",
        "Train_Type": "Rajdhani",
        "From_Station": "NDLS",
        "To_Station": "HWH",
        "Departure_Time": "16:55",
        "Arrival_Time": "09:55",
        "Duration": "17h 00m",
        "Days_Of_Operation": "All Days",
        "Is_Active": "true"
    }
}
```

---

### 4.3 Create Train (Admin)

**Endpoint:** `POST /trains`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainNumber": "12425",
    "trainName": "New Delhi Rajdhani Express",
    "trainType": "Rajdhani",
    "fromStation": "NDLS",
    "toStation": "JAT",
    "departureTime": "20:20",
    "arrivalTime": "05:00",
    "duration": "8h 40m",
    "daysOfOperation": "Daily",
    "totalSeatsSL": 0,
    "totalSeats3A": 256,
    "totalSeats2A": 64,
    "totalSeats1A": 24,
    "totalSeatsCC": 0
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "203",
        "Train_Number": "12425",
        "Train_Name": "New Delhi Rajdhani Express",
        "Train_Type": "Rajdhani",
        "Is_Active": "true"
    }
}
```

---

### 4.4 Update Train (Admin)

**Endpoint:** `PUT /trains/:train_id`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainName": "Updated Train Name",
    "departureTime": "21:00",
    "isActive": false
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Train updated"
}
```

---

### 4.5 Delete Train (Admin)

**Endpoint:** `DELETE /trains/:train_id`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Train deleted"
}
```

---

## 5. Train Routes API

### 5.1 Get All Routes

**Endpoint:** `GET /train-routes`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "301",
            "Train_ID": "201",
            "Route_Name": "Delhi-Howrah Route",
            "Total_Distance": 1447
        }
    ]
}
```

---

### 5.2 Get Route by ID (with Stops)

**Endpoint:** `GET /train-routes/:route_id`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "301",
        "Train_ID": "201",
        "Route_Name": "Delhi-Howrah Route",
        "Total_Distance": 1447,
        "stops": [
            {
                "ROWID": "401",
                "Route_ID": "301",
                "Station_ID": "101",
                "Stop_Sequence": 1,
                "Arrival_Time": "-",
                "Departure_Time": "16:55",
                "Distance_From_Origin": 0,
                "Halt_Duration": 0,
                "Platform": "8"
            },
            {
                "ROWID": "402",
                "Route_ID": "301",
                "Station_ID": "105",
                "Stop_Sequence": 2,
                "Arrival_Time": "19:02",
                "Departure_Time": "19:05",
                "Distance_From_Origin": 220,
                "Halt_Duration": 3,
                "Platform": "1"
            }
        ]
    }
}
```

---

### 5.3 Create Route (Admin)

**Endpoint:** `POST /train-routes`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainId": "202",
    "routeName": "Delhi-Mumbai Route",
    "totalDistance": 1384
}
```

**Lookup:** `trainId` → Trains.ROWID

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "302",
        "Train_ID": "202",
        "Route_Name": "Delhi-Mumbai Route",
        "Total_Distance": 1384
    }
}
```

---

### 5.4 Add Stop to Route (Admin)

**Endpoint:** `POST /train-routes/:route_id/stops`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "stationId": "102",
    "stopSequence": 5,
    "arrivalTime": "08:35",
    "departureTime": "-",
    "distanceFromOrigin": 1384,
    "haltDuration": 0,
    "platform": "5"
}
```

**Lookups:**
- `stationId` → Stations.ROWID
- `route_id` (path) → Train_Routes.ROWID

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "410",
        "Route_ID": "302",
        "Station_ID": "102",
        "Stop_Sequence": 5
    }
}
```

---

## 6. Bookings API

### 6.1 Get All Bookings (Admin)

**Endpoint:** `GET /bookings`
**Auth Required:** Yes (Admin)
**Query Params:** `limit`, `offset`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "501",
            "PNR": "PNR8A4BC2D1",
            "User_ID": "1001",
            "Train_ID": "201",
            "Journey_Date": "2026-04-15",
            "Travel_Class": "3A",
            "Quota": "GN",
            "From_Station": "NDLS",
            "To_Station": "HWH",
            "Booking_Status": "Confirmed",
            "Payment_Status": "Paid",
            "Total_Fare": 2450,
            "Booking_Time": "2026-03-27T10:30:00"
        }
    ]
}
```

---

### 6.2 Get Booking by ID

**Endpoint:** `GET /bookings/:booking_id`
**Auth Required:** Yes

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "501",
        "PNR": "PNR8A4BC2D1",
        "User_ID": "1001",
        "Train_ID": "201",
        "Journey_Date": "2026-04-15",
        "Travel_Class": "3A",
        "Quota": "GN",
        "From_Station": "NDLS",
        "To_Station": "HWH",
        "Booking_Status": "Confirmed",
        "Payment_Status": "Paid",
        "Total_Fare": 2450,
        "passengers": [
            {
                "ROWID": "601",
                "Booking_ID": "501",
                "Passenger_Name": "John Doe",
                "Age": 35,
                "Gender": "Male",
                "Berth_Preference": "Lower",
                "Seat_Status": "CNF",
                "Seat_Number": "45",
                "Coach": "B1"
            },
            {
                "ROWID": "602",
                "Booking_ID": "501",
                "Passenger_Name": "Jane Doe",
                "Age": 32,
                "Gender": "Female",
                "Berth_Preference": "Lower",
                "Seat_Status": "CNF",
                "Seat_Number": "46",
                "Coach": "B1"
            }
        ]
    }
}
```

---

### 6.3 Get Booking by PNR

**Endpoint:** `GET /bookings/pnr/:pnr`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "501",
        "PNR": "PNR8A4BC2D1",
        "Train_ID": "201",
        "Journey_Date": "2026-04-15",
        "Travel_Class": "3A",
        "Booking_Status": "Confirmed",
        "passengers": [
            {
                "Passenger_Name": "John Doe",
                "Seat_Status": "CNF",
                "Seat_Number": "45",
                "Coach": "B1"
            }
        ]
    }
}
```

---

### 6.4 Create Booking

**Endpoint:** `POST /bookings`
**Auth Required:** Yes

**Request:**
```json
{
    "trainId": "201",
    "journeyDate": "2026-04-15",
    "travelClass": "3A",
    "quota": "GN",
    "fromStation": "NDLS",
    "toStation": "HWH",
    "totalFare": 2450,
    "passengers": [
        {
            "name": "John Doe",
            "age": 35,
            "gender": "Male",
            "berthPreference": "Lower"
        },
        {
            "name": "Jane Doe",
            "age": 32,
            "gender": "Female",
            "berthPreference": "Lower"
        }
    ]
}
```

**Lookups:**
- `trainId` → Trains.ROWID

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "booking": {
            "ROWID": "501",
            "PNR": "PNR8A4BC2D1",
            "User_ID": "1001",
            "Train_ID": "201",
            "Booking_Status": "Pending"
        },
        "pnr": "PNR8A4BC2D1"
    }
}
```

---

### 6.5 Pay for Booking

**Endpoint:** `POST /bookings/:booking_id/pay`
**Auth Required:** Yes

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Payment recorded"
}
```

---

### 6.6 Cancel Booking

**Endpoint:** `POST /bookings/:booking_id/cancel`
**Auth Required:** Yes

**Request:**
```json
{
    "reason": "Change of plans"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Booking cancelled"
}
```

---

### 6.7 Get User Bookings

**Endpoint:** `GET /users/:user_id/bookings`
**Auth Required:** Yes

**Lookup:** `user_id` → Users.ROWID

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "501",
            "PNR": "PNR8A4BC2D1",
            "Journey_Date": "2026-04-15",
            "Booking_Status": "Confirmed"
        }
    ]
}
```

---

## 7. Fares API

### 7.1 Get All Fare Rules

**Endpoint:** `GET /fares`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "701",
            "Train_Type": "Rajdhani",
            "Travel_Class": "3A",
            "Base_Rate_Per_Km": 1.70,
            "Min_Fare": 260,
            "Max_Fare": 4500
        }
    ]
}
```

---

### 7.2 Calculate Fare

**Endpoint:** `POST /fares/calculate`
**Auth Required:** No

**Request:**
```json
{
    "distance": 1447,
    "travelClass": "3A",
    "isTatkal": false,
    "isSuperfast": true,
    "concession": null
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "baseFare": 2459.90,
        "reservationCharge": 40,
        "superfastSurcharge": 45,
        "tatkalCharge": 0,
        "subtotal": 2544.90,
        "gst": 127.25,
        "concessionDiscount": 0,
        "totalFare": 2672.15
    }
}
```

---

### 7.3 Create Fare Rule (Admin)

**Endpoint:** `POST /fares`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainType": "Shatabdi",
    "travelClass": "CC",
    "baseRatePerKm": 1.25,
    "minFare": 130,
    "maxFare": 2500
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "702",
        "Train_Type": "Shatabdi",
        "Travel_Class": "CC"
    }
}
```

---

## 8. Inventory API

### 8.1 Get Inventory

**Endpoint:** `GET /inventory`
**Auth Required:** No
**Query Params:** `trainId`, `journeyDate`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "801",
            "Train_ID": "201",
            "Journey_Date": "2026-04-15",
            "Available_Seats_SL": 0,
            "Available_Seats_3A": 256,
            "Available_Seats_2A": 64,
            "Available_Seats_1A": 24,
            "Available_Seats_CC": 0
        }
    ]
}
```

---

### 8.2 Create Inventory (Admin)

**Endpoint:** `POST /inventory`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainId": "201",
    "journeyDate": "2026-04-20",
    "availableSeatsSL": 0,
    "availableSeats3A": 384,
    "availableSeats2A": 92,
    "availableSeats1A": 36,
    "availableSeatsCC": 0
}
```

**Lookup:** `trainId` → Trains.ROWID

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "802",
        "Train_ID": "201",
        "Journey_Date": "2026-04-20"
    }
}
```

---

## 9. Quotas API

### 9.1 Get All Quotas

**Endpoint:** `GET /quotas`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "901",
            "Train_ID": "201",
            "Quota_Type": "GN",
            "Travel_Class": "3A",
            "Seats_Allocated": 300
        },
        {
            "ROWID": "902",
            "Train_ID": "201",
            "Quota_Type": "TK",
            "Travel_Class": "3A",
            "Seats_Allocated": 84
        }
    ]
}
```

---

### 9.2 Get Quota Types

**Endpoint:** `GET /quotas/types`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "GN": "General Quota",
        "TK": "Tatkal Quota",
        "PT": "Premium Tatkal",
        "LD": "Ladies Quota",
        "HP": "Handicapped Quota",
        "DF": "Defence Quota",
        "FT": "Foreign Tourist Quota",
        "SS": "Senior Citizen Quota"
    }
}
```

---

### 9.3 Create Quota (Admin)

**Endpoint:** `POST /quotas`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "trainId": "202",
    "quotaType": "GN",
    "travelClass": "2A",
    "seatsAllocated": 60
}
```

**Lookup:** `trainId` → Trains.ROWID

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "903",
        "Train_ID": "202",
        "Quota_Type": "GN"
    }
}
```

---

## 10. Announcements API

### 10.1 Get All Announcements

**Endpoint:** `GET /announcements`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1001",
            "Title": "Platform Change Alert",
            "Message": "Train 12301 will depart from Platform 9 instead of 8",
            "Type": "warning",
            "Priority": "high",
            "Is_Active": "true",
            "Created_At": "2026-03-27T08:00:00"
        }
    ]
}
```

---

### 10.2 Get Active Announcements

**Endpoint:** `GET /announcements/active`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1001",
            "Title": "Platform Change Alert",
            "Message": "Train 12301 will depart from Platform 9",
            "Type": "warning",
            "Priority": "high",
            "Is_Active": "true"
        }
    ]
}
```

---

### 10.3 Create Announcement (Admin)

**Endpoint:** `POST /announcements`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "title": "Maintenance Notice",
    "message": "Online booking will be unavailable from 2 AM to 4 AM for scheduled maintenance.",
    "type": "info",
    "priority": "normal"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1002",
        "Title": "Maintenance Notice",
        "Type": "info",
        "Is_Active": "true"
    }
}
```

---

## 11. Settings API

### 11.1 Get All Settings

**Endpoint:** `GET /settings`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1101",
            "Setting_Key": "booking_advance_days",
            "Setting_Value": "120",
            "Description": "Days in advance tickets can be booked",
            "Category": "booking"
        },
        {
            "ROWID": "1102",
            "Setting_Key": "tatkal_open_hour",
            "Setting_Value": "10",
            "Description": "Hour when Tatkal booking opens",
            "Category": "booking"
        }
    ]
}
```

---

### 11.2 Get Setting by Key

**Endpoint:** `GET /settings/key/:key`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1101",
        "Setting_Key": "booking_advance_days",
        "Setting_Value": "120",
        "Description": "Days in advance tickets can be booked",
        "Category": "booking"
    }
}
```

---

### 11.3 Create Setting (Admin)

**Endpoint:** `POST /settings`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "key": "max_passengers_per_booking",
    "value": "6",
    "description": "Maximum passengers allowed per booking",
    "category": "booking"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1103",
        "Setting_Key": "max_passengers_per_booking",
        "Setting_Value": "6"
    }
}
```

---

## 12. Admin Logs API

### 12.1 Get All Logs (Admin)

**Endpoint:** `GET /admin/logs`
**Auth Required:** Yes (Admin)
**Query Params:** `limit`, `offset`, `actionType`, `userEmail`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1201",
            "User_Email": "admin@railway.com",
            "Action_Type": "CREATE",
            "Action_Details": "Created train 12425",
            "Entity_Type": "Train",
            "Entity_ID": "203",
            "IP_Address": "192.168.1.100",
            "Timestamp": "2026-03-27T10:30:00"
        }
    ]
}
```

---

### 12.2 Create Log Entry (Admin)

**Endpoint:** `POST /admin/logs`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "actionType": "UPDATE",
    "actionDetails": "Updated fare rules for Rajdhani trains",
    "entityType": "Fare",
    "entityId": "701"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1202",
        "User_Email": "admin@railway.com",
        "Action_Type": "UPDATE"
    }
}
```

---

## 13. Admin Users API

### 13.1 Get Admin Users

**Endpoint:** `GET /admin/users`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "ROWID": "1002",
            "Full_Name": "Admin User",
            "Email": "admin@railway.com",
            "Role": "Admin",
            "Account_Status": "Active"
        }
    ]
}
```

---

### 13.2 Create Admin User

**Endpoint:** `POST /admin/users`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "fullName": "New Admin",
    "email": "newadmin@catalyst-cs2.onslate.in",
    "password": "AdminPass123!"
}
```

**Success Response (201):**
```json
{
    "status": "success",
    "data": {
        "ROWID": "1003",
        "Full_Name": "New Admin",
        "Email": "newadmin@catalyst-cs2.onslate.in",
        "Role": "Admin"
    }
}
```

---

### 13.3 Promote to Admin

**Endpoint:** `POST /admin/users/:user_id/promote`
**Auth Required:** Yes (Admin)

**Lookup:** `user_id` → Users.ROWID

**Success Response (200):**
```json
{
    "status": "success",
    "message": "User promoted to admin"
}
```

---

### 13.4 Demote from Admin

**Endpoint:** `POST /admin/users/:user_id/demote`
**Auth Required:** Yes (Admin)

**Lookup:** `user_id` → Users.ROWID

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Admin demoted to user"
}
```

---

## 14. Module Master API

### 14.1 Get All Modules

**Endpoint:** `GET /modules`
**Auth Required:** No
**Query Params:** `limit`, `offset`, `active` (true/false), `category`, `search`, `orderBy`

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "id": "1401",
            "moduleName": "Dashboard",
            "moduleCode": "DASHBOARD",
            "description": "Main analytics dashboard",
            "category": "Admin",
            "displayOrder": 1,
            "isActive": true,
            "icon": "dashboard",
            "route": "/admin/dashboard",
            "permissions": "view_dashboard",
            "parentModuleId": "",
            "createdAt": "2026-03-27T10:00:00",
            "updatedAt": "2026-03-27T10:00:00"
        },
        {
            "id": "1402",
            "moduleName": "User Management",
            "moduleCode": "USER_MGMT",
            "description": "Manage system users",
            "category": "Admin",
            "displayOrder": 2,
            "isActive": true,
            "icon": "users",
            "route": "/admin/users",
            "permissions": "manage_users",
            "parentModuleId": "",
            "createdAt": "2026-03-27T10:00:00",
            "updatedAt": "2026-03-27T10:00:00"
        }
    ],
    "meta": {
        "total": 2,
        "limit": 100,
        "offset": 0,
        "cached": false
    }
}
```

---

### 14.2 Get Module by ID

**Endpoint:** `GET /modules/:module_id`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": {
        "id": "1401",
        "moduleName": "Dashboard",
        "moduleCode": "DASHBOARD",
        "description": "Main analytics dashboard",
        "category": "Admin",
        "displayOrder": 1,
        "isActive": true,
        "icon": "dashboard",
        "route": "/admin/dashboard",
        "permissions": "view_dashboard",
        "parentModuleId": "",
        "createdAt": "2026-03-27T10:00:00",
        "updatedAt": "2026-03-27T10:00:00"
    }
}
```

---

### 14.3 Create Module (Admin)

**Endpoint:** `POST /modules`
**Auth Required:** Yes (Admin)
**Rate Limit:** 50 requests/hour

**Request:**
```json
{
    "moduleName": "Train Management",
    "moduleCode": "TRAIN_MGMT",
    "description": "Manage trains and schedules",
    "category": "Operations",
    "displayOrder": 3,
    "isActive": true,
    "icon": "train",
    "route": "/admin/trains",
    "permissions": "manage_trains",
    "parentModuleId": ""
}
```

**Lookup:** `parentModuleId` → Module_Master.ROWID (optional, for nested modules)

**Success Response (201):**
```json
{
    "status": "success",
    "message": "Module created successfully",
    "data": {
        "id": "1403",
        "moduleName": "Train Management",
        "moduleCode": "TRAIN_MGMT",
        "description": "Manage trains and schedules",
        "category": "Operations",
        "displayOrder": 3,
        "isActive": true,
        "icon": "train",
        "route": "/admin/trains",
        "permissions": "manage_trains",
        "parentModuleId": "",
        "createdAt": "2026-03-27T11:00:00",
        "updatedAt": "2026-03-27T11:00:00"
    }
}
```

**Error Response (409 - Duplicate):**
```json
{
    "status": "error",
    "message": "Module with code \"TRAIN_MGMT\" already exists"
}
```

---

### 14.4 Update Module (Admin)

**Endpoint:** `PUT /modules/:module_id`
**Auth Required:** Yes (Admin)

**Request:**
```json
{
    "description": "Updated module description",
    "displayOrder": 5,
    "isActive": false,
    "icon": "new-icon"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Module updated successfully",
    "data": {
        "id": "1403",
        "moduleName": "Train Management",
        "moduleCode": "TRAIN_MGMT",
        "description": "Updated module description",
        "displayOrder": 5,
        "isActive": false,
        "icon": "new-icon",
        "updatedAt": "2026-03-27T11:30:00"
    }
}
```

---

### 14.5 Delete Module (Admin)

**Endpoint:** `DELETE /modules/:module_id`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Module deleted successfully"
}
```

**Error Response (400 - Has Children):**
```json
{
    "status": "error",
    "message": "Cannot delete module with child modules. Delete children first."
}
```

---

### 14.6 Toggle Module Status (Admin)

**Endpoint:** `POST /modules/:module_id/toggle-status`
**Auth Required:** Yes (Admin)

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Module deactivated successfully",
    "data": {
        "id": "1403",
        "isActive": false
    }
}
```

---

### 14.7 Get Module Hierarchy

**Endpoint:** `GET /modules/hierarchy`
**Auth Required:** No

**Success Response (200):**
```json
{
    "status": "success",
    "data": [
        {
            "id": "1401",
            "moduleName": "Administration",
            "moduleCode": "ADMIN",
            "displayOrder": 1,
            "isActive": true,
            "children": [
                {
                    "id": "1402",
                    "moduleName": "User Management",
                    "moduleCode": "USER_MGMT",
                    "displayOrder": 1,
                    "isActive": true,
                    "children": []
                },
                {
                    "id": "1403",
                    "moduleName": "Settings",
                    "moduleCode": "SETTINGS",
                    "displayOrder": 2,
                    "isActive": true,
                    "children": []
                }
            ]
        },
        {
            "id": "1404",
            "moduleName": "Operations",
            "moduleCode": "OPS",
            "displayOrder": 2,
            "isActive": true,
            "children": []
        }
    ]
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
    "status": "error",
    "message": "Error description here"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (Missing/Invalid Token) |
| 403 | Forbidden (Insufficient Permissions) |
| 404 | Not Found |
| 409 | Conflict (Duplicate Resource) |
| 429 | Too Many Requests (Rate Limited) |
| 500 | Internal Server Error |

---

## Lookup ID Reference Summary

When creating records with foreign key relationships, use these ID references:

| Field in Request | Lookup Table | Example |
|------------------|--------------|---------|
| `trainId` / `Train_ID` | Trains | `"trainId": "201"` |
| `stationId` / `Station_ID` | Stations | `"stationId": "101"` |
| `userId` / `User_ID` | Users | `"userId": "1001"` |
| `routeId` / `Route_ID` | Train_Routes | `"routeId": "301"` |
| `bookingId` / `Booking_ID` | Bookings | `"bookingId": "501"` |
| `parentModuleId` / `Parent_Module_ID` | Module_Master | `"parentModuleId": "1401"` |

---

## Sample Test Data IDs

For testing, use these sample IDs (create them first):

| Entity | Sample ROWID | Sample Code/Number |
|--------|--------------|-------------------|
| User | 1001 | john.doe@example.com |
| Admin | 1002 | admin@railway.com |
| Station (Delhi) | 101 | NDLS |
| Station (Mumbai) | 102 | CSTM |
| Station (Howrah) | 103 | HWH |
| Train (Rajdhani) | 201 | 12301 |
| Route | 301 | Delhi-Howrah |
| Booking | 501 | PNR8A4BC2D1 |
| Module | 1401 | DASHBOARD |

---

*Generated: 2026-03-27 | Smart Railway Ticketing System v2.0*
