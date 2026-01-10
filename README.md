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

# Expose the server to the internet (requires ngrok token but free)
ssh {compute node}
cd ......
bash scripts/nibi_serve_example.sh
```

## Running the Agent
```bash
python main.py
```

## Related Projects
- [mcp-agent](https://github.com/lastmile-ai/mcp-agent)
- [arxiv-mcp](https://github.com/kelvingao/arxiv-mcp)

## TODO
- [ ] Fix stage 3 (parallel execution)
- [ ] Stage 4: Score papers
- [ ] Stage 5: Summarize papers
- [ ] Gather all results to output (categories + filtered papers list, selected top-k paper summaries)
- [ ] Email notification (put in main.py or add something between workflows and outputs/exporters?)
- [ ] Add Notion server
- [ ] Push results to Notion (same issue as above)
- [ ] ...