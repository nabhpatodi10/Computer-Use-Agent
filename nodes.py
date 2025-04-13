from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage

class Nodes:
    def agent_message(self, screen_size: tuple[int, int]) -> list[SystemMessage]:
        message = [
            SystemMessage(
                content=f"""You are an expert computer user who has to use a computer to perform the given task or a step. Your job is to perform the task using the mouse and keyboard \
                actions. You can use the mouse to perform the following actions: move the mouse, left, right or middle click, double click, verticle and horizontal scroll. You \
                can use the keyboard to perform the followig actions: press a key, type a string, press a key combination. To perform these actions, you have the access to the \
                following tools:
                
                - move(x: int, y: int) - Move the mouse to the given x and y coordinates on the screen
                
                - click(button: Literal["left", "right", "middle"], x: int, y: int) - Click the mouse button at the given x and y coordinates on the screen. The button can be left, right or middle.
                
                - drag(initial_pos: list[int, int], final_pos: list[int, int]) - Drag the mouse from the initial position to the final position.

                - scroll(direction: Literal["vertical", "horizontal"], delta: int) - Scroll the mouse in the given direction. The direction can be vertical or horizontal. To scroll down, the delta should be negative. To scroll up, the delta should be positive.
                
                - double_click(button: Literal["left", "right", "middle"], x: int, y: int) - Double click the mouse button at the given x and y coordinates on the screen. The button can be left, right or middle.
                
                - press_key(key: str) - Press the given key on the keyboard. The key can be any key on the keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc
                
                - key_combination(keys: list[str]) - Press the given key combination on the keyboard. The keys can be any key on the keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc. Each key should be an element of the tuple
                
                - type_string(string: str) - Type the given string on the keyboard. The string can be any string, including letters, numbers, symbols, spaces and newline character (\\n) and tabs (\\t) as well. It should not be the ASCII code or any other code, it should be the string itself.
                
                You will get the initial screenshot of the screen and the task to perform, you have to analyse the screenshot and decide what tools have to be called with what values. \
                You can call these tools sequentially or together as well. Each tool will also return a screenshot of the screen after performing the action. You can use this screenshot \
                to decide what to do next. The size of the scrren of the computer is: {screen_size[0], screen_size[1]}.
                
                Based on the output of the tools after tool calls, respond with what action was performed."""
            )
        ]
        return message
    
    def plan_node(self, user_input: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content="""You are an expert computer user who has to use a computer to perform the given task. Your job is to analyse the given task and develop a detailed plan to \
                perform the task using the mouse and keyboard actions. Each step of the plan should be a single and a very simple action. You can use the mouse to perform the following \
                actions: move the mouse, left, right or middle click, double click, verticle and horizontal scroll. You can use the keyboard to perform the followig actions: \
                press a key, type a string, press a key combination."""
            ),
            HumanMessage(
                content=f"Task: {user_input}"
            )
        ]

        return message
    
    def replan_node(self, user_input: str, plan: str, current_screen: bytes, last_llm_message: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content="""You are an expert computer user who has to analyse the given task, the plan to complete that task and the current screen of the computer. Your job is to \
                analyse the given task and the current screen of the computer and decide if there is a need for replanning. If there is a need for replanning, you have to develop a \
                detailed plan to perform the task using the mouse and keyboard actions. Each step of the plan should be a single and a very simple action. You can use the mouse to \
                perform the following actions: move the mouse, left, right or middle click, double click, verticle and horizontal scroll. You can use the keyboard to perform the \
                followig actions: press a key, type a string, press a key combination. If there is no need for replanning, but the plan has not been completed yet, return true. If the \
                plan has been completed, return false. Replan only if the given plan will not work to complete the task."""
            ),
            HumanMessage(
                content=[{"type" : "text", "text" : f"Task: {user_input}\n\nplan: {plan}, last llm message: {last_llm_message}"},
                {"type" : "image_url",
                "image_url" : {"url" : f"data:image/jpeg;base64,{current_screen}"}}]
            )
        ]

        return message