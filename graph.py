from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, HumanMessage
from typing import Annotated, TypedDict
import operator
import time
from PIL import ImageGrab
import base64

from agent import Agent
from nodes import Nodes
from structures import Plan, Replan
from windows import Screen, Mouse, Keyboard

class GraphState(TypedDict):
    task: str
    plan: Plan
    steps_completed: Annotated[list[str], operator.add]
    messages: Annotated[list[AnyMessage], operator.add]
    replan: Replan

class Graph:

    def __init__(self, model: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(model = "models/gemini-2.0-flash")):

        __graph = StateGraph(GraphState)
        __graph.add_node("plan_node", self.__plan)
        __graph.add_node("agent", self.__agent)
        __graph.add_node("replan_node", self.__replan)
        __graph.add_edge("plan_node", "agent")
        __graph.add_edge("agent", "replan_node")
        __graph.add_conditional_edges("replan_node", self.__check_end, {True : "agent", False : END})
        __graph.set_entry_point("plan_node")
        self.graph = __graph.compile()
        self.__model = model
        self.__nodes = Nodes()

    def __plan(self, state: GraphState):
        try:
            print(f"Task: {state['task']}")
            message = self.__model.with_structured_output(Plan).invoke(self.__nodes.plan_node(state["task"]))
            print(f"Plan: {message.as_str}")
            return {"messages" : [message.as_str], "plan" : message}
        except Exception:
            time.sleep(20)
            self.__plan(state)

    def __agent(self, state: GraphState):
        print("in agent node")
        __tools = Mouse().return_tools() + Keyboard().return_tools()
        __agent = Agent(__tools, self.__nodes.agent_message(Screen().get_size()))
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        print("screenshot saved")
        with open("screenshot.jpeg", "rb") as image_file:
            image = base64.b64encode(image_file.read()).decode('utf-8')
            image_file.close()
        print("agent created, now invoking")
        __messages = __agent.graph.invoke({"messages" : [
            HumanMessage(
                content=[
                    {"type" : "text", "text" : f"step to be performed: {state['plan'].plan[0].step}"},
                    {"type" : "image_url",
                    "image_url" : {"url" : f"data:image/jpeg;base64,{image}"}},
                ]
            )
        ]})
        step = state["plan"].plan.pop(0)
        return {"messages" : __messages["messages"], "steps_completed" : [step.step]}
    
    def __replan(self, state: GraphState):
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.jpeg")
        screenshot.close()
        with open("screenshot.jpeg", "rb") as image_file:
            image = base64.b64encode(image_file.read()).decode('utf-8')
        print("last llm message: ", state["messages"][-1].content)
        __replan = self.__model.with_structured_output(Replan).invoke(self.__nodes.replan_node(state["task"], state["plan"].as_str, image, state["messages"][-1].content))
        if isinstance(__replan.replan, bool):
            print(f"Replan: {__replan.replan}")
            return {"replan" : __replan.replan}
        else:
            print(f"Replan: {__replan.replan.as_str}")
            return {"replan" : __replan.replan, "plan" : __replan.replan}
        
    def __check_end(self, state: GraphState):
        if isinstance(state["replan"], bool):
            return not state["replan"]
        else:
            if len(state["plan"].plan) == 0:
                return False
            else:
                return True