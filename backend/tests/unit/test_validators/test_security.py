"""Unit tests for security utilities."""
from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify_success(self):
        pwd = "SecretPass@123"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("CorrectPass@1")
        assert not verify_password("WrongPass@1", hashed)

    def test_hash_is_different_each_call(self):
        pwd = "SamePass@1"
        assert hash_password(pwd) != hash_password(pwd)


class TestPasswordValidation:
    def test_valid_password_no_errors(self):
        errors = validate_password_strength("ValidPass@123")
        assert errors == []

    def test_too_short_returns_error(self):
        errors = validate_password_strength("Sh@1")
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase_returns_error(self):
        errors = validate_password_strength("lowercase@123")
        assert any("uppercase" in e for e in errors)

    def test_no_digit_returns_error(self):
        errors = validate_password_strength("NoDigitPass@!")
        assert any("digit" in e for e in errors)

    def test_no_special_char_returns_error(self):
        errors = validate_password_strength("NoSpecial123A")
        assert any("special" in e for e in errors)


class TestJWTTokens:
    def test_access_token_round_trip(self):
        token, jti = create_access_token("user-123", "tenant-456", "customer")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["tenant_id"] == "tenant-456"
        assert payload["role"] == "customer"
        assert payload["type"] == "access"
        assert payload["jti"] == jti

    def test_refresh_token_round_trip(self):
        token, jti = create_refresh_token("user-123", "tenant-456")
        payload = decode_refresh_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_access_token_with_wrong_secret_fails(self):
        token, _ = create_access_token("user-123", "tenant-456", "customer")
        # Tamper with token — change last char
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(ValueError):
            decode_access_token(tampered)

    def test_wrong_token_type_rejected(self):
        refresh_token, _ = create_refresh_token("user-123", "tenant-456")
        with pytest.raises(ValueError, match="Invalid token type"):
            decode_access_token(refresh_token)
