from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, ToolMessage
from typing import Annotated, TypedDict
import operator
import time
from openai import RateLimitError
from PIL import ImageGrab
import base64

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:

    def __init__(self, tools: list, model: ChatOpenAI = ChatOpenAI(model = "gpt-4.1-mini")):

        __graph = StateGraph(AgentState)
        __graph.add_node("llm", self.__call_llm)
        __graph.add_node("action", self.__take_action)
        __graph.add_conditional_edges(
            "llm",
            self.__check_action,
            {True : "action", False : END}
        )
        __graph.add_edge("action", "llm")
        __graph.set_entry_point("llm")
        self.graph = __graph.compile()
        self.__tools = {t.name: t for t in tools}
        self.__model = model.bind_tools(tools)

    def __call_llm(self, state: AgentState):
        try:
            message = self.__model.invoke(state["messages"])
            for m in range(len(state["messages"])):
                if isinstance(state["messages"][m], ToolMessage):
                    state["messages"][m].content = ""
            print(f"LLM: {message.content}")
            return {"messages" : [message]}
        except RateLimitError as error:
            print("Got error\n", error)
            print("retrying...")
            time.sleep(20)
            message = self.__model.invoke(state["messages"])
            for m in range(len(state["messages"])):
                if isinstance(state["messages"][m], ToolMessage):
                    state["messages"][m].content = ""
            print(f"LLM: {message.content}")
            return {"messages" : [message]}
    
    def __take_action(self, state: AgentState):
        try:
            tool_calls = state["messages"][-1].tool_calls
            results = []
            for t in tool_calls:
                print(f"Calling: {t}")
                if not t["name"] in self.__tools:
                    result = "bad tool name, retry"
                else:
                    result = self.__tools[t["name"]].invoke(t["args"])
                results.append(ToolMessage(tool_call_id = t["id"], name = t["name"], content = str(result)))
            print("Back to model!")
            screenshot = ImageGrab.grab()
            screenshot.save("screenshot.jpeg")
            screenshot.close()
            print("screenshot saved")
            with open("screenshot.jpeg", "rb") as image_file:
                image = base64.b64encode(image_file.read()).decode('utf-8')
                image_file.close()
            results[-1].content = [
                {"type" : "text", "text" : f"{results[-1].content}\n\nAlso, the following is the screenshot of the screen after performing all the previous actions:\n"},
                {"type" : "image_url",
                "image_url" : {"url" : f"data:image/jpeg;base64,{image}"}}
            ]
            return {"messages" : results}
        except Exception as error:
            print(t)
            raise error
    
    def __check_action(self, state: AgentState):
        return len(state["messages"][-1].tool_calls) > 0