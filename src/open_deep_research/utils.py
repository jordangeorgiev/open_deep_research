"""Utility functions and helpers for the Deep Research agent."""

import asyncio
import json
import logging
import os
import warnings
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional, Type, TypeVar

import aiohttp
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    MessageLikeRepresentation,
    SystemMessage,
    filter_messages,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import (
    BaseTool,
    InjectedToolArg,
    StructuredTool,
    ToolException,
    tool,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.config import get_store
from mcp import McpError
from pydantic import BaseModel, ValidationError
from tavily import AsyncTavilyClient

from open_deep_research.configuration import Configuration, SearchAPI
from open_deep_research.prompts import summarize_webpage_prompt
from open_deep_research.state import ResearchComplete, Summary

T = TypeVar('T', bound=BaseModel)

##########################
# Structured Output Compatibility Utils
##########################

def supports_structured_output(model_name: str) -> bool:
    """Check if a model supports LangChain's with_structured_output() method.

    Args:
        model_name: The model identifier string

    Returns:
        True if the model supports structured output, False otherwise
    """
    model_str = str(model_name).lower()

    # Models that support structured output
    supported_providers = [
        'openai:',
        'anthropic:',
        'google:',
        'gemini:',
    ]

    # Ollama and other local models don't support structured output
    unsupported_providers = [
        'ollama:',
        'together:',
        'groq:',  # Groq may support it, but being conservative
    ]

    # Check if it's an unsupported provider
    for provider in unsupported_providers:
        if model_str.startswith(provider):
            return False

    # Check if it's a supported provider
    for provider in supported_providers:
        if model_str.startswith(provider):
            return True

    # Default to False for unknown providers
    return False

def get_model_with_structured_output(
    model: BaseChatModel,
    model_name: str,
    schema: Type[T],
    max_retries: int = 3
) -> BaseChatModel:
    """Get a model configured for structured output with fallback to JSON mode.

    This function handles both models that support with_structured_output()
    (like OpenAI, Anthropic) and those that don't (like Ollama), providing
    a consistent interface for getting structured responses.

    Args:
        model: The base chat model instance
        model_name: The model identifier string
        schema: Pydantic model class for the expected output structure
        max_retries: Maximum number of retry attempts

    Returns:
        Configured model that can return structured output
    """
    if supports_structured_output(model_name):
        # Use native structured output for supported models
        return model.with_structured_output(schema).with_retry(
            stop_after_attempt=max_retries
        )
    else:
        # For Ollama and other models, we'll use JSON mode
        # Return the base model - we'll handle JSON parsing manually
        return model.with_retry(stop_after_attempt=max_retries)

async def get_structured_output_from_model(
    model: BaseChatModel,
    model_name: str,
    messages: List[MessageLikeRepresentation],
    schema: Type[T],
    schema_name: str = "output"
) -> T:
    """Get structured output from a model with automatic fallback to JSON parsing.

    For models that support structured output (OpenAI, Anthropic), uses that directly.
    For Ollama and other models, instructs them to output JSON and parses it.

    Args:
        model: The chat model instance
        model_name: The model identifier
        messages: List of messages to send to the model
        schema: Pydantic model class for validation
        schema_name: Name to use in JSON schema description

    Returns:
        Validated instance of the schema type

    Raises:
        ValidationError: If the model's output doesn't match the schema
    """
    if supports_structured_output(model_name):
        # Model supports structured output directly
        response = await model.ainvoke(messages)
        return response
    else:
        # Use JSON mode for Ollama and similar models
        # Add JSON schema instruction to the last message
        schema_dict = schema.model_json_schema()

        # Create a clearer example of what we expect
        field_descriptions = []
        for field_name, field_info in schema_dict.get('properties', {}).items():
            field_desc = field_info.get('description', '')
            field_type = field_info.get('type', 'string')
            field_descriptions.append(f'  "{field_name}": <{field_type}> - {field_desc}')

        json_instruction = f"""

IMPORTANT: You must respond with a valid JSON object (NOT the schema itself).

Required JSON format:
{{
{chr(10).join(field_descriptions)}
}}

Respond ONLY with a JSON object containing actual values for these fields. Do NOT return the schema definition itself."""

        # Clone messages and add instruction to last message
        modified_messages = list(messages)
        if modified_messages:
            last_msg = modified_messages[-1]
            if isinstance(last_msg, HumanMessage):
                modified_messages[-1] = HumanMessage(
                    content=last_msg.content + json_instruction
                )
            else:
                # If last message isn't human, add a new one
                modified_messages.append(HumanMessage(content=json_instruction))

        # Get response from model
        response = await model.ainvoke(modified_messages)

        # Parse JSON from response
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Try to extract JSON from markdown code blocks if present
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            # Generic code block
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()

        # Parse and validate JSON
        try:
            parsed_data = json.loads(response_text.strip())
            return schema(**parsed_data)
        except (json.JSONDecodeError, ValidationError) as e:
            logging.error(f"Failed to parse structured output from {model_name}: {e}")
            logging.error(f"Response was: {response_text[:500]}")
            raise

##########################
# Tavily Search Tool Utils
##########################
TAVILY_SEARCH_DESCRIPTION = (
    "A search engine optimized for comprehensive, accurate, and trusted results. "
    "Useful for when you need to answer questions about current events."
)
@tool(description=TAVILY_SEARCH_DESCRIPTION)
async def tavily_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 5,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
    config: RunnableConfig = None
) -> str:
    """Fetch and summarize search results from Tavily search API.

    Args:
        queries: List of search queries to execute
        max_results: Maximum number of results to return per query
        topic: Topic filter for search results (general, news, or finance)
        config: Runtime configuration for API keys and model settings

    Returns:
        Formatted string containing summarized search results
    """
    # Step 1: Execute search queries asynchronously
    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
        config=config
    )
    
    # Step 2: Deduplicate results by URL to avoid processing the same content multiple times
    unique_results = {}
    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = {**result, "query": response['query']}
    
    # Step 3: Set up the summarization model with configuration
    configurable = Configuration.from_runnable_config(config)

    # Character limit to stay within model token limits (configurable)
    max_char_to_include = configurable.max_content_length

    # Initialize summarization model with retry logic
    model_api_key = get_api_key_for_model(configurable.summarization_model, config)
    base_model = init_chat_model(
        model=configurable.summarization_model,
        max_tokens=configurable.summarization_model_max_tokens,
        api_key=model_api_key,
        tags=["langsmith:nostream"]
    )

    # Use our helper to configure structured output with Ollama support
    summarization_model = get_model_with_structured_output(
        base_model,
        configurable.summarization_model,
        Summary,
        configurable.max_structured_output_retries
    )

    # Step 4: Create summarization tasks (skip empty content)
    async def noop():
        """No-op function for results without raw content."""
        return None

    summarization_tasks = [
        noop() if not result.get("raw_content")
        else summarize_webpage(
            summarization_model,
            result['raw_content'][:max_char_to_include],
            configurable.summarization_model
        )
        for result in unique_results.values()
    ]
    
    # Step 5: Execute all summarization tasks in parallel
    summaries = await asyncio.gather(*summarization_tasks)
    
    # Step 6: Combine results with their summaries
    summarized_results = {
        url: {
            'title': result['title'], 
            'content': result['content'] if summary is None else summary
        }
        for url, result, summary in zip(
            unique_results.keys(), 
            unique_results.values(), 
            summaries
        )
    }
    
    # Step 7: Format the final output
    if not summarized_results:
        return "No valid search results found. Please try different search queries or use a different search API."
    
    formatted_output = "Search results: \n\n"
    for i, (url, result) in enumerate(summarized_results.items()):
        formatted_output += f"\n\n--- SOURCE {i+1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "\n\n" + "-" * 80 + "\n"
    
    return formatted_output

