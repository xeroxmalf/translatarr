<div align="center">
  
# 🎬 Translatarr

[![CI/CD](https://github.com/xeroxmalf/translatarr/actions/workflows/ci.yml/badge.svg)](https://github.com/xeroxmalf/translatarr/actions/workflows/ci.yml)
[![Docker Release](https://github.com/xeroxmalf/translatarr/actions/workflows/cd.yml/badge.svg)](https://github.com/xeroxmalf/translatarr/actions/workflows/cd.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The Missing "Arr" Application for Automated AI Movie Translation and Dubbing**

</div>

---

## 📖 What is Translatarr?

Translatarr fits right alongside your Radarr, Sonarr, and Lidarr stack. It is an automated pipeline that takes MKV movie files, extracts their audio and subtitles, dynamically translates the text using LLMs (Large Language Models), generates entirely new AI-dubbed audio tracks, and remuxes everything back into a perfect MKV container.

Whether you want to translate a foreign film into your native language with highly accurate subtitles, or fully auto-dub an anime using cutting-edge neural TTS voices, Translatarr handles it seamlessly in the background.

## ✨ Core Features

* **🕸️ Premium Web UI**: A beautiful, dark-mode, glassmorphic Web UI to view your job queue, manage history, and configure AI settings.
* **🧠 Context-Aware LLM Translation**: Uses OpenAI-compatible endpoints (GPT-4, Claude, or local Ollama) to translate subtitles. It passes rolling 200-character context windows to the LLM to ensure pronouns and character tones remain consistent across subtitle boundaries!
* **🎙️ AI Voice Dubbing (TTS)**: Leverages `edge-tts` to generate neural voice tracks perfectly timed to the video's original subtitle timestamps.
* **🎥 Hardware Acceleration**: Fully supports NVIDIA CUDA GPUs for blazing-fast `openai-whisper` transcription and FFmpeg stream multiplexing.
* **📂 Watchdog Auto-Importing**: Just drop an `.mkv` into the mapped `/movies` directory. Translatarr will automatically wait for the network transfer to finish, then queue it using your default translation settings.
* **🔗 Sonarr & Radarr Webhooks**: Exposes a REST API (`POST /api/webhook`) that parses standard *Arr JSON payloads. When Radarr downloads a movie, it can trigger Translatarr to instantly dub it!
* **🎛️ Ultimate Control**: Easily override the LLM Temperature and inject Custom System Prompts (e.g., *"Translate this to English, but make the characters speak like pirates"*).

---

## 🚀 Getting Started (Docker Compose)

The easiest and most robust way to run Translatarr is via Docker Compose.

1. Ensure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on your host if you plan to use GPU acceleration for Whisper.
2. Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  translatarr:
    image: ghcr.io/xeroxmalf/translatarr:latest
    container_name: translatarr
    ports:
      - "8000:8000"
    volumes:
      - ./movies:/movies
      - ./translatarr.db:/app/translatarr.db
    environment:
      - OPENAI_API_KEY=your_default_api_key  # Optional, can be set in Web UI
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

3. Spin up the container:
```bash
docker compose up -d
```

4. Navigate to `http://localhost:8000` in your web browser!

> **Note:** If you do not have an NVIDIA GPU, you can remove the `deploy` block from the docker-compose file. Translatarr will automatically fall back to CPU processing, though Whisper transcription will be significantly slower.

---

## ⚙️ Radarr / Sonarr Webhook Integration

Translatarr can be integrated directly into your existing automation stack. 

In Radarr or Sonarr:
1. Go to **Settings > Connect > + Add > Webhook**.
2. Name: `Translatarr`
3. On Grab: `No`
4. On Import / On Upgrade: `Yes`
5. URL: `http://<translatarr-ip>:8000/api/webhook`
6. Method: `POST`

Translatarr will intercept the JSON payload, locate the downloaded MKV file on the shared filesystem, and immediately queue it using the "Auto-Import Defaults" configured in the Translatarr Settings page!

---

## 💻 Manual CLI Usage

If you prefer to run Translatarr natively without the Web UI daemon, you can trigger the pipeline directly via the Python CLI.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Basic Subtitle Translation
python main.py /path/to/movie.mkv --lang "Spanish" --lang-code "spa" --api-key "sk-..."

# Full Neural Audio Dubbing & Subtitle Translation, Overwriting the Original File
python main.py /path/to/movie.mkv --lang "French" --lang-code "fre" --generate-audio --voice "fr-FR-HenriNeural" --replace-original
```

### CLI Arguments
* `--lang`: Target language name for the AI to understand (e.g., `"Japanese"`).
* `--lang-code`: 3-letter ISO code for MKV metadata tracks (e.g., `"jpn"`).
* `--api-key`: Your OpenAI (or alternative provider) API key.
* `--base-url`: Custom endpoint URL (e.g., `http://localhost:11434/v1` for Ollama).
* `--llm-model`: The model to use (default: `gpt-3.5-turbo`, or `llama3` for local).
* `--temperature`: Adjust LLM creativity/strictness (default: `0.3`).
* `--system-prompt`: Override the default AI behavior instructions.
* `--generate-audio`: Triggers the TTS engine to dub the translated text.
* `--voice`: The edge-tts voice mapping to use.
* `--replace-original`: Overwrites the input MKV instead of generating a copy.

---

## 🧠 How the Pipeline Works

Under the hood, Translatarr executes a highly resilient 5-step pipeline:

1. **Extraction**: `ffprobe` analyzes the MKV. If subtitle tracks exist, it extracts them via `ffmpeg`. If no subtitles exist, it rips the default audio track to a temporary `.wav`.
2. **Transcription**: If audio was ripped, `openai-whisper` processes the `.wav` file (accelerated via CUDA) and generates a perfectly timed `.srt` transcript.
3. **Translation**: The `.srt` file is batched and streamed to the LLM. The AI translates the dialogue while receiving a rolling memory context of the previous lines to maintain grammatical consistency and tone.
4. **Dubbing (Optional)**: `edge-tts` analyzes the translated `.srt`. It generates audio snippets for every line, optionally using syntax heuristics (like `-` dialogue markers) to swap voices dynamically, then speed-syncs and overlays them into a master audio track.
5. **Multiplexing**: `ffmpeg` takes the original video, the original audio, the new translated `.srt`, and the new dubbed audio track, and remuxes them into a finalized `.mkv` container with correct metadata tagging!

---

## 🛠️ Tech Stack
* **Backend**: FastAPI, Python 3.10+, SQLAlchemy (SQLite)
* **Job Queue**: APScheduler (Background Threads)
* **Frontend**: HTML5, Jinja2, Custom Glassmorphic CSS
* **Media Processing**: FFmpeg, Whisper, PyDub, Edge-TTS

## 📝 License
MIT License. Feel free to fork, modify, and integrate!
