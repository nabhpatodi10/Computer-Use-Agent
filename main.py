from graph import Graph
from langchain_core.messages import HumanMessage

Graph().graph.invoke({"task" : "open github.com on edge, to open edge use the windows key and then search edge", "messages" : [HumanMessage(content="Task: open github.com on edge, to open edge use the windows key and then search edge")]})