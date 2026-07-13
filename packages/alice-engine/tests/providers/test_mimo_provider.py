"""MiMo provider tests, including OpenAI-compatible usage-only chunks."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from alice_engine.providers.mimo import MiMoProvider


def _chunk(*, content=None, finish_reason=None, usage=None, choices=True):
    if choices:
        choice = SimpleNamespace(
            delta=SimpleNamespace(content=content, tool_calls=None),
            finish_reason=finish_reason,
        )
        chunk_choices = [choice]
    else:
        chunk_choices = []
    return SimpleNamespace(choices=chunk_choices, usage=usage)


def test_stream_preserves_usage_from_choices_empty_chunk():
    usage = SimpleNamespace(prompt_tokens=7, completion_tokens=3)
    stream_chunks = [
        _chunk(content="OK"),
        _chunk(finish_reason="stop"),
        _chunk(usage=usage, choices=False),
    ]

    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = iter(stream_chunks)
        mock_openai.return_value = client

        provider = MiMoProvider(api_key="test-key", model="mimo-v2.5")
        stream = provider.stream("system", "user", max_tokens=16)
        events = []
        final_response = None
        while True:
            try:
                events.append(next(stream))
            except StopIteration as stop:
                final_response = stop.value
                break

    done = next(event for event in events if event.type == "done")
    assert done.token_usage == {"input": 7, "output": 3}
    assert final_response.usage == {"input": 7, "output": 3}
