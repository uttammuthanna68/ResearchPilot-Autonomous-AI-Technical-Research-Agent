"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Literal, Optional, Type, TypeVar

from langchain_core.runnables import RunnableConfig, ensure_config


@dataclass(kw_only=True)
class BaseConfiguration:
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and
    retrieval processes, including embedding model selection, retriever provider choice, and search parameters.
    """

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        default="google_genai/gemini-embedding-001",
        metadata={
            "description": "Name of the embedding model to use. Must be a valid embedding model name."
        },
    )

    retriever_provider: Annotated[
        Literal["chroma", "elastic-local", "elastic", "pinecone", "mongodb"],
        {"__template_metadata__": {"kind": "retriever"}},
    ] = field(
        default="chroma",
        metadata={
            "description": "The vector store provider to use for retrieval. Options are 'chroma', 'elastic', 'pinecone', or 'mongodb'."
        },
    )

    chroma_persist_directory: str = field(
        default="./data/chroma",
        metadata={
            "description": "Local directory path to persist embedded Chroma vector database."
        },
    )

    search_kwargs: dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever."
        },
    )

    enable_web_search: bool = field(
        default=True,
        metadata={
            "description": "Whether web research is enabled for the research workflow."
        },
    )

    web_search_provider: Literal["duckduckgo", "tavily", "serper"] = field(
        default="duckduckgo",
        metadata={
            "description": "The web search provider to use ('duckduckgo', 'tavily', or 'serper')."
        },
    )

    web_search_max_results: int = field(
        default=3,
        metadata={
            "description": "Maximum number of web search results per query."
        },
    )

    web_search_timeout_seconds: float = field(
        default=8.0,
        metadata={
            "description": "Timeout limit in seconds for web search operations."
        },
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create an IndexConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of IndexConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


T = TypeVar("T", bound=BaseConfiguration)
