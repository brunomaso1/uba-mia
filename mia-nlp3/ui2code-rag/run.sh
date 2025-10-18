#!/usr/bin/env bash
set -euo pipefail

VISUAL_AGENT_ENV=src/agents/visual_a2a_agent/.env
CODE_AGENT_ENV=src/agents/code_a2a_agent/.env
STREAMLIT_ENV=.env

# Obtener ancho de terminal (default 80 si no se puede detectar)
COLS=$(tput cols 2>/dev/null || echo 80)

print_centered() {
    local text="$1"
    local text_length=${#text}
    local padding=$(( (COLS - text_length) / 2 ))
    printf "%*s%s\n" $padding "" "$text"
}

print_banner() {
    echo
    print_centered "🚀 Iniciando setup del entorno..."
    print_centered "ℹ️  Este script te permitirá configurar y ejecutar los contenedores Docker necesarios (como paso final realiza docker compose up --build)."
    print_centered "La aplicación requiere como única dependencia del sistema operativo tener Docker y Docker Compose instalados."
    print_centered "Para la configuración de los modelos del lenguaje e interacciones con -embeddings-, se utilizará OpenRouter y Pinecone."
    print_centered "Debes contar con dichas cuentas y API_KEYs."
    print_centered "⚠️  La aplicación también funciona con OpenAI, pero este script configura por defecto OpenRouter y Pinecone."
    print_centered "(Parece código de un LLM por los emojis, pero una persona escribió este código)."
    print_centered "⭐ Vamos allá!"
    echo
    # Esperar confirmación
    read -p "👉 Presiona ENTER para continuar..." _
    echo
}

check_docker() {
    echo "🔎 Verificando Docker..."
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker no está instalado o no está en el PATH."
        exit 1
    fi

    if ! docker ps &> /dev/null; then
        echo "❌ Docker está instalado pero el daemon no se está ejecutando."
        echo "Por favor, inicia Docker Desktop o el servicio de Docker."
        exit 1
    fi

    if docker compose version &> /dev/null; then
        :
    elif docker-compose version &> /dev/null; then
        :
    else
        echo "❌ Docker Compose no está instalado."
        exit 1
    fi

    echo -e "✅ Docker está instalado correctamente. Continuando...\n"
    sleep 1
}

check_visual_agent_env() {
    if [ -f "$VISUAL_AGENT_ENV" ]; then
        echo "   Archivo $VISUAL_AGENT_ENV encontrado."
    

        if ! grep -q '^OPENROUTER_API_KEY=' "$VISUAL_AGENT_ENV"; then
            echo "❌ OPENROUTER_API_KEY no está configurada en $VISUAL_AGENT_ENV."
            echo "Por favor, edita el archivo y añade tu clave API de OpenRouter (https://openrouter.ai/settings/keys)."
            exit 1
        fi
        if ! grep -q '^GUARDRAILS_API_KEY=' "$VISUAL_AGENT_ENV"; then
            echo "❌ GUARDRAILS_API_KEY no está configurada en $VISUAL_AGENT_ENV."
            echo "Por favor, edita el archivo y añade tu clave API de Guardrails (https://hub.guardrailsai.com/keys)."
            exit 1
        fi
        if ! grep -q '^OPENROUTER_VISUAL_MODEL=' "$VISUAL_AGENT_ENV"; then
            echo "❌ OPENROUTER_VISUAL_MODEL no está configurada en $VISUAL_AGENT_ENV."
            echo "Por favor, edita el archivo y añade el modelo visual que deseas usar (ejemplo: meta-llama/llama-4-maverick:free). Puedes ver los modelos disponibles en https://openrouter.ai/models?fmt=cards&input_modalities=image&max_price=0. Asegurate de que sea un modelo visual."
            exit 1
        fi
    else
        echo "   No se encontró el archivo $VISUAL_AGENT_ENV."
        echo "   Creando..."
        # Solicitar claves al usuario
        read -p "   Introduce tu OPENROUTER_API_KEY (https://openrouter.ai/settings/keys): " OPENROUTER_API_KEY
        read -p "   Introduce tu GUARDRAILS_API_KEY (https://hub.guardrailsai.com/keys): " GUARDRAILS_API_KEY
        read -p "   Introduce el modelo visual que deseas usar (ejemplo: meta-llama/llama-4-maverick:free). Puedes ver los modelos disponibles en https://openrouter.ai/models?fmt=cards&input_modalities=image&max_price=0. Asegurate de que sea un modelo visual: " OPENROUTER_VISUAL_MODEL

        # Crear el archivo .env con las variables necesarias
        cat <<EOF > "$VISUAL_AGENT_ENV"
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
GUARDRAILS_API_KEY=$GUARDRAILS_API_KEY
OPENROUTER_VISUAL_MODEL=$OPENROUTER_VISUAL_MODEL
EOF
    fi  

    echo "✅ Archivo $VISUAL_AGENT_ENV creado con las variables de entorno necesarias."
}

check_code_agent_env() {
    if [ -f "$CODE_AGENT_ENV" ]; then
        echo "   Archivo $CODE_AGENT_ENV encontrado."

        if ! grep -q '^OPENROUTER_API_KEY=' "$CODE_AGENT_ENV"; then
            echo "❌ OPENROUTER_API_KEY no está configurada en $CODE_AGENT_ENV."
            echo "Por favor, edita el archivo y añade tu clave API de OpenRouter (https://openrouter.ai/settings/keys)."
            exit 1
        fi
        if ! grep -q '^GUARDRAILS_API_KEY=' "$CODE_AGENT_ENV"; then
            echo "❌ GUARDRAILS_API_KEY no está configurada en $CODE_AGENT_ENV."
            echo "Por favor, edita el archivo y añade tu clave API de Guardrails (https://hub.guardrailsai.com/keys)."
            exit 1
        fi
        if ! grep -q '^OPENROUTER_CODE_MODEL=' "$CODE_AGENT_ENV"; then
            echo "❌ OPENROUTER_CODE_MODEL no está configurada en $CODE_AGENT_ENV."
            echo "Por favor, edita el archivo y añade el modelo de código que deseas usar (ejemplo: deepseek/deepseek-chat-v3.1:free). Puedes ver los modelos disponibles en https://openrouter.ai/models?fmt=cards&input_modalities=text&max_price=0."
            exit 1
        fi
    else
        echo "   No se encontró el archivo $CODE_AGENT_ENV."
        echo "   Creando..."

        read -p "   Introduce tu OPENROUTER_API_KEY (https://openrouter.ai/settings/keys): " OPENROUTER_API_KEY
        read -p "   Introduce tu GUARDRAILS_API_KEY (https://hub.guardrailsai.com/keys): " GUARDRAILS_API_KEY
        read -p "   Introduce tu OPENROUTER_CODE_MODEL (ejemplo: deepseek/deepseek-chat-v3.1:free). Puedes ver los modelos disponibles en https://openrouter.ai/models?fmt=cards&input_modalities=text&max_price=0: " OPENROUTER_CODE_MODEL

        # Crear el archivo .env con las variables necesarias
        cat <<EOF > "$CODE_AGENT_ENV"
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
GUARDRAILS_API_KEY=$GUARDRAILS_API_KEY
OPENROUTER_CODE_MODEL=$OPENROUTER_CODE_MODEL
EOF
    fi

    echo "✅ Archivo $CODE_AGENT_ENV creado con las variables de entorno necesarias."
}

check_streamlit_env() {
    if [ -f "$STREAMLIT_ENV" ]; then
        echo "   Archivo $STREAMLIT_ENV encontrado."

        if ! grep -q '^PINECONE_API_KEY=' "$STREAMLIT_ENV"; then
            echo "❌ PINECONE_API_KEY no está configurada en $STREAMLIT_ENV. (en el root del proyecto)"
            echo "Por favor, edita el archivo y añade tu clave API de Pinecone (https://app.pinecone.io/)."
            exit 1
        fi
    else
        echo "   No se encontró el archivo $STREAMLIT_ENV."
        echo "   Creando..."

        read -p "   Introduce tu PINECONE_API_KEY (https://app.pinecone.io/): " PINECONE_API_KEY

        # Crear el archivo .env con las variables necesarias
        cat <<EOF > "$STREAMLIT_ENV"
PINECONE_API_KEY=$PINECONE_API_KEY
EOF
    fi

    echo "✅ Archivo $STREAMLIT_ENV creado con las variables de entorno necesarias."
}

check_envs() {
    echo "🔎 Verificando variables de entorno..."
    check_visual_agent_env
    check_code_agent_env
    check_streamlit_env
    echo -e "✅ Variables de entorno verificadas correctamente.\n"
    sleep 1
}

start_docker() {
    echo "🚀 Iniciando contenedores con build..."
    echo "⚠️  Prepárate un café ☕, la primera vez puede tardar (≈30 GB de imágenes)."
    docker compose up --build
}

main() {
    print_banner
    check_docker
    check_envs
    start_docker
}

main "$@"
