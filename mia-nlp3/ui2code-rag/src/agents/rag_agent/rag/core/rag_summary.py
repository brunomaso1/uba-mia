import os

try:
    import openai
except ImportError:
    openai = None


def generar_rag_summary(docs: list[dict[str, str]], max_tokens: int = 1200) -> str:
    """
    Genera un resumen citado a partir de una lista de documentos usando OpenAI.

    Args:
        docs: Lista de diccionarios con keys: 'text', 'source', 'page'
        max_tokens: Máximo número de tokens para la respuesta

    Returns:
        String con el resumen generado y las citas

    Raises:
        RuntimeError: Si OpenAI no está configurado o disponible
    """
    if openai is None:
        raise RuntimeError("openai library not installed. Install with: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment variables")

    # Construir el contexto
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("source", "unknown")
        page = doc.get("page", "")
        text = doc.get("text", "")

        citation = f"[{source}"
        if page:
            citation += f", p. {page}"
        citation += "]"

        context_parts.append(f"Documento {i}: {text}\nFuente: {citation}")

    context = "\n\n---\n\n".join(context_parts)

    # Construir el prompt
    prompt = f"""Basándote en los siguientes documentos, genera un resumen coherente y completo. 
Incluye citas específicas al final de cada afirmación usando el formato [fuente, p. X] que se muestra en cada documento.

Documentos de referencia:
{context}

Resumen con citas:"""

    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)

        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que genera resúmenes académicos precisos con citas apropiadas.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            top_p=0.9,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # If OpenAI fails, return fallback
        fallback = "\n\n---\n\n".join(
            [
                f"{doc.get('text', '')}\n[{doc.get('source', 'unknown')}"
                + (f", p. {doc.get('page', '')}]" if doc.get("page") else "]")
                for doc in docs
            ]
        )
        return fallback


if __name__ == "__main__":
    # Test the function
    test_docs = [
        {
            "text": "RAG systems combine retrieval and generation for better AI responses.",
            "source": "rag_paper.pdf",
            "page": 3,
        },
        {
            "text": "Cross-encoders provide better relevance scoring than bi-encoders.",
            "source": "reranking_study.pdf",
            "page": 12,
        },
    ]

    try:
        summary = generar_rag_summary(test_docs)
        print("Generated summary:")
        print(summary)
    except Exception as e:
        print(f"Error: {e}")
