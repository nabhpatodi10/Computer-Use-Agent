# Computer-Use-Agent

This project implements an AI agent that understands natural-language tasks and controls a Windows computer’s mouse and keyboard to accomplish them. It uses a compact LangGraph state machine to iteratively plan tool calls, execute them, observe the screen, and repeat until the model stops calling tools.

## Overview

Given a high-level task (e.g., “search for github.com/nabhpatodi10 in Edge”), the agent:
1. Analyzes the current screen (initial screenshot).
2. Decides one or more tool calls (mouse/keyboard actions) to perform next.
3. Executes those actions.
4. Takes a new screenshot and feeds it back to the model.
5. Repeats until the model returns no further tool calls.

The iteration loop is implemented as a two-node LangGraph Agent in `agent.py`:
- llm: decide tools
- action: execute tools and attach a fresh screenshot

The loop ends when the LLM returns no tool calls.

## Features

- Task execution loop:
  - Iterative perception-action loop with screenshots after each batch of actions.
- Screen analysis backends:
  - Microsoft GUI-Actor (default): A VLM that points to UI elements and returns normalized coordinates.
  - OmniParser + LLM (optional): Parse screen into labeled elements and select the best match via an LLM.
- Mouse control:
  - Click (left/right/middle), double-click, drag, and scroll (vertical/horizontal).
  - Targets are specified by object name/description; coordinates are resolved by GUI-Actor or OmniParser+LLM.
- Keyboard control:
  - Press single key, press key combinations, and type arbitrary strings.
- Tkinter GUI:
  - Minimal always-on-top window for entering the task and viewing logs.

## Project Structure

- `main.py`: Entry point. Creates a small Tkinter GUI, builds toolset, takes the initial screenshot, and invokes the agent loop.
- `agent.py`: Defines the `Agent` class and a two-node LangGraph (llm → action → llm). Uses:
  - ChatOpenAI model: `gpt-5` for tool selection.
  - Simple rate limit retry (20s backoff) on `RateLimitError`.
- `nodes.py`: Prompt builders:
  - `agent_message(...)`: System + human messages with the initial screenshot and task.
  - `mouse_functions(...)`: Prompt for OmniParser element selection via LLM with structured output.
- `windows.py`: Windows-specific control layer:
  - `Screen`: Screen size, cursor position, and window rect helpers.
  - `Mouse`: Backend switch between `"gui_actor"` (default) and `"omni"`. Exposes click, drag, scroll, and double_click as tools.
    - GUI-Actor flow: send screenshot + object description to GUI-Actor to get coordinates.
    - OmniParser flow: parse items, then use `gpt-5-mini` to pick the best element name from the parsed list.
  - `Keyboard`: Exposes press_key, key_combination, and type_string as tools.
- `guiactor.py`: Wrapper around `microsoft/GUI-Actor-7B-Qwen2.5-VL` with FlashAttention 2. Returns normalized (x, y) ∈ [0,1].
- `omniparser.py`: OmniParser integration (clone from Microsoft repo; ensure weights as per their docs).
- `requirements.txt`: Python dependencies.
- `.env.example`: Copy to `.env` and set `OPENAI_API_KEY`.

Note:
- There is no separate `graph.py` planning/replanning file. Planning happens implicitly inside the `Agent` loop.
- Models referenced in-code are `gpt-5` and `gpt-5-mini` (not `gpt-4.1-mini`/`o4-mini`).

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nabhpatodi10/Computer-Use-Agent.git
   cd Computer-Use-Agent
   ```

2. Choose a screen parsing backend (one or both):
   - GUI-Actor (default; requires NVIDIA GPU):
     ```bash
     git clone https://github.com/microsoft/GUI-Actor.git
     ```
     - You only need the `gui_actor` folder placed in the project root so imports like `from gui_actor...` work.
     - Weights will be downloaded on first run.
     - The code loads `microsoft/GUI-Actor-7B-Qwen2.5-VL` with `attn_implementation="flash_attention_2"` and `device_map={"": 0}` (CUDA device 0). A CUDA-capable GPU is required. FlashAttention 2 is recommended:
       ```bash
       pip install flash-attn --no-build-isolation
       ```
   - OmniParser (optional):
     ```bash
     git clone https://github.com/microsoft/OmniParser.git
     ```
     - Follow OmniParser’s setup, including downloading weights (e.g., YOLO, Florence2) and placing them where OmniParser expects (e.g., `weights/icon_detect/model.pt`, `weights/icon_caption_florence`).

3. Create a virtual environment (Windows):
   ```bat
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   - If using a compatible GPU and the GUI-Actor backend, consider:
     ```bash
     pip install flash-attn --no-build-isolation
     ```
   - Ensure you have a CUDA-enabled PyTorch installation when using GUI-Actor.

