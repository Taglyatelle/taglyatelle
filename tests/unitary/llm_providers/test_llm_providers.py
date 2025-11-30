"""Unit tests for LLM providers."""

import pytest
from taglyatelle.llm_providers.core.llm_factory import LlmProvider
from taglyatelle.llm_providers.openai_api import OpenAIAdapter
from taglyatelle.llm_providers.anthropic_api import AnthropicAdapter
from taglyatelle.llm_providers.gemini_api import GeminiAdapter
from taglyatelle.llm_providers.meta_api import MetaAdapter
from taglyatelle.llm_providers.mistral_api import MistralAdapter


@pytest.mark.parametrize(
    "provider_name,adapter_path,client_path,return_value",
    [
        (
            "openai",
            "taglyatelle.llm_providers.openai_api.OpenAIAdapter.invoke_llm",
            "taglyatelle.llm_providers.openai_api.OpenAI",
            "openai response",
        ),
        (
            "gemini",
            "taglyatelle.llm_providers.gemini_api.GeminiAdapter.invoke_llm",
            "taglyatelle.llm_providers.gemini_api.genai.Client",
            "gemini response",
        ),
        (
            "anthropic",
            "taglyatelle.llm_providers.anthropic_api.AnthropicAdapter.invoke_llm",
            "taglyatelle.llm_providers.anthropic_api.Anthropic",
            "anthropic response",
        ),
    ],
)
def test_llm_provider_invoke_llm(
    provider_name, adapter_path, client_path, return_value, mocker
):
    """
    Test LlmProvider.invoke_llm for different providers using mocks.
    """
    mocker.patch(client_path)
    mocker.patch(adapter_path, return_value=return_value)
    provider = LlmProvider(provider=provider_name, model="test-model", temperature=0)
    result = provider.invoke_llm("test prompt")
    assert result == return_value


def test_anthropic_adapter_invoke_llm_text_block(mocker):
    mock_client = mocker.Mock()
    text_block = mocker.Mock()
    text_block.text = "anthropic text"
    response = mocker.Mock()
    response.content = [text_block]
    mock_client.messages.create.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.anthropic_api.Anthropic", return_value=mock_client
    )
    adapter = AnthropicAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result == "anthropic text"


def test_anthropic_adapter_invoke_llm_no_text_block(mocker):
    mock_client = mocker.Mock()
    response = mocker.Mock()
    response.content = []
    mock_client.messages.create.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.anthropic_api.Anthropic", return_value=mock_client
    )
    adapter = AnthropicAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result is None


def test_gemini_adapter_invoke_llm(mocker):
    mock_client = mocker.Mock()
    response = mocker.Mock()
    response.text = "gemini text"
    mock_client.models.generate_content.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.gemini_api.genai.Client", return_value=mock_client
    )
    adapter = GeminiAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result == "gemini text"


def test_openai_adapter_invoke_llm(mocker):
    mock_client = mocker.Mock()
    message = mocker.Mock()
    message.content = "openai text"
    choice = mocker.Mock()
    choice.message = message
    response = mocker.Mock()
    response.choices = [choice]
    mock_client.chat.completions.create.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.openai_api.OpenAI", return_value=mock_client
    )
    adapter = OpenAIAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result == "openai text"


def test_meta_adapter_invoke_llm(mocker):
    mock_client = mocker.Mock()
    content = mocker.Mock()
    content.text = "meta text"
    completion_message = mocker.Mock()
    completion_message.content = content
    response = mocker.Mock()
    response.completion_message = completion_message
    mock_client.chat.completions.create.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.meta_api.LlamaAPIClient", return_value=mock_client
    )
    adapter = MetaAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result == "meta text"


def test_mistral_adapter_invoke_llm(mocker):
    mock_client = mocker.Mock()
    message = mocker.Mock()
    message.content = "mistral text"
    choice = mocker.Mock()
    choice.message = message
    response = mocker.Mock()
    response.choices = [choice]
    mock_client.chat.complete.return_value = response
    mocker.patch(
        "taglyatelle.llm_providers.mistral_api.Mistral", return_value=mock_client
    )
    adapter = MistralAdapter(model="test-model", temperature=0)
    result = adapter.invoke_llm("prompt")
    assert result == "mistral text"
