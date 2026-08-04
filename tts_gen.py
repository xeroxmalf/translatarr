import asyncio
import edge_tts
import pysrt
import os
import logging
from pydub import AudioSegment
from pydub.utils import mediainfo

logger = logging.getLogger(__name__)

async def _generate_tts_for_sub(text, output_file, voice="en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def time_to_ms(t):
    return (t.hours * 3600 + t.minutes * 60 + t.seconds) * 1000 + t.milliseconds

def generate_audio_from_srt(srt_file, output_audio_file, video_file, default_voice="es-ES-AlvaroNeural"):
    logger.info(f"Generating TTS audio track from {srt_file}")
    subs = pysrt.open(srt_file)
    
    # Define a secondary voice to alternate for multiple speakers
    secondary_voice = "es-ES-ElviraNeural" if "es" in default_voice.lower() else "en-US-AriaNeural"
    
    # Get total video duration to make sure our audio track is long enough
    try:
        info = mediainfo(video_file)
        duration_str = info.get('duration')
        if not duration_str:
            duration_str = "0"
        duration_ms = int(float(duration_str) * 1000)
    except Exception as e:
        logger.warning(f"Could not get video duration, using subtitle end time. {e}")
        if subs:
            duration_ms = time_to_ms(subs[-1].end) + 5000
        else:
            duration_ms = 0
            
    # Create silent audio track
    base_audio = AudioSegment.silent(duration=duration_ms)
    
    # Generate TTS for each sub and overlay
    temp_dir = os.path.dirname(output_audio_file)
    
    for i, sub in enumerate(subs):
        text = sub.text.replace('\n', ' ')
        start_ms = time_to_ms(sub.start)
        
        # Simple Diarization Heuristic: Swap voice if line starts with '-' indicating a new speaker dialogue
        current_voice = default_voice
        if text.strip().startswith("-"):
            current_voice = secondary_voice
            text = text.lstrip("- ")
            
        tmp_mp3 = os.path.join(temp_dir, f"tmp_{i}.mp3")
        
        # Run async edge-tts
        try:
            asyncio.run(_generate_tts_for_sub(text, tmp_mp3, current_voice))
            if os.path.exists(tmp_mp3):
                sub_audio = AudioSegment.from_file(tmp_mp3)
                
                # Speed up if TTS is longer than subtitle duration
                sub_duration = time_to_ms(sub.end) - start_ms
                if len(sub_audio) > sub_duration:
                    speed_ratio = len(sub_audio) / sub_duration
                    # simple speedup using frame_rate hack
                    sub_audio = sub_audio.speedup(playback_speed=speed_ratio)
                    
                base_audio = base_audio.overlay(sub_audio, position=start_ms)
                os.remove(tmp_mp3)
        except Exception as e:
            logger.error(f"Failed to generate TTS for line {i}: {e}")
            
    base_audio.export(output_audio_file, format="wav")
    logger.info(f"Saved generated audio track to {output_audio_file}")
    return output_audio_file
