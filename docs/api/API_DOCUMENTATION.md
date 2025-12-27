# SmartHR360 API Documentation

**Complete API Reference Guide**

Last Updated: November 26, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Accounts Module](#accounts-module)
4. [HR Module](#hr-module)
5. [Reviews Module](#reviews-module)
6. [Wellbeing Module](#wellbeing-module)
7. [API Documentation Tools](#api-documentation-tools)

---

## Overview

SmartHR360 is a comprehensive HR management system built with Django REST Framework. The API follows RESTful conventions and returns responses in JSON format with a standardized envelope structure:

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-26T10:30:00Z",
    "path": "/api/endpoint/",
    "request_id": "unique-id"
  }
}
```

**Base URL**: `http://localhost:8000/` (development)

**Authentication**: JWT Bearer Token (except where specified as "Public")

---

## Authentication

All API endpoints require authentication via JWT tokens unless marked as public. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Accounts Module

Base Path: `/api/auth/`

### 1. **Register**

- **Endpoint**: `POST /api/auth/register/`
- **Authentication**: Public (No authentication required)
- **Description**: Create a new user account
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE"
  }
  ```
- **Roles**: `EMPLOYEE`, `MANAGER`, `HR`, `ADMIN`
- **Response**: Returns user object and JWT tokens (access + refresh)
- **Status Codes**:
  - `201 Created`: Success
  - `400 Bad Request`: Validation errors

---

### 2. **Login**

- **Endpoint**: `POST /api/auth/login/`
- **Authentication**: Public
- **Description**: Authenticate user and receive JWT tokens. Logs login activity.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response**: User object and tokens
- **Features**:
  - Rate limiting after multiple failed attempts
  - Account lockout after excessive failures
  - Login activity tracking (IP, user agent)
- **Status Codes**:
  - `200 OK`: Success
  - `401 Unauthorized`: Invalid credentials
  - `403 Forbidden`: Account locked

---

### 3. **Refresh Token**

- **Endpoint**: `POST /api/auth/refresh/`
- **Authentication**: Public (requires refresh token)
- **Description**: Get a new access token using a valid refresh token
- **Request Body**:
  ```json
  {
    "refresh": "refresh_token_here"
  }
  ```
- **Response**: New access token
- **Status Codes**:
  - `200 OK`: Success
  - `401 Unauthorized`: Invalid/expired refresh token

---

### 4. **Get Current User**

- **Endpoint**: `GET /api/auth/me/`
- **Authentication**: Required
- **Description**: Retrieve current authenticated user's profile
- **Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE",
    "is_active": true,
    "is_email_verified": true,
    "is_staff": false,
    "date_joined": "2025-01-15T10:00:00Z"
  }
  ```
- **Status Codes**:
  - `200 OK`: Success
  - `401 Unauthorized`: Not authenticated

---

### 5. **List All Users**

- **Endpoint**: `GET /api/auth/users/`
- **Authentication**: Required (HR/ADMIN or SUPPORT group)
- **Description**: Retrieve a list of all registered users (HR/ADMIN or SUPPORT)
- **Response**: Array of user objects
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions

---

### 6. **Change Password**

- **Endpoint**: `POST /api/auth/change-password/`
- **Authentication**: Required
- **Description**: Change password for authenticated user
- **Request Body**:
  ```json
  {
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!",
    "confirm_password": "NewPassword456!"
  }
  ```
- **Response**: Success message
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Validation errors (wrong old password, password mismatch)

---

### 7. **Logout**

- **Endpoint**: `POST /api/auth/logout/`
- **Authentication**: Required
- **Description**: Logout user by blacklisting refresh token. Records logout activity.
- **Request Body**:
  ```json
  {
    "refresh": "refresh_token_here"
  }
  ```
- **Response**: Success message
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Invalid token

---

### 8. **Request Password Reset**

- **Endpoint**: `POST /api/auth/password-reset/request/`
- **Authentication**: Public
- **Description**: Request password reset token (sent via email in production, returned in debug mode)
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**: Success message (always returns success even if email doesn't exist - security measure)
- **Debug Mode**: Returns token in response
- **Token Expiration**: 1 hour
- **Status Codes**:
  - `200 OK`: Always success

---

### 9. **Confirm Password Reset**

- **Endpoint**: `POST /api/auth/password-reset/confirm/`
- **Authentication**: Public
- **Description**: Reset password using the token received
- **Request Body**:
  ```json
  {
    "token": "reset_token_here",
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }
  ```
- **Response**: Success message
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Invalid/expired token or validation errors

---

### 10. **Request Email Verification**

- **Endpoint**: `POST /api/auth/email/verify/request/`
- **Authentication**: Public
- **Description**: Request email verification token
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**: Success message
- **Debug Mode**: Returns token in response
- **Token Expiration**: 24 hours
- **Status Codes**:
  - `200 OK`: Success

---

### 11. **Confirm Email Verification**

- **Endpoint**: `POST /api/auth/email/verify/confirm/`
- **Authentication**: Public
- **Description**: Verify email address using the token
- **Request Body**:
  ```json
  {
    "token": "verification_token_here"
  }
  ```
- **Response**: Success message
- **Effect**: Sets `is_email_verified = True` on user account
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Invalid/expired token

---

## HR Module

Base Path: `/api/hr/`

### Departments

#### 1. **List/Create Departments**

- **Endpoint**: `GET /api/hr/departments/`
- **Authentication**: Required
- **Description**: List all departments
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Information Technology",
      "code": "IT",
      "description": "Technology department"
    }
  ]
  ```
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/hr/departments/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Create a new department
- **Request Body**:
  ```json
  {
    "name": "Information Technology",
    "code": "IT",
    "description": "Technology department"
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 2. **Department Detail**

- **Endpoint**: `GET /api/hr/departments/{id}/`
- **Authentication**: Required
- **Description**: Get department details
- **Access Control**: Any authenticated user

---

- **Endpoint**: `PATCH /api/hr/departments/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Update department

---

- **Endpoint**: `DELETE /api/hr/departments/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Delete department

---

### Employee Profiles

#### 3. **Get Current Employee Profile**

- **Endpoint**: `GET /api/hr/employees/me/`
- **Authentication**: Required
- **Description**: Get authenticated user's employee profile (auto-created if doesn't exist)
- **Response**:
  ```json
  {
    "id": 1,
    "user_id": 5,
    "user_email": "john@example.com",
    "user_full_name": "John Doe",
    "department_id": 2,
    "department_name": "IT",
    "manager_id": 3,
    "manager_name": "Jane Manager",
    "job_title": "Software Engineer",
    "employment_type": "FULL_TIME",
    "hire_date": "2024-01-15",
    "date_of_birth": "1990-05-20",
    "phone_number": "+1234567890",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2025-11-26T10:00:00Z"
  }
  ```
- **Status Codes**: `200 OK`

---

- **Endpoint**: `PATCH /api/hr/employees/me/`
- **Authentication**: Required
- **Description**: Update own employee profile (limited fields)
- **Allowed Fields**: `phone_number`, `date_of_birth`
- **Request Body**:
  ```json
  {
    "phone_number": "+1234567890",
    "date_of_birth": "1990-05-20"
  }
  ```
- **Status Codes**: `200 OK`

---

#### 4. **List/Create Employees**

- **Endpoint**: `GET /api/hr/employees/`
- **Authentication**: Required (HR/ADMIN or AUDITOR read-only)
- **Description**: List all employee profiles with filtering
- **Access Control**:
  - **HR/ADMIN**: View all employees
  - **AUDITOR**: Read-only access to all employees
- **Query Parameters**:
  - `department`: Filter by department code (e.g., `?department=IT`)
  - `is_active`: Filter by active status (e.g., `?is_active=true`)
  - `manager`: Filter by manager ID (e.g., `?manager=3`)
- **Examples**:
  - `/api/hr/employees/?department=IT`
  - `/api/hr/employees/?is_active=false`
  - `/api/hr/employees/?manager=3&department=IT`
- **Response**: Array of employee profile objects
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/hr/employees/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Create employee profile for a user
- **Request Body**:
  ```json
  {
    "user_id": 5,
    "department_id": 2,
    "manager_id": 3,
    "job_title": "Software Engineer",
    "employment_type": "FULL_TIME",
    "hire_date": "2024-01-15",
    "is_active": true
  }
  ```
- **Employment Types**: `FULL_TIME`, `PART_TIME`, `INTERN`, `CONTRACTOR`
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 5. **Employee Detail**

- **Endpoint**: `GET /api/hr/employees/{id}/`
- **Authentication**: Required
- **Description**: Get employee profile details
- **Access Control**:
  - **HR/ADMIN**: Can view any employee
  - **MANAGER**: Can view their direct team members
  - **EMPLOYEE**: Can view only their own profile
  - **AUDITOR**: Read-only access to all employees
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions
  - `404 Not Found`: Employee not found

---

- **Endpoint**: `PATCH /api/hr/employees/{id}/`
- **Authentication**: Required
- **Description**: Update employee profile
- **Access Control**: Same as GET
- **Status Codes**: `200 OK`

---

#### 6. **My Team**

- **Endpoint**: `GET /api/hr/employees/my-team/`
- **Authentication**: Required (MANAGER, HR, ADMIN, or AUDITOR read-only)
- **Description**: List employees in current user's team
- **Behavior**:
  - **HR/ADMIN**: Returns all employees
  - **MANAGER**: Returns only direct reports
  - **AUDITOR**: Returns all employees (read-only)
- **Response**: Array of employee profile objects
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions

---

### Skills

#### 7. **List/Create Skills**

- **Endpoint**: `GET /api/hr/skills/`
- **Authentication**: Required
- **Description**: List all active skills in the catalog
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Python Programming",
      "code": "PYTHON",
      "description": "Python development skills",
      "category": "Technical",
      "is_active": true,
      "created_by_id": 2,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
  ```
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/hr/skills/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Create a new skill in the catalog
- **Request Body**:
  ```json
  {
    "name": "Python Programming",
    "code": "PYTHON",
    "description": "Python development skills",
    "category": "Technical",
    "is_active": true
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 8. **Skill Detail**

- **Endpoint**: `GET /api/hr/skills/{id}/`
- **Authentication**: Required
- **Description**: Get skill details

---

- **Endpoint**: `PATCH /api/hr/skills/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Update skill

---

- **Endpoint**: `DELETE /api/hr/skills/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Delete skill

---

### Employee Skills

#### 9. **List/Create Employee Skills**

- **Endpoint**: `GET /api/hr/employee-skills/`
- **Authentication**: Required
- **Description**: List employee skill evaluations
- **Access Control**:
  - **HR/ADMIN**: View all employee skills
  - **MANAGER**: View team member skills
  - **EMPLOYEE**: View only their own skills
  - **AUDITOR**: Read-only access to all employee skills
- **Response**:
  ```json
  [
    {
      "id": 1,
      "employee_id": 5,
      "employee_name": "John Doe",
      "skill_id": 1,
      "skill_name": "Python Programming",
      "proficiency_level": "ADVANCED",
      "years_of_experience": 5,
      "last_evaluated_by_id": 3,
      "last_evaluated_at": "2025-11-20T10:00:00Z",
      "notes": "Strong Python skills"
    }
  ]
  ```
- **Proficiency Levels**: `BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/hr/employee-skills/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Create skill evaluation for an employee
- **Request Body**:
  ```json
  {
    "employee_id": 5,
    "skill_id": 1,
    "proficiency_level": "ADVANCED",
    "years_of_experience": 5,
    "notes": "Strong Python skills"
  }
  ```
- **Validation**:
  - MANAGER can only create evaluations for their team members
  - HR/ADMIN can create for any employee
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 10. **Employee Skill Detail**

- **Endpoint**: `GET /api/hr/employee-skills/{id}/`
- **Authentication**: Required
- **Description**: Get employee skill evaluation details
- **Access Control**: Same as list endpoint

---

- **Endpoint**: `PATCH /api/hr/employee-skills/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Update employee skill evaluation
- **Access Control**: Same as create endpoint
- **Status Codes**: `200 OK`

---

### Future Competencies

#### 11. **List/Create Future Competencies**

- **Endpoint**: `GET /api/hr/future-competencies/`
- **Authentication**: Required
- **Description**: List future competencies (skills needed in the future)
- **Response**:
  ```json
  [
    {
      "id": 1,
      "skill_id": 5,
      "skill_name": "AI/Machine Learning",
      "department_id": 2,
      "department_name": "IT",
      "priority": "HIGH",
      "target_date": "2026-06-30",
      "description": "AI skills needed for upcoming projects",
      "created_by_id": 2,
      "created_at": "2025-11-01T10:00:00Z"
    }
  ]
  ```
- **Priority Levels**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/hr/future-competencies/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Create future competency requirement
- **Request Body**:
  ```json
  {
    "skill_id": 5,
    "department_id": 2,
    "priority": "HIGH",
    "target_date": "2026-06-30",
    "description": "AI skills needed for upcoming projects"
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 12. **Future Competency Detail**

- **Endpoint**: `GET /api/hr/future-competencies/{id}/`
- **Authentication**: Required
- **Description**: Get future competency details

---

- **Endpoint**: `PATCH /api/hr/future-competencies/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Update future competency

---

- **Endpoint**: `DELETE /api/hr/future-competencies/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Delete future competency

---

## Reviews Module

Base Path: `/api/reviews/`

### Review Cycles

#### 1. **List/Create Review Cycles**

- **Endpoint**: `GET /api/reviews/cycles/`
- **Authentication**: Required
- **Description**: List all review cycles
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Q1 2025 Review",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "is_active": true,
      "created_at": "2024-12-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
  ```
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/reviews/cycles/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Create a new review cycle
- **Request Body**:
  ```json
  {
    "name": "Q1 2025 Review",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "is_active": true
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 2. **Review Cycle Detail**

- **Endpoint**: `GET /api/reviews/cycles/{id}/`
- **Authentication**: Required
- **Description**: Get review cycle details

---

- **Endpoint**: `PATCH /api/reviews/cycles/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Update review cycle

---

### Performance Reviews

#### 3. **List/Create Performance Reviews**

- **Endpoint**: `GET /api/reviews/`
- **Authentication**: Required
- **Description**: List performance reviews
- **Access Control**:
  - **HR/ADMIN**: View all reviews
  - **MANAGER**: View reviews where they are the manager
  - **EMPLOYEE**: View only their own reviews
  - **AUDITOR**: Read-only access to all reviews
- **Response**:
  ```json
  [
    {
      "id": 1,
      "employee_id": 5,
      "employee_name": "John Doe",
      "manager_id": 3,
      "manager_name": "Jane Manager",
      "cycle_id": 1,
      "cycle_name": "Q1 2025 Review",
      "status": "DRAFT",
      "overall_score": null,
      "employee_comment": "",
      "manager_comment": "",
      "items": [],
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
  ```
- **Review Status**: `DRAFT`, `SUBMITTED`, `COMPLETED`
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/reviews/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Create a performance review
- **Request Body**:
  ```json
  {
    "employee_id": 5,
    "cycle_id": 1
  }
  ```
- **Validation**:
  - MANAGER can only create reviews for their direct reports
  - HR/ADMIN can create for any employee
  - One review per employee per cycle (enforced by database constraint)
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions
  - `400 Bad Request`: Validation errors

---

#### 4. **Performance Review Detail**

- **Endpoint**: `GET /api/reviews/{id}/`
- **Authentication**: Required
- **Description**: Get performance review details
- **Access Control**: Same as list endpoint (AUDITOR read-only)

---

- **Endpoint**: `PATCH /api/reviews/{id}/`
- **Authentication**: Required
- **Description**: Update performance review
- **Access Control**:
  - **HR/ADMIN**: Can always update
  - **MANAGER**: Can update only if they are the review manager AND status is DRAFT
  - **EMPLOYEE**: Can update only `employee_comment` field while status is DRAFT
- **Request Body**:
  ```json
  {
    "manager_comment": "Good performance this quarter",
    "employee_comment": "Thank you for the feedback"
  }
  ```
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 5. **Submit Review**

- **Endpoint**: `POST /api/reviews/{id}/submit/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Submit a review (change status from DRAFT to SUBMITTED)
- **Request Body**:
  ```json
  {
    "manager_comment": "Final comments before submission"
  }
  ```
- **Validation**:
  - Only DRAFT reviews can be submitted
  - MANAGER can only submit reviews they created
- **Effect**: Changes status to SUBMITTED
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Review not in DRAFT status
  - `403 Forbidden`: Insufficient permissions

---

#### 6. **Acknowledge Review**

- **Endpoint**: `POST /api/reviews/{id}/acknowledge/`
- **Authentication**: Required (Employee being reviewed)
- **Description**: Employee acknowledges their review (change status from SUBMITTED to COMPLETED)
- **Request Body**:
  ```json
  {
    "employee_comment": "I acknowledge and understand this review"
  }
  ```
- **Validation**:
  - Only SUBMITTED reviews can be acknowledged
  - Only the employee being reviewed can acknowledge
- **Effect**: Changes status to COMPLETED
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Review not in SUBMITTED status
  - `403 Forbidden`: Not the employee being reviewed

---

### Review Items

#### 7. **List/Create Review Items**

- **Endpoint**: `GET /api/reviews/{review_id}/items/`
- **Authentication**: Required
- **Description**: List items (criteria) within a performance review
- **Access Control**: Same visibility as parent review (AUDITOR read-only)
- **Response**:
  ```json
  [
    {
      "id": 1,
      "review_id": 1,
      "criterion": "Technical Skills",
      "score": 4.5,
      "comments": "Excellent technical abilities",
      "created_at": "2025-01-15T11:00:00Z"
    }
  ]
  ```
- **Score Range**: 1.0 to 5.0
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/reviews/{review_id}/items/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Add a review item to a DRAFT review
- **Request Body**:
  ```json
  {
    "criterion": "Technical Skills",
    "score": 4.5,
    "comments": "Excellent technical abilities"
  }
  ```
- **Validation**:
  - Items can only be added to DRAFT reviews
  - MANAGER can only add to their own reviews
- **Effect**: Recalculates overall_score of the review
- **Status Codes**:
  - `201 Created`: Success
  - `400 Bad Request`: Review not in DRAFT status
  - `403 Forbidden`: Insufficient permissions

---

#### 8. **Review Item Detail**

- **Endpoint**: `GET /api/reviews/items/{id}/`
- **Authentication**: Required
- **Description**: Get review item details
- **Access Control**: Same as parent review

---

- **Endpoint**: `PATCH /api/reviews/items/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Update review item (only on DRAFT reviews)
- **Effect**: Recalculates overall_score
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Review not in DRAFT status

---

- **Endpoint**: `DELETE /api/reviews/items/{id}/`
- **Authentication**: Required (MANAGER, HR, or ADMIN)
- **Description**: Delete review item (only on DRAFT reviews)
- **Effect**: Recalculates overall_score
- **Status Codes**:
  - `200 OK`: Success
  - `400 Bad Request`: Review not in DRAFT status

---

### Goals

#### 9. **List/Create Goals**

- **Endpoint**: `GET /api/reviews/goals/`
- **Authentication**: Required
- **Description**: List goals
- **Access Control**:
  - **HR/ADMIN**: View all goals
  - **MANAGER**: View team goals
  - **EMPLOYEE**: View own goals
  - **AUDITOR**: Read-only access to all goals
- **Query Parameters**:
  - `employee_id`: Filter by employee (e.g., `?employee_id=5`)
  - `cycle_id`: Filter by review cycle (e.g., `?cycle_id=1`)
- **Response**:
  ```json
  [
    {
      "id": 1,
      "employee_id": 5,
      "employee_name": "John Doe",
      "cycle_id": 1,
      "cycle_name": "Q1 2025 Review",
      "title": "Complete certification",
      "description": "Complete AWS certification by end of quarter",
      "target_date": "2025-03-31",
      "status": "IN_PROGRESS",
      "progress": 50,
      "created_by_id": 5,
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-02-15T10:00:00Z"
    }
  ]
  ```
- **Goal Status**: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/reviews/goals/`
- **Authentication**: Required
- **Description**: Create a goal
- **Request Body**:
  ```json
  {
    "employee_id": 5,
    "cycle_id": 1,
    "title": "Complete certification",
    "description": "Complete AWS certification by end of quarter",
    "target_date": "2025-03-31",
    "status": "NOT_STARTED"
  }
  ```
- **Access Control**:
  - **EMPLOYEE**: Can create own goals (employee_id optional, defaults to self)
  - **MANAGER**: Can create goals for team members
  - **HR/ADMIN**: Can create goals for any employee
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 10. **Goal Detail**

- **Endpoint**: `GET /api/reviews/goals/{id}/`
- **Authentication**: Required
- **Description**: Get goal details
- **Access Control**: Same as list endpoint

---

- **Endpoint**: `PATCH /api/reviews/goals/{id}/`
- **Authentication**: Required
- **Description**: Update goal
- **Access Control**:
  - **EMPLOYEE**: Can update own goals
  - **MANAGER**: Can update team goals
  - **HR/ADMIN**: Can update any goal
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions

---

- **Endpoint**: `DELETE /api/reviews/goals/{id}/`
- **Authentication**: Required
- **Description**: Delete goal
- **Access Control**: Same as update

---

## Wellbeing Module

Base Path: `/api/wellbeing/`

### Wellbeing Surveys

#### 1. **List/Create Wellbeing Surveys**

- **Endpoint**: `GET /api/wellbeing/surveys/`
- **Authentication**: Required
- **Description**: List all wellbeing surveys
- **Response**:
  ```json
  [
    {
      "id": 1,
      "title": "Q1 2025 Wellbeing Survey",
      "description": "Quarterly mental health and satisfaction survey",
      "is_active": true,
      "created_by_id": 2,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
  ```
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/wellbeing/surveys/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Create a wellbeing survey
- **Request Body**:
  ```json
  {
    "title": "Q1 2025 Wellbeing Survey",
    "description": "Quarterly mental health and satisfaction survey",
    "is_active": true
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 2. **Wellbeing Survey Detail**

- **Endpoint**: `GET /api/wellbeing/surveys/{id}/`
- **Authentication**: Required
- **Description**: Get survey details

---

- **Endpoint**: `PATCH /api/wellbeing/surveys/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Update survey

---

### Survey Questions

#### 3. **List/Create Survey Questions**

- **Endpoint**: `GET /api/wellbeing/surveys/{survey_id}/questions/`
- **Authentication**: Required
- **Description**: List questions for a survey
- **Response**:
  ```json
  [
    {
      "id": 1,
      "survey_id": 1,
      "text": "How satisfied are you with your work-life balance?",
      "type": "SCALE_1_5",
      "order": 1,
      "created_at": "2025-01-01T11:00:00Z"
    }
  ]
  ```
- **Question Types**:
  - `SCALE_1_5`: Numeric rating 1-5
  - `YES_NO`: Yes/No question
  - `TEXT`: Free text response
- **Status Codes**: `200 OK`

---

- **Endpoint**: `POST /api/wellbeing/surveys/{survey_id}/questions/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Add a question to a survey
- **Request Body**:
  ```json
  {
    "text": "How satisfied are you with your work-life balance?",
    "type": "SCALE_1_5",
    "order": 1
  }
  ```
- **Status Codes**:
  - `201 Created`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 4. **Survey Question Detail**

- **Endpoint**: `GET /api/wellbeing/questions/{id}/`
- **Authentication**: Required
- **Description**: Get question details

---

- **Endpoint**: `PATCH /api/wellbeing/questions/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Update question

---

- **Endpoint**: `DELETE /api/wellbeing/questions/{id}/`
- **Authentication**: Required (HR or ADMIN only)
- **Description**: Delete question

---

### Survey Submission

#### 5. **Submit Survey Response**

- **Endpoint**: `POST /api/wellbeing/surveys/{survey_id}/submit/`
- **Authentication**: Required
- **Description**: Submit anonymous survey response
- **Request Body**:
  ```json
  {
    "answers": {
      "1": 4,
      "2": "yes",
      "3": "I feel satisfied with my role"
    }
  }
  ```
- **Answer Format**: `{ "question_id": "answer_value" }`
- **Privacy**:
  - Responses are **anonymous**
  - No link to user or employee profile stored
  - Only department (if available) is stored for aggregated stats
  - No IP address or user agent stored
  - Each response gets a random UUID
- **Status Codes**:
  - `201 Created`: Success
  - `400 Bad Request`: Survey not active or validation errors

---

### Survey Statistics

#### 6. **Get Survey Stats**

- **Endpoint**: `GET /api/wellbeing/surveys/{survey_id}/stats/`
- **Authentication**: Required (HR, ADMIN, or AUDITOR)
- **Description**: Get global statistics for a survey
- **Response**:
  ```json
  {
    "count_responses": 25,
    "questions": [
      {
        "id": 1,
        "text": "How satisfied are you with your work-life balance?",
        "type": "SCALE_1_5",
        "avg": 3.8,
        "distribution": {
          "1": 2,
          "2": 3,
          "3": 5,
          "4": 10,
          "5": 5
        }
      },
      {
        "id": 2,
        "text": "Do you feel supported by your manager?",
        "type": "YES_NO",
        "yes": 20,
        "no": 5
      },
      {
        "id": 3,
        "text": "Any additional comments?",
        "type": "TEXT",
        "count_text": 15
      }
    ]
  }
  ```
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Insufficient permissions

---

#### 7. **Get Team Stats**

- **Endpoint**: `GET /api/wellbeing/surveys/{survey_id}/team-stats/`
- **Authentication**: Required (MANAGER, HR, ADMIN, or AUDITOR)
- **Description**: Get aggregated statistics for manager's team or department
- **Response**:
  ```json
  {
    "team_size": 10,
    "responses": 8,
    "aggregates": {
      "1": 4.2,
      "3": 3.8,
      "5": 4.5
    }
  }
  ```
- **Access Control**:
  - **HR/ADMIN**: Stats for all employees
  - **MANAGER**: Stats for direct reports' departments
  - **AUDITOR**: Stats for all employees (read-only)
- **Aggregates**: Only computed for SCALE_1_5 questions (average scores)
- **Status Codes**:
  - `200 OK`: Success
  - `403 Forbidden`: Not a manager or above

---

## API Documentation Tools

### Interactive Documentation

The API provides interactive documentation through multiple interfaces:

#### 1. **OpenAPI Schema**

- **Endpoint**: `GET /api/schema/`
- **Format**: OpenAPI 3.0 JSON/YAML
- **Description**: Machine-readable API specification

---

#### 2. **Swagger UI**

- **Endpoint**: `GET /docs/`
- **Description**: Interactive API documentation with "Try it out" functionality
- **Features**:
  - Test API endpoints directly from the browser
  - View request/response schemas
  - Authentication support

---

#### 3. **ReDoc**

- **Endpoint**: `GET /redoc/`
- **Description**: Clean, three-panel API documentation
- **Features**:
  - Responsive design
  - Search functionality
  - Code samples

---

## Common Response Patterns

### Success Response

```json
{
  "data": {
    "id": 1,
    "name": "Example"
  },
  "meta": {
    "timestamp": "2025-11-26T10:30:00Z",
    "path": "/api/endpoint/",
    "request_id": "abc-123"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input data",
    "details": {
      "field_name": ["Error message"]
    }
  },
  "meta": {
    "timestamp": "2025-11-26T10:30:00Z",
    "path": "/api/endpoint/",
    "request_id": "abc-123"
  }
}
```

### Pagination Response

```json
{
  "data": {
    "count": 100,
    "next": "http://localhost:8000/api/endpoint/?page=2",
    "previous": null,
    "results": [ ... ]
  },
  "meta": { ... }
}
```

---

## HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

- Login attempts are rate-limited to prevent brute force attacks
- After 5 failed login attempts, account is temporarily locked
- Account automatically unlocks after 30 minutes (configurable)

---

## Notes

1. **Timestamps**: All timestamps are in ISO 8601 format with UTC timezone
2. **IDs**: All resource IDs are integers
3. **Email**: Email addresses are case-insensitive
4. **Passwords**: Must be strong (minimum 8 characters, mix of letters, numbers, symbols)
5. **Token Expiration**:
   - Access tokens: 30 minutes
   - Refresh tokens: 7 days
   - Password reset tokens: 1 hour
   - Email verification tokens: 24 hours

---

**End of API Documentation**
