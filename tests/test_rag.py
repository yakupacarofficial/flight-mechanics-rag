"""rag.answer_query: sohbet gecmisinin mesajlara katilmasi ve kirpilmasi."""
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

import rag


@pytest.fixture
def idx():
    rows = [
        (0, "a.md", "S", "## S\nstall happens past the critical angle of attack"),
        (1, "b.md", "D", "## D\ninduced drag comes from wingtip vortices"),
    ]
    vec = TfidfVectorizer(stop_words="english")
    matrix = vec.fit_transform([r[3] for r in rows])
    return vec, matrix, rows


@pytest.fixture
def captured(monkeypatch):
    """rag.chat'i yakala: modele giden mesaj listesini sakla, sahte cevap don."""
    box = {}

    def fake_chat(base_url, model, messages, **kw):
        box["messages"] = messages
        return "FAKE ANSWER"

    monkeypatch.setattr(rag, "chat", fake_chat)
    return box


def test_history_sits_between_system_and_current_question(idx, captured):
    vec, matrix, rows = idx
    history = [{"role": "user", "content": "q1"},
               {"role": "assistant", "content": "a1"}]
    ans, chunks = rag.answer_query(
        "why does it stall past the critical angle", "u", "mdl",
        vec, matrix, rows, history,
    )
    msgs = captured["messages"]
    assert ans == "FAKE ANSWER"
    assert msgs[0]["role"] == "system"
    assert msgs[1:3] == history
    assert msgs[-1] == {"role": "user",
                        "content": "why does it stall past the critical angle"}


def test_history_truncated_to_max(idx, captured):
    vec, matrix, rows = idx
    long_history = [{"role": "user", "content": f"m{i}"} for i in range(20)]
    rag.answer_query("stall critical angle attack", "u", "mdl",
                     vec, matrix, rows, long_history)
    msgs = captured["messages"]
    assert len(msgs) == 1 + rag.MAX_HISTORY_MESSAGES + 1  # system + gecmis + soru
    assert msgs[1]["content"] == f"m{20 - rag.MAX_HISTORY_MESSAGES}"


def test_no_history_still_works(idx, captured):
    vec, matrix, rows = idx
    rag.answer_query("stall critical angle attack", "u", "mdl", vec, matrix, rows)
    msgs = captured["messages"]
    assert [m["role"] for m in msgs] == ["system", "user"]


def test_low_confidence_returns_no_answer_without_calling_model(idx, captured):
    vec, matrix, rows = idx
    ans, chunks = rag.answer_query(
        "unrelated astrophysics question about distant quasars", "u", "mdl",
        vec, matrix, rows, [],
    )
    assert ans == rag.NO_ANSWER
    assert "messages" not in captured  # model cagrilmadi


@pytest.fixture
def captured_stream(monkeypatch):
    box = {}

    def fake_stream(base_url, model, messages, **kw):
        box["messages"] = messages
        return iter(["FA", "KE"])

    monkeypatch.setattr(rag, "chat_stream", fake_stream)
    return box


def test_stream_true_returns_generator(idx, captured_stream):
    vec, matrix, rows = idx
    gen, chunks = rag.answer_query("stall critical angle attack", "u", "mdl",
                                   vec, matrix, rows, stream=True)
    assert "".join(gen) == "FAKE"
    assert captured_stream["messages"][-1]["content"] == "stall critical angle attack"


def test_stream_true_low_confidence_yields_no_answer_once(idx, captured_stream):
    vec, matrix, rows = idx
    gen, chunks = rag.answer_query("unrelated quasar astrophysics question",
                                   "u", "mdl", vec, matrix, rows, stream=True)
    assert list(gen) == [rag.NO_ANSWER]
    assert "messages" not in captured_stream  # model cagrilmadi
