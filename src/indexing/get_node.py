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

### Instruction:
Your task is to analyze the provided **app screenshot** and **app description**, and return a structured JSON object describing the app state, its purpose, and available user actions.
An *app state* refers to a specific screen or view that the user sees at a point in time. It has a purpose (e.g., login, file conversion), interactive elements (e.g., buttons), and may accomplish a specific goal (e.g., "converted a video").


### App Description:
CleanMyMac X is a powerful macOS utility developed by MacPaw that combines system cleaning, performance optimization, malware protection, and application management into one sleek and user-friendly tool. It’s designed to help users free up disk space, boost Mac performance, and keep the system secure and organized.
At the heart of the app is the Smart Scan feature, which performs a quick yet thorough checkup of your Mac—cleaning system junk, detecting malware, and optimizing performance. Additional modules allow for more targeted actions, like uninstalling apps without leftovers, clearing old downloads and large files, and securely deleting sensitive data.
CleanMyMac X also protects your privacy and security by detecting macOS-specific threats such as spyware and adware, and erasing traces of online activity. Its built-in health monitor keeps an eye on CPU load, RAM usage, battery condition, and storage availability, helping your Mac run efficiently over time.
Trusted by over 29 million users and endorsed by Apple, CleanMyMac X stands out with its award-winning design, robust feature set, and consistently updated malware detection engine—making it the go-to solution for keeping any Mac clean, safe, and fast.

### Output:
"""
MODEL = "openai:gpt-4o"


class EnableOption(BaseModel):
    """
    Represents an action that can be taken from a particular app state/screen.
    Each option defines a possible user interaction that navigates to another state.
    """

    name: str = Field(description="Display name of the user-facing action (e.g., 'Convert Video')")
    description: str = Field(description="Detailed explanation of what the action does or where it leads to")
    action: str = Field(description="Internal/system action identifier used for programmatic references (e.g., 'click_convert_button')")


class AppView(BaseModel):
    """
    Represents a distinct state or screen in an application's UI flow.
    Maps the visual elements, available actions, and semantic context of a single app screen.
    Used for building knowledge graphs of desktop application navigation.
    """

    state_id: int = Field(description="Unique identifier for this app state/screen")
    state_name: str = Field(description="Human-readable name of the screen (e.g., 'Start Screen')")
    state_description: str = Field(description="Purpose and context of this screen within the application flow")
    done: Optional[str] = Field(default=None, description="Task or result that is accomplished upon reaching this state")
    screenshot_path: Optional[str] = Field(default=None, description="Path to a visual reference of this screen, if available")
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Keywords for semantic matching, search, and categorization of this screen"
    )
    enables: List[EnableOption] = Field(description="Available actions that can be taken from this screen, leading to other states")


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_str = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"


def get_node(image_path: str) -> AppView:
    system_message = SystemMessagePromptTemplate.from_template(PROMPT)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
            HumanMessage(
                content=[
                    {"type": "image_url", "image_url": {"url": encode_image_to_base64(image_path)}},
                ]
            ),
        ]
    ).format_messages()

    chat_model = init_chat_model(MODEL, temperature=0.2).with_structured_output(AppView)

    result = chat_model.invoke(chat_prompt)

    return result


def get_node_best_result(image_path: str) -> str:
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(get_node, image_path) for _ in range(3)]
        results = [future.result().model_dump() for future in futures]

        results_str = [json.dumps(r) for r in results]

    longest_idx = max(range(len(results_str)), key=lambda i: len(results_str[i]))

    result = results[longest_idx]

    return result


def process_all():
    for route in os.listdir("datasets/routes"):
        for step in os.listdir(f"datasets/routes/{route}"):
            image_path = f"datasets/routes/{route}/{step}/image.png"
            result = get_node_best_result(image_path)
            with open(f"datasets/routes/{route}/{step}/node_desc.json", "w") as f:
                json.dump(result, f, indent=4)
            print(f"Processed {route}/{step}")


if __name__ == "__main__":
    process_all()
