.PHONY: help install install-dev clean lint test format run-server build-index demo setup-dirs check-config check-deps ui-to-code-demo
.DEFAULT_GOAL := help

# Variables
PROJECT_NAME = ui-to-code-system
ifeq ($(OS),Windows_NT)
    PYTHON_INTERPRETER = py
else
    PYTHON_INTERPRETER = python
endif

export HOST=localhost

SCRIPTS_FOLDER = src/scripts

VENV_NAME = venv
ENV_FILE = .env
PORT = 8501

WEBSIGHT_OFFSET = 0
WEBSIGHT_LENGTH = 1000
WEBSIGHT_STEPS=100

WEBSIGHT_LOADER_MODULE = src.agents.rag_agent.rag.ingestion.websight_loader
WEBSIGHT_MAX_EXAMPLES = 1000

## Download a subset of the WebSight dataset for testing
download-websight:
	@echo "Descargando WebSight dataset en pasos de $(WEBSIGHT_STEPS) desde $(WEBSIGHT_OFFSET) hasta $(WEBSIGHT_LENGTH)..."
	mkdir -p data/websight
	@for step in $(shell seq $(WEBSIGHT_OFFSET) $(WEBSIGHT_STEPS) $(WEBSIGHT_LENGTH)); do \
		echo "Descargando offset $$step..."; \
		curl -X GET "https://datasets-server.huggingface.co/rows?dataset=HuggingFaceM4%2FWebSight&config=v0.2&split=train&offset=$$step&length=$(WEBSIGHT_STEPS)" -o data/websight/websight_$$step.json; \
		echo "Guardado en data/websight/websight_$$step.json"; \
	done

download-websight-win:
	@echo Descargando WebSight dataset (train, offset $(WEBSIGHT_OFFSET), length $(WEBSIGHT_LENGTH))...
	if not exist data\websight mkdir data\websight
	@for step in $(shell seq $(WEBSIGHT_OFFSET) $(WEBSIGHT_STEPS) $(WEBSIGHT_LENGTH)); do \
		echo "Descargando offset $$step..."; \
		curl -X GET "https://datasets-server.huggingface.co/rows?dataset=HuggingFaceM4%2FWebSight&config=v0.2&split=train&offset=$$step&length=$(WEBSIGHT_STEPS)" -o data/websight/websight_$$step.json; \
		echo "Guardado en data/websight/websight_$$step.json"; \
	done

run-guardrails-configuration:
	@echo "Running Guardrails configuration..."
	bash $(SCRIPTS_FOLDER)/guardrails_config.sh $(ENV_FILE)

run-visual-agent:
	@echo "Running Visual Agent..."
	$(PYTHON_INTERPRETER) -m src.agents.visual_a2a_agent.src.server.main

run-code-agent:
	@echo "Running Code Agent..."
	$(PYTHON_INTERPRETER) -m src.agents.code_a2a_agent.src.server.main

## Run Streamlit web app
run-server:
	@echo "Starting UI-to-Code Streamlit app on port $(PORT)..."
	$(PYTHON_INTERPRETER) -m streamlit run src/app/main.py --server.port $(PORT) --server.address 0.0.0.0

## Build Pinecone vector index from HTML/CSS examples
build-html:
	@echo "Building Pinecone vector index for HTML/CSS examples..."
	$(PYTHON_INTERPRETER) -m $(WEBSIGHT_LOADER_MODULE) --max-examples=$(WEBSIGHT_MAX_EXAMPLES)

evaluate-retrieval:
	$(PYTHON_INTERPRETER) -m src.agents.rag_agent.rag.evaluators.evaluate_retrieval --docs data/evaluate/docs_ui_code_en.jsonl --qrels data/evaluate/qrels_ui_code_en.csv --ks 3,5 --top_retrieve 10 --top_final 5