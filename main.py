from graph import Graph
from langchain_core.messages import HumanMessage

task = "search for github.com/nabhpatodi10 on edge browser"

Graph().graph.invoke({"task" : task, "messages" : [HumanMessage(content=f"Task: {task}")]}, {"recursion_limit": 100})