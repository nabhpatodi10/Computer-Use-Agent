from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, HumanMessage
from typing import Annotated, TypedDict
import operator
import time
from PIL import ImageGrab
import base64
from openai import RateLimitError

from agent import Agent
from nodes import Nodes
from structures import Plan, Replan
from windows import Screen, Mouse, Keyboard

class GraphState(TypedDict):
    task: str
    plan: Plan
    messages: Annotated[list[AnyMessage], operator.add]
    replan: Replan

class Graph:

    def __init__(self, model: ChatOpenAI = ChatOpenAI(model = "gpt-4.1-nano")):

        __graph = StateGraph(GraphState)
        __graph.add_node("plan_node", self.__plan)
        __graph.add_node("agent", self.__agent)
        __graph.add_node("replan_node", self.__replan)
        __graph.add_edge("plan_node", "agent")
        __graph.add_edge("agent", "replan_node")
        __graph.add_conditional_edges("replan_node", self.__check_end, {False : "agent", True : END})
        __graph.set_entry_point("plan_node")
        self.graph = __graph.compile()
        self.__model = model
        self.__nodes = Nodes()

    def __plan(self, state: GraphState):
        try:
            screenshot = ImageGrab.grab()
            screenshot.save("screenshot.jpeg")
            screenshot.close()
            print("screenshot saved")
            with open("screenshot.jpeg", "rb") as image_file:
                image = base64.b64encode(image_file.read()).decode('utf-8')
                image_file.close()
            print(f"Task: {state['task']}")
            message = self.__model.with_structured_output(Plan).invoke(self.__nodes.plan_node(state["task"], image))
            print(f"Plan: {message.as_str}")
            return {"messages" : [message.as_str], "plan" : message}
        except RateLimitError:
            time.sleep(20)
            self.__plan(state)

    def __agent(self, state: GraphState):
        print("in agent node")
        __tools = Mouse().return_tools() + Keyboard().return_tools()
        __agent = Agent(__tools)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        print("screenshot saved")
        with open("screenshot.jpeg", "rb") as image_file:
            image = base64.b64encode(image_file.read()).decode('utf-8')
            image_file.close()
        print("agent created, now invoking")
        __messages = __agent.graph.invoke({"messages" : self.__nodes.agent_message(Screen().get_size(), state["plan"], image)})
        return {"messages" : __messages["messages"]}
    
    def __replan(self, state: GraphState):
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            image = base64.b64encode(image_file.read()).decode('utf-8')
        print("last llm message: ", state["messages"][-1].content)
        try:
            __replan = self.__model.with_structured_output(Replan).invoke(self.__nodes.replan_node(state["task"], state["plan"].as_str, image, state["messages"][-1].content))
        except RateLimitError:
            time.sleep(20)
            __replan = self.__model.with_structured_output(Replan).invoke(self.__nodes.replan_node(state["task"], state["plan"].as_str, image, state["messages"][-1].content))
        if isinstance(__replan.replan, bool):
            print(f"Replan: {__replan.replan}")
            return {"replan" : __replan.replan}
        else:
            print(f"Replan: {__replan.replan.as_str}")
            return {"replan" : __replan.replan, "plan" : __replan.replan}
        
    def __check_end(self, state: GraphState):
        print("Current Plan: ", state["plan"].as_str)
        if isinstance(state["replan"], bool):
            return True
        else:
            if len(state["plan"].plan) == 0:
                return True
            else:
                return False