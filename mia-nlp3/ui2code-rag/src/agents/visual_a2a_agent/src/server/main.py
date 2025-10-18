from loguru import logger
import sys
import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Custom dependencies
from ..agent.visual_a2a_agent_executor import VisualA2AAgentExecutor
from ..config import settings

HOST = settings.host
PORT = settings.port
SERVER_TIMEOUT_KEEP_ALIVE = settings.server_timeout_keep_alive


@click.command()
@click.option("--port", "port", default=PORT)
def main(port: int):
    logger.info(f"Starting Visual Agent server on {HOST}:{port}")
    try:
        capabilities = AgentCapabilities()
        skills = [
            AgentSkill(
                id="web-design-image-analyzer",
                name="Web design image analyzer",
                description="Analyzes image from a web design and extracts structured information about the core concepts image.",
                tags=["web-design", "image-analysis", "generator"],
                examples=["Some web scratch image design."],
                input_modes=["image/png", "image/jpeg", "image/jpg"],
                output_modes=["application/json"],
            )
        ]
        agent_card = AgentCard(
            name="Visual Agent",
            description="Helps with getting information from images.",
            url=f"http://{HOST}:{port}/",
            version="1.0.0",
            default_input_modes=["image/png", "image/jpeg", "image/jpg"],
            default_output_modes=["text/plain", "application/json"],
            capabilities=capabilities,
            skills=skills,
        )

        request_handler = DefaultRequestHandler(
            agent_executor=VisualA2AAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

        uvicorn.run(server.build(), host="0.0.0.0", port=port, timeout_keep_alive=SERVER_TIMEOUT_KEEP_ALIVE)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