5. Environment variables:
   - Copy `.env.example` to `.env`:
     ```bat
     copy .env.example .env
     ```
   - Set your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

## Configuration

- Backend switch (GUI-Actor vs OmniParser):
  - Default is GUI-Actor: `Mouse(choice="gui_actor")`.
  - To use OmniParser, you can either:
    - Change the default in `windows.py` (`Mouse.__init__`), or
    - Change the construction in `main.py` to `Mouse(choice="omni")`.

- Models used:
  - Agent loop (tool selection): `gpt-5`
  - OmniParser element selection: `gpt-5-mini`

- Tools exposed to the LLM:
  - Mouse: `click`, `double_click`, `drag`, `scroll` (no standalone `move` tool exposed)
  - Keyboard: `press_key`, `key_combination`, `type_string`

## How It Works

1. Initialization (`main.py`):
   - Builds tool list: Mouse tools + Keyboard tools.
   - Captures an initial screenshot (`screenshot.jpeg`) and encodes it into the first message.
   - Sends the task + screenshot to the `Agent` graph.

2. Agent loop (`agent.py`):
   - llm node:
     - LLM decides which tools to call and with what arguments.
     - If no tool calls are present, the graph ends.
   - action node:
     - Executes all tool calls in order.
     - Takes a new screenshot and attaches it to the final tool result as an image message.
     - Returns to llm for another decision.

3. Completion:
   - When the LLM returns no more tool calls, the loop ends and the final message content is printed in the GUI.

Notes:
- For object targeting, the Mouse backend converts object descriptions into coordinates:
  - GUI-Actor: Vision model returns normalized coordinates directly from the screenshot.
  - OmniParser: Parses all elements, then `gpt-5-mini` picks the best element name; its bbox is converted to screen coordinates.

## Running

1. Ensure setup is complete and your venv is activated.
2. Run:
   ```bash
   python main.py
   ```
3. A small always-on-top GUI appears. Enter your task and click “Run”.
   - The app sends Win + D first to show the Desktop before starting.
   - Progress and outputs stream into the GUI.

## Key Components & Technologies

- LangGraph: Lightweight, stateful loop (llm → action → llm).
- LangChain: Tool binding and message handling.
- OpenAI Models: `gpt-5` (agent loop) and `gpt-5-mini` (OmniParser element choice).
- Microsoft GUI-Actor (7B, Qwen2.5-VL base): UI element localization from screenshots.
- Microsoft OmniParser: Vision-based screen parsing to structured elements.
- Pillow (PIL): Screenshots.
- Pydantic: Structured outputs (`ObjectName` for OmniParser flow).
- Windows API (`pywin32`): Mouse and keyboard control.
- Tkinter: Minimal GUI.

## Troubleshooting

- Rate limits (OpenAI):
  - The agent retries after a 20s delay on `RateLimitError`. If frequent, reduce task frequency or upgrade your plan.

- GUI-Actor issues:
  - Requires a CUDA GPU (device 0). Ensure:
    - PyTorch with CUDA is installed.
    - `flash-attn` is installed for best performance.
    - Sufficient VRAM (8 GB+ recommended).
  - First run downloads large weights; ensure disk space and a stable connection.

- OmniParser setup:
  - Ensure the repository is cloned into the project and all its model weights are downloaded to expected paths.

- Permissions and environment (Windows):
  - The app writes `screenshot.jpeg` to the project root; ensure write permissions (Windows Defender “Controlled folder access” can block this).
  - If input injection fails, try running the IDE/terminal “as Administrator”.

- Multi-monitor setups:
  - Coordinates assume the primary display. Behavior on non-primary monitors may be limited.

## Notes & Limitations

- Windows only (uses `win32api`, `win32con`, `win32gui`).
- The `move` mouse tool exists internally but is not exposed to the agent; targeting happens as part of the click/drag/double-click flows.
- The GUI-Actor loader targets CUDA device 0. Adjust in `guiactor.py` if you need a