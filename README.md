# ⚾ Player Service

Player Service is a backend application that serves baseball player data. In addition, Player service integrates with [Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md), which allows us to run the [tinyllama LLM]((https://ollama.com/library/tinyllama)) locally.

## Dependencies

- Python3.9+
- sqllite3
- Docker
- [Ollama Python SDK](https://github.com/ollama/ollama-python)

## 🛠️ Setup Instructions

1. Verify system dependencies
   1. Python
      - Verify installation: `python3 --version`
   3. Container Manager
      - Download and install from [docker.com](https://www.docker.com/)(recommended) or [podman](https://podman.io/) (alternative)
      - Verify installation, run: `docker --version` for docker

2. Clone this repository or Download the code as zip
   - run `git clone https://github.com/Intuit-A4A/backend-python-player-service.git`

## Run the application

### Part 1: Application Dependencies

*OPTIONAL* Create & activate virtual env
```shell
   $ python3 -m venv env # use `python -m venv env` on Windows
   $ source env/bin/activate  # use `env\Scripts\activate` on Windows
```

1. Install application dependencies
    - Move into the application directory: `cd player-service-app`.
    - Create and activate a virtual environment (recommended on macOS/Linux with system Python):

    ```shell
    python3 -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

### Part 1b: Run tests

Tests do not require Docker or Ollama. From the repository root or from `player-service-app`:

```shell
cd player-service-app
pytest
```

### Part 2: Run Player Service (without LLM)

1. Start the Player service

   ```shell
    python3 app.py
   ```

2. Verify the Player service is running
      1. Open your browser and visit `http://localhost:8000/v1/players`
      2. If the application is running successfully, you will see player data appear in the browser

### Part 3: Start LLM Docker Container

Player service integrates with Ollama 🦙, which allows us to run LLMs locally. This app runs [tinyllama](https://ollama.com/library/tinyllama) model.

- [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Python SDK](https://github.com/ollama/ollama-python)

1. Pull and run Ollama docker image and download `tinyllama` model
   - Pull Ollama docker image

    ```shell
    docker pull ollama/ollama
    ```

2. Run Ollama docker image on port 11434 as a background process

    ```shell
    docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    ```

3. Download the `tinyllama` model (wait until the Ollama container is running)

    ```shell
    until docker exec ollama ollama list >/dev/null 2>&1; do sleep 2; done
    docker exec ollama ollama pull tinyllama
    ```

4. Confirm the model is available

    ```shell
    curl -s http://localhost:11434/api/tags | grep -i tinyllama
    ```

5. Test Ollama API server

    ```curl
    curl -v --location 'http://localhost:11434/api/generate' --header 'Content-Type: application/json' --data '{"model": "tinyllama","prompt": "why is the sky blue?", "stream": false}'
    ```

Having trouble with docker? Try using podman as an alternative. Instructions [here](https://github.com/Intuit-A4A/backend-python-player-service/wiki/Supplemental-Materials:-Set-up-help)

### Part 4: Verify Player Service and LLM Integration

1. Ensure Player Service is running

    ```shell
   python3 app.py
    ```

2. Open your browser and visit `http://localhost:8000/v1/chat/list-models`
   - If the application is running successfully, you will see a json response that include information about tinyllama
