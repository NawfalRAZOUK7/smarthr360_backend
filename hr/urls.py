from django.urls import path

from .views import (
    DepartmentListCreateView,
    DepartmentDetailView,
    EmployeeMeView,
    EmployeeListCreateView,
    EmployeeDetailView,
)

urlpatterns = [
    # Departments
    path("departments/", DepartmentListCreateView.as_view(), name="hr-department-list"),
    path("departments/<int:pk>/", DepartmentDetailView.as_view(), name="hr-department-detail"),

    # Employees
    path("employees/me/", EmployeeMeView.as_view(), name="hr-employee-me"),
    path("employees/", EmployeeListCreateView.as_view(), name="hr-employee-list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="hr-employee-detail"),
]
