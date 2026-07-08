from agents.agent import get_agent
from langchain_core.messages import HumanMessage
from database.database import init_db

init_db()

agent = get_agent()

config = {
    "configurable":{"thread_id":"1"}
}

messages = {"messages":[HumanMessage(content="What is my name?")]}

for message_chunk,metadata in agent.stream(messages,config=config,stream_mode="messages"):
    if message_chunk.content:
        print(message_chunk.content,end=" ",flush=True)