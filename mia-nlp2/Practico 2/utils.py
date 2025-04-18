import os
import time
from dotenv import load_dotenv

# Pinecone imports
from pinecone import Pinecone, ServerlessSpec

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.embeddings import Embeddings

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
EMBEDDINGS_DIMENSION = 1024
INDEX_NAME = "nlp2-practico2"
BRUNO_CV_NAMESPACE = "nlp2-practico2-bruno-namespace"
JOSE_CV_NAMESPACE = "nlp2-practico2-jose-namespace"
CV_BRUNO_FILE_PATH = "../resources/cv_candidatos/cv-bruno-masoller.pdf"
CV_JOSE_FILE_PATH = "../resources/cv_candidatos/cv-jose-martinez.pdf"


def load_document(namespace: str) -> list:
    match namespace:
        case ns if ns == BRUNO_CV_NAMESPACE:
            file_path = CV_BRUNO_FILE_PATH
        case ns if ns == JOSE_CV_NAMESPACE:
            file_path = CV_JOSE_FILE_PATH
        case _:
            raise ValueError(f"Namespace '{namespace}' no reconocido.")

    loader = PyPDFLoader(file_path=file_path, mode="single")
    document = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", "(?=\\.)", " ", ""],
        length_function=len,
    )
    return text_splitter.split_documents(document)


# Función principal para obtener el vector store
def get_vector_store(
    text_embeddings: Embeddings, namespace: str
) -> PineconeVectorStore:
    # Inicializar Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Crear el índice si no existe
    if not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDINGS_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        # Esperar a que el índice esté listo
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)

    index = pc.Index(INDEX_NAME)

    # Verificar si el namespace ya tiene vectores
    stats = index.describe_index_stats()
    vector_count = stats.namespaces.get(namespace, {"vector_count": 0})["vector_count"]

    if vector_count == 0:
        # Cargar el documento y subir los vectores al namespace
        chunks = load_document(namespace)
        if not chunks:
            raise ValueError(
                f"El documento {namespace} está vacío o no se pudo cargar."
            )

        # Upsert de los vectores
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=text_embeddings,
            index_name=INDEX_NAME,
            namespace=namespace,
        )

    # Crear el vector store desde el índice existente
    vector_store = PineconeVectorStore.from_existing_index(
        embedding=text_embeddings,
        index_name=INDEX_NAME,
        namespace=namespace,
    )

    return vector_store
