from dotenv import load_dotenv
from src.agent import agent

load_dotenv()

response = agent.invoke({
    "messages": [
        {
            "role": "user",
            #again, this content is hardcoded rn, we will make it dynamic to the users request
            "content": "Classify this task: summarize a small local text file. Should it run on edge or cloud?"
        }
    ]
})

print(response["messages"][-1].content)