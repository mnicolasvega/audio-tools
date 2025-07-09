from dotenv import load_dotenv
from pathlib import Path
from pydub import AudioSegment
import json
import math
import os
import os
import subprocess



load_dotenv()
OVERWRITE_TRACKS = False
OVERWRITE_MIX = False
CONFIG_DISPLAY_AT_END = True
CONFIG = {
    'path_album': os.getenv('ALBUM_DIR'),
    'song_file': os.getenv('SONG_FILE_NAME'),
    'bitrate': '320k',
    'model': os.getenv('MODEL'),
    'volume': {
        'drums': 1.0,
        'vocals': 0.3,
        'bass': 0.3,
        'other': 0.3,
    }
}



def create_dir_if_needed(dir: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok = True)
        print(f"created dir: '{dir}'")



def notify(title: str, content: str) -> None:
    print(f"  {title}")
    print(f"    {content}")



def get_demucs_output_dir(input_path: str) -> str:
    base_name = Path(input_path).stem
    output_folder = os.path.join("separated", CONFIG['model'], base_name)
    create_dir_if_needed(output_folder)
    return output_folder



def has_to_run_demucs(output_dir: str) -> bool:
    wav_files = sorted(
        f for f in os.listdir(output_dir) if f.endswith(".wav")
    )
    expected_track_names = CONFIG['volume'].keys()
    count_expected = len(expected_track_names)
    count_wavs = len(wav_files)
    return not count_expected == count_wavs



def run_demucs(input_mp3: str, output_dir: str) -> None:
    if has_to_run_demucs(output_dir):
        notify("demucs", f"splitting track: '{input_mp3}'")
        subprocess.run([
            "python3", "-m", "demucs", "-n", CONFIG['model'], input_mp3
        ])
    else:
        notify("demucs", f"skipping: .wav files already exist in '{output_dir}'")



def merge_tracks(input_dir: str, song_name: str, config: dict) -> None:
    mixed_track = None
    song_name = Path(song_name).stem
    tracks = {}
    db_label = ''
    for track_name in config.keys():
        input_file = f"{input_dir}/{track_name}.mp3"
        gain_percentage = config[track_name]
        gain_dB = 20 * math.log10(gain_percentage)
        db_str = f"%.1fdB" % (gain_dB)
        db_formatted = db_str.replace(".", ",")
        db_label = db_label + f" {track_name}_{db_formatted}"
        track = AudioSegment.from_mp3(input_file)
        track = track.apply_gain(gain_dB)
        tracks[track_name] = track
        mixed_track = track \
            if mixed_track is None else \
            mixed_track.overlay(track)
    output_file = f"{input_dir}/{song_name} {db_label}.mp3"
    if OVERWRITE_MIX or not os.path.exists(output_file):
        notify("mix", f"merging tracks into: '{output_file}'")
        mixed_track.export(
            output_file,
            format = "mp3",
            bitrate = CONFIG['bitrate']
        )
    else:
        notify("mix", f"skipping: merged file already exist '{output_file}'")



def convert_file(input_wav_file: str, output_dir: str) -> None:
    track_name = Path(input_wav_file).stem
    mp3_path = f"{output_dir}/{track_name}.mp3"
    if OVERWRITE_TRACKS or not os.path.exists(mp3_path):
        notify("conversion", f"converting to mp3: '{input_wav_file}'")
        audio = AudioSegment.from_wav(input_wav_file)
        audio.export(mp3_path, format = "mp3")
    else:
        notify("conversion", f"skipping: .mp3 already exists '{mp3_path}'")



def convert_files(input_dir: str, output_dir: str) -> None:
    input_files = sorted(
        f for f in os.listdir(input_dir) if f.endswith(".wav")
    )
    for input_file_name in input_files:
        input_file = f"{input_dir}/{input_file_name}"
        convert_file(input_file, output_dir)



def split_song(input_file: str, output_dir: str) -> None:
    print(f"input song: '{input_file}'")
    create_dir_if_needed(output_dir)
    demucs_output_dir = get_demucs_output_dir(input_file)
    run_demucs(input_file, demucs_output_dir)
    convert_files(demucs_output_dir, output_dir)
    volume = CONFIG['volume']
    song_name = Path(input_file).stem
    merge_tracks(output_dir, song_name, volume)



def split_album(album_dir: str) -> None:
    print(f"input album: '{album_dir}'")
    song_files = sorted(
        f for f in os.listdir(album_dir) if f.endswith(".mp3")
    )
    for song_file in song_files:
        song_name = Path(song_file).stem
        output_dir = f"{album_dir}/tracks/{song_name}"
        create_dir_if_needed(output_dir)
        song_file = f"{album_dir}/{song_file}"
        split_song(song_file, output_dir)



def display_config() -> None:
    formatted_json = json.dumps(
        CONFIG,
        indent = 4,
        ensure_ascii = False
    )
    print(formatted_json)



if __name__ == "__main__":
    album_dir = CONFIG['path_album']
    song_file = CONFIG['song_file']
    if song_file is None:
        split_album(album_dir)
    else:
        source = f"{album_dir}/{song_file}"
        song_name = Path(source).stem
        split_song(source, f"{album_dir}/tracks/{song_name}")
    if CONFIG_DISPLAY_AT_END:
        display_config()
