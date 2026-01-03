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

## Related Projects
- [mcp-agent](https://github.com/lastmile-ai/mcp-agent)
- [arxiv-mcp](https://github.com/kelvingao/arxiv-mcp)

## TODO
- [ ] Collect related Subjects from Arxiv
- [ ] Build a LLM agent to crawl Arxiv new papers
- [ ] Build a LLM agent to summarize papers
- [ ] Build a LLM agent to push papers to notion
- [ ] Related works agent
- [ ] ...