async def tavily_search_async(
    search_queries, 
    max_results: int = 5, 
    topic: Literal["general", "news", "finance"] = "general", 
    include_raw_content: bool = True, 
    config: RunnableConfig = None
):
    """Execute multiple Tavily search queries asynchronously.
    
    Args:
        search_queries: List of search query strings to execute
        max_results: Maximum number of results per query
        topic: Topic category for filtering results
        include_raw_content: Whether to include full webpage content
        config: Runtime configuration for API key access
        
    Returns:
        List of search result dictionaries from Tavily API
    """
    # Initialize the Tavily client with API key from config
    tavily_client = AsyncTavilyClient(api_key=get_tavily_api_key(config))
    
    # Create search tasks for parallel execution
    search_tasks = [
        tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic
        )
        for query in search_queries
    ]
    
    # Execute all search queries in parallel and return results
    search_results = await asyncio.gather(*search_tasks)
    return search_results

async def summarize_webpage(
    model: BaseChatModel,
    webpage_content: str,
    model_name: str = None
) -> str:
    """Summarize webpage content using AI model with timeout protection.

    Args:
        model: The chat model configured for summarization
        webpage_content: Raw webpage content to be summarized
        model_name: Optional model name for determining structured output support

    Returns:
        Formatted summary with key excerpts, or original content if summarization fails
    """
    try:
        # Create prompt with current date context
        prompt_content = summarize_webpage_prompt.format(
            webpage_content=webpage_content,
            date=get_today_str()
        )

        # Determine if we need to use structured output helper
        if model_name and not supports_structured_output(model_name):
            # Use JSON mode for Ollama and similar models
            summary = await asyncio.wait_for(
                get_structured_output_from_model(
                    model,
                    model_name,
                    [HumanMessage(content=prompt_content)],
                    Summary,
                    "webpage_summary"
                ),
                timeout=60.0
            )
        else:
            # Use native structured output for OpenAI/Anthropic
            summary = await asyncio.wait_for(
                model.ainvoke([HumanMessage(content=prompt_content)]),
                timeout=60.0
            )

        # Format the summary with structured sections
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except asyncio.TimeoutError:
        # Timeout during summarization - return original content
        logging.warning("Summarization timed out after 60 seconds, returning original content")
        return webpage_content
    except Exception as e:
        # Other errors during summarization - log and return original content
        logging.warning(f"Summarization failed with error: {str(e)}, returning original content")
        return webpage_content

##########################
# SearXNG Search Tool Utils
##########################
SEARXNG_SEARCH_DESCRIPTION = (
    "A local privacy-focused metasearch engine that aggregates results from multiple sources. "
    "Useful for when you need to answer questions about current events using local search infrastructure."
)

