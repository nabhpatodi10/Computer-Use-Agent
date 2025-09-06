from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage

class Nodes:
    def agent_message(self, screen_size: tuple[int, int], task: str, image: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content=f"""You are an expert computer user who has to use a computer to perform the given task. Your job is to complete the given task using the mouse and keyboard \
actions. You can use the mouse to perform the following actions: left, right or middle click, double click, verticle and horizontal scroll. You can use the keyboard to perform the \
following actions: press a key, type a string, press a key combination. To perform these actions, you have the access to the following tools:

    - click(button: Literal["left", "right", "middle"], to_object: str) - Click the mouse button at the given object or icon on the screen. The button can be left, right or middle.

    - drag(from_object: str, to_object: str) - Drag the mouse from the initial object or icon to the final object or icon.

    - scroll(direction: Literal["vertical", "horizontal"], delta: int) - Scroll the mouse in the given direction. The direction can be vertical or horizontal. To scroll down, the delta should be negative. To scroll up, the delta should be positive.

    - double_click(button: Literal["left", "right", "middle"], to_object: str) - Double click the mouse button at the given object or icon on the screen. The button can be left, right or middle.

    - press_key(key: str) - Press the given key on the keyboard. This tool is only for single keys. The key can be any commonly found key on most keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc

    - key_combination(keys: list[str]) - Press the given key combination on the keyboard. The keys can be any commonly found key on most keyboard, including letters, numbers, symbols and function keys. It should not be the ASCII code or any other code, it should be either be the symbol on the key (if there is a symbol, like !, @, # etc) or the name of the key, like enter, shift, ctrl, alt, a, b, c, 1, 2, 3 etc. Each key should be an element of the tuple

    - type_string(string: str) - Type the given string on the keyboard. The string can be any string, including letters, numbers, symbols, spaces and newline character (\\n) and tabs (\\t) as well. It should not be the ASCII code or any other code, it should be the string itself.

You can call these tools either one at a time or together as well. If you call these tools together, be careful about the order in which you call them because they will be executed \
in the same order.

You will get the initial screenshot of the screen and the task , you have to analyse the screenshot and decide what tools have to be called with what values. Each set of tool calls \
will also return a screenshot of the screen after performing the action. You can use this screenshot to decide what to do next. The size of the screen of the computer is: \
{screen_size[0], screen_size[1]}.

Based on these tools and their functions, first plan out how you will use them to complete the task. Consider the order in which you will call the tools and what steps you have to \
perform to complete the task. Once you have planned your approach, you can start executing the tools as per your plan. Do not stop until the task is completed."""
            ),
            HumanMessage(
                content=[
                    {"type" : "text", "text" : f"The task given by the user is: {task}\\n\nAlso, the following is the screenshot of the screen:\n"},
                    {"type" : "image_url",
                    "image_url" : {"url" : f"data:image/jpeg;base64,{image}"}},
                ]
            )
        ]
        return message
    
    def mouse_functions(self, screen_object: str, screen_items: dict, screenshot: str) -> list[AnyMessage]:
        message = [
            SystemMessage(
                content=f"""You are an expert computer user who has to find the given object or icon. Your job is to find the given object or icon from the \
                given json format data and the screenshot of the screen and return the name of the object or icon from the given json format data. Based on the \
                object to be identified, analyse the screenshot, you would find bounding boxes on all icons and objects on the screen. Each bounding box would \
                have a number. Find the object you have been asked to identify, analyse the number of the bounding box around that and then analyse the json \
                data. The json data would have the data for each bounding box and the name of the icon or the object would be the 'content' field for that \
                number in the json data. The json data is a dict where the bounding box number is the key and the object or icon details are the value. Each \
                object or icon detail is also a dict and has a 'content' field which is the name of the object or icon. You have to return the correct name of \
                the object which you have been asked to identify. The name being returned should strictly be from the given json data, do not make up any name. \
                Do not edit any name, give it as it is, do not remove any special characters or spaces from the name or add any, just return the name as it is \
                in the json data. Analyse the entire josn data and find the best suited object or icon that matches the given icon or object name. There can me \
                multiple objects or icons with similar names, give the most relevant one."""
            ),
            HumanMessage(
                content=[{"type" : "text", "text" : f"From the following json data, find the {screen_object} and give me the name of the object or icon \
                corresponding to {screen_object} from the data.\n\nThe data is: {str(screen_items)}\n\nAnd the following is the screenshot of the \
                screen containing all the numbered bounding boxes:"},
                {"type" : "image_url",
                "image_url" : {"url" : f"data:image/jpeg;base64,{screenshot}"}}
                ]
            )
        ]

        return message