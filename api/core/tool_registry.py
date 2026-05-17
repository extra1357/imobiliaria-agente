class ToolRegistry:
    def __init__(self):
        self.tools={}

    def register(self,name,func):
        self.tools[name]=func

    def get(self,name):
        return self.tools.get(name)
