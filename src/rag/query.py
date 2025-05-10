import argparse
import logging
import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from pydantic import BaseModel, Field
from rich import print

from src.rag.find_nearest_path import find_nearest_graph_path
from src.rag.find_target_node import get_target_node
from src.rag.utils import get_neo4j_engine

logging.getLogger("neo4j").setLevel(logging.ERROR)

PROMPT = """
You are a professional software UX assistant tasked with helping users understand and navigate a macOS desktop application.
You must use the information provided in the **Graph Path** (which contains a sequence of screens and actions taken by the user) to understand the user journey and respond accurately.

### Instruction
Your response must:
- Be **detailed**, yet **structured**.
- Clearly explain **how to perform the action** they asked about.
- Mention any **important warnings, side effects, or related features**.

### Applicatoin Overview
CleanMyMac X is a powerful macOS utility developed by MacPaw that combines system cleaning, performance optimization, malware protection, and application management into one sleek and user-friendly tool. It’s designed to help users free up disk space, boost Mac performance, and keep the system secure and organized.
At the heart of the app is the Smart Scan feature, which performs a quick yet thorough checkup of your Mac—cleaning system junk, detecting malware, and optimizing performance. Additional modules allow for more targeted actions, like uninstalling apps without leftovers, clearing old downloads and large files, and securely deleting sensitive data.
CleanMyMac X also protects your privacy and security by detecting macOS-specific threats such as spyware and adware, and erasing traces of online activity. Its built-in health monitor keeps an eye on CPU load, RAM usage, battery condition, and storage availability, helping your Mac run efficiently over time.
Trusted by over 29 million users and endorsed by Apple, CleanMyMac X stands out with its award-winning design, robust feature set, and consistently updated malware detection engine—making it the go-to solution for keeping any Mac clean, safe, and fast.

### User Query
{user_input}

### Graph Path
{graph_path}

### Answer
"""
CORRECT_PROMPT = """
Your goal is to define the user intent and validate if the user query is related to the application navigation.
Mostly query is should be about using computer or some application on the computer. Reject only directly unrelated queries.

### User Query
{user_input}

### Answer
"""
MODEL = "openai:gpt-4o"


class LLMResponse(BaseModel):
    """
    Structured response from the LLM for user queries about application navigation.

    This model captures both the reasoning process and the final answer to provide
    transparent, explainable AI responses for desktop application navigation assistance.
    """

    reasoning: str = Field(
        description="Step-by-step reasoning process explaining how the answer was derived from the graph path data. "
        "Should include analysis of the current state, available actions, and justification for the recommended path."
    )
    answer: str = Field(
        description="Clear, concise answer to the user query that explains how to accomplish the requested task. "
        "Should include specific UI elements to interact with and the sequence of actions needed."
    )


class InputCorrectness(BaseModel):
    """
    Validate user input to be related to the application navigation on the computer.
    """

    is_correct: bool = Field(description="Boolean value indicating whether the user query is on valid topic.")


def is_query_correct(user_input: str) -> bool:
    system_message = SystemMessagePromptTemplate.from_template(CORRECT_PROMPT)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
        ]
    ).format_messages(user_input=user_input)

    chat_model = init_chat_model(MODEL, temperature=0.2).with_structured_output(InputCorrectness)
    result = chat_model.invoke(chat_prompt)
    return result.is_correct


def get_llm_response(user_input: str, graph_path: str) -> LLMResponse:
    system_message = SystemMessagePromptTemplate.from_template(PROMPT)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
        ]
    ).format_messages(user_input=user_input, graph_path=graph_path)
    # for message in chat_prompt:
    #     print(message.content)

    chat_model = init_chat_model(MODEL, temperature=0.2).with_structured_output(LLMResponse)

    result = chat_model.invoke(chat_prompt)

    return result


def query(user_input: str) -> str:
    load_dotenv()
    driver = get_neo4j_engine()

    if not is_query_correct(user_input):
        return "Sorry, but i cannot answer this question."

    target_state = get_target_node(user_input)
    graph_path = find_nearest_graph_path(driver, target_state)
    response = get_llm_response(user_input, graph_path)
    # print(response.answer)

    return response.answer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the application graph for information.")
    parser.add_argument("user_input", type=str, help="User query")
    args = parser.parse_args()

    response = query(args.user_input)

    sys.exit(response)