@tool(description=SEARXNG_SEARCH_DESCRIPTION)
async def searxng_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 5,
    config: RunnableConfig = None
) -> str:
    """Fetch and summarize search results from SearXNG local search engine.

    Args:
        queries: List of search queries to execute
        max_results: Maximum number of results to return per query
        config: Runtime configuration for SearXNG URL and model settings

    Returns:
        Formatted string containing summarized search results
    """
    # Step 1: Execute search queries asynchronously
    search_results = await searxng_search_async(
        queries,
        max_results=max_results,
        config=config
    )

    # Step 2: Deduplicate results by URL to avoid processing the same content multiple times
    unique_results = {}
    for response in search_results:
        for result in response.get('results', []):
            url = result.get('url')
            if url and url not in unique_results:
                unique_results[url] = {
                    'title': result.get('title', 'No title'),
                    'content': result.get('content', ''),
                    'query': response.get('query', '')
                }

    # Step 3: Set up the summarization model with configuration
    configurable = Configuration.from_runnable_config(config)

    # Character limit to stay within model token limits (configurable)
    max_char_to_include = configurable.max_content_length

    # Initialize summarization model with retry logic
    model_api_key = get_api_key_for_model(configurable.summarization_model, config)
    base_model = init_chat_model(
        model=configurable.summarization_model,
        max_tokens=configurable.summarization_model_max_tokens,
        api_key=model_api_key,
        tags=["langsmith:nostream"]
    )

    # Use our helper to configure structured output with Ollama support
    summarization_model = get_model_with_structured_output(
        base_model,
        configurable.summarization_model,
        Summary,
        configurable.max_structured_output_retries
    )

    # Step 4: Create summarization tasks (skip empty content)
    async def noop():
        """No-op function for results without content."""
        return None

    summarization_tasks = [
        noop() if not result.get("content")
        else summarize_webpage(
            summarization_model,
            result['content'][:max_char_to_include],
            configurable.summarization_model
        )
        for result in unique_results.values()
    ]

    # Step 5: Execute all summarization tasks in parallel
    summaries = await asyncio.gather(*summarization_tasks)

    # Step 6: Combine results with their summaries
    summarized_results = {
        url: {
            'title': result['title'],
            'content': result['content'] if summary is None else summary
        }
        for url, result, summary in zip(
            unique_results.keys(),
            unique_results.values(),
            summaries
        )
    }

    # Step 7: Format the final output
    if not summarized_results:
        return "No valid search results found. Please try different search queries or check SearXNG server status."

    formatted_output = "Search results: \n\n"
    for i, (url, result) in enumerate(summarized_results.items()):
        formatted_output += f"\n\n--- SOURCE {i+1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "\n\n" + "-" * 80 + "\n"

    return formatted_output

