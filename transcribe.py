import whisper
import os
import logging

logger = logging.getLogger(__name__)

def transcribe_audio(audio_file, output_dir, model_name="base"):
    logger.info(f"Loading whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    logger.info(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file)
    
    # Write to SRT
    output_srt = os.path.join(output_dir, "transcribed.srt")
    
    def format_timestamp(seconds: float):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result.get("segments", [])):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            f.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")
            
    logger.info(f"Saved transcription to {output_srt}")
    return output_srt
