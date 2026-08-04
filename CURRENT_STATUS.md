# Current Status (MVP)

Translatarr is currently in an **MVP (Minimum Viable Product)** state. The core functionality is implemented and fully operational as a Dockerized web application.

## 🏗️ Architecture
- **Backend:** Python + FastAPI
- **Audio/Video Processing:** FFmpeg via `subprocess` and `ffmpeg-python`
- **Transcription:** OpenAI Whisper (CUDA GPU accelerated)
- **Translation:** OpenAI-compatible API (LLMs) via `openai` python package
- **TTS Engine:** Microsoft Edge TTS (`edge-tts`)
- **Web UI:** Jinja2 Templates + Bootstrap 5 (Responsive HTML/JS)

## ✅ Working Features
1. **Subtitle Extraction:** Automatically detects and extracts existing subtitles from MKV files.
2. **Audio Transcription:** If no subtitles exist, extracts audio and transcribes it to an SRT file using Whisper.
3. **LLM Translation:** Translates the parsed SRT file into any target language, maintaining time-codes using batch prompts.
4. **Audio Dubbing (TTS):** Generates translated audio segments matched precisely to subtitle timings, effectively dubbing the movie.
5. **Remuxing:** Combines original video, original audio, new translated subtitles, and the new dubbed audio track into a fresh MKV.
6. **Web Interface:** Users can queue jobs via a web interface running on port `8000`.
7. **Containerized:** Deploys easily with `docker compose` including NVIDIA GPU support.

## ⚠️ Known Limitations
- The job queue is currently **in-memory**. If the Docker container restarts, queued/running jobs will be lost.
- No database is implemented yet (e.g., SQLite), so there is no historical log of completed movies.
- Directory watching / automated library scanning (like Radarr/Sonarr) is not yet active. Users must manually paste file paths.
- LLM translation occurs in basic chunks. Context spanning across large chunks might occasionally lose nuance.
- TTS voice mapping is currently static (`es-ES-AlvaroNeural` default) and doesn't support dynamically identifying speakers to change voices.
