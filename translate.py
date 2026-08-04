import pysrt
import os
import logging
from openai import OpenAI
from tqdm import tqdm

logger = logging.getLogger(__name__)

def translate_text(client, text, target_lang, model_name="gpt-3.5-turbo", context=""):
    system_prompt = "You are a professional subtitle translator."
    if context:
        system_prompt += f" For context, here is the previous translated segment:\n\n{context}\n\nMaintain character consistency and tone."
        
    prompt = f"Translate the following subtitle text to {target_lang}. Preserve the original formatting. Only output the translation, no conversational text.\n\nText:\n{text}"
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text

def translate_srt(srt_file, output_file, target_lang, api_key=None, base_url=None, model_name="gpt-3.5-turbo"):
    logger.info(f"Translating {srt_file} to {target_lang}...")
    
    # Initialize client
    client = OpenAI(
        api_key=api_key or os.environ.get("OPENAI_API_KEY", "dummy"),
        base_url=base_url
    )
    
    subs = pysrt.open(srt_file)
    
    # Batching could be more efficient, but doing it line by line is safer for formatting
    # For a real implementation, we would batch them to save API calls
    
    # Simple batching implementation
    batch_size = 10
    previous_translation = ""
    for i in tqdm(range(0, len(subs), batch_size), desc="Translating Subtitles"):
        batch = subs[i:i+batch_size]
        text_to_translate = "\n---\n".join([sub.text for sub in batch])
        translated = translate_text(client, text_to_translate, target_lang, model_name, previous_translation)
        
        # Save context for next batch (last 200 chars to save tokens)
        previous_translation = translated[-200:]
        
        # Split back
        translated_parts = translated.split("\n---\n")
        
        # If the number of parts matches, assign them. Otherwise, fallback to line-by-line for this batch
        if len(translated_parts) == len(batch):
            for j, sub in enumerate(batch):
                sub.text = translated_parts[j]
        else:
            for sub in batch:
                sub.text = translate_text(client, sub.text, target_lang, model_name, previous_translation)
                previous_translation = sub.text[-200:]
                
    subs.save(output_file, encoding='utf-8')
    logger.info(f"Saved translated subtitles to {output_file}")
    return output_file