async def searxng_search_async(
    search_queries: List[str],
    max_results: int = 5,
    config: RunnableConfig = None
):
    """Execute multiple SearXNG search queries asynchronously.

    Args:
        search_queries: List of search query strings to execute
        max_results: Maximum number of results per query
        config: Runtime configuration for SearXNG URL access

    Returns:
        List of search result dictionaries from SearXNG API
    """
    # Get SearXNG URL from configuration
    configurable = Configuration.from_runnable_config(config)
    searxng_url = configurable.searxng_url.rstrip('/')

    async def execute_search(query: str):
        """Execute a single SearXNG search query."""
        try:
            async with aiohttp.ClientSession() as session:
                # SearXNG search endpoint with JSON format
                search_url = f"{searxng_url}/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'pageno': 1
                }

                async with session.get(search_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Add query to response for tracking
                        return {
                            'query': query,
                            'results': data.get('results', [])[:max_results]
                        }
                    else:
                        logging.warning(f"SearXNG search failed with status {response.status} for query: {query}")
                        return {'query': query, 'results': []}

        except asyncio.TimeoutError:
            logging.warning(f"SearXNG search timed out for query: {query}")
            return {'query': query, 'results': []}
        except Exception as e:
            logging.warning(f"SearXNG search error for query '{query}': {str(e)}")
            return {'query': query, 'results': []}

    # Create search tasks for parallel execution
    search_tasks = [execute_search(query) for query in search_queries]

    # Execute all search queries in parallel and return results
    search_results = await asyncio.gather(*search_tasks)
    return search_results

##########################
# Ollama Tool Calling Emulation (ReAct Style)
##########################

def format_tools_for_ollama(tools: List[Any]) -> str:
    """Format tools as text descriptions for Ollama models.

    Args:
        tools: List of tools (can be BaseTools, dicts, or Pydantic classes)

    Returns:
        Formatted string describing all available tools
    """
    tool_descriptions = []

    for tool in tools:
        # Handle different tool types
        if isinstance(tool, dict):
            # Native API tools like web_search
            tool_name = tool.get('name', tool.get('type', 'unknown'))
            tool_desc = f"Tool for {tool_name}"
            tool_descriptions.append(f"- **{tool_name}**: {tool_desc}")

        elif isinstance(tool, type) and issubclass(tool, BaseModel):
            # Pydantic model tools like ConductResearch
            tool_name = tool.__name__
            tool_desc = tool.__doc__ or f"Use {tool_name}"

            # Get field information
            fields_info = []
            for field_name, field_info in tool.model_fields.items():
                field_desc = field_info.description or ""
                fields_info.append(f"  - {field_name}: {field_desc}")

            tool_text = f"- **{tool_name}**: {tool_desc}"
            if fields_info:
                tool_text += "\n" + "\n".join(fields_info)
            tool_descriptions.append(tool_text)

        elif hasattr(tool, 'name') and hasattr(tool, 'description'):
            # LangChain tools
            tool_descriptions.append(f"- **{tool.name}**: {tool.description}")

            # Add parameter info if available
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                if 'properties' in schema:
                    for param_name, param_info in schema['properties'].items():
                        param_desc = param_info.get('description', '')
                        tool_descriptions.append(f"  - {param_name}: {param_desc}")

    return "\n".join(tool_descriptions)

def parse_ollama_tool_call(response_text: str) -> tuple[str, dict | None]:
    """Parse Ollama model response for tool calls.

    Expected format:
    ```
    Thought: <reasoning>
    Action: <tool_name>
    Action Input: <json_parameters>
    ```

    Or for completion:
    ```
    Thought: <reasoning>
    Final Answer: <response>
    ```

    Args:
        response_text: The model's response text

    Returns:
        Tuple of (action_type, action_data) where:
        - action_type is "tool_call", "final_answer", or "none"
        - action_data is the parsed tool call data or final answer
    """
    response_text = response_text.strip()

    # Check for Final Answer
    if "Final Answer:" in response_text or "FINAL ANSWER:" in response_text:
        # Extract final answer
        if "Final Answer:" in response_text:
            final_answer = response_text.split("Final Answer:", 1)[1].strip()
        else:
            final_answer = response_text.split("FINAL ANSWER:", 1)[1].strip()
        return ("final_answer", final_answer)

    # Check for Action (tool call)
    if "Action:" in response_text or "ACTION:" in response_text:
        try:
            # Extract action and input
            if "Action:" in response_text:
                action_part = response_text.split("Action:", 1)[1]
            else:
                action_part = response_text.split("ACTION:", 1)[1]

            # Get tool name (first line after Action:)
            lines = action_part.strip().split('\n')
            tool_name = lines[0].strip()

            # Get action input
            action_input = {}
            if "Action Input:" in response_text or "ACTION INPUT:" in response_text:
                if "Action Input:" in response_text:
                    input_part = response_text.split("Action Input:", 1)[1].strip()
                else:
                    input_part = response_text.split("ACTION INPUT:", 1)[1].strip()

                # Try to parse as JSON
                # Look for JSON block
                if '{' in input_part:
                    json_start = input_part.find('{')
                    json_end = input_part.rfind('}') + 1
                    if json_end > json_start:
                        json_str = input_part[json_start:json_end]
                        try:
                            action_input = json.loads(json_str)
                        except json.JSONDecodeError:
                            # If JSON parsing fails, use the raw string
                            action_input = {"input": input_part}
                else:
                    # No JSON, use raw input
                    action_input = {"input": input_part}

            return ("tool_call", {"tool": tool_name, "input": action_input})

        except Exception as e:
            logging.warning(f"Failed to parse tool call from response: {e}")
            return ("none", None)

    # No clear action detected
    return ("none", None)

async def get_ollama_react_response(
    model: BaseChatModel,
    messages: List[MessageLikeRepresentation],
    tools: List[Any],
    system_prompt: str = None
) -> AIMessage:
    """Get a single ReAct-style response from Ollama model.

    This prepares messages with tool descriptions and ReAct formatting instructions,
    then gets one response from the model. The response will be in ReAct format
    that can be parsed for tool calls.

    Args:
        model: The Ollama chat model
        messages: Conversation messages
        tools: List of available tools
        system_prompt: Optional system prompt to prepend

    Returns:
        AIMessage with model's response in ReAct format
    """
    # Format tools for the model
    tools_text = format_tools_for_ollama(tools)

    # Create ReAct instruction
    react_instruction = f"""You are a helpful AI assistant that can use tools to help answer questions.

Available Tools:
{tools_text}

To use a tool, respond in this exact format:
Thought: [Your reasoning about what to do next]
Action: [Tool name from the list above]
Action Input: {{"parameter": "value"}}

When you have enough information to provide a final answer, respond in this format:
Thought: [Your final reasoning]
Final Answer: [Your complete answer]

IMPORTANT:
- Always start with "Thought:" to explain your reasoning
- Use "Action:" with the EXACT tool name from the available tools list
- Use "Action Input:" with valid JSON containing the required parameters
- Use "Final Answer:" only when you're ready to provide the complete final response
- Only call ONE tool per response"""

    # Add system prompt if provided
    if system_prompt:
        react_instruction = system_prompt + "\n\n" + react_instruction

    # Create working message list with ReAct instructions
    working_messages = [SystemMessage(content=react_instruction)] + list(messages)

    # Get model response
    response = await model.ainvoke(working_messages)

    return response

def normalize_tool_parameters(tool_name: str, tool_input: dict) -> dict:
    """Normalize tool parameters to handle common LLM variations in parameter naming.

    This helps make tool calling more robust when LLMs use slightly different
    parameter names than what's expected by the tool schemas.

    Args:
        tool_name: Name of the tool being called
        tool_input: Original parameters from the LLM

    Returns:
        Normalized parameters that match the tool's expected schema
    """
    if not isinstance(tool_input, dict):
        return tool_input

    normalized = tool_input.copy()

    # Normalize think_tool parameters
    if tool_name == "think_tool":
        # Map common variations to 'reflection'
        if 'reflection' not in normalized:
            for alt_key in ['prompt', 'thought', 'thinking', 'question', 'input', 'content']:
                if alt_key in normalized:
                    normalized['reflection'] = normalized.pop(alt_key)
                    break
            # If still no reflection and dict is not empty, use first value
            if 'reflection' not in normalized and normalized:
                first_key = list(normalized.keys())[0]
                normalized['reflection'] = normalized.pop(first_key)
            # If dict is empty, provide a default
            if 'reflection' not in normalized:
                normalized['reflection'] = "Reflecting on progress..."

    # Normalize searxng_search parameters
    elif tool_name == "searxng_search":
        # Convert 'query' (singular) to 'queries' (list)
        if 'queries' not in normalized and 'query' in normalized:
            query_value = normalized.pop('query')
            # Ensure it's a list
            if isinstance(query_value, str):
                normalized['queries'] = [query_value]
            elif isinstance(query_value, list):
                normalized['queries'] = query_value
            else:
                normalized['queries'] = [str(query_value)]
        # Ensure queries is a list if present
        elif 'queries' in normalized and not isinstance(normalized['queries'], list):
            normalized['queries'] = [str(normalized['queries'])]

    return normalized

async def execute_tool(tools: List[Any], tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return its result as a string.

    Args:
        tools: List of available tools
        tool_name: Name of the tool to execute
        tool_input: Parameters for the tool

    Returns:
        String representation of the tool's result
    """
    # Normalize tool input parameters for common variations
    tool_input = normalize_tool_parameters(tool_name, tool_input)

    # Find the tool
    target_tool = None
    for tool in tools:
        if isinstance(tool, dict):
            if tool.get('name') == tool_name or tool.get('type') == tool_name:
                target_tool = tool
                break
        elif isinstance(tool, type) and issubclass(tool, BaseModel):
            if tool.__name__ == tool_name:
                target_tool = tool
                break
        elif hasattr(tool, 'name') and tool.name == tool_name:
            target_tool = tool
            break

    if target_tool is None:
        return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join([str(t.get('name', t.__name__ if hasattr(t, '__name__') else str(t))) for t in tools])}"

    try:
        # Execute based on tool type
        if isinstance(target_tool, dict):
            # Can't execute dict-based tools (they're API-level)
            return f"Tool {tool_name} requires API-level support (not available with Ollama)"

        elif isinstance(target_tool, type) and issubclass(target_tool, BaseModel):
            # Pydantic model tool - return instantiated object
            instance = target_tool(**tool_input)
            return f"Called {tool_name}: {instance.model_dump_json()}"

        elif hasattr(target_tool, 'ainvoke'):
            # Async LangChain tool
            result = await target_tool.ainvoke(tool_input)
            return str(result)

        elif hasattr(target_tool, 'invoke'):
            # Sync LangChain tool
            result = target_tool.invoke(tool_input)
            return str(result)

        elif callable(target_tool):
            # Callable tool
            if asyncio.iscoroutinefunction(target_tool):
                result = await target_tool(**tool_input)
            else:
                result = target_tool(**tool_input)
            return str(result)

        else:
            return f"Error: Don't know how to execute tool {tool_name}"

    except Exception as e:
        logging.error(f"Error executing tool {tool_name}: {e}")
        return f"Error executing {tool_name}: {str(e)}"

##########################
# Reflection Tool Utils
##########################

@tool(description="Strategic reflection tool for research planning")
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"

##########################
# MCP Utils
##########################

async def get_mcp_access_token(
    supabase_token: str,
    base_mcp_url: str,
) -> Optional[Dict[str, Any]]:
    """Exchange Supabase token for MCP access token using OAuth token exchange.
    
    Args:
        supabase_token: Valid Supabase authentication token
        base_mcp_url: Base URL of the MCP server
        
    Returns:
        Token data dictionary if successful, None if failed
    """
    try:
        # Prepare OAuth token exchange request data
        form_data = {
            "client_id": "mcp_default",
            "subject_token": supabase_token,
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "resource": base_mcp_url.rstrip("/") + "/mcp",
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        }
        
        # Execute token exchange request
        async with aiohttp.ClientSession() as session:
            token_url = base_mcp_url.rstrip("/") + "/oauth/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            async with session.post(token_url, headers=headers, data=form_data) as response:
                if response.status == 200:
                    # Successfully obtained token
                    token_data = await response.json()
                    return token_data
                else:
                    # Log error details for debugging
                    response_text = await response.text()
                    logging.error(f"Token exchange failed: {response_text}")
                    
    except Exception as e:
        logging.error(f"Error during token exchange: {e}")
    
    return None

async def get_tokens(config: RunnableConfig):
    """Retrieve stored authentication tokens with expiration validation.
    
    Args:
        config: Runtime configuration containing thread and user identifiers
        
    Returns:
        Token dictionary if valid and not expired, None otherwise
    """
    store = get_store()
    
    # Extract required identifiers from config
    thread_id = config.get("configurable", {}).get("thread_id")
    if not thread_id:
        return None
        
    user_id = config.get("metadata", {}).get("owner")
    if not user_id:
        return None
    
    # Retrieve stored tokens
    tokens = await store.aget((user_id, "tokens"), "data")
    if not tokens:
        return None
    
    # Check token expiration
    expires_in = tokens.value.get("expires_in")  # seconds until expiration
    created_at = tokens.created_at  # datetime of token creation
    current_time = datetime.now(timezone.utc)
    expiration_time = created_at + timedelta(seconds=expires_in)
    
    if current_time > expiration_time:
        # Token expired, clean up and return None
        await store.adelete((user_id, "tokens"), "data")
        return None

    return tokens.value

async def set_tokens(config: RunnableConfig, tokens: dict[str, Any]):
    """Store authentication tokens in the configuration store.
    
    Args:
        config: Runtime configuration containing thread and user identifiers
        tokens: Token dictionary to store
    """
    store = get_store()
    
    # Extract required identifiers from config
    thread_id = config.get("configurable", {}).get("thread_id")
    if not thread_id:
        return
        
    user_id = config.get("metadata", {}).get("owner")
    if not user_id:
        return
    
    # Store the tokens
    await store.aput((user_id, "tokens"), "data", tokens)

async def fetch_tokens(config: RunnableConfig) -> dict[str, Any]:
    """Fetch and refresh MCP tokens, obtaining new ones if needed.
    
    Args:
        config: Runtime configuration with authentication details
        
    Returns:
        Valid token dictionary, or None if unable to obtain tokens
    """
    # Try to get existing valid tokens first
    current_tokens = await get_tokens(config)
    if current_tokens:
        return current_tokens
    
    # Extract Supabase token for new token exchange
    supabase_token = config.get("configurable", {}).get("x-supabase-access-token")
    if not supabase_token:
        return None
    
    # Extract MCP configuration
    mcp_config = config.get("configurable", {}).get("mcp_config")
    if not mcp_config or not mcp_config.get("url"):
        return None
    
    # Exchange Supabase token for MCP tokens
    mcp_tokens = await get_mcp_access_token(supabase_token, mcp_config.get("url"))
    if not mcp_tokens:
        return None

    # Store the new tokens and return them
    await set_tokens(config, mcp_tokens)
    return mcp_tokens

def wrap_mcp_authenticate_tool(tool: StructuredTool) -> StructuredTool:
    """Wrap MCP tool with comprehensive authentication and error handling.
    
    Args:
        tool: The MCP structured tool to wrap
        
    Returns:
        Enhanced tool with authentication error handling
    """
    original_coroutine = tool.coroutine
    
    async def authentication_wrapper(**kwargs):
        """Enhanced coroutine with MCP error handling and user-friendly messages."""
        
        def _find_mcp_error_in_exception_chain(exc: BaseException) -> McpError | None:
            """Recursively search for MCP errors in exception chains."""
            if isinstance(exc, McpError):
                return exc
            
            # Handle ExceptionGroup (Python 3.11+) by checking attributes
            if hasattr(exc, 'exceptions'):
                for sub_exception in exc.exceptions:
                    if found_error := _find_mcp_error_in_exception_chain(sub_exception):
                        return found_error
            return None
        
        try:
            # Execute the original tool functionality
            return await original_coroutine(**kwargs)
            
        except BaseException as original_error:
            # Search for MCP-specific errors in the exception chain
            mcp_error = _find_mcp_error_in_exception_chain(original_error)
            if not mcp_error:
                # Not an MCP error, re-raise the original exception
                raise original_error
            
            # Handle MCP-specific error cases
            error_details = mcp_error.error
            error_code = getattr(error_details, "code", None)
            error_data = getattr(error_details, "data", None) or {}
            
            # Check for authentication/interaction required error
            if error_code == -32003:  # Interaction required error code
                message_payload = error_data.get("message", {})
                error_message = "Required interaction"
                
                # Extract user-friendly message if available
                if isinstance(message_payload, dict):
                    error_message = message_payload.get("text") or error_message
                
                # Append URL if provided for user reference
                if url := error_data.get("url"):
                    error_message = f"{error_message} {url}"
                
                raise ToolException(error_message) from original_error
            
            # For other MCP errors, re-raise the original
            raise original_error
    
    # Replace the tool's coroutine with our enhanced version
    tool.coroutine = authentication_wrapper
    return tool

async def load_mcp_tools(
    config: RunnableConfig,
    existing_tool_names: set[str],
) -> list[BaseTool]:
    """Load and configure MCP (Model Context Protocol) tools with authentication.
    
    Args:
        config: Runtime configuration containing MCP server details
        existing_tool_names: Set of tool names already in use to avoid conflicts
        
    Returns:
        List of configured MCP tools ready for use
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Step 1: Handle authentication if required
    if configurable.mcp_config and configurable.mcp_config.auth_required:
        mcp_tokens = await fetch_tokens(config)
    else:
        mcp_tokens = None
    
    # Step 2: Validate configuration requirements
    config_valid = (
        configurable.mcp_config and 
        configurable.mcp_config.url and 
        configurable.mcp_config.tools and 
        (mcp_tokens or not configurable.mcp_config.auth_required)
    )
    
    if not config_valid:
        return []
    
    # Step 3: Set up MCP server connection
    server_url = configurable.mcp_config.url.rstrip("/") + "/mcp"
    
    # Configure authentication headers if tokens are available
    auth_headers = None
    if mcp_tokens:
        auth_headers = {"Authorization": f"Bearer {mcp_tokens['access_token']}"}
    
    mcp_server_config = {
        "server_1": {
            "url": server_url,
            "headers": auth_headers,
            "transport": "streamable_http"
        }
    }
    # TODO: When Multi-MCP Server support is merged in OAP, update this code
    
    # Step 4: Load tools from MCP server
    try:
        client = MultiServerMCPClient(mcp_server_config)
        available_mcp_tools = await client.get_tools()
    except Exception:
        # If MCP server connection fails, return empty list
        return []
    
    # Step 5: Filter and configure tools
    configured_tools = []
    for mcp_tool in available_mcp_tools:
        # Skip tools with conflicting names
        if mcp_tool.name in existing_tool_names:
            warnings.warn(
                f"MCP tool '{mcp_tool.name}' conflicts with existing tool name - skipping"
            )
            continue
        
        # Only include tools specified in configuration
        if mcp_tool.name not in set(configurable.mcp_config.tools):
            continue
        
        # Wrap tool with authentication handling and add to list
        enhanced_tool = wrap_mcp_authenticate_tool(mcp_tool)
        configured_tools.append(enhanced_tool)
    
    return configured_tools


##########################
# Tool Utils
##########################

async def get_search_tool(search_api: SearchAPI):
    """Configure and return search tools based on the specified API provider.

    Args:
        search_api: The search API provider to use (Anthropic, OpenAI, Tavily, SearXNG, or None)

    Returns:
        List of configured search tool objects for the specified provider
    """
    if search_api == SearchAPI.ANTHROPIC:
        # Anthropic's native web search with usage limits
        return [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }]

    elif search_api == SearchAPI.OPENAI:
        # OpenAI's web search preview functionality
        return [{"type": "web_search_preview"}]

    elif search_api == SearchAPI.TAVILY:
        # Configure Tavily search tool with metadata
        search_tool = tavily_search
        search_tool.metadata = {
            **(search_tool.metadata or {}),
            "type": "search",
            "name": "web_search"
        }
        return [search_tool]

    elif search_api == SearchAPI.SEARXNG:
        # Configure SearXNG local search tool with metadata
        search_tool = searxng_search
        search_tool.metadata = {
            **(search_tool.metadata or {}),
            "type": "search",
            "name": "web_search"
        }
        return [search_tool]

    elif search_api == SearchAPI.NONE:
        # No search functionality configured
        return []

    # Default fallback for unknown search API types
    return []
    
async def get_all_tools(config: RunnableConfig):
    """Assemble complete toolkit including research, search, and MCP tools.
    
    Args:
        config: Runtime configuration specifying search API and MCP settings
        
    Returns:
        List of all configured and available tools for research operations
    """
    # Start with core research tools
    tools = [tool(ResearchComplete), think_tool]
    
    # Add configured search tools
    configurable = Configuration.from_runnable_config(config)
    search_api = SearchAPI(get_config_value(configurable.search_api))
    search_tools = await get_search_tool(search_api)
    tools.extend(search_tools)
    
    # Track existing tool names to prevent conflicts
    existing_tool_names = {
        tool.name if hasattr(tool, "name") else tool.get("name", "web_search") 
        for tool in tools
    }
    
    # Add MCP tools if configured
    mcp_tools = await load_mcp_tools(config, existing_tool_names)
    tools.extend(mcp_tools)
    
    return tools

def get_notes_from_tool_calls(messages: list[MessageLikeRepresentation]):
    """Extract notes from tool call messages."""
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]

