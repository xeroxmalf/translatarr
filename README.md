# Translatarr

An auto translation program for MKV movies.

Translatarr takes an MKV as input, extracts the audio and subtitle files, runs them through an AI/LLM based translation to a specified language, and remuxes the MKV back together with the translated subtitles.

## Features
- **Web UI & Job Queue:** Functions similarly to the "Arr" family (Radarr, Sonarr) where you can queue up movies for translation via a web interface.
- Automatically extracts existing subtitles from MKV files.
- If no subtitles exist, it uses [Whisper](https://github.com/openai/whisper) to transcribe the audio into an SRT file.
- Uses LLM (via OpenAI-compatible API) to accurately translate subtitles to any language.
- **Audio Generation:** Generates a dubbed audio track using Edge-TTS matching the exact timing of the subtitles.
- Preserves the original video and audio, remuxing the new subtitle track and dubbed audio track back into an MKV container.

## Requirements
- Python 3.8+
- `ffmpeg` installed on your system (`sudo apt install ffmpeg` or `brew install ffmpeg`)

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py input_video.mkv --lang "Spanish" --lang-code "spa" --api-key "YOUR_OPENAI_API_KEY"
```

### Options

- `--lang`: The target language for the LLM translation (e.g. "Spanish", "French", "Japanese")
- `--lang-code`: The 3-letter language code used for the MKV metadata (e.g. "spa", "fre", "jpn")
- `--output`: Custom output file name (defaults to `{original_name}_{lang_code}.mkv`)
- `--whisper-model`: Whisper model to use if transcribing audio (base, small, medium, large). Default is `base`.
- `--llm-model`: LLM model name (default: `gpt-3.5-turbo`)
- `--api-key`: API key for the LLM API.
- `--base-url`: Base URL for the LLM API, useful if you are using a local LLM via Ollama or vLLM.

## Local LLMs

You can use local LLMs (like Ollama) for translation by passing the base URL:
```bash
python main.py movie.mkv --lang "German" --lang-code "ger" --base-url "http://localhost:11434/v1" --llm-model "llama3" --api-key "dummy"
```

## Docker Usage (with Hardware Transcoding / GPU Support & Web UI)

Translatarr comes with a Dockerfile and docker-compose setup that utilizes NVIDIA GPUs for hardware-accelerated transcription (Whisper) and video processing (FFmpeg NVENC/CUVID), and provides a clean Web UI for managing tasks.

1. Ensure you have [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed.
2. Build the Docker image natively:
   ```bash
   docker compose build
   ```
   *(Alternatively, if published via CI/CD, you can pull the image from `ghcr.io`)*
3. Place your videos in a `movies` folder inside the project directory.
4. Run the container:
   ```bash
   OPENAI_API_KEY="your_api_key_here" docker compose up
   ```
5. Open your browser and navigate to `http://localhost:8000`.

From the Web UI, you can queue up `.mkv` files (e.g. `/movies/input.mkv`), select the target language, and choose whether to generate a dubbed audio track.

You can also run it via standard `docker run`:
```bash
docker run --gpus all -v $(pwd)/movies:/movies -e OPENAI_API_KEY="your_api_key_here" translatarr /movies/input.mkv --lang "French" --lang-code "fre" --output /movies/output.mkv
```
