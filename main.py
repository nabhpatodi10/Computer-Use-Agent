import tkinter as tk
from tkinter import scrolledtext
import tkinter.font as tkfont
from threading import Thread
import sys

from graph import Graph
from langchain_core.messages import HumanMessage
from windows import Keyboard

class ConsoleRedirector:
    def __init__(self, text_widget: scrolledtext.ScrolledText) -> None:
        self.text_widget = text_widget

    def write(self, message: str) -> None:
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state=tk.DISABLED)

    def flush(self) -> None:
        pass

def run_agent(task: str, output_widget: scrolledtext.ScrolledText) -> None:
    graph = Graph()
    graph.graph.invoke({"task": task, "messages": [HumanMessage(content=f"Task: {task}")]}, {"recursion_limit": 100})
    output_widget.configure(state=tk.NORMAL)
    output_widget.insert(tk.END, "\nTask completed\n")
    run_button.config(state=tk.NORMAL)
    output_widget.configure(state=tk.DISABLED)

def start_task(task_entry: tk.Entry, output_widget: scrolledtext.ScrolledText) -> None:
    task = task_entry.get()
    task_entry.config(text="")
    run_button.config(state=tk.DISABLED)
    if not task:
        return
    Keyboard().key_combination(["win", "d"])
    thread = Thread(target=run_agent, args=(task, output_widget), daemon=True)
    thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Computer Use Agent")
    root.attributes("-alpha", 0.9)
    root.configure(bg="#1e1e1e")
    root.resizable(False, False)
    root.wm_attributes("-topmost", True)

    root.option_add("*Font", "{Segoe UI} 10")
    mono_font = tkfont.Font(family="Consolas", size=9)

    width, height = 500, 300
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = screen_w - width - 20
    y = screen_h - height - 50
    root.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(root, text="Enter Task:", bg="#1e1e1e", fg="white").pack(pady=5)
    task_entry = tk.Entry(root, width=60, bg="#333333", fg="white", insertbackground="white", borderwidth=0, relief=tk.FLAT)
    task_entry.pack(pady=5, padx=10, fill=tk.X)

    output = scrolledtext.ScrolledText(root, state=tk.DISABLED, height=12, width=70, bg="#202020", fg="white", insertbackground="white", borderwidth=0, relief=tk.FLAT, font=mono_font)
    output.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    sys_redirect = ConsoleRedirector(output)
    sys.stdout = sys_redirect

    button_frame = tk.Frame(root, bg="#1e1e1e")
    button_frame.pack(pady=5)

    run_button = tk.Button(
        button_frame,
        text="Run",
        command=lambda: start_task(task_entry, output),
        bg="#4caf50",
        fg="white",
        activebackground="#45a049",
        borderwidth=0,
        font=("Segoe UI", 10, "bold"),
    )
    run_button.pack(side=tk.LEFT, padx=5)

    close_button = tk.Button(
        button_frame,
        text="Close",
        command=root.destroy,
        bg="#f44336",
        fg="white",
        activebackground="#e53935",
        borderwidth=0,
        font=("Segoe UI", 10, "bold"),
    )
    close_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()