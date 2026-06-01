from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_response_contract() -> None:
    response = client.post(
        "/api/chat",
        json={"message": "У меня депрессия, нет сил и не могу спать", "age": 25},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "risk_level",
        "risk_score",
        "conversation_mode",
        "risk_assessment",
        "safety_check",
        "response",
    }
    assert payload["risk_level"] == "medium"
    assert payload["conversation_mode"] == "deep_support"
    assert payload["response"] == payload["safety_check"]["safe_response"]
    assert payload["safety_check"]["passed"] is True


def test_chat_rejects_invalid_input() -> None:
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "ok", "age": -1}).status_code == 422
    assert client.post("/api/chat", json={"message": "ok", "age": 121}).status_code == 422

