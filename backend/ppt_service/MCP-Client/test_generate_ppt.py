import argparse
import asyncio
import sys
from pathlib import Path


def _load_backend_ai():
    backend_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(backend_dir))
    from ai_service.ai_pipeline import build_ppt_bundle

    return build_ppt_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="软件工程介绍")
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    build_ppt_bundle = _load_backend_ai()
    bundle = build_ppt_bundle(args.topic, stream=args.stream)
    plan = bundle["ppt_plan"].model_dump()

    client_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(client_dir))
    import client

    out_path = args.out or f"{args.topic}.pptx"
    out = asyncio.run(client.render_ppt_plan(plan, out_path))
    print(out)


if __name__ == "__main__":
    main()
