# SmartHR360 Backend

> **Comprehensive HR Management System API** built with Django REST Framework

SmartHR360 is a full-featured Human Resources Management System that handles employee profiles, skills tracking, performance reviews, goal management, and wellbeing surveys.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Authentication](#-authentication)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Development Guidelines](#-development-guidelines)
- [License](#-license)

---

## ✨ Features

### 🔐 Authentication & Authorization

- User registration and login with JWT tokens
- Role-based access control (Employee, Manager, HR, Admin)
- Email verification system
- Password reset functionality
- Account lockout after failed login attempts
- Login activity tracking

### 👥 Employee Management

- Complete employee profiles with hire dates, job titles, and departments
- Department organization
- Advanced filtering (by department, role, status, hire date)
- Search functionality across names and emails
- Self-service profile updates for employees
- HR-managed comprehensive profile editing

### 🎯 Skills & Competencies

- Skills catalog with categories
- Employee skill tracking with proficiency levels (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)
- Future competencies planning
- Skills gap analysis capabilities

### 📊 Performance Reviews

- Review cycle management
- Performance review creation and tracking
- Multi-competency ratings with weighted scores
- Review workflow (Draft → Submitted → Approved)
- Manager and employee collaboration
- Review item comments and scoring

### 🎯 Goal Management

- Individual and team goal setting
- Goal status tracking (Not Started, In Progress, Completed, Cancelled)
- Deadline management
- Goal visibility based on roles

### 💚 Wellbeing Surveys

- Anonymous or identified surveys
- Multiple wellbeing metrics:
  - Work-life balance
  - Job satisfaction
  - Stress levels
  - Management support
  - Team collaboration
- Survey statistics and analytics for HR
- Time-series tracking of employee wellbeing

---

## 🛠 Tech Stack

- **Framework:** Django 5.2.8
- **API:** Django REST Framework 3.16+
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Documentation:** drf-spectacular (OpenAPI 3.0)
- **Database:** SQLite (development) / PostgreSQL (production)
- **Python:** 3.10+

---

## 📦 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- virtualenv (recommended)
- Git

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smarthr360_backend.git
cd smarthr360_backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

---

## ⚙️ Configuration

### Environment Variables

For production, create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL example)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=smarthr360
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smarthr360.com

# JWT Settings (optional - defaults are set)
ACCESS_TOKEN_LIFETIME_MINUTES=30
REFRESH_TOKEN_LIFETIME_DAYS=1
```

### Settings Configuration

Key settings in `smarthr360_backend/settings.py`:

- **INSTALLED_APPS:** Includes all necessary Django apps and third-party packages
- **REST_FRAMEWORK:** Configured with JWT authentication and pagination
- **SIMPLE_JWT:** Token lifetime and authentication settings
- **SPECTACULAR_SETTINGS:** API documentation configuration

---

## 🏃 Running the Application

### Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

### Run Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test hr
python manage.py test reviews
python manage.py test wellbeing

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 📚 API Documentation

SmartHR360 provides interactive API documentation using drf-spectacular:

### Swagger UI (Recommended)

Interactive API explorer with request/response examples:

```
http://localhost:8000/docs/
```

### ReDoc

Clean, three-panel documentation:

```
http://localhost:8000/redoc/
```

### OpenAPI Schema

Raw OpenAPI 3.0 schema in JSON format:

```
http://localhost:8000/api/schema/
```

---

## 📁 Project Structure

```
smarthr360_backend/
├── accounts/                 # User authentication & management
│   ├── models.py            # User, PasswordResetToken, LoginActivity
│   ├── serializers.py       # Auth serializers
│   ├── views.py             # Auth endpoints
│   ├── permissions.py       # Custom permissions
│   ├── schemas.py           # API documentation schemas
│   └── tests/               # Authentication tests
├── hr/                      # HR & Employee management
│   ├── models.py            # Department, EmployeeProfile, Skill
│   ├── serializers.py       # HR serializers
│   ├── views.py             # HR endpoints
│   ├── schemas.py           # API documentation schemas
│   └── tests/               # HR tests
├── reviews/                 # Performance reviews & goals
│   ├── models.py            # ReviewCycle, PerformanceReview, Goal
│   ├── serializers.py       # Review serializers
│   ├── views.py             # Review endpoints
│   ├── schemas.py           # API documentation schemas
│   └── tests/               # Review tests
├── wellbeing/               # Wellbeing surveys
│   ├── models.py            # WellbeingSurvey, SurveyResponse
│   ├── serializers.py       # Survey serializers
│   ├── views.py             # Survey endpoints
│   ├── schemas.py           # API documentation schemas
│   └── tests/               # Wellbeing tests
├── smarthr360_backend/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL configuration
│   ├── api_mixins.py        # Reusable API mixins
│   └── pagination.py        # Custom pagination classes
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔐 Authentication

SmartHR360 uses JWT (JSON Web Tokens) for authentication.

### Registration

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "john.doe@company.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "EMPLOYEE"
}
```

**Response:**

```json
{
  "user": {
    "id": 1,
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "john.doe@company.com",
  "password": "SecurePass123!"
}
```

### Using Tokens

Include the access token in the Authorization header:

```http
GET /api/auth/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Token Refresh

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 🌐 API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint                       | Description                 | Access        |
| ------ | ------------------------------ | --------------------------- | ------------- |
| POST   | `/register/`                   | Register new user           | Public        |
| POST   | `/login/`                      | User login                  | Public        |
| POST   | `/logout/`                     | User logout                 | Authenticated |
| GET    | `/me/`                         | Get current user profile    | Authenticated |
| POST   | `/change-password/`            | Change password             | Authenticated |
| POST   | `/request-password-reset/`     | Request password reset link | Public        |
| POST   | `/password-reset/`             | Reset password with token   | Public        |
| POST   | `/request-email-verification/` | Request verification email  | Public        |
| POST   | `/email-verification/`         | Verify email with token     | Public        |
| GET    | `/users/`                      | List all users              | HR Only       |

### Departments (`/api/hr/departments/`)

| Method | Endpoint | Description            | Access        |
| ------ | -------- | ---------------------- | ------------- |
| GET    | `/`      | List all departments   | Authenticated |
| POST   | `/`      | Create department      | HR Only       |
| GET    | `/<id>/` | Get department details | Authenticated |
| PATCH  | `/<id>/` | Update department      | HR Only       |
| DELETE | `/<id>/` | Delete department      | HR Only       |

### Employees (`/api/hr/employees/`)

| Method | Endpoint | Description                   | Access        |
| ------ | -------- | ----------------------------- | ------------- |
| GET    | `/`      | List employees (with filters) | HR Only       |
| POST   | `/`      | Create employee profile       | HR Only       |
| GET    | `/me/`   | Get own profile               | Authenticated |
| PATCH  | `/me/`   | Update own profile            | Authenticated |
| GET    | `/<id>/` | Get employee details          | Manager+      |
| PATCH  | `/<id>/` | Update employee               | HR/Manager    |
| DELETE | `/<id>/` | Delete employee               | HR Only       |

**Available Filters:**

- `?department=IT` - Filter by department code
- `?is_active=true` - Filter by active status
- `?role=MANAGER` - Filter by user role
- `?hired_after=2023-01-01` - Filter by hire date
- `?search=john` - Search in names and email

### Skills (`/api/hr/skills/`)

| Method | Endpoint | Description       | Access        |
| ------ | -------- | ----------------- | ------------- |
| GET    | `/`      | List all skills   | Authenticated |
| POST   | `/`      | Create skill      | HR Only       |
| GET    | `/<id>/` | Get skill details | Authenticated |
| PATCH  | `/<id>/` | Update skill      | HR Only       |
| DELETE | `/<id>/` | Delete skill      | HR Only       |

### Employee Skills (`/api/hr/employees/<employee_id>/skills/`)

| Method | Endpoint       | Description                | Access     |
| ------ | -------------- | -------------------------- | ---------- |
| GET    | `/`            | List employee's skills     | Manager+   |
| POST   | `/`            | Add skill to employee      | Manager/HR |
| PATCH  | `/<skill_id>/` | Update skill proficiency   | Manager/HR |
| DELETE | `/<skill_id>/` | Remove skill from employee | Manager/HR |

### Future Competencies (`/api/hr/future-competencies/`)

| Method | Endpoint | Description            | Access        |
| ------ | -------- | ---------------------- | ------------- |
| GET    | `/`      | List all competencies  | Authenticated |
| POST   | `/`      | Create competency      | HR Only       |
| GET    | `/<id>/` | Get competency details | Authenticated |
| PATCH  | `/<id>/` | Update competency      | HR Only       |
| DELETE | `/<id>/` | Delete competency      | HR Only       |

### Review Cycles (`/api/reviews/cycles/`)

| Method | Endpoint | Description         | Access        |
| ------ | -------- | ------------------- | ------------- |
| GET    | `/`      | List all cycles     | Authenticated |
| POST   | `/`      | Create review cycle | HR/Admin      |
| GET    | `/<id>/` | Get cycle details   | Authenticated |
| PATCH  | `/<id>/` | Update cycle        | HR/Admin      |

### Performance Reviews (`/api/reviews/`)

| Method | Endpoint         | Description                     | Access           |
| ------ | ---------------- | ------------------------------- | ---------------- |
| GET    | `/`              | List reviews (filtered by role) | Authenticated    |
| POST   | `/`              | Create review                   | Manager/HR       |
| GET    | `/<id>/`         | Get review details              | Owner/Manager/HR |
| PATCH  | `/<id>/`         | Update review                   | Manager/HR       |
| DELETE | `/<id>/`         | Delete review                   | HR Only          |
| POST   | `/<id>/submit/`  | Submit review                   | Manager/HR       |
| POST   | `/<id>/approve/` | Approve review                  | HR/Admin         |

### Review Items (`/api/reviews/<review_id>/items/`)

| Method | Endpoint      | Description        | Access           |
| ------ | ------------- | ------------------ | ---------------- |
| GET    | `/`           | List review items  | Owner/Manager/HR |
| POST   | `/`           | Add item to review | Manager/HR       |
| PATCH  | `/<item_id>/` | Update item        | Manager/HR       |
| DELETE | `/<item_id>/` | Delete item        | Manager/HR       |

### Goals (`/api/reviews/goals/`)

| Method | Endpoint | Description                   | Access              |
| ------ | -------- | ----------------------------- | ------------------- |
| GET    | `/`      | List goals (filtered by role) | Authenticated       |
| POST   | `/`      | Create goal                   | Manager/HR/Employee |
| GET    | `/<id>/` | Get goal details              | Owner/Manager/HR    |
| PATCH  | `/<id>/` | Update goal                   | Owner/Manager/HR    |
| DELETE | `/<id>/` | Delete goal                   | Owner/Manager/HR    |

**Available Filters:**

- `?employee_id=5` - Filter by employee
- `?status=IN_PROGRESS` - Filter by status

### Wellbeing Surveys (`/api/wellbeing/surveys/`)

| Method | Endpoint       | Description           | Access        |
| ------ | -------------- | --------------------- | ------------- |
| GET    | `/`            | List all surveys      | Authenticated |
| POST   | `/`            | Create survey         | HR/Admin      |
| GET    | `/<id>/`       | Get survey details    | Authenticated |
| PATCH  | `/<id>/`       | Update survey         | HR/Admin      |
| DELETE | `/<id>/`       | Delete survey         | HR/Admin      |
| GET    | `/<id>/stats/` | Get survey statistics | HR/Admin      |

### Survey Responses (`/api/wellbeing/responses/`)

| Method | Endpoint | Description                       | Access        |
| ------ | -------- | --------------------------------- | ------------- |
| GET    | `/`      | List responses (filtered by role) | Authenticated |
| POST   | `/`      | Submit survey response            | Authenticated |
| GET    | `/<id>/` | Get response details              | Owner/HR      |
| PATCH  | `/<id>/` | Update response                   | Owner         |
| DELETE | `/<id>/` | Delete response                   | Owner/HR      |

**Available Filters:**

- `?survey_id=1` - Filter by survey
- `?employee_id=5` - Filter by employee (HR only)

---

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts.tests.test_auth_flow
python manage.py test hr.tests.test_employee_filters
python manage.py test reviews.tests.test_reviews
python manage.py test wellbeing.tests.test_wellbeing

# Run with verbosity
python manage.py test --verbosity=2

# Generate coverage report
coverage run --source='.' manage.py test
coverage html
# Open htmlcov/index.html in browser
```

### Test Files

- `accounts/tests/` - Authentication, permissions, login tracking
- `hr/tests/` - Employee management, skills, filters
- `reviews/tests/` - Reviews, goals, cycles
- `wellbeing/tests/` - Surveys and responses

---

## 💻 Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions small and focused

### API Design

- Use proper HTTP methods (GET, POST, PATCH, DELETE)
- Return appropriate status codes
- Include pagination for list endpoints
- Provide clear error messages

### Security Best Practices

- Never commit sensitive data (`.env` files)
- Use environment variables for secrets
- Validate all user inputs
- Implement proper permission checks
- Keep dependencies updated

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add: feature description"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Adding New Endpoints

1. Define models in `models.py`
2. Create serializers in `serializers.py`
3. Add schema decorators in `schemas.py`
4. Implement views in `views.py`
5. Register URLs in `urls.py`
6. Write tests in `tests/`
7. Update API documentation

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 👥 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

---

## 📞 Support

For issues and questions:

- Create an issue on GitHub
- Contact: support@smarthr360.com

---

## 🙏 Acknowledgments

Built with:

- Django REST Framework
- drf-spectacular
- djangorestframework-simplejwt

---

**Made with ❤️ by the SmartHR360 Team**
