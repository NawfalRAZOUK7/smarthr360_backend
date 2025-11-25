# Postman Collection Import Guide

## 📥 Importing the Collection

1. **Open Postman**

   - Launch the Postman application or visit [Postman Web](https://web.postman.co)

2. **Import the Collection**

   - Click **Import** button (top left)
   - Drag and drop `SmartHR360_API.postman_collection.json`
   - Or click **Upload Files** and select the file

3. **Collection is Ready!**
   - You'll see "SmartHR360 API" in your Collections sidebar
   - Contains 80+ organized endpoints

---

## 🗂 Collection Structure

The collection is organized into **5 main categories**:

### 🔐 Authentication (10 endpoints)

- Register
- Login (auto-saves tokens)
- Get Current User
- Change Password
- Password Reset Flow
- Email Verification Flow
- Logout
- List Users (HR only)

### 🏢 HR - Departments (5 endpoints)

- List/Create/Update/Delete departments
- Get department details

### 👥 HR - Employees (6 endpoints)

- List employees with advanced filters
- Get/Update my profile
- Create/Update/View employee profiles

### 🎯 Skills (7 endpoints)

- List/Create/Update skills
- Manage employee skills
- Track proficiency levels
- Future competencies

### 📊 Reviews (12 endpoints)

- Review cycle management
- Create/Submit/Approve reviews
- Review items and ratings
- Goal management

### 💚 Wellbeing (8 endpoints)

- Survey management
- Submit responses
- View statistics
- Track wellbeing metrics

---

## ⚙️ Configuration

### Setting the Base URL

The collection uses a variable for the base URL:

1. Click on **SmartHR360 API** collection
2. Go to **Variables** tab
3. Update `base_url`:
   - Local: `http://localhost:8000`
   - Staging: `https://staging-api.smarthr360.com`
   - Production: `https://api.smarthr360.com`

### Authentication Setup

The collection uses **Bearer Token** authentication with automatic token management.

#### Auto-Login (Recommended)

1. Open the **Login** request
2. Update the email/password in the body
3. Send the request
4. ✅ Tokens are **automatically saved** to collection variables
5. All subsequent requests will use the saved token

#### Manual Token Setup

If needed, you can manually set tokens:

1. Click on collection → **Variables**
2. Set `access_token` value
3. Set `refresh_token` value

---

## 🚀 Quick Start

### 1. Register a New User

```
POST {{base_url}}/api/auth/register/
```

**Body:**

```json
{
  "email": "test@company.com",
  "password": "TestPass123!",
  "first_name": "Test",
  "last_name": "User",
  "role": "EMPLOYEE"
}
```

### 2. Login

```
POST {{base_url}}/api/auth/login/
```

**Body:**

```json
{
  "email": "test@company.com",
  "password": "TestPass123!"
}
```

**✅ Tokens automatically saved!**

### 3. Get Current User Profile

```
GET {{base_url}}/api/auth/me/
```

**Authorization:** Automatic (uses saved token)

### 4. Explore Other Endpoints

All requests are pre-configured with:

- ✅ Correct HTTP methods
- ✅ Sample request bodies
- ✅ Authentication headers
- ✅ Query parameter examples

---

## 🔍 Using Filters

Many list endpoints support filters via query parameters:

### Employee Filters

```
GET {{base_url}}/api/hr/employees/
  ?department=IT
  &is_active=true
  &role=MANAGER
  &hired_after=2023-01-01
  &search=john
```

### Goal Filters

```
GET {{base_url}}/api/reviews/goals/
  ?employee_id=5
  &status=IN_PROGRESS
```

### Survey Response Filters

```
GET {{base_url}}/api/wellbeing/responses/
  ?survey_id=1
  &employee_id=5
```

**💡 Tip:** Enable/disable query parameters in Postman by checking/unchecking them

---

## 🎯 Role-Based Testing

Test different user roles:

### Employee Account

```json
{
  "email": "employee@company.com",
  "password": "Pass123!",
  "role": "EMPLOYEE"
}
```

- ✅ Can view own profile
- ✅ Can submit surveys
- ✅ Can view own goals
- ❌ Cannot access HR endpoints

### Manager Account

```json
{
  "email": "manager@company.com",
  "password": "Pass123!",
  "role": "MANAGER"
}
```

- ✅ All Employee permissions
- ✅ Can create reviews for team
- ✅ Can view team goals
- ❌ Cannot create departments

### HR Account

```json
{
  "email": "hr@company.com",
  "password": "Pass123!",
  "role": "HR"
}
```

- ✅ All Manager permissions
- ✅ Can manage employees
- ✅ Can create departments
- ✅ Can view all data

### Admin Account

```json
{
  "email": "admin@company.com",
  "password": "Pass123!",
  "role": "ADMIN"
}
```

- ✅ Full system access
- ✅ Can approve reviews
- ✅ Can create review cycles

---

## 📝 Request Examples

### Create Employee Profile

```json
{
  "user_id": 1,
  "department_id": 1,
  "job_title": "Software Engineer",
  "hire_date": "2024-01-01"
}
```

### Add Skill to Employee

```json
{
  "skill_id": 1,
  "proficiency_level": "INTERMEDIATE",
  "notes": "Completed Python certification"
}
```

### Create Performance Review

```json
{
  "employee_id": 1,
  "cycle_id": 1,
  "manager_id": 2,
  "review_period_start": "2024-01-01",
  "review_period_end": "2024-03-31"
}
```

### Submit Survey Response

```json
{
  "survey_id": 1,
  "work_life_balance": 4,
  "job_satisfaction": 5,
  "stress_level": 2,
  "management_support": 4,
  "team_collaboration": 5,
  "comments": "Very satisfied with work environment"
}
```

---

## 🔧 Troubleshooting

### 401 Unauthorized Error

- ✅ Check if you're logged in
- ✅ Verify `access_token` is set in collection variables
- ✅ Token might be expired - login again

### 403 Forbidden Error

- ✅ Check user role permissions
- ✅ Some endpoints require HR/Manager/Admin roles

### 400 Bad Request Error

- ✅ Verify request body format
- ✅ Check required fields are included
- ✅ Validate data types (dates, IDs, etc.)

### 404 Not Found Error

- ✅ Verify the ID exists
- ✅ Check the base URL is correct
- ✅ Ensure server is running

---

## 💡 Pro Tips

1. **Use Environments**

   - Create separate environments for Dev/Staging/Prod
   - Switch between them easily

2. **Save Responses**

   - Use Postman's "Save Response" for examples
   - Build documentation from real responses

3. **Use Pre-request Scripts**

   - Add timestamps or dynamic data
   - Generate test data automatically

4. **Create Test Suites**

   - Group related requests into folders
   - Run entire workflows with Collection Runner

5. **Export & Share**
   - Export updated collection after changes
   - Share with team via Git or Postman workspace

---

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8000/docs/`
- **ReDoc:** `http://localhost:8000/redoc/`
- **OpenAPI Schema:** `http://localhost:8000/api/schema/`
- **README:** See `README.md` for full API documentation

---

## 🆘 Need Help?

- Check the request descriptions in Postman
- Review the README.md for detailed endpoint info
- Visit the interactive docs at `/docs/`
- Contact: support@smarthr360.com

---

**Happy Testing! 🚀**
