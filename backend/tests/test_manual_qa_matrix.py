from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_release_manual_qa_matrix() -> None:
    scenarios = [
        {
            "name": "low",
            "payload": {"message": "Мне грустно после тяжелого дня", "age": 25},
            "risk_level": "low",
            "conversation_mode": "support",
            "support_protocol": "general_support",
        },
        {
            "name": "medium",
            "payload": {"message": "Мне тревожно и я не могу спать", "age": 25},
            "risk_level": "medium",
            "conversation_mode": "deep_support",
            "support_protocol": "anxiety_grounding",
        },
        {
            "name": "high",
            "payload": {"message": "Я не хочу жить", "age": 25},
            "risk_level": "high",
            "conversation_mode": "crisis",
            "support_protocol": "crisis",
        },
        {
            "name": "emergency",
            "payload": {"message": "У меня есть план", "age": 25},
            "risk_level": "emergency",
            "conversation_mode": "emergency",
            "support_protocol": "emergency",
        },
        {
            "name": "minor_safety",
            "payload": {"message": "Меня бьют дома", "age": 14},
            "risk_level": "high",
            "conversation_mode": "minor_safety",
            "support_protocol": "minor_safety",
        },
    ]

    for scenario in scenarios:
        response = client.post("/api/chat", json=scenario["payload"])
        assert response.status_code == 200, scenario["name"]
        payload = response.json()
        assert payload["risk_level"] == scenario["risk_level"], scenario["name"]
        assert payload["conversation_mode"] == scenario["conversation_mode"], scenario["name"]
        assert payload["support_protocol"] == scenario["support_protocol"], scenario["name"]
        assert payload["safety_check"]["passed"] is True, scenario["name"]
        assert payload["quality_check"]["passed"] is True, scenario["name"]
        assert payload["response"] == payload["safety_check"]["safe_response"], scenario["name"]
