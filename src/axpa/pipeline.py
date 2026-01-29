from axpa.workflows import run_arxiv_analysis_workflow
from axpa.configs import PipelineConfig
from axpa.outputs.data_models import WorkflowResult
from axpa.outputs.exporters.exporter_dispatcher import ExporterDispatcher
from axpa.outputs.formatters import load_formatter


async def run_pipeline(config: PipelineConfig) -> dict:
    """
    Run the complete pipeline for all queries in the config.

    This function:
    1. Processes each orchestrator config sequentially
    2. Collects results from all queries
    3. Aggregates all results together
    4. Exports once using user-level exporters (one email with all queries combined)

    Args:
        config: PipelineConfig containing user info and list of orchestrator configs

    Returns:
        Dict containing aggregated results and export statuses
    """
    all_results: list[WorkflowResult] = []
    export_statuses: list[dict] = []

    # Process each query
    for orchestrator_config in config.orchestrator_configs:
        print(f"\n{'='*60}")
        print(f"Processing query: {orchestrator_config.query}")
        print(f"{'='*60}\n")

        try:
            result = await run_arxiv_analysis_workflow(orchestrator_config, config.additional_html_formatting)
            all_results.append(result)

            print(f"\nCompleted query: {orchestrator_config.query}")
            print(f"  - Total papers: {result.total_papers}")
            print(f"  - Filtered papers: {result.filtered_papers}")
            print(f"  - Accepted papers: {result.accepted_papers}")
            print(f"  - Summaries generated: {len(result.summaries)}")

        except Exception as e:
            print(f"\nError processing query '{orchestrator_config.query}': {e}")
            continue

    # Export results using user-level exporters (once for all queries combined)
    dispatcher = ExporterDispatcher()

    for exporter_cfg in config.user.summary_exporters:
        try:
            # Determine destination based on export type
            if exporter_cfg.destination == "email":
                destination = config.user.user_email
            # elif exporter_cfg.destination == "notion":
            else:
                # For local, use a generic filename
                destination = config.user.user_name

            formatter = load_formatter(exporter_cfg.format)
            content = formatter.prepare_all(config.user.user_name, exporter_cfg.summary_type, all_results)

            status = await dispatcher.export(
                content=content,
                destination=destination,
                export_destination=exporter_cfg.destination,
                export_format=exporter_cfg.format,
            )
            export_statuses.append({
                "exporter": f"{exporter_cfg.destination}:{exporter_cfg.format}",
                **status
            })

            print(f"\nExport [{exporter_cfg.destination}:{exporter_cfg.format}]: {status.get('message', status.get('status'))}")

        except Exception as e:
            export_statuses.append({
                "exporter": f"{exporter_cfg.destination}:{exporter_cfg.format}",
                "status": "error",
                "message": str(e)
            })
            print(f"\nExport error [{exporter_cfg.destination}:{exporter_cfg.format}]: {e}")

    return {
        "results": all_results,
        "export_statuses": export_statuses,
    }
