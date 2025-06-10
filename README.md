# Computer-Use-Agent

This project implements an AI agent capable of understanding user tasks and controlling a computer's mouse and keyboard to accomplish them. It uses LangGraph to orchestrate a series of steps involving planning, acting, and replanning based on screen analysis and [`Microsoft OmniParser`](https://github.com/microsoft/OmniParser) to analyse the screen content.

## Overview

The Computer-Use-Agent takes a high-level task from the user (e.g., "search for github.com/nabhpatodi10 on edge browser"). It then:
1.  Analyzes the current screen.
2.  Formulates a step-by-step plan.
3.  Executes the plan using simulated mouse and keyboard actions.
4.  Observes the screen changes after each action.
5.  Replans if necessary, until the task is completed.

## Features

*   **Task Planning**: Generates a sequence of actions to achieve a given task.
*   **Screen Analysis**: Uses [`Microsoft OmniParser`](https://github.com/microsoft/OmniParser) to understand the content of the screen, including identifying icons and text.
*   **Mouse Control**: Simulates mouse clicks (left, right, middle), double-clicks, drags, and scrolls using the [`Mouse`](./windows.py) class. Mouse movements are performed as part of these actions.
*   **Keyboard Control**: Simulates key presses, key combinations, and typing strings using the [`Keyboard`](./windows.py) class.
*   **Replanning**: Adapts the plan based on the outcome of actions and changes in the screen state.
*   **LangGraph Integration**: Uses a stateful graph to manage the flow of planning, execution, and replanning.

## Project Structure

*   **`main.py`**: The entry point for running the agent. Initializes a styled Tkinter GUI (borderless, dark-themed, specific fonts, and positioned on screen) for task input and log display, initializes the graph, and invokes it with a task.
*   **`graph.py`**: Defines the main LangGraph structure ([`Graph`](./graph.py)). It orchestrates the planning (`__plan`), agent execution (`__agent`), and replanning (`__replan`) nodes. It defaults to using the `gpt-4.1-mini` model for planning and replanning.
*   **`agent.py`**: Contains the [`Agent`](./agent.py) class, which is a LangGraph sub-graph responsible for executing actions based on the current plan and screen state. It interacts with an LLM (defaulting to `o4-mini`) to decide which tool to use.
*   **`nodes.py`**: Implements the [`Nodes`](./nodes.py) class, which provides the logic and prompts for different nodes in the main graph, such as `plan_node`, `agent_message`, and `replan_node`.
*   **`windows.py`**: Contains the [`Screen`](./windows.py), [`Mouse`](./windows.py), and [`Keyboard`](./windows.py) classes for interacting with the Windows operating system (screen capture, cursor position, mouse/keyboard events). The `Mouse` class uses `gpt-4.1-mini` for object identification on the screen.
*   **`omniparser.py`**: Implements the [`OmniParser`](./omniparser.py) class, which uses computer vision models (YOLO, Florence2) and OCR to parse the screen image and identify interactive elements.
*   **`structures.py`**: Defines Pydantic models like [`Step`](./structures.py), [`Plan`](./structures.py), [`Replan`](./structures.py), and [`ObjectName`](./structures.py) for structured data exchange.
*   **`.env.example`**: Example file for environment variables. Copy this to `.env` and fill in your API keys.
*   **`requirements.txt`**: Lists the Python dependencies for the project.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nabhpatodi10/Computer-Use-Agent.git
    cd Computer-Use-Agent
    ```
2.  **Clone and Set up OmniParser Repository in the Root Folder**
    ```bash
    git clone https://github.com/microsoft/OmniParser # follow the remaining steps from the OmniParser Repository
    ```
    Ensure that any necessary model weights for OmniParser (e.g., for YOLO, Florence2) are downloaded and placed in their expected locations (e.g., `weights/icon_detect/model.pt`, `weights/icon_caption_florence`) as per OmniParser's setup instructions.
3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set up environment variables:**
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Open `.env` and add your API keys. You will need an `OPENAI_API_KEY` for the OpenAI models.
        ```bash
        # .env
        OPENAI_API_KEY=your_openai_api_key_here
        ```

## How It Works

The agent operates based on a stateful graph defined in [`graph.py`](./graph.py):

1.  **Initialization**: The [`main.py`](./main.py) script initializes the GUI, defines a task (taken from GUI input), and invokes the main graph ([`Graph.graph`](./graph.py)).
2.  **Planning (`plan_node`)**:
    *   Takes the user's task and a current screenshot of the screen.
    *   Uses an LLM (default `gpt-4.1-mini` via [`Nodes.plan_node`](./nodes.py)) to generate a [`Plan`](./structures.py) consisting of simple, actionable steps.
3.  **Agent Execution (`agent` node)**:
    *   This node internally runs another graph defined in [`agent.py`](./agent.py).
    *   The [`Agent`](./agent.py) receives the current plan and a screenshot.
    *   It uses an LLM (default `o4-mini`, configured with tools from [`Mouse`](./windows.py) and [`Keyboard`](./windows.py)) to decide the next action based on the plan and screen.
    *   Mouse action methods like `click`, `drag`, and `double_click` use `Mouse.__analyse_position` (which in turn calls `OmniParser.parse_image` and uses `gpt-4.1-mini`) to identify the coordinates of target objects on the screen.
    *   After each tool execution, a new screenshot is taken and provided back to the LLM for the next decision within the agent's loop.
4.  **Replanning (`replan_node`)**:
    *   After the agent node completes its current set of actions (or if it decides the current plan segment is done), the `replan_node` is invoked.
    *   It takes the original task, the current plan, the latest screenshot, and the last message from the agent's LLM.
    *   Uses an LLM (default `gpt-4.1-mini` via [`Nodes.replan_node`](./nodes.py)) to determine if the overall task is complete by outputting a [`Replan`](./structures.py) object containing a boolean flag.
    *   If the task is not complete, this flag (being `False`) signals that the process should continue, leading to a new planning phase.
5.  **Loop or End**:
    *   If the `replan_node` determines the task is not yet complete (i.e., the `Replan` object's flag is `False`), the flow returns to the `plan_node`. The `plan_node` then generates a new plan based on the current screen and task status. This new plan is subsequently passed to the `agent` node for execution.
    *   If the `replan_node` determines the task is complete (i.e., the `Replan` object's flag is `True`), the graph execution ends.

Screenshots are captured using `PIL.ImageGrab` and saved temporarily as `screenshot.jpeg`. This image is then base64 encoded to be passed to multimodal LLMs.

## Running the Project

1.  Ensure all setup steps are completed (virtual environment, dependencies, API keys, model weights).
2.  Run the `main.py` script:
    ```bash
    python main.py
    ```
3.  A small GUI window will appear. Enter your desired task in the input field (e.g., "open notepad and type 'hello world'") and click "Run".
    The agent will start processing the task, and you will see logs in the GUI's text area, indicating its progress, including plans, actions, and LLM messages.

## Key Components & Technologies

*   **LangGraph**: Used to create robust, stateful agentic applications.
*   **LangChain**: Leveraged for LLM interactions, tool definitions, and structured output parsing.
*   **OpenAI Models**: Utilizes `gpt-4.1-mini` (for planning, replanning, and screen object analysis via the `Mouse` class) and `o4-mini` (for agent tool selection and execution).
*   **[`Microsoft OmniParser`](https://github.com/microsoft/OmniParser)**: A Vision Based Model by Microsoft which converts on-screen data to LLM ready data.
*   **Pillow (PIL)**: For capturing screenshots.
*   **Pydantic**: For data validation and defining structured data models ([`structures.py`](./structures.py)).
*   **Windows API**: Interacted with via `win32api`, `win32gui`, `win32con` (likely through `pywin32` library) for direct mouse and keyboard control in [`windows.py`](./windows.py).
*   **Tkinter**: Used for the graphical user interface in `main.py`.

## Troubleshooting

*   **RateLimitError**: The agent makes multiple calls to LLMs. If you encounter rate limit errors, you might need to add delays or check your API plan limits. The code has some basic `time.sleep(20)` handlers for this.
*   **Tool Errors**: Ensure that the tools (mouse/keyboard actions) are behaving as expected. Debugging might involve checking the coordinates identified by `OmniParser` or the arguments passed to `win32api` functions.
*   **Model Performance**: The effectiveness of the agent heavily depends on the LLM's ability to plan and use tools correctly, and on `OmniParser`'s accuracy.
*   **Permissions**: The agent interacts directly with the OS. Ensure it has the necessary permissions if running in restricted environments.
*   **OmniParser Setup**: If `OmniParser` fails, ensure it was cloned correctly into the project root and all its setup steps, including model weight downloads, were completed.