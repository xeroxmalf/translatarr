# Translatarr Roadmap

This document outlines the planned future enhancements and architectural shifts to make Translatarr a full-fledged member of the "Arr" application ecosystem.

## Phase 1: Persistence & Stability (Near Term)
- [ ] **Database Integration:** Replace the in-memory job array with a SQLite database using SQLAlchemy.
- [ ] **Job Queue Persistence:** Use Celery or APScheduler to persist tasks across container restarts.
- [ ] **Settings UI:** Add a settings page to configure API keys, default languages, and preferred LLM models directly from the web interface instead of relying on environment variables.

## Phase 2: True "Arr" Functionality (Mid Term)
- [ ] **Directory Watching:** Implement a filesystem watcher (e.g., `watchdog`) to automatically detect new MKVs dropped into specific folders and auto-queue them.
- [ ] **Media Library View:** Add a library page showing all processed movies with their available subtitle/audio tracks and metadata.
- [ ] **API Integrations:** Expose RESTful endpoints so tools like Radarr or Sonarr can trigger Translatarr via webhooks on download completion.
- [ ] **Multi-File Support:** Support batch uploading or scanning of entire directories (e.g., TV show seasons).

## Phase 3: Advanced Audio & AI (Long Term)
- [ ] **Speaker Diarization:** Use Pyannote.audio or WhisperX to detect different speakers in the movie.
- [ ] **Multi-Voice TTS:** Map different detected speakers to different TTS voices so the generated dub has a diverse cast instead of a single narrator voice.
- [ ] **Voice Cloning (Optional):** Integrate with ElevenLabs or Coqui XTTS to clone original actors' voices and generate the dubbed audio in their exact tone.
- [ ] **Advanced LLM Context:** Pass previous subtitle chunks as context to the LLM to maintain consistent name translations, slang, and pronouns throughout the movie.
- [ ] **Hardcode Subtitle Support:** Implement OCR to read hardcoded subtitles if no subtitle track is available.
