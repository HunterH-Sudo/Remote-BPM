from flask import Flask, render_template, request, jsonify
import threading
import time
import pygame
import json
import os

app = Flask(__name__)

SONGS_FILE = "songs.json"

# --------------------------
# GLOBAL STATE
# --------------------------

current_bpm = 120
current_signature = "4/4"

state_lock = threading.Lock()

stop_event = threading.Event()
metronome_thread = None

# --------------------------
# AUDIO INIT
# --------------------------

pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

click_sound = pygame.mixer.Sound("click.wav")
accent_sound = pygame.mixer.Sound("accent.wav")


# --------------------------
# SONG STORAGE
# --------------------------

def load_songs():
    if not os.path.exists(SONGS_FILE):
        default_songs = [
            {"id": "1", "name": "Song 1", "bpm": 80, "signature": "4/4"},
            {"id": "2", "name": "Song 2", "bpm": 90, "signature": "4/4"},
        ]
        save_songs(default_songs)
        return default_songs

    with open(SONGS_FILE, "r") as f:
        return json.load(f)


def save_songs(songs):
    with open(SONGS_FILE, "w") as f:
        json.dump(songs, f, indent=4)


# --------------------------
# TIME SIGNATURE HELPERS
# --------------------------

def beats_per_bar(signature: str) -> int:
    try:
        return int(signature.split("/")[0])
    except:
        return 4


# --------------------------
# METRONOME (DRIFT-FREE + ACCENTED)
# --------------------------

def metronome_loop():
    next_tick = time.time()
    beat_in_bar = 0

    while not stop_event.is_set():

        with state_lock:
            bpm = current_bpm
            signature = current_signature

        # 🔥 Accent first beat of bar
        if beat_in_bar == 0:
            accent_sound.play()
        else:
            click_sound.play()

        beat_in_bar = (beat_in_bar + 1) % beats_per_bar(signature)

        # drift-free timing
        interval = 60.0 / bpm
        next_tick += interval

        sleep_time = max(0, next_tick - time.time())

        if stop_event.wait(sleep_time):
            break


# --------------------------
# ROUTES
# --------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/songs", methods=["GET"])
def get_songs():
    return jsonify(load_songs())


@app.route("/songs", methods=["POST"])
def update_songs():
    songs = request.get_json()

    if not isinstance(songs, list):
        return jsonify({"error": "invalid data"}), 400

    # ensure valid structure
    cleaned = []
    for s in songs:
        if "name" in s:
            cleaned.append({
                "id": s.get("id", str(time.time())),
                "name": s["name"],
                "bpm": int(s.get("bpm", 120)),
                "signature": s.get("signature", "4/4")
            })

    save_songs(cleaned)

    return jsonify({"status": "saved", "count": len(cleaned)})


@app.route("/play/<song_name>", methods=["POST"])
def play_song(song_name):
    global metronome_thread

    stop_event.set()

    if metronome_thread and metronome_thread.is_alive():
        metronome_thread.join(timeout=1)

    stop_event.clear()

    metronome_thread = threading.Thread(target=metronome_loop, daemon=True)
    metronome_thread.start()

    return jsonify({"status": "playing", "song": song_name})


@app.route("/stop", methods=["POST"])
def stop():
    stop_event.set()
    return jsonify({"status": "stopped"})


@app.route("/set_bpm", methods=["POST"])
def set_bpm():
    global current_bpm

    data = request.get_json()
    bpm = int(data["bpm"])
    bpm = max(30, min(300, bpm))

    with state_lock:
        current_bpm = bpm

    return jsonify({"status": "ok", "bpm": current_bpm})


@app.route("/set_signature", methods=["POST"])
def set_signature():
    global current_signature

    data = request.get_json()
    current_signature = data["signature"]

    return jsonify({"status": "ok", "signature": current_signature})


if __name__ == "__main__":
    print("Starting Church Metronome...")
    app.run(host="0.0.0.0", port=5000)