##########################
# Model Provider Native Websearch Utils
##########################

def anthropic_websearch_called(response):
    """Detect if Anthropic's native web search was used in the response.
    
    Args:
        response: The response object from Anthropic's API
        
    Returns:
        True if web search was called, False otherwise
    """
    try:
        # Navigate through the response metadata structure
        usage = response.response_metadata.get("usage")
        if not usage:
            return False
        
        # Check for server-side tool usage information
        server_tool_use = usage.get("server_tool_use")
        if not server_tool_use:
            return False
        
        # Look for web search request count
        web_search_requests = server_tool_use.get("web_search_requests")
        if web_search_requests is None:
            return False
        
        # Return True if any web search requests were made
        return web_search_requests > 0
        
    except (AttributeError, TypeError):
        # Handle cases where response structure is unexpected
        return False

def openai_websearch_called(response):
    """Detect if OpenAI's web search functionality was used in the response.
    
    Args:
        response: The response object from OpenAI's API
        
    Returns:
        True if web search was called, False otherwise
    """
    # Check for tool outputs in the response metadata
    tool_outputs = response.additional_kwargs.get("tool_outputs")
    if not tool_outputs:
        return False
    
    # Look for web search calls in the tool outputs
    for tool_output in tool_outputs:
        if tool_output.get("type") == "web_search_call":
            return True
    
    return False


