# Computer-Use-Agent

This project implements an AI agent capable of understanding user tasks and controlling a computer's mouse and keyboard to accomplish them. It uses LangGraph to orchestrate a series of steps involving planning, acting, and replanning based on screen analysis.

## Overview

The Computer-Use-Agent takes a high-level task from the user (e.g., "search for github.com/nabhpatodi10 on edge browser"). It then:
1.  Analyzes the current screen.
2.  Formulates a step-by-step plan.
3.  Executes the plan using simulated mouse and keyboard actions.
4.  Observes the screen changes after each action.
5.  Replans if necessary, until the task is completed.

## Features

*   **Task Planning**: Generates a sequence of actions to achieve a given task.
*   **Screen Analysis**: Uses advanced vision models to understand the content of the screen.
*   **Mouse Control**: Simulates mouse clicks, double-clicks, drags, and scrolls. It uses one of two methods for identifying object coordinates on the screen:
    *   **Microsoft GUI-Actor (Default)**: A specialized vision model that directly identifies the coordinates of a described object.
    *   **OmniParser + LLM**: Uses [`Microsoft OmniParser`](https://github.com/microsoft/OmniParser) to parse the screen into labeled elements, and then a separate LLM call to select the correct element.
*   **Keyboard Control**: Simulates key presses, key combinations, and typing strings using the [`Keyboard`](./windows.py) class.
*   **Replanning**: Adapts the plan based on the outcome of actions and changes in the screen state.
*   **LangGraph Integration**: Uses a stateful graph to manage the flow of planning, execution, and replanning.

## Project Structure

*   **`main.py`**: The entry point for running the agent. Initializes a styled Tkinter GUI for task input and log display, initializes the graph, and invokes it with a task.
*   **`graph.py`**: Defines the main LangGraph structure ([`Graph`](./graph.py)). It orchestrates the planning, agent execution, and replanning nodes. It defaults to using the `gpt-4.1-mini` model for planning and replanning.
*   **`agent.py`**: Contains the [`Agent`](./agent.py) class, a LangGraph sub-graph responsible for executing actions based on the current plan and screen state. It interacts with an LLM (defaulting to `o4-mini`) to decide which tool to use.
*   **`nodes.py`**: Implements the [`Nodes`](./nodes.py) class, which provides the logic and prompts for different nodes in the main graph.
*   **`windows.py`**: Contains the [`Screen`](./windows.py), [`Mouse`](./windows.py), and [`Keyboard`](./windows.py) classes for interacting with the Windows OS. The `Mouse` class is configurable to use either `GUI-Actor` (default) or `OmniParser` for identifying object coordinates on the screen.
*   **`guiactor.py`**: Implements the [`GUIActor`](./guiactor.py) class, a wrapper for the `microsoft/GUI-Actor-3B-Qwen2.5-VL` model, which can find the coordinates of a specific UI element on the screen given a text description.
*   **`omniparser.py`**: Implements the [`OmniParser`](./omniparser.py) class, which provides one of the methods for screen analysis. It uses computer vision models (YOLO, Florence2) and OCR to parse the screen image and identify all interactive elements.
*   **`structures.py`**: Defines Pydantic models like [`Step`](./structures.py), [`Plan`](./structures.py), and [`Replan`](./structures.py) for structured data exchange.
*   **`.env.example`**: Example file for environment variables. Copy this to `.env` and fill in your API keys.
*   **`requirements.txt`**: Lists the Python dependencies for the project.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nabhpatodi10/Computer-Use-Agent.git
    cd Computer-Use-Agent
    ```
2.  **Set up for Screen Parsing (Choose one or both):**
    *   **GUI-Actor (Default)**: Download and setup the repository, the model weights will be downloaded on first run.
        ```bash
        git clone https://github.com/microsoft/GUI-Actor.git # follow the remaining steps from the GUI-Actor Repository
        ```
        You would only need the gui_actor folder in the root directory
    *   **OmniParser (Optional)**: If you want to use OmniParser, you need to set it up.
        ```bash
        git clone https://github.com/microsoft/OmniParser.git # follow the remaining steps from the OmniParser Repository
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
    The dependencies include libraries like `transformers`, `torch`, and `accelerate`. If you have a compatible GPU, you might want to install `flash-attn` for better performance with `GUI-Actor`: `pip install flash-attn --no-build-isolation`. The first time you run the agent with the default settings, it will download the `microsoft/GUI-Actor-3B-Qwen2.5-VL` model (approx. 3B parameters), which may take some time and requires significant disk space.

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

1.  **Initialization**: The [`main.py`](./main.py) script initializes the GUI, defines a task, and invokes the main graph.
2.  **Planning (`plan_node`)**:
    *   Takes the user's task and a current screenshot.
    *   Uses an LLM (`gpt-4.1-mini`) to generate a [`Plan`](./structures.py) of simple, actionable steps.
3.  **Agent Execution (`agent` node)**:
    *   This node runs a sub-graph defined in [`agent.py`](./agent.py).
    *   It uses an LLM (`o4-mini`) with tools from [`Mouse`](./windows.py) and [`Keyboard`](./windows.py) to decide the next action.
    *   Mouse actions like `click` and `drag` require coordinates for the target object. The [`Mouse`](./windows.py) class (defaulting to `GUI-Actor`) obtains these coordinates:
        *   **`GUI-Actor`**: The `__give_coordinates` method passes the screenshot and object description directly to the `GUI-Actor` model, which returns the precise coordinates.
        *   **`OmniParser`**: The `__analyse_position` method first uses `OmniParser` to get a list of all labeled elements on the screen, and then makes a call to `gpt-4.1-mini` to select the best match for the target object from that list.
    *   After each tool execution, a new screenshot is taken and fed back to the LLM for the next decision.
4.  **Replanning (`replan_node`)**:
    *   After the agent node completes, the `replan_node` is invoked.
    *   It uses `gpt-4.1-mini` to determine if the overall task is complete based on the latest screen.
5.  **Loop or End**:
    *   If the task is not complete, the flow returns to the `plan_node` to generate a new plan from the current state.
    *   If the task is complete, the graph execution ends.

To switch between `GUI-Actor` and `OmniParser`, you can modify the `__init__` method of the `Mouse` class in [`windows.py`](./windows.py).

## Running the Project

1.  Ensure all setup steps are completed.
2.  Run the `main.py` script:
    ```bash
    python main.py
    ```
3.  A small GUI window will appear. Enter your task and click "Run". The agent will start processing, with logs appearing in the GUI.

## Key Components & Technologies

*   **LangGraph**: Used to create robust, stateful agentic applications.
*   **LangChain**: Leveraged for LLM interactions, tool definitions, and structured output parsing.
*   **OpenAI Models**: Utilizes `gpt-4.1-mini` (for planning, replanning, and optionally for screen object analysis if using the `OmniParser` method) and `o4-mini` (for agent tool selection and execution).
*   **Microsoft GUI-Actor**: A specialized 3B parameter vision-language model (`Qwen2.5-VL` base) for identifying UI elements on a screen.
*   **[`Microsoft OmniParser`](https://github.com/microsoft/OmniParser)**: An alternative, vision-based screen parser that converts on-screen data into a structured list of elements.
*   **Pillow (PIL)**: For capturing screenshots.
*   **Pydantic**: For data validation and defining structured data models.
*   **Windows API**: Interacted with via `pywin32` for direct mouse and keyboard control.
*   **Tkinter**: Used for the graphical user interface.

## Troubleshooting

*   **RateLimitError**: The agent makes multiple calls to LLMs. If you encounter rate limit errors, you might need to add delays or check your API plan limits.
*   **GUI-Actor Model**: The `GUI-Actor` model is large and requires significant VRAM (approx. 8GB) and RAM (approx. 26GB for CPU). Ensure you have sufficient resources. The first run will download the model weights. If you encounter performance issues, check your `torch` and CUDA setup. Installing `flash-attn` is recommended for GPU users.
*   **OmniParser Setup**: If you choose to use the `OmniParser` backend, ensure it was cloned correctly into the project root and all its setup steps, including model weight downloads, were completed.
*   **Permissions**: The agent interacts directly with the OS. Ensure it has the