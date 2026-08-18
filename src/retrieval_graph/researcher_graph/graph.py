"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and executing parallel retrieval
from both local Knowledge Base vector stores and Web Research APIs.
"""

from typing import TypedDict, cast

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from retrieval_graph.configuration import AgentConfiguration
from retrieval_graph.researcher_graph.state import QueryState, ResearcherState
from shared import retrieval
from shared.utils import load_chat_model
from shared.tools.web_search import search_web_with_timeout


async def generate_queries(
    state: ResearcherState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate search queries based on the question (a step in the research plan).

    This function uses a language model to generate diverse search queries to help answer the question.

    Args:
        state (ResearcherState): The current state of the researcher, including the user's question.
        config (RunnableConfig): Configuration with the model used to generate queries.

    Returns:
        dict[str, list[str]]: A dictionary with a 'queries' key containing the list of generated search queries.
    """

    class Response(TypedDict):
        queries: list[str]

    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(Response)
    messages = [
        {"role": "system", "content": configuration.generate_queries_system_prompt},
        {"role": "human", "content": state.question},
    ]
    response = cast(Response, await model.ainvoke(messages))
    return {"queries": response["queries"]}


async def retrieve_documents(
    state: QueryState, *, config: RunnableConfig
) -> dict[str, list[Document]]:
    """Retrieve documents from local Knowledge Base vector store based on a given query.

    Args:
        state (QueryState): The current state containing the query string.
        config (RunnableConfig): Configuration with the retriever used to fetch documents.

    Returns:
        dict[str, list[Document]]: A dictionary with a 'documents' key containing the list of retrieved documents.
    """
    with retrieval.make_retriever(config) as retriever:
        response = await retriever.ainvoke(state.query, config)
        return {"documents": response}


async def web_search_documents(
    state: QueryState, *, config: RunnableConfig
) -> dict[str, list[Document]]:
    """Retrieve documents from live Web Research APIs based on a given query with timeout and error protection."""
    configuration = AgentConfiguration.from_runnable_config(config)
    if not configuration.enable_web_search:
        return {"documents": []}

    docs = await search_web_with_timeout(
        query=state.query,
        provider=configuration.web_search_provider,
        max_results=configuration.web_search_max_results,
        timeout_seconds=configuration.web_search_timeout_seconds,
    )
    return {"documents": docs}


def retrieve_in_parallel(state: ResearcherState) -> list[Send]:
    """Create parallel retrieval tasks for each generated query across Knowledge Base & Web Research.

    Args:
        state (ResearcherState): The current state of the researcher, including the generated queries.

    Returns:
        list[Send]: A list of Send objects targeting both Knowledge Base and Web Research nodes.
    """
    tasks = []
    for query in state.queries:
        tasks.append(Send("retrieve_documents", QueryState(query=query)))
        tasks.append(Send("web_search_documents", QueryState(query=query)))
    return tasks


# Define the graph
builder = StateGraph(ResearcherState)
builder.add_node(generate_queries)
builder.add_node(retrieve_documents)
builder.add_node(web_search_documents)

builder.add_edge(START, "generate_queries")
builder.add_conditional_edges(
    "generate_queries",
    retrieve_in_parallel,  # type: ignore
    path_map=["retrieve_documents", "web_search_documents"],
)
builder.add_edge("retrieve_documents", END)
builder.add_edge("web_search_documents", END)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "ResearcherGraph"
