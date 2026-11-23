from app.engine import create_session
from app.store import clear, get, save


def test_save_and_get_session():
    session = create_session()
    session["plan"]["question"] = "持久化测试问题"
    save(session)

    loaded = get(session["id"])
    assert loaded is not None
    assert loaded["plan"]["question"] == "持久化测试问题"
    assert loaded["messages"][0]["kind"] == "welcome"


def test_clear_removes_sessions():
    session = create_session()
    save(session)
    clear()
    assert get(session["id"]) is None
