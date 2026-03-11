class Pipeline:
    def __init__(self,steps):
        self.steps=steps

    def run(self,data=None):
        r=data
        for s in self.steps:
            r=s()
        return r
