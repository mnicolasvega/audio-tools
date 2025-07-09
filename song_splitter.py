from dotenv import load_dotenv
from pathlib import Path
from pydub import AudioSegment
import os
import os
import subprocess



load_dotenv()
ALBUM_DIR = os.getenv('ALBUM_DIR')
SONG_FILE = os.getenv('SONG_FILE')
MODEL = os.getenv('MODEL')
BITRATE = "320k"
VOLUME_DB = {
    'drums': -6,
    'vocals': -6,
    'bass': -6,
    'other': -6,
}



def run_demucs(input_mp3: str) -> None:
    print("running demucs:")
    subprocess.run([
        "python3", "-m", "demucs", "-n", MODEL, input_mp3
    ])



def unify_tracks(input_dir: str, output_file: str, config: dict) -> None:
    # load tracks
    track_vocals = AudioSegment.from_mp3(f"{input_dir}/vocals.mp3")
    track_drums = AudioSegment.from_mp3(f"{input_dir}/drums.mp3")
    track_bass = AudioSegment.from_mp3(f"{input_dir}/bass.mp3")
    track_other = AudioSegment.from_mp3(f"{input_dir}/other.mp3")

    # normalize lenghts
    min_len = min(len(track_vocals), len(track_drums), len(track_bass), len(track_other))
    track_vocals = track_vocals[:min_len]
    track_drums = track_drums[:min_len]
    track_bass = track_bass[:min_len]
    track_other = track_other[:min_len]

    # adjust volume:
    #  100% ( 0 dB)
    #   50% (-6 dB)
    track_drums = track_drums.apply_gain(config['drums'])
    track_vocals = track_vocals.apply_gain(config['vocals'])
    track_bass = track_bass.apply_gain(config['bass'])
    track_other = track_other.apply_gain(config['other'])

    track_mix = track_drums \
        .overlay(track_vocals) \
        .overlay(track_bass) \
        .overlay(track_other)
    track_mix.export(
        output_file,
        format = "mp3",
        bitrate = BITRATE
    )
    print(f"mix finished: '{output_file}'")



def get_demucs_output_dir(input_path: str) -> str:
    base_name = Path(input_path).stem
    output_folder = os.path.join("separated", MODEL, base_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok = True)
        print(f"error: demucs output folder not found: '{output_folder}'")
        print( "  -> creating it")
    return output_folder



def convert_file(input_wav_file: str, output_dir: str) -> None:
    if not input_wav_file.endswith(".wav"):
        print(f"skipping: .wav not found '{input_wav_file}'")
        return
    track_name = Path(input_wav_file).stem
    mp3_path = f"{output_dir}/{track_name}.mp3"
    if os.path.exists(mp3_path):
        print(f"skipping: .mp3 already exists '{mp3_path}'")
        return
    print(f"converting to mp3: '{input_wav_file}'")
    audio = AudioSegment.from_wav(input_wav_file)
    audio.export(mp3_path, format = "mp3")



def convert_files(input_dir: str, output_dir: str) -> None:
    for input_file_name in os.listdir(input_dir):
        input_file = f"{input_dir}/{input_file_name}"
        convert_file(input_file, output_dir)



def split_song(input_file: str, output_dir: str) -> None:
    print(f"input song: '{input_file}'")
    run_demucs(input_file)
    output_demucs = get_demucs_output_dir(input_file)
    convert_files(output_demucs, output_dir)
    unify_tracks(output_dir, f"{output_dir}/mixed.mp3", VOLUME_DB)



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
    # input_mp3 = f"{ALBUM_DIR}/{SONG_FILE}"
    # split_song(input_mp3)
    split_album(ALBUM_DIR)
