import pysrt
import os
import logging
from openai import OpenAI
from tqdm import tqdm

logger = logging.getLogger(__name__)

def translate_text(client, text, target_lang, model_name="gpt-3.5-turbo", previous_translation="", temperature=0.3, system_prompt_override=None):
    if not text.strip():
        return text

    sys_prompt = system_prompt_override if system_prompt_override else f"You are a professional movie subtitle translator. Translate the following subtitles into {target_lang}. Preserve the exact SRT timestamps, newlines, and structure. Only output the translated text. Do not add conversational text."
    
    if previous_translation:
        sys_prompt += f"\n\nFor context to help with pronoun resolution and tone, the previous lines were translated as: {previous_translation}"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text

def translate_srt(srt_file, output_file, target_lang, api_key=None, base_url=None, model_name="gpt-3.5-turbo", temperature=0.3, system_prompt_override=None):
    logger.info(f"Translating {srt_file} to {target_lang}...")
    
    # Initialize client
    client = OpenAI(
        api_key=api_key or os.environ.get("OPENAI_API_KEY", "dummy"),
        base_url=base_url if base_url else None
    )
    
    subs = pysrt.open(srt_file)
    
    # Simple batching implementation
    batch_size = 10
    previous_translation = ""
    for i in tqdm(range(0, len(subs), batch_size), desc="Translating Subtitles"):
        try:
            batch = subs[i:i+batch_size]
            logger.info(f"Translating batch {i+1}...")
            batch_text = "\n---\n".join([sub.text for sub in batch])
            translated = translate_text(client, batch_text, target_lang, model_name, previous_translation, temperature, system_prompt_override)
            previous_translation = translated[-200:]
            
            translated_parts = translated.split("\n---\n")
            
            # If the number of parts matches, assign them. Otherwise, fallback to line-by-line for this batch
            if len(translated_parts) == len(batch):
                for j, sub in enumerate(batch):
                    sub.text = translated_parts[j]
            else:
                for sub in batch:
                    sub.text = translate_text(client, sub.text, target_lang, model_name, previous_translation, temperature, system_prompt_override)
                    previous_translation = sub.text[-200:]
                    
        except Exception as e:
            logger.error(f"Translation failed for a chunk: {e}")
            # Fallback to appending original
            for sub in batch:
                sub.text = translate_text(client, sub.text, target_lang, model_name, previous_translation, temperature, system_prompt_override)
                previous_translation = sub.text[-200:]
                
    subs.save(output_file, encoding='utf-8')
    logger.info(f"Saved translated subtitles to {output_file}")
    return output_file
