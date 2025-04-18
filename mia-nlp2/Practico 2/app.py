import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from graph import invoke_graph
from st_callable_util import (
    get_streamlit_cb,
)

st.title("Chatea con un agente de RRHH! 🤖")

# Initialize the expander state
if "expander_open" not in st.session_state:
    st.session_state.expander_open = True

# Capture user input from chat input
prompt = st.chat_input()

# Toggle expander state based on user input
if prompt is not None:
    st.session_state.expander_open = (
        False  # Close the expander when the user starts typing
    )

# st write magic
with st.expander(
    label="Instrucciones del agente",
    expanded=st.session_state.expander_open,
):
    """
    En esta aplicación puedes interactuar con un agente de RRHH que puede responder preguntas sobre los CVs de dos candidatos: Bruno y José.

    Haz una pregunta y el agente te responderá con información relevante de los CVs de los candidatos!
    """

if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content="Hola, realiza una pregunta sobre los CVs de Bruno o José. ¡Con gusto buscaré la información que necesitas!")]

for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)

if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        st_callback = get_streamlit_cb(st.container())
        response = invoke_graph(st.session_state.messages, [st_callback])
        st.session_state.messages.append(
            AIMessage(content=response["messages"][-1].content)
        )
