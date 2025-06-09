from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage

from structures import Plan

class Nodes:
    def agent_message(self, screen_size: tuple[int, int], task: str, plan: Plan, image: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content=f"""You are an expert computer user who has to use a computer to perform the given task. Your job is to follow the given plan using the mouse \
                and keyboard actions. You can use the mouse to perform the following actions: move the mouse, left, right or middle click, double click, verticle and horizontal \
                scroll. You can use the keyboard to perform the followig actions: press a key, type a string, press a key combination. To perform these actions, you have the \
                access to the following tools:
                
                - move(to_object: str) - Move the mouse to the given object or icon on the screen
                
                - click(button: Literal["left", "right", "middle"], to_object: str) - Click the mouse button at the given object or icon on the screen. The button can be left, right or middle.
                
                - drag(from_object: str, to_object: str) - Drag the mouse from the initial object or icon to the final object or icon.

                - scroll(direction: Literal["vertical", "horizontal"], delta: int) - Scroll the mouse in the given direction. The direction can be vertical or horizontal. To scroll down, the delta should be negative. To scroll up, the delta should be positive.
                
                - double_click(button: Literal["left", "right", "middle"], to_object: str) - Double click the mouse button at the given object or icon on the screen. The button can be left, right or middle.
                
                - press_key(key: str) - Press the given key on the keyboard. This tool is only for single keys. The key can be any commonly found key on most keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc
                
                - key_combination(keys: list[str]) - Press the given key combination on the keyboard. The keys can be any commonly found key on most keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc. Each key should be an element of the tuple
                
                - type_string(string: str) - Type the given string on the keyboard. The string can be any string, including letters, numbers, symbols, spaces and newline character (\\n) and tabs (\\t) as well. It should not be the ASCII code or any other code, it should be the string itself.
                
                You will get the initial screenshot of the screen, the task and the plan to follow, you have to analyse the screenshot and decide what tools have to be called with what values. \
                It is preferred that you call one tool at a time and analyse the output of each tool call and then accordingly call the next tool. Each tool will also return a \
                screenshot of the screen after performing the action. You can use this screenshot to decide what to do next. The size of the scrren of the computer is: \
                {screen_size[0], screen_size[1]}.
                
                Decide the next action or tool call based on the current screen. The final goal is to complete the task given to you. If you have to perform additional or intermediate \
                steps other than those mentioned in the plan to complete the task, you can do that as well. Perform the next action or tool call only after properly analysing the current \
                screen. Prefer to use keyboard actions over mouse actions, use mouse when absolutely necessary."""
            ),
            HumanMessage(
                content=[
                    {"type" : "text", "text" : f"The task given by the user is: {task}\n\nThe plan to complete this task is:\n{plan.as_str}\n\nAlso, the following is the screenshot of the screen:\n"},
                    {"type" : "image_url",
                    "image_url" : {"url" : f"data:image/jpeg;base64,{image}"}},
                ]
            )
        ]
        return message
    
    def plan_node(self, user_input: str, current_screen: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content="""You are an expert computer user who has to use a computer to perform the given task. Your job is to analyse the given task along with the current screen, \
                understand what is on the screen and then develop a detailed plan to perform the task from the current state of the screen using the mouse and keyboard actions. \
                Each step of the plan should be a single and a very simple action. You can use the mouse to perform the following actions: move the mouse, left, right or middle \
                click, double click, verticle and horizontal scroll. You can use the keyboard to perform the followig actions: press a key, type a string, press a key combination."""
            ),
            HumanMessage(
                content=[{"type" : "text", "text" : f"Task: {user_input}\n\nAlso, the following is the screenshot of the screen:\n"},
                {"type" : "image_url",
                "image_url" : {"url" : f"data:image/jpeg;base64,{current_screen}"}}]
            )
        ]

        return message
    
    def replan_node(self, user_input: str, plan: str, current_screen: str, last_llm_message: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content="""You are an expert computer user who has to analyse the given task, the plan to complete that task and the current screen of the computer. Your job is to \
                analyse the given task and the current screen of the computer and decide if the given task was completed or not based on the current computer screen. If the task \
                was completed, you can return boolean value True. If the task was not completed, you have to return the boolean value False.
                
                Analyse the current screen properly and only then return the boolean value."""
            ),
            HumanMessage(
                content=[{"type" : "text", "text" : f"Task: {user_input}\n\nplan: {plan}, last llm message: {last_llm_message}, and the current screen is:\n"},
                {"type" : "image_url",
                "image_url" : {"url" : f"data:image/jpeg;base64,{current_screen}"}}]
            )
        ]

        return message
    
    def mouse_functions(self, screen_object: str, screen_items: list) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content=f"""You are an expert computer user who has to find the given object or icon. Your job is to find the given object or icon from the \
                given json format data and return the name of the object or icon from the given json format data. The name would be the 'content' field in the \
                json data. The json data is a list of objects, each object has a 'content' field which is the name of the object or icon. The name being \
                returned should strictly be from the given json data, do not make up any name. Do not edit any name, give it as it is, do not remove any special \
                characters or spaces from the name or add any, just return the name as it is in the json data. Analyse the entire josn data and find the best \
                suited object or icon that matches the given icon or object name. There can me multiple objects or icons with similar names, give the most \
                relevant one."""
            ),
            HumanMessage(
                content=[{"type" : "text", "text" : f"From the following json data, find the {screen_object} and give me the name of the object or icon \
                corresponding to {screen_object} from the data.\n\nThe data is: {str(screen_items)}"}
                ]
            )
        ]

        return message