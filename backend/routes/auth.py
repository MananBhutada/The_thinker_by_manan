"""FounderOS account authentication.

Passwords are hashed with PBKDF2-HMAC-SHA256 and only opaque session tokens are
stored server-side. Authentication is deliberately independent from graph data;
workspace ownership is enforced by the application middleware.
"""
import base64
import hashlib
import hmac
import os
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import db

router = APIRouter(prefix="/api/auth")
COOKIE = "founderos_auth"
ITERATIONS = 310_000


class Credentials(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return "pbkdf2_sha256$" + str(ITERATIONS) + "$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE)
    user_id = db.get_user_id_from_auth_token(token)
    return db.get_user(user_id) if user_id else None


def _session_response(payload: dict, token: str) -> JSONResponse:
    response = JSONResponse(payload)
    response.set_cookie(
        COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=os.environ.get("RENDER", "").lower() == "true",
        samesite="lax",
        path="/",
    )
    return response


@router.post("/signup")
def signup(credentials: Credentials):
    email = credentials.email.lower().strip()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = db.create_user(email, _hash_password(credentials.password))
    workspace_id = db.current_workspace_id()
    if not db.claim_workspace_for_user(workspace_id, user["userId"]):
        raise HTTPException(status_code=409, detail="This workspace is already owned by another account.")
    token = db.create_auth_session(user["userId"])
    return _session_response({"user": user, "workspaces": db.get_user_workspaces(user["userId"])}, token)


@router.post("/login")
def login(credentials: Credentials):
    row = db.get_user_by_email(credentials.email)
    if not row or not _verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    user_id = row["user_id"]
    workspaces = db.get_user_workspaces(user_id)
    if not workspaces:
        workspace_id = db.current_workspace_id()
        db.claim_workspace_for_user(workspace_id, user_id)
        workspaces = db.get_user_workspaces(user_id)
    token = db.create_auth_session(user_id)
    return _session_response({"user": db.get_user(user_id), "workspaces": workspaces}, token)


@router.get("/me")
def me(request: Request):
    user = _current_user(request)
    if not user:
        return {"authenticated": False, "user": None, "workspaces": []}
    return {"authenticated": True, "user": user, "workspaces": db.get_user_workspaces(user["userId"])}


@router.post("/logout")
def logout(request: Request):
    db.revoke_auth_session(request.cookies.get(COOKIE))
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE, path="/")
    return response
