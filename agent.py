from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from typing import Annotated, TypedDict
import operator

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:

    def __init__(self, tools: list, system_message: list[SystemMessage], model: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(model = "models/gemini-2.0-flash")):

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
        self.__system_message = system_message
        self.__tools = {t.name: t for t in tools}
        self.__model = model.bind_tools(tools)

    def __call_llm(self, state: AgentState):
        try:
            messages = self.__system_message + state["messages"]
            message = self.__model.invoke(messages)
            for m in state["messages"]:
                if isinstance(m, ToolMessage):
                    state["messages"].remove(m)
            print(f"LLM: {message.content}")
            return {"messages" : [message]}
        except Exception as error:
            # time.sleep(20)
            # self.__call_llm(state)
            raise error
    
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
            return {"messages" : results}
        except Exception as error:
            print(t)
            raise error
    
    def __check_action(self, state: AgentState):
        return len(state["messages"][-1].tool_calls) > 0