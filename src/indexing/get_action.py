import base64
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from pydantic import BaseModel, Field

load_dotenv()


PROMPT = """
You are a professional software UX analyst trained to understand the structure and purpose of application interfaces.

You are give the description of two continues script from desktop application and your task is to return the action (or multiple actions) that causes a transition from one state to another.
Take in the account that multiple action can lead to the same transition, list them all.
Skip very user-specific action (like data that only related to this user)

### App Description:
CleanMyMac X is a powerful macOS utility developed by MacPaw that combines system cleaning, performance optimization, malware protection, and application management into one sleek and user-friendly tool. It’s designed to help users free up disk space, boost Mac performance, and keep the system secure and organized.
At the heart of the app is the Smart Scan feature, which performs a quick yet thorough checkup of your Mac—cleaning system junk, detecting malware, and optimizing performance. Additional modules allow for more targeted actions, like uninstalling apps without leftovers, clearing old downloads and large files, and securely deleting sensitive data.
CleanMyMac X also protects your privacy and security by detecting macOS-specific threats such as spyware and adware, and erasing traces of online activity. Its built-in health monitor keeps an eye on CPU load, RAM usage, battery condition, and storage availability, helping your Mac run efficiently over time.
Trusted by over 29 million users and endorsed by Apple, CleanMyMac X stands out with its award-winning design, robust feature set, and consistently updated malware detection engine—making it the go-to solution for keeping any Mac clean, safe, and fast.

### State 1:
{state_1}

### State 2:
{state_2}

### Output:
"""
MODEL = "openai:gpt-4o"


class StateTransition(BaseModel):
    """
    Represents a directed user interaction that causes a transition
    from one AppView state to another within a navigation graph.

    This model defines the core semantics of a UI-triggered action, such as
    a click, shortcut, or interaction, which changes the state of the app.
    """

    action: str = Field(
        ...,
        description="Canonical system-friendly name of the action, "
        "used to uniquely identify the interaction (e.g., 'start_scan', 'click_convert').",
    )

    description: str = Field(
        ...,
        description="Human-readable explanation of what this action does, "
        "for use in UIs, LLM responses, or documentation (e.g., 'Start full system scanning').",
    )

    trigger_type: str = Field(
        ..., description="The method by which the action is triggered. " "Examples include 'left_click', 'keyboard', 'swipe', 'drag_drop'."
    )


class StateTransitionList(BaseModel):
    state_transitions: List[StateTransition] = Field(..., description="List of state transitions that can be triggered by user actions.")


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_str = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"


def read_state(state_path: str) -> str:
    with open(state_path, "r") as f:
        return json.load(f)


def get_action(state_1_path: str, state_2_path: str) -> StateTransitionList:
    state_1 = read_state(state_1_path)
    state_2 = read_state(state_2_path)

    system_message = SystemMessagePromptTemplate.from_template(PROMPT)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
        ]
    ).format_messages(state_1=state_1, state_2=state_2)

    chat_model = init_chat_model(MODEL, temperature=0.2).with_structured_output(StateTransitionList)

    result = chat_model.invoke(chat_prompt).model_dump()

    return result


def process_all():
    for route in os.listdir("datasets/routes"):
        for i, step in enumerate(sorted(os.listdir(f"datasets/routes/{route}"))[:-1]):
            state_1_path = f"datasets/routes/{route}/{step}/node_desc.json"
            state_2_path = f"datasets/routes/{route}/{int(step)+1}/node_desc.json"
            result = get_action(state_1_path, state_2_path)
            with open(f"datasets/routes/{route}/{step}/action_desc.json", "w") as f:
                json.dump(result, f, indent=4)
            print(f"Processed {route}/{step}")


process_all()
