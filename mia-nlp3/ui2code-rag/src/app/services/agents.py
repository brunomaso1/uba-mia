import streamlit as st
import asyncio
from src.agents.orchestator_agent.orchestator_agent import OrchestratorAgent
from src.agents.rag_agent.rag_agent import RAGAgent

@st.cache_resource
def get_orchestrator() -> OrchestratorAgent | None:
    try:
        agent = OrchestratorAgent()
        asyncio.run(agent.initialize())
        return agent
    except Exception as e:
        st.error(f"No se pudo inicializar OrchestratorAgent: {e}")
        return None

@st.cache_resource
def get_rag_agent() -> RAGAgent | None:
    try:
        return RAGAgent()
    except Exception as e:
        st.error(f"No se pudo inicializar RAGAgent: {e}")
        return None
