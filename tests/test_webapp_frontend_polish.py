from pathlib import Path


def test_v1_0_5_frontend_uses_canonical_visible_version_labels():
    page = Path("webapp/static/index.html").read_text(encoding="utf-8")
    app = Path("webapp/app.py").read_text(encoding="utf-8")
    package = Path("src/__init__.py").read_text(encoding="utf-8")

    assert "semi-ver1.0.4" not in page
    assert 'v=v1.0.5' in page
    assert 'version="1.0.5"' in app
    assert '__version__ = "1.0.5"' in package


def test_frontend_polish_keeps_pending_evidence_and_action_modal_hooks():
    page = Path("webapp/static/index.html").read_text(encoding="utf-8")
    script = Path("webapp/static/app.js").read_text(encoding="utf-8")
    styles = Path("webapp/static/styles.css").read_text(encoding="utf-8")

    assert 'id="action-modal"' in page
    assert 'id="upload-summary"' in page
    assert "function withPending" in script
    assert "Không tìm thấy nguồn phù hợp trong phạm vi tài liệu" in script
    assert "openActionModal" in script
    assert "button:focus-visible" in styles
