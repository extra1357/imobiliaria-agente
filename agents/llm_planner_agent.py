import os
from groq import Groq

client = Groq()

class LLMPlannerAgent:

    def plan(self, task:str):

        prompt = f'''
You are an AI planner.

Break the task into tool steps.

Available tools:
- hello
- add

Return ONLY a python list.

Example:
["hello"]

Task:
{task}
'''

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"user","content":prompt}
            ]
        )

        text = response.choices[0].message.content.strip()

        try:
            steps = eval(text)
        except:
            steps = []

        return steps
