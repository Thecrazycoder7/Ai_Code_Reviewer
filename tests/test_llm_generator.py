import json
import pytest
from unittest.mock import patch, MagicMock
from core.docstring_engine.groq_integration import generate_placeholder_docstring
# ---------------- Sample input ----------------
FN_INFO = {
    "name": "add_numbers",
    "args": ["a", "b"],
    "returns": "int"
}

LLM_JSON = {
    "summary": "Adds two numbers.",
    "arg_descs": {
        "a": "First number",
        "b": "Second number"
    },
    "ret_desc": "Sum of numbers"
}

# ---------------- Test: Google style ----------------
@patch("core.docstring_engine.groq_integration.client")
@patch("core.docstring_engine.generator.to_google")
def test_google_docstring_success(mock_to_google, mock_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(LLM_JSON)))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    mock_to_google.return_value = "GOOGLE DOCSTRING"

    result = generate_placeholder_docstring(FN_INFO, "google")

    assert result == "GOOGLE DOCSTRING"
    mock_to_google.assert_called_once()

# ---------------- Test: NumPy style ----------------
@patch("core.docstring_engine.groq_integration.client")
@patch("core.docstring_engine.generator.to_numpy")
def test_numpy_docstring_success(mock_to_numpy, mock_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(LLM_JSON)))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    mock_to_numpy.return_value = "NUMPY DOCSTRING"

    result = generate_placeholder_docstring(FN_INFO, "numpy")

    assert result == "NUMPY DOCSTRING"
    mock_to_numpy.assert_called_once()

# ---------------- Test: reST style ----------------
@patch("core.docstring_engine.groq_integration.client")
@patch("core.docstring_engine.generator.to_rest")
def test_rest_docstring_success(mock_to_rest, mock_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(LLM_JSON)))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    mock_to_rest.return_value = "REST DOCSTRING"

    result = generate_placeholder_docstring(FN_INFO, "rest")

    assert result == "REST DOCSTRING"
    mock_to_rest.assert_called_once()

# ---------------- Test: LLM failure ----------------
@patch("core.docstring_engine.groq_integration.client")
def test_llm_failure_returns_error(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("LLM error")

    result = generate_placeholder_docstring(FN_INFO, "google")

    assert result == "Error generating docstring."
