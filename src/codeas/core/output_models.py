"""
Unified output data models for use case operations.

These models replace the dynamic type() antipattern used throughout
the UI components for creating mock Output objects.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field


class CostInfo(BaseModel):
    """Token cost information."""

    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0


class TokenInfo(BaseModel):
    """Token count information."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class UseCaseOutput(BaseModel):
    """
    Unified output model for all use case operations.

    This replaces the `type("Output", (), {...})` antipattern used
    throughout the UI components.
    """

    response: Any = None
    cost: CostInfo = Field(default_factory=CostInfo)
    tokens: TokenInfo = Field(default_factory=TokenInfo)
    messages: List[Dict[str, str]] = Field(default_factory=list)

    @classmethod
    def from_agent_output(cls, agent_output) -> "UseCaseOutput":
        """
        Convert an AgentOutput to UseCaseOutput.

        Args:
            agent_output: AgentOutput instance from agent.run()

        Returns:
            UseCaseOutput instance
        """
        cost_dict = agent_output.cost
        tokens_dict = agent_output.tokens

        return cls(
            response=agent_output.response,
            cost=CostInfo(
                input_cost=cost_dict.get("input_cost", 0.0),
                output_cost=cost_dict.get("output_cost", 0.0),
                total_cost=cost_dict.get("total_cost", 0.0),
            ),
            tokens=TokenInfo(
                input_tokens=tokens_dict.get("input_tokens", 0),
                output_tokens=tokens_dict.get("output_tokens", 0),
                total_tokens=tokens_dict.get("total_tokens", 0),
            ),
            messages=(
                agent_output.messages if isinstance(agent_output.messages, list) else []
            ),
        )

    @classmethod
    def from_cached(cls, cached_data: dict) -> "UseCaseOutput":
        """
        Reconstruct from cached JSON data.

        Args:
            cached_data: Dictionary loaded from JSON cache file

        Returns:
            UseCaseOutput instance
        """
        cost_data = cached_data.get("cost", {})
        tokens_data = cached_data.get("tokens", {})

        return cls(
            response={"content": cached_data.get("content")},
            cost=CostInfo(
                input_cost=cost_data.get("input_cost", 0.0),
                output_cost=cost_data.get("output_cost", 0.0),
                total_cost=cost_data.get("total_cost", 0.0),
            ),
            tokens=TokenInfo(
                input_tokens=tokens_data.get("input_tokens", 0),
                output_tokens=tokens_data.get("output_tokens", 0),
                total_tokens=tokens_data.get("total_tokens", 0),
            ),
            messages=cached_data.get("messages", []),
        )

    def to_cache_dict(self) -> dict:
        """
        Convert to dictionary for JSON caching.

        Returns:
            Dictionary suitable for JSON serialization
        """
        content = None
        if isinstance(self.response, dict):
            content = self.response.get("content", self.response)
        else:
            content = self.response

        return {
            "content": content,
            "cost": self.cost.model_dump(),
            "tokens": self.tokens.model_dump(),
            "messages": self.messages,
        }


T = TypeVar("T", bound=BaseModel)


class ParsedUseCaseOutput(UseCaseOutput):
    """
    Output model for structured response formats.

    Used when the agent returns a Pydantic model response.
    """

    parsed_content: Optional[Any] = None

    @classmethod
    def from_agent_output(
        cls, agent_output, model_class: Optional[Type[T]] = None
    ) -> "ParsedUseCaseOutput":
        """
        Convert an AgentOutput with structured response to ParsedUseCaseOutput.

        Args:
            agent_output: AgentOutput instance from agent.run()
            model_class: Optional Pydantic model class for parsing

        Returns:
            ParsedUseCaseOutput instance
        """
        base = UseCaseOutput.from_agent_output(agent_output)
        instance = cls(
            response=base.response,
            cost=base.cost,
            tokens=base.tokens,
            messages=base.messages,
        )

        # Extract parsed content from structured response
        if model_class and hasattr(agent_output.response, "choices"):
            try:
                instance.parsed_content = agent_output.response.choices[
                    0
                ].message.parsed
            except (AttributeError, IndexError):
                pass

        return instance

    @classmethod
    def from_cached(
        cls, cached_data: dict, model_class: Optional[Type[T]] = None
    ) -> "ParsedUseCaseOutput":
        """
        Reconstruct from cached JSON data with optional model validation.

        Args:
            cached_data: Dictionary loaded from JSON cache file
            model_class: Optional Pydantic model class for content validation

        Returns:
            ParsedUseCaseOutput instance
        """
        base = UseCaseOutput.from_cached(cached_data)
        instance = cls(
            response=base.response,
            cost=base.cost,
            tokens=base.tokens,
            messages=base.messages,
        )

        if model_class and "content" in cached_data:
            try:
                instance.parsed_content = model_class.model_validate(
                    cached_data["content"]
                )
            except Exception:
                pass

        return instance

    def to_cache_dict(self) -> dict:
        """
        Convert to dictionary for JSON caching.

        Returns:
            Dictionary suitable for JSON serialization
        """
        result = super().to_cache_dict()

        # If we have parsed content, use that for caching
        if self.parsed_content is not None:
            if hasattr(self.parsed_content, "model_dump"):
                result["content"] = self.parsed_content.model_dump()
            else:
                result["content"] = self.parsed_content

        return result
