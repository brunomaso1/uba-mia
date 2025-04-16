SYSTEM_PROMPT = """
Responde la pregunta del usuario basándote en el siguiente contexto:

<contexto>
{context}
</contexto>

Si no hay información relevante en el contexto, di "No sé la respuesta".
"""

REFORMULATE_HISTORY_PROMPT = """
Dado un historial de un chat y la última pregunta del usuario, que podría referencial al contexto del historial, crea una pregunta independiente que pueda entenderse sin el historial. NO respondas a la pregunta; simplemente reformula si es necesario; de lo contrario, devuélvala tal como está.
"""
