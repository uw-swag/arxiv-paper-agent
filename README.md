# arxiv-paper-agent
Internal tool to crawl Arxiv new papers

## Environment Setup
1. Install [uv](https://docs.astral.sh/uv/) if you haven't.
2. Create or update `.venv` and activate the Python virtual environment for this project:

```bash
uv sync --dev
source .venv/bin/activate
```

## Managing Dependencies
- Add runtime dependencies: `uv add <package>` updates `pyproject.toml` and the lock file, then resyncs the environment.
- Add development-only tools: `uv add --dev <package>`
- Remove packages with `uv remove <package>` and rerun `uv sync`.

## Deploying the LLM
```bash
# 4 H100
sbatch scripts/deploy_minimax.sh
# 2 H100
sbatch scripts/deploy_gptoss.sh

# Optional: Expose the server to the internet (requires ngrok token but free)
ssh {compute node}
cd {project directory}
bash scripts/nibi_serve_example.sh
```

## Running the Agent
```bash
python main.py
```

## Related Projects
- [mcp-agent](https://github.com/lastmile-ai/mcp-agent)
- [arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server)
- [pdf-reader-mcp](https://github.com/SylphxAI/pdf-reader-mcp)

## TODO
- [ ] Stage 5: Summarize papers
- [ ] Additional features: customized summarization (combing current work with the paper), force categorization settings, configs...
- [ ] Gather all results to output (categories + filtered papers list, selected top-k paper summaries)
- [ ] (Exporter) file system mcp to structure and export the results to /outputs
- [ ] (Exporter) Email notification (put in main.py or add something between workflows and outputs/exporters?)
- [ ] (Exporter) Add Notion server and push results to Notion (same issue as above)
- [ ] ...