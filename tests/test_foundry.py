"""foundry: port aday listesi (override + CLI + fallback) ve model secimi."""
import foundry
from foundry import _candidate_ports, _pick_model


def _no_cli(monkeypatch):
    """foundry CLI'si yokmus gibi davran: sadece env + fallback kalir."""
    monkeypatch.setattr(foundry.shutil, "which", lambda _name: None)
    monkeypatch.delenv("FOUNDRY_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_PORT", raising=False)


# ---- _candidate_ports ------------------------------------------------

def test_fallback_only_when_no_env_no_cli(monkeypatch):
    _no_cli(monkeypatch)
    assert _candidate_ports() == list(foundry.FALLBACK_PORTS)


def test_env_port_takes_priority(monkeypatch):
    _no_cli(monkeypatch)
    monkeypatch.setenv("FOUNDRY_PORT", "1234")
    ports = _candidate_ports()
    assert ports[0] == 1234


def test_env_endpoint_url_port_parsed_not_ip_octet(monkeypatch):
    _no_cli(monkeypatch)
    monkeypatch.setenv("FOUNDRY_ENDPOINT", "http://127.0.0.1:9000/v1")
    ports = _candidate_ports()
    assert ports[0] == 9000          # 127 degil
    assert 127 not in ports


def test_candidate_ports_are_unique(monkeypatch):
    _no_cli(monkeypatch)
    monkeypatch.setenv("FOUNDRY_PORT", str(foundry.FALLBACK_PORTS[0]))
    ports = _candidate_ports()
    assert len(ports) == len(set(ports))
    assert ports.count(foundry.FALLBACK_PORTS[0]) == 1


def test_cli_port_inserted_before_fallback(monkeypatch):
    monkeypatch.delenv("FOUNDRY_ENDPOINT", raising=False)
    monkeypatch.delenv("FOUNDRY_PORT", raising=False)
    monkeypatch.setattr(foundry.shutil, "which", lambda _name: "/usr/bin/foundry")

    class _Result:
        stdout = "Model management service is running on http://127.0.0.1:54321/openai/status"

    monkeypatch.setattr(foundry.subprocess, "run", lambda *a, **k: _Result())
    ports = _candidate_ports()
    assert ports[0] == 54321
    assert list(foundry.FALLBACK_PORTS) == ports[-len(foundry.FALLBACK_PORTS):]


# ---- _pick_model ---------------------------------------------------

def test_pick_model_prefers_phi():
    models = {"data": [{"id": "qwen2.5-0.5b"}, {"id": "Phi-3.5-mini-instruct-gpu:2"}]}
    assert _pick_model(models) == "Phi-3.5-mini-instruct-gpu:2"


def test_pick_model_falls_back_to_first():
    models = {"data": [{"id": "qwen2.5-0.5b"}, {"id": "mistral-7b"}]}
    assert _pick_model(models) == "qwen2.5-0.5b"


def test_pick_model_empty_returns_alias():
    assert _pick_model({"data": []}) == "phi-3.5-mini"
