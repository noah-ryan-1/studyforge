from unittest.mock import MagicMock, patch 
from studyforge.llm.router import LLMRouter, Provider, Message


def make_mock_response(text: str):
	mock_choice = MagicMock()
	mock_choice.message = MagicMock()
	mock_choice.message.content = text

	mock_response = MagicMock()
	mock_response.choices = [mock_choice]
	return mock_response


@patch("studyforge.llm.router.OpenAI")
def test_chat_returns_response(mock_deepseek):
	mock_client = MagicMock()
	mock_deepseek.return_value = mock_client
	mock_client.chat.completions.create.return_value = make_mock_response("4")

	router = LLMRouter()
	result = router.chat("What is 2+2?")

	assert result == "4"
	assert len(router.history) == 2
	assert router.history[0] == Message(role="user", content="What is 2+2?")
	assert router.history[1] == Message(role="assistant", content="4")


@patch("studyforge.llm.router.OpenAI")
def test_history_accumulates(mock_deepseek):
	mock_client = MagicMock()
	mock_deepseek.return_value = mock_client
	mock_client.messages.create.return_value = make_mock_response("yes")

	router = LLMRouter()
	router.chat("First message")
	router.chat("Second message")

	assert len(router.history) == 4


@patch("studyforge.llm.router.OpenAI")
def test_clear_history(mock_deepseek):
	mock_client = MagicMock()
	mock_deepseek.return_value = mock_client
	mock_client.messages.create.return_value = make_mock_response("ok")
	
	router = LLMRouter()
	router.chat("Hello")
	router.clear_history()

	assert router.history == []
