import os

# Suppress ONNX Runtime thread affinity errors on HPC clusters
os.environ["OMP_NUM_THREADS"] = "16"
os.environ["ORT_CPU_ONLY"] = "1"
os.environ["ONNXRUNTIME_DISABLE_SPINNING"] = "1"

import onnxruntime
onnxruntime.set_default_logger_severity(4)  # Only show fatal errors

import asyncio
import sys
from pathlib import Path

from axpa.configs import PipelineConfig
from axpa.pipeline import run_pipeline


def find_config_files(config_dir: str = "user_configs") -> list[Path]:
    """Find all YAML config files in the config directory."""
    config_path = Path(config_dir)
    if not config_path.exists():
        print(f"Config directory not found: {config_dir}")
        return []

    yaml_files = list(config_path.glob("*.yaml")) + list(config_path.glob("*.yml"))

    # Exclude example.yaml
    yaml_files = [f for f in yaml_files if f.name != "example.yaml"]

    return sorted(yaml_files)


async def process_config_file(config_path: Path) -> dict:
    """Process a single config file."""
    print(f"\n{'#'*70}")
    print(f"# Loading config: {config_path}")
    print(f"{'#'*70}\n")

    try:
        config = PipelineConfig.from_yaml(config_path)

        print(f"User: {config.user.user_name} ({config.user.user_email})")
        print(f"Queries: {len(config.orchestrator_configs)}")
        for i, oc in enumerate(config.orchestrator_configs, 1):
            print(f"  {i}. {oc.query} (top_k={oc.top_k}, limit={oc.search_limit})")

        result = await run_pipeline(config)

        return result

    except Exception as e:
        print(f"Error processing config {config_path}: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


async def main_async(config_files: list[Path] | None = None):
    """Main async entry point."""
    if config_files is None:
        config_files = find_config_files()

    if not config_files:
        print("No config files found in user_configs/")
        print("Please create a YAML config file (see user_configs/test.yaml for example)")
        return

    print(f"Found {len(config_files)} config file(s)")

    all_results = []
    for config_path in config_files:
        result = await process_config_file(config_path)
        all_results.append({
            "config": str(config_path),
            "result": result
        })

    print(f"\n{'='*70}")
    print("Pipeline Complete")
    print(f"{'='*70}")
    print(f"Processed {len(config_files)} config file(s)")

    return all_results


def main():
    """Main entry point."""
    # Check for specific config file argument
    config_files = None
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
        if config_path.exists():
            config_files = [config_path]
        else:
            print(f"Config file not found: {config_path}")
            sys.exit(1)

    asyncio.run(main_async(config_files))


if __name__ == "__main__":
    # FIXME: This is a hardcoded directory
    pdf_cache_dir = Path("./outputs/papers/pdf_cache")
    if not pdf_cache_dir.exists():
        pdf_cache_dir.mkdir(parents=True, exist_ok=True)

    main()
