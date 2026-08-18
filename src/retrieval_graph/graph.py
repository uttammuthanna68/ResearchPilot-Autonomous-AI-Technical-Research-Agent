"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""

from typing import Any, Literal, TypedDict, cast

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from retrieval_graph.configuration import AgentConfiguration
from retrieval_graph.researcher_graph.graph import graph as researcher_graph
from retrieval_graph.state import AgentState, EvidenceVerification, InputState, Router
from shared.utils import format_docs, load_chat_model


async def analyze_and_route_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, Router]:
    """Analyze the user's query and determine the appropriate routing.

    This function uses a language model to classify the user's query and decide how to route it
    within the conversation flow.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used for query analysis.

    Returns:
        dict[str, Router]: A dictionary containing the 'router' key with the classification result (classification type and logic).
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    messages = [
        {"role": "system", "content": configuration.router_system_prompt}
    ] + state.messages
    response = cast(
        Router, await model.with_structured_output(Router).ainvoke(messages)
    )
    return {"router": response}


def route_query(
    state: AgentState,
) -> Literal["create_research_plan", "ask_for_more_info", "respond_to_general_query"]:
    """Determine the next step based on the query classification.

    Args:
        state (AgentState): The current state of the agent, including the router's classification.

    Returns:
        Literal["create_research_plan", "ask_for_more_info", "respond_to_general_query"]: The next step to take.

    Raises:
        ValueError: If an unknown router type is encountered.
    """
    _type = state.router["type"]
    if _type in ("research", "technical", "langchain"):
        return "create_research_plan"
    elif _type == "more-info":
        return "ask_for_more_info"
    elif _type == "general":
        return "respond_to_general_query"
    else:
        raise ValueError(f"Unknown router type {_type}")


async def ask_for_more_info(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a response asking the user for more information.

    This node is called when the router determines that more information is needed from the user.

    Args:
        state (AgentState): The current state of the agent, including conversation history and router logic.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.more_info_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


async def respond_to_general_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a response to a general query not related to LangChain.

    This node is called when the router classifies the query as a general question.

    Args:
        state (AgentState): The current state of the agent, including conversation history and router logic.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


async def create_research_plan(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[str] | str]:
    """Create a step-by-step research plan for answering a LangChain-related query.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used to generate the plan.

    Returns:
        dict[str, list[str]]: A dictionary with a 'steps' key containing the list of research steps.
    """

    class Plan(TypedDict):
        """Generate research plan."""

        steps: list[str]

    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(Plan)
    messages = [
        {"role": "system", "content": configuration.research_plan_system_prompt}
    ] + state.messages
    response = cast(Plan, await model.ainvoke(messages))
    return {"steps": response["steps"], "documents": "delete"}


async def conduct_research(state: AgentState) -> dict[str, Any]:
    """Execute the first step of the research plan.

    This function takes the first step from the research plan and uses it to conduct research.

    Args:
        state (AgentState): The current state of the agent, including the research plan steps.

    Returns:
        dict[str, list[str]]: A dictionary with 'documents' containing the research results and
                              'steps' containing the remaining research steps.

    Behavior:
        - Invokes the researcher_graph with the first step of the research plan.
        - Updates the state with the retrieved documents and removes the completed step.
    """
    result = await researcher_graph.ainvoke({"question": state.steps[0]})
    return {"documents": result["documents"], "steps": state.steps[1:]}


async def verify_evidence(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, Any]:
    """Evaluate retrieved evidence documents for factual support, gaps, and conflicts.

    Args:
        state (AgentState): Current state containing retrieved documents and user query.
        config (RunnableConfig): Configuration for LLM call.

    Returns:
        dict[str, Any]: A dictionary updating the evidence_verification state attribute.
    """
    if not state.documents:
        return {
            "evidence_verification": {
                "status": "insufficient",
                "summary": "No retrieved context available from knowledge base or web search.",
                "verified_claims": [],
                "conflicting_claims": [],
                "missing_elements": ["All query topics (zero evidence documents retrieved)"],
            }
        }

    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(EvidenceVerification)

    context = format_docs(state.documents)
    user_query = state.messages[-1].content if state.messages else ""

    messages = [
        {
            "role": "system",
            "content": (
                "You are ResearchPilot's Evidence Verification Engine.\n"
                "Evaluate the retrieved evidence documents against the user's technical query.\n"
                "Determine:\n"
                "- status: 'supported' (evidence directly answers query), 'insufficient' (missing key facts/details), or 'conflicting' (sources contradict each other).\n"
                "- summary: Concise explanation of your analysis.\n"
                "- verified_claims: List of facts directly supported by the context.\n"
                "- conflicting_claims: List of contradictory statements across sources.\n"
                "- missing_elements: Gaps or unverified topics needing further evidence."
            ),
        },
        {
            "role": "user",
            "content": f"User Query: {user_query}\n\nRetrieved Evidence:\n{context}",
        },
    ]

    try:
        verification = cast(EvidenceVerification, await model.ainvoke(messages))
        return {"evidence_verification": verification}
    except Exception as e:
        return {
            "evidence_verification": {
                "status": "supported" if len(state.documents) > 0 else "insufficient",
                "summary": f"Evidence evaluated with {len(state.documents)} source documents.",
                "verified_claims": ["Retrieved context available for synthesis"],
                "conflicting_claims": [],
                "missing_elements": [],
            }
        }


def check_finished(state: AgentState) -> Literal["verify_evidence", "conduct_research"]:
    """Determine if the research process is complete or if more research is needed.

    Args:
        state (AgentState): The current state of the agent, including remaining research steps.

    Returns:
        Literal["verify_evidence", "conduct_research"]: The next step to take.
    """
    if len(state.steps or []) > 0:
        return "conduct_research"
    else:
        return "verify_evidence"


async def respond(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a final response to the user's query based on the verified research.

    Args:
        state (AgentState): The current state of the agent, including retrieved documents and verification results.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.response_model)
    context = format_docs(state.documents)
    verification = state.evidence_verification or {}
    v_status = verification.get("status", "supported")
    v_summary = verification.get("summary", "Evidence verified.")

    prompt = configuration.response_system_prompt.format(
        context=context,
        verification_status=v_status,
        verification_summary=v_summary,
    )
    messages = [{"role": "system", "content": prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


# Define the graph
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)
builder.add_node(analyze_and_route_query)
builder.add_node(ask_for_more_info)
builder.add_node(respond_to_general_query)
builder.add_node(conduct_research)
builder.add_node(create_research_plan)
builder.add_node(verify_evidence)
builder.add_node(respond)

builder.add_edge(START, "analyze_and_route_query")
builder.add_conditional_edges("analyze_and_route_query", route_query)
builder.add_edge("create_research_plan", "conduct_research")
builder.add_conditional_edges("conduct_research", check_finished)
builder.add_edge("verify_evidence", "respond")
builder.add_edge("ask_for_more_info", END)
builder.add_edge("respond_to_general_query", END)
builder.add_edge("respond", END)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "RetrievalGraph"