##########################
# Token Limit Exceeded Utils
##########################

def is_token_limit_exceeded(exception: Exception, model_name: str = None) -> bool:
    """Determine if an exception indicates a token/context limit was exceeded.
    
    Args:
        exception: The exception to analyze
        model_name: Optional model name to optimize provider detection
        
    Returns:
        True if the exception indicates a token limit was exceeded, False otherwise
    """
    error_str = str(exception).lower()
    
    # Step 1: Determine provider from model name if available
    provider = None
    if model_name:
        model_str = str(model_name).lower()
        if model_str.startswith('openai:'):
            provider = 'openai'
        elif model_str.startswith('anthropic:'):
            provider = 'anthropic'
        elif model_str.startswith('gemini:') or model_str.startswith('google:'):
            provider = 'gemini'
    
    # Step 2: Check provider-specific token limit patterns
    if provider == 'openai':
        return _check_openai_token_limit(exception, error_str)
    elif provider == 'anthropic':
        return _check_anthropic_token_limit(exception, error_str)
    elif provider == 'gemini':
        return _check_gemini_token_limit(exception, error_str)
    
    # Step 3: If provider unknown, check all providers
    return (
        _check_openai_token_limit(exception, error_str) or
        _check_anthropic_token_limit(exception, error_str) or
        _check_gemini_token_limit(exception, error_str)
    )

