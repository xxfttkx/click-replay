import json
import os
import time
import threading
import argparse
from pynput import mouse, keyboard
from pynput.mouse import Controller, Button

RECORD_DIR = "records"
os.makedirs(RECORD_DIR, exist_ok=True)

recording = []
recording_start = None
is_recording = False
is_playing = False
stop_event = threading.Event()


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


def play_record(filename, loop=False, loop_interval=0):
    global is_playing
    filepath = os.path.join(RECORD_DIR, filename)
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        actions = json.load(f)

    m = Controller()
    is_playing = True
    stop_event.clear()

    # ✅ 新增：监听 ESC 键退出
    def on_key_press(key):
        if key == keyboard.Key.esc:
            stop_event.set()
            return False  # 停止监听

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    print(f"▶ Playing back {filename}{' in loop' if loop else ''}...")
    try:
        while not stop_event.is_set():
            start_time = time.time()
            for i, a in enumerate(actions):
                if stop_event.is_set():
                    break
                if i > 0:
                    time.sleep(a["time"] - actions[i - 1]["time"])
                m.position = (a["x"], a["y"])
                btn = Button.left if "left" in a["button"] else Button.right
                m.click(btn)
            print(f"✅ One playback done ({time.time() - start_time:.1f}s).")

            if not loop or stop_event.is_set():
                break
            if loop_interval > 0:
                print(f"⏳ Waiting {loop_interval}s before next loop...")
                for _ in range(int(loop_interval * 10)):
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
    finally:
        is_playing = False
        print("🛑 Playback stopped.")


def start_play_thread(filename, loop=False, loop_interval=0):
    thread = threading.Thread(target=play_record, args=(filename, loop, loop_interval), daemon=True)
    thread.start()


def on_key_press(key):
    global is_recording
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
                start_play_thread(files[idx])

        elif key == keyboard.Key.esc:
            if is_playing:
                stop_event.set()
            return False

    except Exception as e:
        print("Error:", e)


def main():
    parser = argparse.ArgumentParser(description="click-replay — Simple Mouse Recorder & Player")
    parser.add_argument("--replay", type=str, help="Replay a saved record (JSON filename)")
    parser.add_argument("--loop", action="store_true", help="Loop replay continuously")
    parser.add_argument("--interval", type=float, default=0, help="Interval between loops (seconds)")
    args = parser.parse_args()

    if args.replay:
        play_record(args.replay, loop=args.loop, loop_interval=args.interval)
    else:
        print("🎧 Controls: [F7] Start/Stop Record | [F11] Play | [ESC] Quit")
        with mouse.Listener(on_click=record_mouse_click):
            with keyboard.Listener(on_press=on_key_press) as kl:
                kl.join()


if __name__ == "__main__":
    main()
