import os
import time
from pprint import pprint

import streamlit as st
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.embeddings import JinaEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_groq import ChatGroq

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables.base import Runnable

from langchain.chains import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

import custom_prompts as cust_prmpts


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
JINA_AI_API_KEY = os.getenv("JINA_AI_API_KEY")
EMBEDDINGS_DIMENSION = 1024
EMBEDDINGS_MODEL = "jina-embeddings-v3"
GROQ_MODEL = "llama-3.3-70b-versatile"
INDEX_NAME = "nlp2-practico1"
NAMESPACE = "nlp2-practico1-namespace"
DOCUMENTS_DIRECTORY_PATH = "./resources/cv/"


def load_documents() -> list:
    loader = PyPDFDirectoryLoader(path=DOCUMENTS_DIRECTORY_PATH, mode="single")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
        separators=["\n\n", "\n", "(?=\\.)", " ", ""],
        length_function=len,
    )
    return text_splitter.split_documents(documents)


def get_vector_store(text_embeddings: Embeddings) -> PineconeVectorStore:
    vector_store = None
    pc = Pinecone(api_key=PINECONE_API_KEY)

    if not pc.has_index(INDEX_NAME):
        chunks = load_documents()

        pc.create_index(
            name=INDEX_NAME,
            vector_type="dense",
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            deletion_protection="disabled",
            tags={"environment": "development"},
        )
        # Espera activa hasta que el índice esté listo
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)

        vector_store = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=text_embeddings,
            index_name=INDEX_NAME,
            namespace=NAMESPACE,
        )

    if vector_store is None:
        vector_store = PineconeVectorStore.from_existing_index(
            embedding=text_embeddings, index_name=INDEX_NAME, namespace=NAMESPACE
        )

    return vector_store


def get_retrieval_chain(
    vector_store: PineconeVectorStore, chat: BaseChatModel
) -> Runnable:
    vector_store_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    retriever_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                cust_prmpts.REFORMULATE_HISTORY_PROMPT
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm=chat, retriever=vector_store_retriever, prompt=retriever_prompt
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(cust_prmpts.SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    combine_docs_chain = create_stuff_documents_chain(llm=chat, prompt=qa_prompt)

    retrieval_chain = create_retrieval_chain(
        retriever=history_aware_retriever, combine_docs_chain=combine_docs_chain
    )

    return retrieval_chain


def main():
    # Inicializar vector_store y chat
    chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=GROQ_MODEL)
    text_embeddings = JinaEmbeddings(
        jina_api_key=JINA_AI_API_KEY, model_name=EMBEDDINGS_MODEL
    )

    vector_store = get_vector_store(text_embeddings=text_embeddings)
    retrieval_chain = get_retrieval_chain(vector_store=vector_store, chat=chat)

    st.title("Chatbot con Retrieval y Historial Integrado")
    st.markdown(
        """
        ## Bienvenido al Chatbot de mi CV
        Esta aplicación combina la recuperación de documentos con un historial conversacional.
        Puedes realizar preguntas sobre mi CV, y el chatbot te responderá.
        Además, el historial de la conversación se utilizará para mejorar la interacción.
        """
    )

    # Configuración del historial de conversación utilizando st.session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = (
            []
        )  # Lista de diccionarios {'input': ..., 'chat_history': ...

    if "debug_chat_history" not in st.session_state:
        st.session_state.debug_chat_history = []  # Lista de resultados de la cadena

    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

    # Agregar botón de depuración
    debug_button = st.sidebar.button("Toggle Debug Mode")
    if debug_button:
        st.session_state.debug_mode = not st.session_state.debug_mode

    # Mostrar historial en la barra lateral si el modo debug está activo
    if st.session_state.debug_mode:
        st.sidebar.subheader("Historial de Chat")
        for i, result in enumerate(st.session_state.debug_chat_history):
            st.sidebar.markdown(f"### Turno {i+1}")

            # Mostrar cada parte del resultado
            st.sidebar.markdown(f"**Input:** {result.get('input', '')}")
            st.sidebar.markdown(f"**Answer:** {result.get('answer', '')}")

            # Mostrar contexto de documentos
            st.sidebar.markdown("**Contexto usado:**")
            for doc in result.get("context", []):
                st.sidebar.markdown(f"- {doc.page_content[:100]}...")

            st.sidebar.divider()

    # Entrada del usuario
    user_question = st.text_input("Haz una pregunta sobre mi CV:")

    if user_question:
        # Se invoca la cadena pasando el input y el historial
        result = retrieval_chain.invoke(
            {"input": user_question, "chat_history": st.session_state.chat_history}
        )
        answer = result["answer"]

        st.write("Respuesta del chatbot:", answer)

        # Actualizar el historial en la sesión
        st.session_state.chat_history.extend(
            [
                HumanMessage(content=result["input"]),
                AIMessage(content=result["answer"]),
            ]
        )

        # Actualizar el historial de debug
        st.session_state.debug_chat_history.append(result)

        pprint(result)


if __name__ == "__main__":
    main()
