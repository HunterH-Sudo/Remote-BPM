from flask import Flask, render_template, request, jsonify
import threading
import time
import pygame

app = Flask(__name__)

current_bpm = 120

# Thread control
stop_event = threading.Event()
metronome_thread = None

# Initialize audio
pygame.mixer.init()
click_sound = pygame.mixer.Sound("click.wav")


def metronome_loop():
    global current_bpm

    while not stop_event.is_set():

        click_sound.play()

        interval = 60.0 / current_bpm

        # Wait but allow instant stopping
        if stop_event.wait(interval):
            break


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/play/<song_name>", methods=["POST"])
def play_song(song_name):

    global metronome_thread

    print(f"Starting: {song_name}")

    # Stop previous metronome
    stop_event.set()

    # Wait for old thread to fully stop
    if metronome_thread and metronome_thread.is_alive():
        metronome_thread.join()

    # Reset stop flag
    stop_event.clear()

    # Start new thread
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

    # Clamp safe values
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