def _check_openai_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates OpenAI token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is an OpenAI exception
    is_openai_exception = (
        'openai' in exception_type.lower() or 
        'openai' in module_name.lower()
    )
    
    # Check for typical OpenAI token limit error types
    is_request_error = class_name in ['BadRequestError', 'InvalidRequestError']
    
    if is_openai_exception and is_request_error:
        # Look for token-related keywords in error message
        token_keywords = ['token', 'context', 'length', 'maximum context', 'reduce']
        if any(keyword in error_str for keyword in token_keywords):
            return True
    
    # Check for specific OpenAI error codes
    if hasattr(exception, 'code') and hasattr(exception, 'type'):
        error_code = getattr(exception, 'code', '')
        error_type = getattr(exception, 'type', '')
        
        if (error_code == 'context_length_exceeded' or
            error_type == 'invalid_request_error'):
            return True
    
    return False

def _check_anthropic_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates Anthropic token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is an Anthropic exception
    is_anthropic_exception = (
        'anthropic' in exception_type.lower() or 
        'anthropic' in module_name.lower()
    )
    
    # Check for Anthropic-specific error patterns
    is_bad_request = class_name == 'BadRequestError'
    
    if is_anthropic_exception and is_bad_request:
        # Anthropic uses specific error messages for token limits
        if 'prompt is too long' in error_str:
            return True
    
    return False

