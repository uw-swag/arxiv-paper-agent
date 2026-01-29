# arxiv-paper-agent
A tool to crawl Arxiv new papers and summarize them. 

## Environment Setup
1. Install [uv](https://docs.astral.sh/uv/) if you haven't.
2. Create or update `.venv` and activate the Python virtual environment for this project:

```bash
uv sync --dev
source .venv/bin/activate
```

- See [cluster.md](cluster.md) for more details on how to setup the environment on Compute Canada.
- (Optional) Install Tesseract OCR for PDF to text conversion: [Installation Guide](https://tesseract-ocr.github.io/tessdoc/Installation.html)

## Prepare credentials for Gmail API
**If you want to use the Gmail API to send emails, you need to prepare the credentials.** See [Create access credentials](https://developers.google.com/workspace/guides/create-credentials) for more details. 

Copy the `credentials_example.json` file to the `src/axpa/outputs/exporters/` directory:

```bash
cp credentials_example.json src/axpa/outputs/exporters/credentials.json
```

Replace the example values with the actual values from the Google Cloud Console.

## User Configs
- User configs are stored in the `user_configs/` directory.
- You can create a new user config by copying the `example.yaml` file and modifying the contents. 
```bash
cp user_configs/example.yaml user_configs/your_username.yaml
``` 

## Running the agent
<u><b>(Option 1) Deploy the LLM and run the agent on a compute node: </b></u>
```bash
# 4 H100
sbatch scripts/deploy_minimax.sh
# 2 H100
sbatch scripts/deploy_gptoss.sh
```

<u><b>(Option 2) Run the agent directly by any public api service: </b></u>
You may follow [this guide](https://docs.mcp-agent.com/mcp-agent-sdk/core-components/configuring-your-application#model-providers) to configure the model providers in [mcp_agent.config.yaml](mcp_agent.config.yaml). 

To run the agent directly:
```bash
python main.py
# Run with a specific config file
python main.py --config user_configs/your_username.yaml
```

- (Optional) To expose the vLLM server to the internet, you can use ngrok by running the [ngrok_serve_example.sh](scripts/ngrok_serve_example.sh) script. See [ngrok](https://ngrok.com/docs) for more details.

## Running the Tests
```bash
uv run pytest
```

## Acknowledgments
- [mcp-agent](https://github.com/lastmile-ai/mcp-agent)
- [vLLM](https://github.com/vllm-project/vllm)
- [pymupdf](https://github.com/pymupdf/pymupdf)
- [arxiv-latex-mcp](https://github.com/takashiishida/arxiv-latex-mcp)
- [arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server)
- [pdf-reader-mcp](https://github.com/SylphxAI/pdf-reader-mcp)

## Future Work
- [ ] (Exporter) Add Notion server and push markdown results to Notion
- [ ] Additional features: customized summarization (combing current work with the past papers), force categorization settings...
- [ ] ...