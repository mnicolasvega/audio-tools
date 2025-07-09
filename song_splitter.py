from dotenv import load_dotenv
from pathlib import Path
from pydub import AudioSegment
import math
import os
import os
import subprocess



load_dotenv()
OVERWRITE_TRACKS = False
CONFIG = {
    'path_album': os.getenv('ALBUM_DIR'),
    'song_file': os.getenv('SONG_FILE_NAME'),
    'bitrate': '320k',
    'model': os.getenv('MODEL'),
    'volume': {
        'drums': 1.1,
        'vocals': 0.3,
        'bass': 0.3,
        'other': 0.3,
    }
}



def run_demucs(input_mp3: str) -> None:
    print("running demucs:")
    subprocess.run([
        "python3", "-m", "demucs", "-n", CONFIG['model'], input_mp3
    ])



def unify_tracks(input_dir: str, config: dict) -> None:
    mixed_track = None
    song_name = Path(CONFIG['song_file']).stem
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
    mixed_track.export(
        output_file,
        format = "mp3",
        bitrate = CONFIG['bitrate']
    )
    print(f"mix finished: '{output_file}'")



def get_demucs_output_dir(input_path: str) -> str:
    base_name = Path(input_path).stem
    output_folder = os.path.join("separated", CONFIG['model'], base_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok = True)
        print(f"error: demucs output folder not found: '{output_folder}'")
        print( "  -> creating it")
    return output_folder



def convert_file(input_wav_file: str, output_dir: str) -> None:
    track_name = Path(input_wav_file).stem
    mp3_path = f"{output_dir}/{track_name}.mp3"
    if not OVERWRITE_TRACKS and os.path.exists(mp3_path):
        print(f"skipping: .mp3 already exists '{mp3_path}'")
        return
    print(f"converting to mp3: '{input_wav_file}'")
    audio = AudioSegment.from_wav(input_wav_file)
    audio.export(mp3_path, format = "mp3")



def convert_files(input_dir: str, output_dir: str) -> None:
    input_files = sorted(
        f for f in os.listdir(input_dir) if f.endswith(".wav")
    )
    for input_file_name in input_files:
        input_file = f"{input_dir}/{input_file_name}"
        convert_file(input_file, output_dir)



def split_song(input_file: str, output_dir: str) -> None:
    print(f"input song: '{input_file}'")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok = True)
    run_demucs(input_file)
    output_demucs = get_demucs_output_dir(input_file)
    convert_files(output_demucs, output_dir)
    volume = CONFIG['volume']
    unify_tracks(output_dir, volume)



def split_album(album_dir: str) -> None:
    print(f"input album: '{album_dir}'")
    song_files = sorted(
        f for f in os.listdir(album_dir) if f.endswith(".mp3")
    )
    for song_file in song_files:
        song_name = Path(song_file).stem
        output_dir = f"{album_dir}/tracks/{song_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok = True)
        song_file = f"{album_dir}/{song_file}"
        split_song(song_file, output_dir)




if __name__ == "__main__":
    album_dir = CONFIG['path_album']
    song_file = CONFIG['song_file']
    if song_file is None:
        split_album(album_dir)
    else:
        source = f"{album_dir}/{song_file}"
        song_name = Path(source).stem
        split_song(source, f"{album_dir}/tracks/{song_name}")
    print(CONFIG)
