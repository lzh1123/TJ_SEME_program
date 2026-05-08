import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _tool_result_payload(result) -> Dict[str, Any]:
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if not text:
            continue
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
        except Exception:
            continue
    return {}


@dataclass(frozen=True)
class McpServerConfig:
    server_script: Path
    python_executable: str = "python"


class PowerPointMCPClient:
    def __init__(self, config: McpServerConfig):
        self._config = config
        self._presentation_id: Optional[str] = None

    async def __aenter__(self):
        server_params = StdioServerParameters(
            command=self._config.python_executable,
            args=[str(self._config.server_script)],
            env={},
        )
        self._stdio_cm = stdio_client(server_params)
        self._read, self._write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(self._read, self._write)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session_cm.__aexit__(exc_type, exc, tb)
        await self._stdio_cm.__aexit__(exc_type, exc, tb)

    @property
    def session(self) -> ClientSession:
        return self._session

    @property
    def presentation_id(self) -> str:
        if not self._presentation_id:
            raise RuntimeError("presentation_id is not set, call create_presentation first")
        return self._presentation_id

    async def create_presentation(self, title: str) -> str:
        result = await self._session.call_tool("create_presentation", {})
        payload = _tool_result_payload(result)
        pres_id = payload.get("presentation_id")
        if not pres_id:
            raise RuntimeError(f"create_presentation failed: {payload}")
        self._presentation_id = pres_id

        await self._session.call_tool(
            "set_core_properties",
            {
                "title": title,
                "subject": title,
                "keywords": "AI, PPT, MCP",
                "presentation_id": pres_id,
            },
        )
        return pres_id

    async def apply_theme(self, color_scheme: str = "modern_blue"):
        await self._session.call_tool(
            "apply_professional_design",
            {
                "operation": "theme",
                "color_scheme": color_scheme,
                "apply_to_existing": True,
                "presentation_id": self.presentation_id,
            },
        )

    async def create_from_templates(self, template_sequence: list, color_scheme: str, title: str):
        result = await self._session.call_tool(
            "create_presentation_from_templates",
            {
                "template_sequence": template_sequence,
                "color_scheme": color_scheme,
                "presentation_title": title,
                "presentation_id": self.presentation_id,
            },
        )
        payload = _tool_result_payload(result)
        if payload.get("error"):
            raise RuntimeError(f"create_presentation_from_templates failed: {payload}")
        return payload

    async def add_chart(self, spec: Dict[str, Any]):
        call = {
            "presentation_id": self.presentation_id,
            **spec,
        }
        result = await self._session.call_tool("add_chart", call)
        payload = _tool_result_payload(result)
        if payload.get("error"):
            raise RuntimeError(f"add_chart failed: {payload}")
        return payload

    async def optimize_slide_text(self, slide_index: int):
        result = await self._session.call_tool(
            "optimize_slide_text",
            {
                "slide_index": slide_index,
                "auto_resize": True,
                "auto_wrap": True,
                "optimize_spacing": True,
                "min_font_size": 10,
                "max_font_size": 40,
                "presentation_id": self.presentation_id,
            },
        )
        payload = _tool_result_payload(result)
        if payload.get("error"):
            raise RuntimeError(f"optimize_slide_text failed: {payload}")
        return payload

    async def enhance_slide(self, slide_index: int, color_scheme: str):
        result = await self._session.call_tool(
            "apply_professional_design",
            {
                "operation": "enhance",
                "slide_index": slide_index,
                "color_scheme": color_scheme,
                "enhance_title": True,
                "enhance_content": True,
                "enhance_shapes": True,
                "enhance_charts": True,
                "presentation_id": self.presentation_id,
            },
        )
        payload = _tool_result_payload(result)
        if payload.get("error"):
            raise RuntimeError(f"enhance_slide failed: {payload}")
        return payload

    async def get_presentation_info(self) -> Dict[str, Any]:
        result = await self._session.call_tool(
            "get_presentation_info",
            {"presentation_id": self.presentation_id},
        )
        return _tool_result_payload(result)

    async def save(self, output_path: str) -> str:
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        result = await self._session.call_tool(
            "save_presentation",
            {
                "file_path": str(output),
                "presentation_id": self.presentation_id,
            },
        )
        payload = _tool_result_payload(result)
        if payload.get("error"):
            raise RuntimeError(f"save_presentation failed: {payload}")
        return str(output)


async def render_ppt_plan(plan: Dict[str, Any], output_path: str) -> str:
    backend_dir = Path(__file__).resolve().parents[2]
    server_script = backend_dir / "ppt_service" / "Office-PowerPoint-MCP-Server" / "ppt_mcp_server.py"

    async with PowerPointMCPClient(McpServerConfig(server_script=server_script)) as client:
        await client.create_presentation(plan["title"])
        await client.create_from_templates(
            template_sequence=plan.get("template_sequence", []),
            color_scheme=plan.get("color_scheme", "modern_blue"),
            title=plan["title"],
        )
        await client.apply_theme(plan.get("color_scheme", "modern_blue"))

        info = await client.get_presentation_info()
        slide_count = int(info.get("slide_count", 0) or 0)

        for chart in plan.get("charts", []) or []:
            await client.add_chart(chart)

        if plan.get("optimize_text", True):
            for i in range(slide_count):
                await client.optimize_slide_text(i)

        if plan.get("enhance_slides", True):
            for i in range(slide_count):
                await client.enhance_slide(i, plan.get("color_scheme", "modern_blue"))

        return await client.save(output_path)


def _load_backend_ai_service():
    backend_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(backend_dir))
    from ai_service.ai_pipeline import build_ppt_bundle

    return build_ppt_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="软件工程介绍")
    parser.add_argument("--out", type=str, default="backend/output/软件工程介绍_ai.pptx")
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    build_ppt_bundle = _load_backend_ai_service()
    bundle = build_ppt_bundle(args.topic, stream=args.stream)
    plan = bundle["ppt_plan"].model_dump()
    out = asyncio.run(render_ppt_plan(plan, args.out))
    print(out)


if __name__ == "__main__":
    main()
