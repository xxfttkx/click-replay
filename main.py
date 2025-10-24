
import json
import os
import time
from pynput import mouse, keyboard
from pynput.mouse import Controller, Button
import argparse

RECORD_DIR = "records"
os.makedirs(RECORD_DIR, exist_ok=True)

recording = []
recording_start = None
is_recording = False
is_playing = False


def record_mouse_click(x, y, button, pressed):
    global recording, recording_start, is_recording
    if not is_recording:
        return
    if pressed:
        timestamp = time.time() - recording_start
        recording.append({"x": x, "y": y, "button": str(button), "time": timestamp})
        print(f"[+] Click at ({x}, {y}) @ {timestamp:.2f}s")


def start_record():
    global recording, recording_start, is_recording
    recording = []
    recording_start = time.time()
    is_recording = True
    print("🎬 Start recording mouse clicks...")


def stop_record():
    global is_recording
    is_recording = False
    filename = time.strftime("%Y%m%d_%H%M%S.json")
    filepath = os.path.join(RECORD_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(recording, f, indent=2)
    print(f"💾 Recording saved to {filepath}")


def play_record(filename, loop=False):
    filepath = os.path.join(RECORD_DIR, filename)
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        actions = json.load(f)

    m = Controller()

    print(f"▶ Playing back {filename}{' in loop' if loop else ''}...")
    try:
        while True:
            start_time = time.time()
            for i, a in enumerate(actions):
                if i > 0:
                    time.sleep(a["time"] - actions[i - 1]["time"])
                m.position = (a["x"], a["y"])
                btn = Button.left if "left" in a["button"] else Button.right
                m.click(btn)
            print(f"✅ One playback done ({time.time() - start_time:.1f}s).")
            if not loop:
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")


def on_key_press(key):
    global is_recording, is_playing
    try:
        if key == keyboard.Key.f7:
            if not is_recording:
                start_record()
            else:
                stop_record()
        elif key == keyboard.Key.f11:
            files = os.listdir(RECORD_DIR)
            if not files:
                print("⚠ No record files found.")
                return
            print("Available recordings:")
            for i, f in enumerate(files):
                print(f"{i+1}. {f}")
            idx = int(input("Select file number to play: ")) - 1
            if 0 <= idx < len(files):
                play_record(files[idx])
        elif key == keyboard.Key.esc:
            if is_playing:
                is_playing = False
                print("🛑 Playback stopped.")
            return False
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="click-replay — Simple Mouse Recorder & Player")
    parser.add_argument("--replay", type=str, help="Replay a saved record (JSON filename)")
    parser.add_argument("--loop", action="store_true", help="Loop replay continuously")
    args = parser.parse_args()

    if args.replay:
        play_record(args.replay, loop=args.loop)
    else:
        print("🎧 Controls: [F7] Start/Stop Record | [F11] Play | [ESC] Quit")
        with mouse.Listener(on_click=record_mouse_click):
            with keyboard.Listener(on_press=on_key_press) as kl:
                kl.join()
