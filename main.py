import os
from langchain_groq import ChatGroq
# Mudança nos imports aqui:
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

# Sua chave Groq
os.environ["GROQ_API_KEY"] = "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"

@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"O tempo em {city} está ótimo, faz um sol de 25°C!"

tools = [get_weather]

# Usando o Llama 3 no Groq
llm = ChatGroq(model="llama3-8b-8192", temperature=0)

# O Prompt para Tool Calling
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente prestativo."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Criação do agente e executor
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    # Teste simples
    response = agent_executor.invoke({"input": "Como está o tempo em São Francisco?"})
    print("\nRESPOSTA FINAL:", response["output"])