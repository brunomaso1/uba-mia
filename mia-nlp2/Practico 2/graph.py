import os
from typing import Literal
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.embeddings import JinaEmbeddings
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, create_react_agent

import custom_prompts as cp
from utils import get_vector_store

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JINA_AI_API_KEY = os.getenv("JINA_AI_API_KEY")
EMBEDDINGS_MODEL = "jina-embeddings-v3"
GROQ_MODEL = "llama-3.3-70b-versatile"
BRUNO_CV_NAMESPACE = "nlp2-practico2-bruno-namespace"
JOSE_CV_NAMESPACE = "nlp2-practico2-jose-namespace"

chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=GROQ_MODEL, streaming=True)
text_embeddings = JinaEmbeddings(
    jina_api_key=JINA_AI_API_KEY, model_name=EMBEDDINGS_MODEL
)

vector_store_bruno = get_vector_store(
    text_embeddings=text_embeddings, namespace=BRUNO_CV_NAMESPACE
)
vector_store_jose = get_vector_store(
    text_embeddings=text_embeddings, namespace=JOSE_CV_NAMESPACE
)


@tool(response_format="content_and_artifact")
def retrieve(query: str, candidato: Literal["bruno", "jose"]):
    """Obtiene información relevante del CV de un candidato a partir de una consulta."""
    match candidato:
        case "bruno":
            retrieved_docs = vector_store_bruno.similarity_search(query, k=2)
        case "jose":
            retrieved_docs = vector_store_jose.similarity_search(query, k=2)
        case _:
            raise AssertionError(f"Candidato '{candidato}' no reconocido.")

    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


tools = [retrieve]
tool_node = ToolNode(tools)

# graph = create_react_agent(model=chat, tools=tool_node, prompt=cp.AGENT_PROMPT)
graph = create_react_agent(
    model=chat, tools=tool_node, prompt=cp.AGENT_PROMPT, debug=True
)  # Debug mode


def invoke_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables debe ser una lista")
    return graph.invoke({"messages": st_messages}, config={"callbacks": callables})
