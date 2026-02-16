from langchain.chat_models import BaseChatModel
from config import config
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_litellm import ChatLiteLLM
from langchain_openai import ChatOpenAI
from agent.tools import create_refund_agent_tools

agent_llm: BaseChatModel | None

if config.GROQ_API_KEY:
    agent_llm = ChatGroq(api_key=config.GROQ_API_KEY, model="openai/gpt-oss-120b") #type: ignore
elif config.LITELLM_API_KEY:
    agent_llm = ChatLiteLLM(api_key=config.LITELLM_API_KEY, api_base="https://llm.keyvalue.systems", model="litellm_proxy/gpt-4.1")
elif config.GOOGLE_API_KEY:
    agent_llm = ChatGoogleGenerativeAI(google_api_key=config.GOOGLE_API_KEY, model="gemini-3-flash-preview")
elif config.OPENAI_API_KEY:
    agent_llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model="gpt-4.1") #type: ignore

tools = create_refund_agent_tools(0, "DUMMY")
agent_llm.bind_tools([tool for tool in tools.values()]) #type: ignore