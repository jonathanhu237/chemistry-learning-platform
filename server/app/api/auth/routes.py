from __future__ import annotations

from fastapi import APIRouter

from server.app.auth import AuthUser, LoginResponse
from server.app.auth import change_password, change_student_password, login, logout, me, student_login


router = APIRouter(prefix="/api/auth", tags=["auth"])
router.post("/login", response_model=LoginResponse)(login)
router.post("/student/login", response_model=LoginResponse)(student_login)
router.get("/me", response_model=AuthUser)(me)
router.post("/logout")(logout)
router.post("/password", response_model=LoginResponse)(change_password)
router.post("/student/password", response_model=LoginResponse)(change_student_password)
