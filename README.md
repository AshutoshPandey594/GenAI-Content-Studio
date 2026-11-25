# GenAI Content Studio

An AI-powered content generation web app built with **Python, Flask, Ollama, Qwen2.5, SQLite, HTML, CSS and JavaScript**. Enter a prompt, adjust creativity and output length, and generate text locally using a pretrained language model.

> This project runs an existing pretrained Qwen2.5 model through Ollama. It does not train a language model from scratch.

## Features

- Prompt-based text generation
- Quick-start prompt templates for learning, stories, roadmaps and brainstorming
- Adjustable creativity (temperature) and output length
- Local model inference through Ollama
- SQLite generation history with reload and delete options
- Copy generated output
- Backend health endpoint and input validation
- Responsive dark-themed interface

## Tech stack

- **Backend:** Python, Flask
- **AI runtime/model:** Ollama, Qwen2.5 1.5B
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download)

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/AshutoshPandey594/GenAI-Content-Studio.git
cd GenAI-Content-Studio
```

### 2. Download the model with Ollama

```bash
ollama pull qwen2.5:1.5b
```

Make sure Ollama is running before generating content.

### 3. Create a virtual environment and install dependencies

**Windows PowerShell**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure (optional)

Copy `.env.example` to `.env` and change values if needed:

- `OLLAMA_URL`: Ollama server URL (default `http://localhost:11434`)
- `OLLAMA_MODEL`: model tag (default `qwen2.5:1.5b`)
- `REQUEST_TIMEOUT`: model request timeout in seconds
- `PORT`: Flask port (default `5000`)

### 5. Start the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web interface |
| GET | `/api/health` | Check app and Ollama status |
| POST | `/api/generate` | Generate text from a prompt |
| GET | `/api/history` | Retrieve recent generations |
| DELETE | `/api/history/<id>` | Delete a saved generation |

### Example generation request

```json
{
  "prompt": "Explain machine learning with a real-world example.",
  "temperature": 0.7,
  "max_tokens": 300
}
```

## Project structure

```text
GenAI-Content-Studio/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
└── tests/
    └── test_app.py
```

## Run tests

After installing the dependencies:

```bash
python -m unittest discover -s tests -v
```

The generation test mocks the Ollama request; a running Ollama model is not required for that test.

## Notes

- The model must be downloaded locally and Ollama must be running for live generation.
- Generated content may be inaccurate; verify important information.
- The Flask development server is intended for local development and learning, not production deployment.
