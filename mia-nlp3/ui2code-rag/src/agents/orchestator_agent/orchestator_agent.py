"""Orchestrator Agent that coordinates between Visual and Code Agents, and integrates RAG for context."""

# TODO: Refactor constants (timeouts, URLs) to config
import json
from loguru import logger
import base64, json, httpx, asyncio, time
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    Message,
    SendMessageSuccessResponse,
)
from a2a.utils import get_message_text, get_text_parts
from PIL import Image
from io import BytesIO

# Local dependencies
from src.agents.rag_agent.rag_agent import RAGAgent
from src.config import visual_agent_url, code_agent_url, server_timeout_keep_alive, server_connect_timeout

VISUAL_AGENT_URL = visual_agent_url
CODE_AGENT_URL = code_agent_url
SERVER_TIMEOUT_KEEP_ALIVE = server_timeout_keep_alive
SERVER_CONNECT_TIMEOUT = server_connect_timeout


class OrchestratorAgent:
    def __init__(self, visual_url: str = VISUAL_AGENT_URL, code_url: str = CODE_AGENT_URL) -> None:
        self.visual_url: str = visual_url
        self.code_url: str = code_url
        self.rag_agent: RAGAgent = RAGAgent()
        self.httpx_client: httpx.AsyncClient | None = None

        self.agents: dict[str, dict[str, object]] = {
            "visual": {"url": self.visual_url, "card": None, "client": None},
            "code": {"url": self.code_url, "card": None, "client": None},
            "rag": {"url": None, "card": None, "client": self.rag_agent},
        }

    async def initialize(self) -> None:
        """Initialize HTTP client and fetch both agents' cards."""
        logger.info("Initializing HTTP client")
        timeout = httpx.Timeout(SERVER_TIMEOUT_KEEP_ALIVE, connect=SERVER_CONNECT_TIMEOUT)
        self.httpx_client = httpx.AsyncClient(timeout=timeout)

        for agent_name, agent_info in self.agents.items():
            url = agent_info["url"]
            if url:
                resolver = A2ACardResolver(
                    httpx_client=self.httpx_client,
                    base_url=url,
                )
                try:
                    card: AgentCard = await resolver.get_agent_card()
                    self.agents[agent_name]["card"] = card
                    self.agents[agent_name]["client"] = A2AClient(
                        httpx_client=self.httpx_client,
                        agent_card=card,
                    )
                    logger.info(f"Fetched {agent_name} agent card: {card.name} v{card.version}")
                except Exception as e:
                    logger.error(
                        f"Critical error fetching {agent_name} agent card: {e}",
                        exc_info=True,
                    )
                    raise RuntimeError(f"Failed to fetch {agent_name} agent card. Cannot continue.") from e

    def _serialize_patterns(self, patterns) -> str:
        """Ensure patterns are JSON-serializable (tuples -> lists)."""
        if not patterns:
            return "[]"
        try:
            return json.dumps(patterns, ensure_ascii=False)
        except TypeError:
            try:
                safe = []
                for p in patterns:
                    if isinstance(p, tuple):
                        safe.append(list(p))
                    else:
                        safe.append(p)
                return json.dumps(safe, ensure_ascii=False)
            except Exception:
                return "[]"

    def _dump_response_safe(self, response) -> str:
        try:
            d = response.model_dump(mode="json", exclude_none=True)
            s = json.dumps(d)
            return s[:10000]
        except Exception:
            try:
                return str(response)[:10000]
            except Exception:
                return "<unprintable response>"

    def _safe_json(self, obj) -> str:
        return json.dumps(obj, ensure_ascii=False)

    def get_agent_client(self, agent_name: str) -> A2AClient | RAGAgent:
        client = self.agents.get(agent_name, {}).get("client")
        if client is None:
            raise RuntimeError(f"Agent '{agent_name}' not initialized.")
        return client

    async def close(self) -> None:
        if self.httpx_client:
            await self.httpx_client.aclose()

    async def _send_message_to_agent(
        self,
        agent_name: str,
        message_payload: dict[str, Any],
    ) -> SendMessageResponse:
        """
        Send a message to the specified agent and return the A2A response.
        Do NOT pass a 'timeout' kwarg here (some a2a versions don't support it).
        """
        client = self.get_agent_client(agent_name)
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**message_payload),
        )

        t0 = time.perf_counter()
        try:
            logger.debug(f"[{agent_name}] Sending message to agent...")
            response: SendMessageResponse = await client.send_message(request)
            dt = time.perf_counter() - t0
            try:
                dump = response.model_dump(mode="json", exclude_none=True)
                root_keys = list(dump.get("root", {}).keys())
                logger.debug(f"[{agent_name}] send_message OK in {dt:.1f}s. Root keys: {root_keys}")
            except Exception:
                logger.debug(f"[{agent_name}] send_message OK in {dt:.1f}s (no dump)")
            return response
        except Exception as e:
            dt = time.perf_counter() - t0
            logger.error(f"[{agent_name}] send_message failed after {dt:.1f}s: {e}", exc_info=True)
            raise

    def _validate_response(self, response: SendMessageResponse) -> bool:
        """Lightweight structural checks for A2A responses."""
        try:
            if not response or not getattr(response, "root", None):
                raise ValueError("Invalid response structure")
            if not isinstance(response.root, SendMessageSuccessResponse):
                logger.error("Non-success response root: {}", type(response.root))
                raise ValueError(f"Non-success response: {type(response.root).__name__}")
            if not isinstance(response.root.result, Message):
                raise ValueError("Non-message result")
            if not response.root.result.parts:
                raise ValueError("No parts in message result")
        except Exception as e:
            logger.error("Response validation error: {}", e, exc_info=True)
            raise RuntimeError("Response validation failed") from e
        return True

    def _get_analysis_result_from_response(self, response: SendMessageResponse) -> dict[str, Any]:
        """
        Extract and parse the visual analysis dict from a Visual Agent response.
        """
        # 1) Try last text part
        try:
            parts_list = get_text_parts(response.root.result.parts)
            if parts_list:
                raw = parts_list[-1]
                return json.loads(raw)
        except Exception:
            pass

        # 2) Fallback to full message text
        try:
            raw = get_message_text(response.root.result)
            if raw and raw.strip():
                return json.loads(raw)
        except Exception:
            pass

        # 3) Log for diagnostics
        dump = self._dump_response_safe(response)
        logger.error(f"Failed to decode JSON from visual analysis response. Dump: {dump[:1200]}")
        raise ValueError("Invalid JSON in visual analysis response")

    async def send_message_to_code_agent(
        self,
        patterns: list | None,
        analysis_result: dict,
        custom_instructions: str = "",
    ) -> dict:
        """Send analysis_result + patterns to the Code Agent (UI image → code)."""
        msg_parts = [
            {"kind": "text", "metadata": {"type": "analysis_result"}, "text": self._safe_json(analysis_result or {})},
            {"kind": "text", "metadata": {"type": "patterns"}, "text": self._serialize_patterns(patterns or [])},
            {"kind": "text", "metadata": {"type": "custom_instructions"}, "text": custom_instructions or ""},
        ]

        payload = {
            "message": {
                "role": "user",
                "parts": msg_parts,
                "messageId": uuid4().hex,
            }
        }

        resp = await self._send_message_to_agent("code", payload)
        if self._validate_response(resp):
            text = get_message_text(resp.root.result)
            return json.loads(text) if text else {"error": "Empty response from Code Agent"}
        return {"error": "Invalid response from Code Agent"}

    async def send_prompt_to_code_agent(
        self,
        prompt_text: str,
        patterns: list | None = None,
        custom_instructions: str = "",
    ) -> dict:
        """Send a natural-language prompt (no visual analysis) to the Code Agent."""
        try:
            msg_parts = [
                {"kind": "text", "metadata": {"type": "prompt"}, "text": prompt_text or ""},
                {"kind": "text", "metadata": {"type": "patterns"}, "text": self._serialize_patterns(patterns or [])},
                {"kind": "text", "metadata": {"type": "custom_instructions"}, "text": custom_instructions or ""},
            ]

            payload = {
                "message": {
                    "role": "user",
                    "parts": msg_parts,
                    "messageId": uuid4().hex,
                }
            }
            payload = {
                "message": {
                    "role": "user",
                    "parts": msg_parts,
                    "messageId": uuid4().hex,
                }
            }

            resp = await self._send_message_to_agent("code", payload)

            # Try to validate response, catch exceptions
            try:
                if self._validate_response(resp):
                    text = get_message_text(resp.root.result)
                    if text:
                        return json.loads(text)
                    else:
                        return {"error": "Empty response from Code Agent"}
            except RuntimeError as e:
                logger.error(f"Code Agent response validation failed: {e}")
                return {"error": f"Code Agent response validation failed: {str(e)}"}

            return {"error": "Invalid response from Code Agent"}

        except Exception as e:
            logger.error(f"Error sending prompt to Code Agent: {e}", exc_info=True)
            return {"error": f"Failed to communicate with Code Agent: {str(e)}"}
    
    async def send_message_to_visual_agent(self, img_path: Path) -> dict[str, Any]:
        """Send an image to the Visual Agent and return the analysis result."""
        # Re-encode + downscale for latency and stability
        try:
            with Image.open(img_path) as im:
                im = im.convert("RGB")
                max_side = 1280
                w, h = im.size
                scale = min(1.0, max_side / max(w, h))
                if scale < 1.0:
                    im = im.resize((int(w * scale), int(h * scale)))
                buf = BytesIO()
                im.save(buf, format="JPEG", quality=85, optimize=True)
                base64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
                buf.close()
                mime = "image/jpeg"
        except Exception:
            with open(img_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png"

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "file",
                        "file": {
                            "name": img_path.name,
                            "mimeType": mime,
                            "bytes": base64_image,
                        },
                    },
                ],
                "messageId": uuid4().hex,
            },
        }

        response = await self._send_message_to_agent("visual", send_message_payload)
        if self._validate_response(response):
            analysis_result = self._get_analysis_result_from_response(response)
            return analysis_result
        else:
            dump = self._dump_response_safe(response)
            raise RuntimeError(f"Invalid response from Visual Agent. Dump: {dump[:1500]}")


    @staticmethod
    async def test_process() -> None:
        """Test function: visual → patterns → code, and prompt-only → code."""
        logger.info("Starting Orchestrator Agent test process")
        orchestrator = OrchestratorAgent(
            visual_url="http://localhost:10000",
            code_url="http://localhost:10001",
        )
        await orchestrator.initialize()
        rag_agent: RAGAgent = orchestrator.get_agent_client("rag")

        logger.info("Sending test message to Visual Agent...")
        image_uri = "E:/Documentos/Git Repositories/ui2code-rag/tests/test_image.png"
        with open(image_uri, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        send_message_payload_visual: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "file",
                        "file": {"name": "test_image.jpg", "mimeType": "image/jpeg", "bytes": base64_image},
                    },
                ],
                "messageId": uuid4().hex,
            },
        }
        response_visual: SendMessageResponse = await orchestrator._send_message_to_agent(
            "visual", send_message_payload_visual
        )
        logger.info("Received response from Visual Agent")
        logger.debug(response_visual.model_dump(mode="json", exclude_none=True))
        assert orchestrator._validate_response(response_visual)
        analysis_result: dict[str, Any] = orchestrator._get_analysis_result_from_response(response_visual)
        logger.debug(f"Extracted visual analysis: {analysis_result}")

        logger.info("Executing RAG Agent with visual analysis...")
        patterns: list[tuple] = rag_agent.invoke(analysis_result, top_k=5)
        logger.debug(f"RAG Agent retrieved patterns: {patterns}")

        custom_instructions = "Use dark theme with purple accents and hover effects."
        logger.info("Sending test message to Code Agent (visual+patterns)...")
        send_message_payload_code: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [
                    {"kind": "text", "metadata": {"type": "analysis_result"}, "text": json.dumps(analysis_result)},
                    {"kind": "text", "metadata": {"type": "patterns"}, "text": json.dumps(patterns)},
                    {"kind": "text", "metadata": {"type": "custom_instructions"}, "text": f"{custom_instructions}"},
                ],
                "messageId": uuid4().hex,
            },
        }
        response_code = await orchestrator._send_message_to_agent("code", send_message_payload_code)
        logger.info("Received response from Code Agent")
        logger.debug(response_code.model_dump(mode="json", exclude_none=True))
        assert orchestrator._validate_response(response_code)
        code_result = get_message_text(response_code.root.result)
        logger.info(f"Code Agent result: {code_result}")

        await orchestrator.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(OrchestratorAgent.test_process())
