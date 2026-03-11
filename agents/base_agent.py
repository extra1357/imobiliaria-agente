class BaseAgent:
    def __init__(self,name,tools=None):
        self.name=name
        self.tools=tools or {}

    def register_tool(self,name,func):
        self.tools[name]=func

    def run(self,name,*a,**k):
        return self.tools[name](*a,**k)
