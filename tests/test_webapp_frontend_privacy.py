from pathlib import Path


def test_session_switch_clears_user_scoped_frontend_state():
    script = Path("webapp/static/app.js").read_text(encoding="utf-8")

    assert 'function resetUserScopedUi()' in script
    assert '$("#conversation").replaceChildren()' in script
    assert 'function setSession(token){resetUserScopedUi();' in script
    assert 'function clearSession(){resetUserScopedUi();' in script


def test_login_copy_does_not_claim_a_specific_password_backend():
    page = Path("webapp/static/index.html").read_text(encoding="utf-8")

    assert "Hệ thống không lưu mật khẩu dạng rõ." in page
    assert "Mật khẩu được băm PBKDF2" not in page
