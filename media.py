import os
import subprocess
import json
import tempfile
import logging

logger = logging.getLogger(__name__)

def get_media_info(input_file):
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(result.stdout)

def extract_audio(input_file, output_audio_file):
    logger.info(f"Extracting audio from {input_file} to {output_audio_file}")
    # Extract only the first audio stream to prevent issues with multi-audio MKVs
    cmd = ['ffmpeg', '-y', '-i', input_file, '-q:a', '0', '-map', '0:a:0', output_audio_file]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_audio_file

def extract_subtitles(input_file, output_dir):
    logger.info(f"Checking for existing subtitles in {input_file}")
    info = get_media_info(input_file)
    subs = []
    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'subtitle':
            index = stream['index']
            lang = stream.get('tags', {}).get('language', f'track_{index}')
            ext = 'srt' # default to srt extraction
            # if stream['codec_name'] in ['ass', 'ssa']:
            #     ext = 'ass'
            out_file = os.path.join(output_dir, f"sub_{index}_{lang}.{ext}")
            cmd = ['ffmpeg', '-y', '-i', input_file, '-map', f'0:{index}', out_file]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            subs.append({'index': index, 'lang': lang, 'file': out_file})
    return subs

def remux_video(input_file, new_srt_file, output_file, lang_code="eng", new_audio_file=None):
    logger.info(f"Remuxing video with new tracks into {output_file}")
    
    if new_audio_file:
        cmd_all = [
            'ffmpeg', '-y', '-i', input_file, '-i', new_audio_file, '-i', new_srt_file,
            '-map', '0', '-map', '1:0', '-map', '2:0',
            '-c', 'copy',
            '-c:a:last', 'aac', '-b:a:last', '192k', # Encode TTS wav to aac
            '-metadata:s:a:last', f'language={lang_code}',
            '-metadata:s:a:last', f'title=Dubbed ({lang_code})',
            '-c:s:last', 'srt',
            '-metadata:s:s:last', f'language={lang_code}',
            '-metadata:s:s:last', f'title=Translated ({lang_code})',
            output_file
        ]
    else:
        cmd_all = [
            'ffmpeg', '-y', '-i', input_file, '-i', new_srt_file,
            '-map', '0', '-map', '1:0',
            '-c', 'copy',
            '-c:s:last', 'srt',
            '-metadata:s:s:last', f'language={lang_code}',
            '-metadata:s:s:last', f'title=Translated ({lang_code})',
            output_file
        ]

    subprocess.run(cmd_all, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_file
