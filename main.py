import asyncio
from axpa.workflows import run_arxiv_analysis_workflow


def main():
    asyncio.run(run_arxiv_analysis_workflow(
        query="Reinforcement enhanced LLM code generation",
        top_k=10,
        search_limit=500,
        output_format="markdown",
    ))


if __name__ == "__main__":
    main()
