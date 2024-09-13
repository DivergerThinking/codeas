from unittest.mock import Mock, patch

import pytest

from codeag.core.agent import Agent, AgentOutput, AgentPreview
from codeag.core.llms import LLMClient


@pytest.fixture
def sample_agent():
    return Agent(
        instructions="Test instruction",
        model="gpt-3.5-turbo",
        system_prompt="You are a helpful assistant.",
    )


@pytest.fixture
def mock_llm_client():
    return Mock(spec=LLMClient)


def test_agent_initialization(sample_agent):
    assert sample_agent.instructions == "Test instruction"
    assert sample_agent.model == "gpt-3.5-turbo"
    assert sample_agent.system_prompt == "You are a helpful assistant."


def test_get_single_messages(sample_agent):
    context = "Test context"
    messages = sample_agent.get_single_messages(context)
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == context
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == sample_agent.instructions


def test_get_multi_messages(sample_agent):
    contexts = ["Context 1", "Context 2"]
    messages = sample_agent.get_multi_messages(contexts)
    assert len(messages) == 4
    assert messages[1]["content"] == contexts[0]
    assert messages[2]["content"] == contexts[1]


def test_get_batch_messages(sample_agent):
    batch_contexts = {"key1": "Context 1", "key2": "Context 2"}
    messages = sample_agent.get_batch_messages(batch_contexts)
    assert len(messages) == 2
    assert len(messages["key1"]) == 3
    assert len(messages["key2"]) == 3


@patch("codeag.core.agent.calculate_all_costs_and_tokens")
@patch("codeag.core.agent.count_message_tokens")
@patch("codeag.core.agent.calculate_prompt_cost")
def test_run(
    mock_calc_prompt_cost,
    mock_count_tokens,
    mock_calc_all_costs,
    sample_agent,
    mock_llm_client,
):
    mock_count_tokens.return_value = 10
    mock_calc_prompt_cost.return_value = 0.001
    mock_calc_all_costs.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "prompt_cost": 0.001,
        "completion_cost": 0.002,
    }
    mock_llm_client.run.return_value = {"content": "Test response"}

    result = sample_agent.run(mock_llm_client, context="Test context")

    assert isinstance(result, AgentOutput)
    assert result.response == {"content": "Test response"}
    assert result.tokens == {
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    }
    assert result.cost == {
        "input_cost": 0.001,
        "output_cost": 0.002,
        "total_cost": 0.003,
    }


def test_preview(sample_agent):
    result = sample_agent.preview("Test context")

    assert isinstance(result, AgentPreview)
    assert len(result.messages) == 3
    assert "input_tokens" in result.tokens
    assert "input_cost" in result.cost
