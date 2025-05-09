'''Handles Speech-to-Text conversion using ElevenLabs API.'''

import os
import sys
from pathlib import Path
from typing import (
    Any,
    List,
    Optional,
)

from dotenv import load_dotenv
from elevenlabs import ElevenLabs


def transcribe_audio_elevenlabs(
    audio_file_path: Path,
    model_id: str = 'scribe_v1',
    language_code: str = 'uk',
) -> str:
    '''Transcribes an audio file using the ElevenLabs Speech-to-Text API.

    The API key is expected to be loaded into environment variables.

    Args:
        audio_file_path: The path to the audio file to transcribe.
        model_id: The ID of the model to use for transcription.
        language_code: The ISO-639-1 language code for the audio language.

    Returns:
        The transcribed text.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If the ELEVENLABS_API_KEY is not set in the environment.
        Exception: If the API call fails or the response format is unexpected.
    '''
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError(
            'ELEVENLABS_API_KEY not found in environment variables. ' \
            'Please ensure .env is loaded and the key is set.'
        )

    if not audio_file_path.exists():
        raise FileNotFoundError(f'Audio file not found: {audio_file_path}')

    client = ElevenLabs(api_key=api_key)

    with open(audio_file_path, 'rb') as audio_file_object:
        response = client.speech_to_text.convert(
            model_id=model_id,
            file_format='other',
            file=audio_file_object,
            language_code=language_code,
            tag_audio_events=False,
            diarize=False,
        )

    if hasattr(response, 'text'):
        return str(response.text)
    else:
        raise Exception(
            'Failed to get transcribed text. ' \
            'The response object does not have a "text" attribute.'
        )


def find_latest_audio_file(
    directory: Path,
    extensions: List[str],
) -> Optional[Path]:
    '''Finds the most recently modified audio file in a directory.

    Args:
        directory: The directory to search for audio files.
        extensions: A list of supported audio file extensions.

    Returns:
        The Path object of the latest audio file, or None if no suitable file is found.
    '''
    latest_file: Optional[Path] = None
    latest_mtime: float = 0

    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory '{directory}' not found or is not a directory.", file=sys.stderr)
        return None

    audio_files_found = []
    for f_name in os.listdir(directory):
        file_path = directory / f_name
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            audio_files_found.append(file_path)

    if not audio_files_found:
        print(f"No supported audio files found in '{directory}'. "
              f"Supported extensions: {', '.join(extensions)}", file=sys.stderr)
        return None

    for audio_file_path_candidate in audio_files_found:
        try:
            mtime = audio_file_path_candidate.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = audio_file_path_candidate
        except FileNotFoundError:
            print(f"Warning: File {audio_file_path_candidate} not found during stat, skipping.", file=sys.stderr)
            continue
    return latest_file


def transcribe_latest_audio_in_folder(
    folder_path: Path,
    supported_extensions: List[str],
) -> Optional[str]:
    '''Transcribes the latest audio file found in the given folder.

    Args:
        folder_path: The path to the folder containing audio files.
        supported_extensions: A list of supported audio file extensions.

    Returns:
        The transcribed text as a string, or None if no file is processed
        or an error occurs.
    '''
    latest_audio_file = find_latest_audio_file(folder_path, supported_extensions)

    if not latest_audio_file:
        # find_latest_audio_file already prints messages
        return None

    print(f"Found latest audio file: {latest_audio_file}")
    print(f"Attempting transcription of {latest_audio_file.name}...")

    try:
        transcribed_text = transcribe_audio_elevenlabs(
            audio_file_path=latest_audio_file,
        )
        return transcribed_text
    except FileNotFoundError as e:
        print(f'Error accessing file for transcription: {e}', file=sys.stderr)
    except ValueError as e:
        # API key issues from transcribe_audio_elevenlabs
        print(f'Configuration Error during transcription: {e}', file=sys.stderr)
    except Exception as e:
        print(f'An unexpected error occurred during transcription: {e}', file=sys.stderr)
    
    return None

# return transcribed text
def run_transcription_pipeline() -> str:
    '''Runs the full pipeline: find latest audio, transcribe, and print.

    Returns:
        Exit code (0 for success, 1 for failure).
    '''
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    speech_input_dir = project_root / 'speech_input'
    dotenv_path = project_root / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    supported_audio_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']

    if not os.getenv('ELEVENLABS_API_KEY'):
        print(
            'ELEVENLABS_API_KEY not found. ' \
            f'Please create a .env file in the project root ({dotenv_path})' \
            ' and add your key:',
            file=sys.stderr
        )
        print('ELEVENLABS_API_KEY=your_actual_api_key_here', file=sys.stderr)
        return 1

    transcribed_text = transcribe_latest_audio_in_folder(
        speech_input_dir,
        supported_audio_extensions
    )

    if transcribed_text is not None:
        print(f'\n--- Transcribed Text ---\n{transcribed_text}\n------------------------')
        return transcribed_text
    else:
        # Specific error messages are printed by transcribe_latest_audio_in_folder or find_latest_audio_file
        print(f"Transcription pipeline failed for folder: '{speech_input_dir}'", file=sys.stderr)
        return None


if __name__ == '__main__':
    transcribed_text = run_transcription_pipeline()
    if transcribed_text is not None:
        print(f'\n--- Transcribed Text ---\n{transcribed_text}\n------------------------')
    else:
        print("Transcription pipeline failed. No text was returned.", file=sys.stderr)
