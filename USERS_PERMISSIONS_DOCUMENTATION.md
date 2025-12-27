# SmartHR360 User Roles & Permissions Documentation

**Complete User Roles and Access Control Guide**

Last Updated: December 27, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [User Roles](#user-roles)
3. [Role Hierarchy](#role-hierarchy)
4. [Permission Matrix](#permission-matrix)
5. [Module-Specific Permissions](#module-specific-permissions)
6. [Object-Level Permissions](#object-level-permissions)
7. [Special Access Rules](#special-access-rules)
8. [Permission Examples](#permission-examples)

---

## Overview

SmartHR360 implements a hierarchical role-based access control (RBAC) system with four distinct user roles. Each role has specific permissions that determine what actions a user can perform and what data they can access.

**Authentication Method**: JWT (JSON Web Token)

**Permission Enforcement**:

- View-level permissions (applied to entire endpoints)
- Object-level permissions (applied to individual resources)
- Field-level restrictions (certain fields editable only by specific roles)

---

## User Roles

### 1. **EMPLOYEE** (Base Level)

- **Description**: Standard employee with access to their own information
- **Primary Use**: Regular employees who need to view their profile, participate in reviews, and complete wellbeing surveys
- **Rank**: 1 (lowest)

### 2. **MANAGER** (Supervisory Level)

- **Description**: Team lead or manager with access to their team members' information
- **Primary Use**: Managing direct reports, conducting performance reviews, and viewing team statistics
- **Rank**: 2

### 3. **HR** (Human Resources Level)

- **Description**: HR personnel with broad access across all employees and HR functions
- **Primary Use**: Managing all employee data, creating surveys, managing review cycles, and viewing organization-wide statistics
- **Rank**: 3

### 4. **ADMIN** (Highest Level)

- **Description**: System administrator with full access to all features
- **Primary Use**: System configuration, user management, and all HR functions
- **Rank**: 4 (highest)

### Special Groups (Non-role)

- **AUDITOR**: Read-only access to HR, Reviews, and Wellbeing endpoints (list/detail only)
- **SUPPORT**: Can list users via `GET /api/auth/users/`
- **SECURITY_ADMIN**: Reserved for security-focused endpoints (future use)

---

## Role Hierarchy

SmartHR360 uses a hierarchical permission system where higher roles inherit permissions from lower roles:

```
ADMIN (Rank 4)
  ↓
  └── Has all permissions of HR + additional admin rights

HR (Rank 3)
  ↓
  └── Has all permissions of MANAGER + HR-specific rights

MANAGER (Rank 2)
  ↓
  └── Has all permissions of EMPLOYEE + team management rights

EMPLOYEE (Rank 1)
  └── Basic employee permissions
```

**Hierarchy Methods**:

- `user.has_role(Role.HR, Role.ADMIN)`: Check if user has one of the specified roles
- `user.is_at_least(Role.MANAGER)`: Check if user's rank is equal to or higher than specified role

---

## Permission Matrix

### Complete Access Control Table

| Feature                      | EMPLOYEE        | MANAGER                | HR          | ADMIN       |
| ---------------------------- | --------------- | ---------------------- | ----------- | ----------- |
| **Authentication**           |
| Register account             | ✅ Public       | ✅ Public              | ✅ Public   | ✅ Public   |
| Login/Logout                 | ✅ Public       | ✅ Public              | ✅ Public   | ✅ Public   |
| View own profile             | ✅              | ✅                     | ✅          | ✅          |
| Change own password          | ✅              | ✅                     | ✅          | ✅          |
| List all users (SUPPORT group) | ❌              | ❌                     | ✅          | ✅          |
| Reset password (self)        | ✅ Public       | ✅ Public              | ✅ Public   | ✅ Public   |
| **Departments**              |
| View departments             | ✅              | ✅                     | ✅          | ✅          |
| Create department            | ❌              | ❌                     | ✅          | ✅          |
| Update department            | ❌              | ❌                     | ✅          | ✅          |
| Delete department            | ❌              | ❌                     | ✅          | ✅          |
| **Employee Profiles**        |
| View own profile             | ✅              | ✅                     | ✅          | ✅          |
| Update own profile (limited) | ✅              | ✅                     | ✅          | ✅          |
| View team profiles           | ❌              | ✅ Team only           | ✅ All      | ✅ All      |
| View all employee profiles   | ❌              | ❌                     | ✅          | ✅          |
| Create employee profile      | ❌              | ❌                     | ✅          | ✅          |
| Update any employee profile  | ❌              | ❌                     | ✅          | ✅          |
| View My Team endpoint        | ❌              | ✅                     | ✅          | ✅          |
| **Skills Catalog**           |
| View skills                  | ✅              | ✅                     | ✅          | ✅          |
| Create skill                 | ❌              | ✅                     | ✅          | ✅          |
| Update skill                 | ❌              | ✅                     | ✅          | ✅          |
| Delete skill                 | ❌              | ✅                     | ✅          | ✅          |
| **Employee Skills**          |
| View own skills              | ✅              | ✅                     | ✅          | ✅          |
| View team skills             | ❌              | ✅ Team only           | ✅ All      | ✅ All      |
| Create skill evaluation      | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| Update skill evaluation      | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| **Future Competencies**      |
| View future competencies     | ✅              | ✅                     | ✅          | ✅          |
| Create future competency     | ❌              | ✅                     | ✅          | ✅          |
| Update future competency     | ❌              | ✅                     | ✅          | ✅          |
| Delete future competency     | ❌              | ✅                     | ✅          | ✅          |
| **Review Cycles**            |
| View review cycles           | ✅              | ✅                     | ✅          | ✅          |
| Create review cycle          | ❌              | ❌                     | ✅          | ✅          |
| Update review cycle          | ❌              | ❌                     | ✅          | ✅          |
| **Performance Reviews**      |
| View own reviews             | ✅              | ✅                     | ✅          | ✅          |
| View team reviews            | ❌              | ✅ Team only           | ✅ All      | ✅ All      |
| Create review                | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| Update own review (DRAFT)    | ✅ Comment only | ✅ If manager          | ✅          | ✅          |
| Submit review                | ❌              | ✅ Own reviews         | ✅          | ✅          |
| Acknowledge review           | ✅ Own only     | ✅ Own only            | ✅ Own only | ✅ Own only |
| **Review Items**             |
| View review items            | ✅ Own reviews  | ✅ Team reviews        | ✅ All      | ✅ All      |
| Create review item           | ❌              | ✅ Own reviews (DRAFT) | ✅ (DRAFT)  | ✅ (DRAFT)  |
| Update review item           | ❌              | ✅ Own reviews (DRAFT) | ✅ (DRAFT)  | ✅ (DRAFT)  |
| Delete review item           | ❌              | ✅ Own reviews (DRAFT) | ✅ (DRAFT)  | ✅ (DRAFT)  |
| **Goals**                    |
| View own goals               | ✅              | ✅                     | ✅          | ✅          |
| View team goals              | ❌              | ✅ Team only           | ✅ All      | ✅ All      |
| Create own goal              | ✅              | ✅                     | ✅          | ✅          |
| Create team goal             | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| Update own goal              | ✅              | ✅                     | ✅          | ✅          |
| Update team goal             | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| Delete own goal              | ✅              | ✅                     | ✅          | ✅          |
| Delete team goal             | ❌              | ✅ Team only           | ✅ Any      | ✅ Any      |
| **Wellbeing Surveys**        |
| View surveys                 | ✅              | ✅                     | ✅          | ✅          |
| Create survey                | ❌              | ❌                     | ✅          | ✅          |
| Update survey                | ❌              | ❌                     | ✅          | ✅          |
| Create questions             | ❌              | ❌                     | ✅          | ✅          |
| Update questions             | ❌              | ❌                     | ✅          | ✅          |
| Delete questions             | ❌              | ❌                     | ✅          | ✅          |
| Submit survey response       | ✅              | ✅                     | ✅          | ✅          |
| View global survey stats     | ❌              | ❌                     | ✅          | ✅          |
| View team survey stats       | ❌              | ✅                     | ✅          | ✅          |

**Legend**:

- ✅ = Full access
- ✅ Public = Available without authentication
- ✅ Team only = Access restricted to direct reports
- ✅ Own only = Access restricted to user's own resources
- ✅ Comment only = Can only update comment fields
- ✅ (DRAFT) = Access restricted to DRAFT status items
- ❌ = No access

**Special groups**:

- **AUDITOR**: Read-only access to HR/Reviews/Wellbeing (list/detail)
- **SUPPORT**: Can list users via `GET /api/auth/users/`

---

## Module-Specific Permissions

### Accounts Module (`/api/auth/`)

#### Public Endpoints (No Authentication Required)

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/password-reset/request/`
- `POST /api/auth/password-reset/confirm/`
- `POST /api/auth/email/verify/request/`
- `POST /api/auth/email/verify/confirm/`

#### Authenticated Endpoints

**All Authenticated Users**:

- `GET /api/auth/me/` - View own profile
- `POST /api/auth/change-password/` - Change own password
- `POST /api/auth/logout/` - Logout

**HR/ADMIN or SUPPORT group**:

- `GET /api/auth/users/` - List all users

**Permission Class**: `IsHRRoleOrSupport`

---

### HR Module (`/api/hr/`)

#### Departments

**Read Access**: All authenticated users
**Write Access** (Create/Update/Delete): HR and ADMIN only

**Permission Classes**:

- List: `IsAuthenticated`
- Create: `IsHRRole`
- Detail (GET): `IsAuthenticated`
- Detail (PATCH/DELETE): `IsHRRole`

---

#### Employee Profiles

**Own Profile**:

- All authenticated users can view and update their own profile
- **Limited fields for self-update**: `phone_number`, `date_of_birth`
- Endpoint: `GET/PATCH /api/hr/employees/me/`

**Team Profiles**:

- **MANAGER**: Can view direct reports only
- **HR/ADMIN**: Can view all employees

**All Profiles**:

- **HR/ADMIN**: Full CRUD access
- **AUDITOR**: Read-only access to all profiles
- Query filters available: `department`, `is_active`, `manager`

**Permission Classes**:

- List/Create: `IsHROrAuditorReadOnly` (auditor = read-only)
- Detail: `IsAuthenticated` + `EmployeeProfileAccessPermission`
- My Team: `IsManagerOrAuditorReadOnly`

**Object-Level Permission**: `EmployeeProfileAccessPermission`

- HR/ADMIN: Full access to all profiles
- EMPLOYEE: Only their own profile
- MANAGER: Their direct team members only

---

#### Skills Catalog

**Read Access**: All authenticated users
**Write Access**: MANAGER, HR, and ADMIN

**Permission Classes**:

- List/Detail (GET): `IsAuthenticated`
- Create/Update/Delete: `IsManagerOrAbove`

---

#### Employee Skills (Evaluations)

**View Access**:

- **EMPLOYEE**: Own skills only
- **MANAGER**: Team member skills
- **HR/ADMIN**: All employee skills
- **AUDITOR**: Read-only access to all employee skills

**Create/Update Access**:

- **MANAGER**: Can evaluate direct reports only
- **HR/ADMIN**: Can evaluate any employee

**Permission Class**: `IsAuthenticated` (with custom queryset filtering)

**Business Rules**:

- Automatically tracks `last_evaluated_by` and `last_evaluated_at`
- Manager can only rate skills of their team members

---

#### Future Competencies

**Read Access**: All authenticated users
**Write Access**: MANAGER, HR, and ADMIN

**Permission Classes**:

- List/Detail (GET): `IsAuthenticated`
- Create/Update/Delete: `IsManagerOrAbove`

---

### Reviews Module (`/api/reviews/`)

#### Review Cycles

**Read Access**: All authenticated users
**Write Access**: HR and ADMIN only

**Permission Class**: `IsAuthenticated` (with role checks in perform_create/update)

---

#### Performance Reviews

**View Access**:

- **EMPLOYEE**: Own reviews only
- **MANAGER**: Reviews where they are the manager
- **HR/ADMIN**: All reviews
- **AUDITOR**: Read-only access to all reviews

**Create Access**:

- **MANAGER**: Can create reviews for direct reports only
- **HR/ADMIN**: Can create reviews for any employee

**Update Access**:

- **HR/ADMIN**: Can always update
- **MANAGER**: Can update only their own reviews while in DRAFT status
- **EMPLOYEE**: Can update only `employee_comment` field while review is DRAFT

**Submit Access** (DRAFT → SUBMITTED):

- **MANAGER**: Can submit only their own reviews
- **HR/ADMIN**: Can submit any review

**Acknowledge Access** (SUBMITTED → COMPLETED):

- **EMPLOYEE**: Can acknowledge only their own reviews

**Permission Class**: `IsAuthenticated` (with custom queryset and business logic)

**Review Status Workflow**:

1. **DRAFT**: Manager creates and edits review, adds items
2. **SUBMITTED**: Manager submits review
3. **COMPLETED**: Employee acknowledges review

---

#### Review Items

**Access Control**: Same visibility as parent review
**AUDITOR**: Read-only access to review items

**Restrictions**:

- Items can only be created/updated/deleted on DRAFT reviews
- Manager can only manage items on their own reviews
- HR/ADMIN can manage items on any review

**Effect**: Creating/updating/deleting items automatically recalculates the review's `overall_score`

---

#### Goals

**View Access**:

- **EMPLOYEE**: Own goals only
- **MANAGER**: Team goals
- **HR/ADMIN**: All goals
- **AUDITOR**: Read-only access to all goals

**Create Access**:

- **EMPLOYEE**: Can create own goals
- **MANAGER**: Can create goals for team members
- **HR/ADMIN**: Can create goals for any employee

**Update/Delete Access**:

- Users can update/delete their own goals
- Managers can update/delete team goals
- HR/ADMIN can update/delete any goal

**Query Filters**: `employee_id`, `cycle_id`

---

### Wellbeing Module (`/api/wellbeing/`)

#### Surveys and Questions

**View Surveys**: All authenticated users
**Create/Update Surveys**: HR and ADMIN only
**Manage Questions**: HR and ADMIN only

**Permission Class**: `IsAuthenticated` (with role checks in perform methods)

---

#### Survey Submission

**Access**: All authenticated users can submit responses

**Privacy Features**:

- Responses are **completely anonymous**
- No user ID or employee ID stored
- No IP address or user agent stored
- Only department (if available) stored for aggregated stats
- Each response assigned a random UUID
- Individual responses cannot be traced back to users

---

#### Survey Statistics

**Global Stats** (`/api/wellbeing/surveys/{id}/stats/`):

- **HR/ADMIN/AUDITOR**: View overall survey statistics
- Shows aggregated data for all responses
- Includes averages, distributions, and counts

**Team Stats** (`/api/wellbeing/surveys/{id}/team-stats/`):

- **MANAGER**: View aggregated stats for their team's departments
- **HR/ADMIN**: View stats for all employees
- **AUDITOR**: View stats for all employees (read-only)
- Only SCALE_1_5 questions show aggregate averages
- Privacy-preserving: Only shows aggregated department-level data

**Permission Classes**:

- Global Stats: `IsAuthenticated` (with HR/ADMIN/AUDITOR role check)
- Team Stats: `IsAuthenticated` (with MANAGER+/AUDITOR role check)

---

## Object-Level Permissions

### EmployeeProfileAccessPermission

Applied to individual employee profile objects:

```python
class EmployeeProfileAccessPermission:
    """
    - HR/ADMIN: Full access to all profiles
    - EMPLOYEE: Only their own profile
    - MANAGER: Only their direct team members
    - AUDITOR: Read-only access to all profiles
    """
```

**Usage**: `GET/PATCH /api/hr/employees/{id}/`

**Logic**:

1. If user is HR or ADMIN → Allow
2. If user is viewing their own profile → Allow
3. If user is MANAGER and the profile's manager is the user → Allow
4. If user is AUDITOR and request is read-only → Allow
5. Otherwise → Deny

---

### Review Access Control

Custom queryset filtering based on role:

```python
def _reviews_queryset_for_user(user):
    # HR & Admin → all reviews
    # Auditor → all reviews (read-only)
    # Manager → reviews where they are the manager
    # Employee → only own reviews
```

**Applied To**:

- Performance Reviews
- Review Items
- Goals

---

## Special Access Rules

### 1. **Self-Service Rules**

All users can manage their own resources:

- View and update own profile (limited fields)
- Change own password
- View own reviews
- Create own goals
- Acknowledge own reviews (when submitted)
- Submit anonymous survey responses

---

### 2. **Manager Team Rules**

Managers have special access limited to direct reports:

- View team member profiles
- Create performance reviews for team members
- View team reviews and goals
- Evaluate team member skills
- View team wellbeing statistics

**Enforcement**: Checks `employee.manager_id == manager_profile.id`

---

### 3. **Review Status Rules**

Certain actions are only allowed in specific review statuses:

| Action                | Allowed Status | Roles                                             |
| --------------------- | -------------- | ------------------------------------------------- |
| Add/Edit/Delete Items | DRAFT          | Manager (own), HR, ADMIN                          |
| Update Review         | DRAFT          | Manager (own), HR, ADMIN, Employee (comment only) |
| Submit Review         | DRAFT          | Manager (own), HR, ADMIN                          |
| Acknowledge Review    | SUBMITTED      | Employee (own only)                               |

---

### 4. **Read vs Write Permissions**

Many endpoints use `SAFE_METHODS` (GET, HEAD, OPTIONS) for read access:

**Pattern**:

- Read: All authenticated users or broader audience
- Write: Restricted to higher roles (MANAGER+, HR+, or ADMIN only)

**Examples**:

- Skills: All can read, MANAGER+ can write
- Departments: All can read, HR+ can write
- Future Competencies: All can read, MANAGER+ can write

---

### 5. **Auditor / Support Group Rules**

- **AUDITOR**: Read-only access to HR, Reviews, and Wellbeing endpoints (list/detail)
- **SUPPORT**: Can list users via `GET /api/auth/users/`

---

### 6. **Anonymous Privacy Rules**

Wellbeing survey responses are **strictly anonymous**:

- No user identification stored
- No IP address tracking
- No user agent logging
- Only department stored (for aggregation)
- Responses identified by random UUID only
- Individual responses cannot be retrieved or linked to users

---

## Permission Examples

### Example 1: Employee John (EMPLOYEE Role)

**Can Do**:

- ✅ View own profile
- ✅ Update phone number and date of birth
- ✅ View own performance reviews
- ✅ Acknowledge own reviews when submitted
- ✅ Create and manage own goals
- ✅ Submit wellbeing survey responses
- ✅ View department list
- ✅ View skills catalog

**Cannot Do**:

- ❌ View other employees' profiles
- ❌ Create performance reviews
- ❌ View team statistics
- ❌ Create skills or evaluate others
- ❌ Create surveys or view survey statistics
- ❌ Update department information

---

### Example 2: Manager Jane (MANAGER Role)

**Inherits all EMPLOYEE permissions, plus**:

**Can Do**:

- ✅ View direct reports' profiles
- ✅ Create performance reviews for team members
- ✅ Submit reviews for team members
- ✅ Add/edit review items on DRAFT reviews
- ✅ Evaluate team member skills
- ✅ Create goals for team members
- ✅ View team wellbeing statistics
- ✅ Create and manage skills in catalog
- ✅ Create future competencies

**Cannot Do**:

- ❌ View employees outside their team
- ❌ Create review cycles
- ❌ Create wellbeing surveys
- ❌ View global wellbeing statistics
- ❌ Manage departments
- ❌ List all users

**Team Scope**: Limited to employees where `employee.manager_id == jane.employee_profile.id`

---

### Example 3: HR Personnel Sarah (HR Role)

**Inherits all MANAGER permissions, plus**:

**Can Do**:

- ✅ View all employees (any department, any manager)
- ✅ Create and manage employee profiles
- ✅ List all users in the system
- ✅ Create and manage departments
- ✅ Create review cycles
- ✅ Create and manage wellbeing surveys
- ✅ Add questions to surveys
- ✅ View global survey statistics
- ✅ Create reviews for any employee
- ✅ Evaluate any employee's skills
- ✅ Update any performance review

**Cannot Do**: (Same as ADMIN, no restrictions)

**Scope**: Organization-wide access

---

### Example 4: System Admin Bob (ADMIN Role)

**Has all permissions**:

- ✅ All EMPLOYEE permissions
- ✅ All MANAGER permissions
- ✅ All HR permissions
- ✅ Full system access
- ✅ Can override any restriction
- ✅ Can manage all resources

**Scope**: System-wide access, no restrictions

---

### Example 5: Auditor Alex (AUDITOR Group)

**Can Do**:

- ✅ View all employee profiles (read-only)
- ✅ View performance reviews, review items, and goals (read-only)
- ✅ View wellbeing global and team stats (read-only)

**Cannot Do**:

- ❌ Create or update employee profiles
- ❌ Create or update reviews, goals, or review items
- ❌ Create or manage wellbeing surveys

## Role Assignment

### Default Role

- New users default to **EMPLOYEE** role unless specified during registration
- Superusers created via `createsuperuser` default to **ADMIN** role

### Role Changes

- Roles can only be changed by HR or ADMIN users
- Role changes are typically done through Django admin interface or direct database updates
- API does not currently expose role change endpoint (security measure)

### Manager Assignment

- Managers are assigned at the EmployeeProfile level (not User level)
- A user with EMPLOYEE role can be set as a manager in an EmployeeProfile
- Manager must have role MANAGER, HR, or ADMIN (validated in model)
- Cannot be own manager (validated in model)

---

## Permission Implementation

### Permission Classes

**Custom Permission Classes**:

1. `IsAdminRole`: Allow only ADMIN users
2. `IsHRRole`: Allow HR and ADMIN users
3. `IsManagerOrAbove`: Allow MANAGER, HR, and ADMIN users
4. `ReadOnlyOrAdmin`: Allow read for all authenticated, write for ADMIN only
5. `EmployeeProfileAccessPermission`: Object-level permission for employee profiles
6. `IsAuditorReadOnly`: Allow auditors read-only access
7. `IsSecurityAdmin`: Allow security admins (or global admins)
8. `IsSupport`: Allow support group (or global admins)
9. `IsHROrAuditorReadOnly`: HR/Admin write, auditors read-only
10. `IsManagerOrAuditorReadOnly`: Manager/HR/Admin write, auditors read-only
11. `IsHRRoleOrSupport`: HR/Admin or Support access

### Role Helper Methods

**On User Model**:

```python
user.has_role(Role.HR, Role.ADMIN)  # Check if user has one of the roles
user.is_at_least(Role.MANAGER)       # Check if rank >= MANAGER
user.role_rank                        # Get numeric rank (1-4)
```

### Queryset Filtering

Many views use custom `get_queryset()` methods to filter data based on user role:

- HR/ADMIN: No filtering, see all
- MANAGER: Filter by `employee.manager == user.employee_profile`
- EMPLOYEE: Filter by `employee.user == user`

---

## Security Considerations

### 1. **Authentication**

- JWT tokens required for all non-public endpoints
- Tokens expire (access: 30 minutes, refresh: 7 days)
- Failed login tracking and account lockout

### 2. **Authorization**

- Role-based checks on all sensitive operations
- Object-level permissions where appropriate
- Field-level restrictions on updates

### 3. **Privacy**

- Wellbeing surveys completely anonymous
- No PII exposed in logs
- Department-level aggregation only for team stats

### 4. **Audit Trail**

- Login activity tracking (IP, user agent, success/failure)
- Review history (created_by, created_at, updated_at)
- Skill evaluation tracking (last_evaluated_by, last_evaluated_at)

### 5. **Validation**

- Manager cannot be own manager
- Manager must have appropriate role
- One review per employee per cycle
- Review status workflow enforced

---

## Permission Testing

### How to Test Permissions

1. **Create test users with different roles**:

   ```python
   employee = User.objects.create_user(email="emp@test.com", password="pass", role="EMPLOYEE")
   manager = User.objects.create_user(email="mgr@test.com", password="pass", role="MANAGER")
   hr = User.objects.create_user(email="hr@test.com", password="pass", role="HR")
   admin = User.objects.create_user(email="admin@test.com", password="pass", role="ADMIN")
   ```

2. **Set up manager relationships**:

   ```python
   manager_profile = EmployeeProfile.objects.create(user=manager, ...)
   employee_profile = EmployeeProfile.objects.create(user=employee, manager=manager_profile, ...)
   ```

3. **Test API access with different tokens**:

   ```bash
   # Login as employee
   curl -X POST http://localhost:8000/api/auth/login/ \
        -H "Content-Type: application/json" \
        -d '{"email":"emp@test.com","password":"pass"}'

   # Use token to access endpoints
   curl -X GET http://localhost:8000/api/hr/employees/ \
        -H "Authorization: Bearer <employee_token>"
   ```

4. **Expected results**:
   - Employee accessing `/api/hr/employees/`: 403 Forbidden
   - Manager accessing `/api/hr/employees/`: 403 Forbidden
   - HR accessing `/api/hr/employees/`: 200 OK with all employees
   - Auditor accessing `/api/hr/employees/`: 200 OK (read-only)
   - Support accessing `/api/auth/users/`: 200 OK

---

## Common Permission Scenarios

### Scenario 1: Performance Review Workflow

1. **HR creates review cycle** (HR role required)
2. **Manager creates review for employee** (Manager must be assigned as employee's manager)
3. **Manager adds review items** (DRAFT status only)
4. **Employee adds comment** (Limited to employee_comment field)
5. **Manager submits review** (Changes to SUBMITTED)
6. **Employee acknowledges review** (Changes to COMPLETED)

**Permissions enforced at each step based on role and review status**

---

### Scenario 2: Team Management

**Manager Jane wants to manage her team**:

1. View team: `GET /api/hr/employees/my-team/` ✅
2. View specific employee: `GET /api/hr/employees/5/` ✅ (if employee reports to Jane)
3. Evaluate employee skill: `POST /api/hr/employee-skills/` ✅ (if employee reports to Jane)
4. View team goals: `GET /api/reviews/goals/?employee_id=5` ✅
5. View employee outside team: `GET /api/hr/employees/99/` ❌ (403 Forbidden)

---

### Scenario 3: Wellbeing Survey

1. **HR creates survey**: `POST /api/wellbeing/surveys/` ✅
2. **HR adds questions**: `POST /api/wellbeing/surveys/1/questions/` ✅
3. **All employees submit responses**: `POST /api/wellbeing/surveys/1/submit/` ✅ (Anonymous)
4. **Manager views team stats**: `GET /api/wellbeing/surveys/1/team-stats/` ✅ (Aggregated only)
5. **HR views global stats**: `GET /api/wellbeing/surveys/1/stats/` ✅
6. **Auditor views global stats**: `GET /api/wellbeing/surveys/1/stats/` ✅ (Read-only)
7. **Employee tries to view stats**: `GET /api/wellbeing/surveys/1/stats/` ❌ (403 Forbidden)

---

## Troubleshooting

### Common Permission Errors

**403 Forbidden - Insufficient Permissions**:

- Check user role: `user.role`
- Verify token is valid and not expired
- Ensure user has required role for the endpoint
- For manager operations, verify manager relationship exists

**404 Not Found (when resource exists)**:

- May indicate permission denial via queryset filtering
- User cannot see the resource due to access restrictions
- Check if user should have access based on role and relationships

**401 Unauthorized**:

- Token missing or invalid
- Token expired (access token valid for 30 minutes)
- User not authenticated

---

## Best Practices

### 1. **Principle of Least Privilege**

- Assign lowest role necessary for job function
- Use EMPLOYEE role as default
- Elevate to MANAGER only for team leads
- Limit HR and ADMIN roles to necessary personnel

### 2. **Manager Relationships**

- Always set manager in EmployeeProfile for team-based permissions
- Ensure managers have MANAGER, HR, or ADMIN role
- Review and update manager assignments regularly

### 3. **Security**

- Rotate JWT tokens regularly
- Monitor login activity for suspicious patterns
- Review permission settings periodically
- Use HTTPS in production

### 4. **Audit and Compliance**

- Review access logs regularly
- Track who creates/updates sensitive data
- Maintain audit trail for performance reviews
- Ensure wellbeing survey anonymity is preserved

---

**End of User Roles & Permissions Documentation**
