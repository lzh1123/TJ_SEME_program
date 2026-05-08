import argparse
import asyncio
import importlib.util
from pathlib import Path

from ai_service.ai_pipeline import build_ppt_bundle


def _load_ppt_client_module():
    client_path = Path(__file__).resolve().parent / "ppt_service" / "MCP-Client" / "client.py"
    spec = importlib.util.spec_from_file_location("ppt_mcp_client", client_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载 PPT Client：{client_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", type=str, help="用户输入需求/主题")
    parser.add_argument("--ppt-out", type=str, default=None, help="输出 PPTX 文件路径（指定后生成 PPT）")
    parser.add_argument("--stream", action="store_true", help="流式输出 DeepSeek 生成内容（只展示最终输出流，不展示模型内部推理）")
    args = parser.parse_args()

    bundle = build_ppt_bundle(args.topic, stream=args.stream)
    outline = bundle["outline"]
    plan = bundle["ppt_plan"]

    if not args.ppt_out:
        print(outline.model_dump_json(ensure_ascii=False, indent=2))
        return

    ppt_client = _load_ppt_client_module()
    out = asyncio.run(ppt_client.render_ppt_plan(plan.model_dump(), args.ppt_out))
    print(out)


if __name__ == "__main__":
    main()
