import argparse
import os
import tempfile
import logging
import shutil
from media import extract_audio, extract_subtitles, remux_video
from transcribe import transcribe_audio
from translate import translate_srt
from tts_gen import generate_audio_from_srt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Translatarr: Auto translate MKV movies")
    parser.add_argument("input", help="Input MKV file")
    parser.add_argument("--lang", default="Spanish", help="Target language for translation")
    parser.add_argument("--lang-code", default="spa", help="Target language code (e.g. spa, fre)")
    parser.add_argument("--output", help="Output MKV file (default: original_name_translated.mkv)")
    parser.add_argument("--whisper-model", default="base", help="Whisper model to use (base, small, medium, large)")
    parser.add_argument("--llm-model", default="gpt-3.5-turbo", help="LLM model name")
    parser.add_argument("--api-key", help="API key for LLM")
    parser.add_argument("--base-url", help="Base URL for LLM API (e.g. for Ollama)")
    parser.add_argument("--generate-audio", action="store_true", help="Generate dubbed audio track using TTS")
    parser.add_argument("--replace-original", action="store_true", help="Replace original file with output file")
    parser.add_argument("--voice", default="es-ES-AlvaroNeural", help="Voice for TTS (edge-tts voice format)")
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.input):
        logger.error(f"Input file not found: {args.input}")
        return

    output_file = args.output
    if not output_file:
        base, ext = os.path.splitext(args.input)
        output_file = f"{base}_{args.lang_code}{ext}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Try to extract existing subtitles
        subs = extract_subtitles(args.input, tmpdir)
        
        srt_to_translate = None
        
        if subs:
            logger.info("Found existing subtitles in the video. Using the first one for translation.")
            srt_to_translate = subs[0]['file']
        else:
            logger.info("No subtitles found. Extracting audio and transcribing...")
            audio_file = os.path.join(tmpdir, "audio.wav")
            extract_audio(args.input, audio_file)
            srt_to_translate = transcribe_audio(audio_file, tmpdir, args.whisper_model)
            
        # Step 2: Translate the subtitles
        translated_srt = os.path.join(tmpdir, f"translated_{args.lang_code}.srt")
        translate_srt(
            srt_file=srt_to_translate,
            output_file=translated_srt,
            target_lang=args.lang,
            api_key=args.api_key,
            base_url=args.base_url,
            model_name=args.llm_model
        )
        
        # Step 3: Generate Audio (Optional)
        new_audio_file = None
        if args.generate_audio:
            logger.info("Generating dubbed audio track...")
            new_audio_file = os.path.join(tmpdir, "dubbed.wav")
            generate_audio_from_srt(translated_srt, new_audio_file, args.input, args.voice)
        
        # Step 4: Remux back to MKV
        remux_video(args.input, translated_srt, output_file, args.lang_code, new_audio_file)
        
    if args.replace_original and output_file != args.input:
        logger.info(f"Replacing original file {args.input} with {output_file}")
        shutil.move(output_file, args.input)
        output_file = args.input
        
    logger.info(f"Done! Output saved to {output_file}")

if __name__ == "__main__":
    main()