def _check_gemini_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates Google/Gemini token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')
    
    # Check if this is a Google/Gemini exception
    is_google_exception = (
        'google' in exception_type.lower() or 
        'google' in module_name.lower()
    )
    
    # Check for Google-specific resource exhaustion errors
    is_resource_exhausted = class_name in [
        'ResourceExhausted', 
        'GoogleGenerativeAIFetchError'
    ]
    
    if is_google_exception and is_resource_exhausted:
        return True
    
    # Check for specific Google API resource exhaustion patterns
    if 'google.api_core.exceptions.resourceexhausted' in exception_type.lower():
        return True
    
    return False

# NOTE: This may be out of date or not applicable to your models. Please update this as needed.
MODEL_TOKEN_LIMITS = {
    "openai:gpt-4.1-mini": 1047576,
    "openai:gpt-4.1-nano": 1047576,
    "openai:gpt-4.1": 1047576,
    "openai:gpt-4o-mini": 128000,
    "openai:gpt-4o": 128000,
    "openai:o4-mini": 200000,
    "openai:o3-mini": 200000,
    "openai:o3": 200000,
    "openai:o3-pro": 200000,
    "openai:o1": 200000,
    "openai:o1-pro": 200000,
    "anthropic:claude-opus-4": 200000,
    "anthropic:claude-sonnet-4": 200000,
    "anthropic:claude-3-7-sonnet": 200000,
    "anthropic:claude-3-5-sonnet": 200000,
    "anthropic:claude-3-5-haiku": 200000,
    "google:gemini-1.5-pro": 2097152,
    "google:gemini-1.5-flash": 1048576,
    "google:gemini-pro": 32768,
    "cohere:command-r-plus": 128000,
    "cohere:command-r": 128000,
    "cohere:command-light": 4096,
    "cohere:command": 4096,
    "mistral:mistral-large": 32768,
    "mistral:mistral-medium": 32768,
    "mistral:mistral-small": 32768,
    "mistral:mistral-7b-instruct": 32768,
    "ollama:codellama": 16384,
    "ollama:llama2:70b": 4096,
    "ollama:llama2:13b": 4096,
    "ollama:llama2": 4096,
    "ollama:mistral": 32768,
    "bedrock:us.amazon.nova-premier-v1:0": 1000000,
    "bedrock:us.amazon.nova-pro-v1:0": 300000,
    "bedrock:us.amazon.nova-lite-v1:0": 300000,
    "bedrock:us.amazon.nova-micro-v1:0": 128000,
    "bedrock:us.anthropic.claude-3-7-sonnet-20250219-v1:0": 200000,
    "bedrock:us.anthropic.claude-sonnet-4-20250514-v1:0": 200000,
    "bedrock:us.anthropic.claude-opus-4-20250514-v1:0": 200000,
    "anthropic.claude-opus-4-1-20250805-v1:0": 200000,
}

def get_model_token_limit(model_string):
    """Look up the token limit for a specific model.
    
    Args:
        model_string: The model identifier string to look up
        
    Returns:
        Token limit as integer if found, None if model not in lookup table
    """
    # Search through known model token limits
    for model_key, token_limit in MODEL_TOKEN_LIMITS.items():
        if model_key in model_string:
            return token_limit
    
    # Model not found in lookup table
    return None

def remove_up_to_last_ai_message(messages: list[MessageLikeRepresentation]) -> list[MessageLikeRepresentation]:
    """Truncate message history by removing up to the last AI message.
    
    This is useful for handling token limit exceeded errors by removing recent context.
    
    Args:
        messages: List of message objects to truncate
        
    Returns:
        Truncated message list up to (but not including) the last AI message
    """
    # Search backwards through messages to find the last AI message
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage):
            # Return everything up to (but not including) the last AI message
            return messages[:i]
    
    # No AI messages found, return original list
    return messages

##########################
# Misc Utils
##########################

def get_today_str() -> str:
    """Get current date formatted for display in prompts and outputs.
    
    Returns:
        Human-readable date string in format like 'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"

def get_config_value(value):
    """Extract value from configuration, handling enums and None values."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return value
    else:
        return value.value

def get_api_key_for_model(model_name: str, config: RunnableConfig):
    """Get API key for a specific model from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    model_name = model_name.lower()
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        if model_name.startswith("openai:"):
            return api_keys.get("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return api_keys.get("ANTHROPIC_API_KEY")
        elif model_name.startswith("google"):
            return api_keys.get("GOOGLE_API_KEY")
        return None
    else:
        if model_name.startswith("openai:"): 
            return os.getenv("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return os.getenv("ANTHROPIC_API_KEY")
        elif model_name.startswith("google"):
            return os.getenv("GOOGLE_API_KEY")
        return None

def get_tavily_api_key(config: RunnableConfig):
    """Get Tavily API key from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        return api_keys.get("TAVILY_API_KEY")
    else:
        return os.getenv("TAVILY_API_KEY")
