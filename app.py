from flask import Flask, render_template, request, jsonify
import threading
import time
import pygame
import json
import os

app = Flask(__name__)

current_bpm = 120

SONGS_FILE = "songs.json"

# Thread control
stop_event = threading.Event()
metronome_thread = None

# Initialize audio
pygame.mixer.init()
click_sound = pygame.mixer.Sound("click.wav")


# --------------------------
# SONG STORAGE
# --------------------------

def load_songs():

    if not os.path.exists(SONGS_FILE):

        default_songs = [
            {"name": "Song 1", "bpm": 80},
            {"name": "Song 2", "bpm": 80},
        ]

        save_songs(default_songs)

        return default_songs

    with open(SONGS_FILE, "r") as f:
        return json.load(f)


def save_songs(songs):

    with open(SONGS_FILE, "w") as f:
        json.dump(songs, f, indent=4)


# --------------------------
# METRONOME
# --------------------------

def metronome_loop():

    global current_bpm

    while not stop_event.is_set():

        click_sound.play()

        interval = 60.0 / current_bpm

        if stop_event.wait(interval):
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

    save_songs(songs)

    return jsonify({
        "status": "saved"
    })


@app.route("/play/<song_name>", methods=["POST"])
def play_song(song_name):

    global metronome_thread

    print(f"Starting: {song_name}")

    stop_event.set()

    if metronome_thread and metronome_thread.is_alive():
        metronome_thread.join()

    stop_event.clear()

    metronome_thread = threading.Thread(target=metronome_loop)
    metronome_thread.daemon = True
    metronome_thread.start()

    return jsonify({
        "status": "playing",
        "song": song_name
    })


@app.route("/stop", methods=["POST"])
def stop():

    stop_event.set()

    return jsonify({
        "status": "stopped"
    })


@app.route("/set_bpm", methods=["POST"])
def set_bpm():

    global current_bpm

    data = request.get_json()

    bpm = int(data["bpm"])

    bpm = max(30, min(300, bpm))

    current_bpm = bpm

    print(f"BPM set to {current_bpm}")

    return jsonify({
        "status": "ok",
        "bpm": current_bpm
    })


if __name__ == "__main__":

    print("Starting Church Metronome...")

    app.run(
        host="0.0.0.0",
        port=5000
    )