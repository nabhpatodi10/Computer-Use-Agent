from typing import Literal
import win32api, win32con, win32gui
from PIL import ImageGrab
import base64
from langchain_core.tools import tool, BaseTool

class Screen:

    def get_size(self) -> tuple[int, int]:
        return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

    def get_cursor_position(self) -> tuple[int, int]:
        return win32api.GetCursorPos()

    def get_window_rect(self, hwnd: int) -> tuple[int, int, int, int]:
        rect = win32gui.GetWindowRect(hwnd)
        return rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]

class Mouse:

    def move(self, x: int, y: int) -> str:
        """Move the mouse to the given x and y coordinates on the screen"""
        win32api.SetCursorPos((x, y))
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    def click(self, button: Literal["left", "right", "middle"], x: int, y: int) -> str:
        """Click the mouse button at the given x and y coordinates on the screen. The button can be left, right or middle."""
        if button == "left":
            self.move(x, y)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        elif button == "right":
            self.move(x, y)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        elif button == "middle":
            self.move(x, y)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def drag(self, initial_pos: list[int, int], final_pos: list[int, int]) -> str:
        """Drag the mouse from the initial position to the final position."""
        self.move(*initial_pos)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        self.move(*final_pos)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def scroll(self, direction: Literal["vertical", "horizontal"], delta: int) -> str:
        """Scroll the mouse in the given direction. The direction can be vertical or horizontal. To scroll down, the delta should be negative. To scroll up, the delta should be positive."""
        if direction == "vertical":
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
        elif direction == "horizontal":
            win32api.mouse_event(win32con.MOUSEEVENTF_HWHEEL, 0, 0, delta, 0)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def double_click(self, button: Literal["left", "right", "middle"], x: int, y: int) -> str:
        """Double click the mouse button at the given x and y coordinates on the screen. The button can be left, right or middle."""
        if button == "left":
            self.click("left", x, y)
            self.click("left", x, y)
        elif button == "right":
            self.click("right", x, y)
            self.click("right", x, y)
        elif button == "middle":
            self.click("middle", x, y)
            self.click("middle", x, y)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def return_tools(self) -> list[BaseTool]:
        return [tool(self.move), tool(self.click), tool(self.drag), tool(self.scroll), tool(self.double_click)]

class Keyboard:

    keys = {"shift" : win32con.VK_SHIFT,
            "ctrl" : win32con.VK_CONTROL,
            "alt" : win32con.VK_MENU,
            "windows" : 0x5B,
            "win" : 0x5B,
            "space" : 0x20,
            "enter" : 0x0D,
            "backspace" : 0x08,
            "delete" : 0x2E,
            "tab" : 0x09,
            "esc" : 0x1B,
            "capslock" : 0x14,
            "f1" : 0x70,
            "f2" : 0x71,
            "f3" : 0x72,
            "f4" : 0x73,
            "f5" : 0x74,
            "f6" : 0x75,
            "f7" : 0x76,
            "f8" : 0x77,
            "f9" : 0x78,
            "f10" : 0x79,
            "f11" : 0x7A,
            "f12" : 0x7B,
            "left" : 0x25,
            "right" : 0x27,
            "up" : 0x26,
            "down" : 0x28,
            "insert" : 0x2D,
            "printscreen" : 0x2C,
            "\n" : 0x0D,
            " " : 0x20,
            "\t" : 0x09,
            "!" : ["shift", 0x31],
            "@" : ["shift", 0x32],
            "#" : ["shift", 0x33],
            "$" : ["shift", 0x34],
            "%" : ["shift", 0x35],
            "^" : ["shift", 0x36],
            "&" : ["shift", 0x37],
            "*" : ["shift", 0x38],
            "(" : ["shift", 0x39],
            ")" : ["shift", 0x30],
            "-" : 0xBD,
            "_" : ["shift", 0xBD],
            "=" : 0xBB,
            "+" : ["shift", 0xBB],
            "," : 0xBC,
            "<" : ["shift", 0xBC],
            "." : 0xBE,
            ">" : ["shift", 0xBE],
            ";" : 0xBA,
            ":" : ["shift", 0xBA],
            "\\" : 0xDC,
            "|" : ["shift", 0xDC],
            "?" : 0xBF,
            "/" : ["shift", 0xBF],
            "`" : 0xC0,
            "~" : ["shift", 0xC0],
            "[" : 0xDB,
            "{" : ["shift", 0xDB],
            "]" : 0xDD,
            "}" : ["shift", 0xDD],
            "'" : 0xDE,
            "\"" : ["shift", 0xDE],
            }

    def press_key(self, key: str) -> str:
        """Press the given key on the keyboard. The key can be any key on the keyboard, including letters, numbers, symbols and function keys."""
        try:
            if key in self.keys.keys():
                if isinstance(self.keys[key], list):
                    self.key_combination(self.keys[key])
                else:
                    win32api.keybd_event(self.keys[key], 0, 0, 0)
                    win32api.keybd_event(self.keys[key], 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                win32api.keybd_event(ord(key.upper()), 0, 0, 0)
                win32api.keybd_event(ord(key.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
            screenshot = ImageGrab.grab()
            screenshot.save("screenshot.jpeg")
            screenshot.close()
            with open("screenshot.jpeg", "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise e

    def key_combination(self, keys: list[str]) -> str:
        """Press the given key combination on the keyboard. The keys can be any key on the keyboard, including letters, numbers, symbols and function keys."""
        for key in keys:
            if key in self.keys.keys():
                win32api.keybd_event(self.keys[key], 0, 0, 0)
            else:
                win32api.keybd_event(ord(key.upper()), 0, 0, 0)
        for key in keys[-1::-1]:
            if key in self.keys.keys():
                win32api.keybd_event(self.keys[key], 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                win32api.keybd_event(ord(key.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def type_string(self, text: str) -> str:
        """Type the given string on the keyboard. The string can be any string, including letters, numbers, symbols, spaces and newline character (\\n) and tabs (\\t) as well."""
        for char in text:
            if char.isnumeric() or char.islower():
                self.press_key(char)
            elif char.isupper():
                self.key_combination(["shift", char])
            else:
                self.press_key(char)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def return_tools(self) -> list[BaseTool]:
        return [tool(self.press_key), tool(self.key_combination), tool(self.type_string)]