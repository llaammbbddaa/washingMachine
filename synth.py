#!/usr/bin/env python3
"""
Lightweight Raspberry Pi voice synthesizer helper.

This script tries multiple local TTS/playback methods in order of preference:
 - espeak --stdout | aplay
 - pico2wave -> aplay
 - pyttsx3 (Python library)

It intentionally does NOT attempt to drive a speaker from GPIO pins. See README for wiring and safety.
"""

import argparse
import shutil
import subprocess
import tempfile
import sys
import os


def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def play_wav(path: str, device: str | None = None) -> None:
    cmd = ["aplay", path]
    if device:
        cmd += ["-D", device]
    subprocess.run(cmd, check=True)


def tts_espeak(text: str, device: str | None = None) -> bool:
    """Use espeak to write WAV to stdout and pipe into aplay."""
    if not command_exists("espeak"):
        raise RuntimeError("espeak not found")
    cmd_espeak = ["espeak", "--stdout", text]
    p1 = subprocess.Popen(cmd_espeak, stdout=subprocess.PIPE)
    cmd_aplay = ["aplay"]
    if device:
        cmd_aplay += ["-D", device]
    p2 = subprocess.Popen(cmd_aplay, stdin=p1.stdout)
    p1.stdout.close()
    p2.communicate()
    return p2.returncode == 0


def tts_pico2wave(text: str, device: str | None = None) -> bool:
    """Generate WAV with pico2wave then play with aplay."""
    if not command_exists("pico2wave"):
        raise RuntimeError("pico2wave not found")
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(["pico2wave", "-w", wav, text], check=True)
        play_wav(wav, device=device)
        return True
    finally:
        try:
            os.unlink(wav)
        except Exception:
            pass


def tts_pyttsx3(text: str, device: str | None = None) -> bool:
    """Try pyttsx3 as a Python fallback. This uses the system audio backend."""
    try:
        import pyttsx3
    except Exception as e:
        raise RuntimeError("pyttsx3 not available: " + str(e))
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return True


def speak(text: str, device: str | None = None, simulate: bool = False) -> None:
    if not text:
        raise ValueError("No text provided")
    if simulate:
        print("[simulate] would speak:", text)
        return

    errors = []
    for fn in (tts_espeak, tts_pico2wave, tts_pyttsx3):
        try:
            if fn is tts_pyttsx3:
                # pyttsx3 doesn't require aplay presence, but it's slower to import.
                pass
            success = fn(text, device=device)
            if success:
                return
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")

    print("All TTS methods failed:\n" + "\n".join(errors), file=sys.stderr)
    raise RuntimeError("No available TTS method. Install espeak or pico2wave or pyttsx3.")


def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi voice synthesizer helper")
    parser.add_argument("text", nargs="+", help="Text to speak (quote it)")
    parser.add_argument("--device", help="ALSA device for aplay, e.g. 'plughw:0,0'", default=None)
    parser.add_argument("--simulate", help="Don't actually play audio; just print what would be spoken", action="store_true")
    args = parser.parse_args()

    text = " ".join(args.text)

    # Safety and wiring reminder (printed each run)
    print("Warning: Do NOT connect a low-impedance speaker directly to Raspberry Pi GPIO pins.")
    print("A 4Ω speaker must be driven by a proper amplifier. Use USB audio, the Pi's headphone jack through an amplifier, or a HAT/amp (e.g. I2S DAC + amp or PAM series).\n")

    try:
        speak(text, device=args.device, simulate=args.simulate)
    except Exception as e:
        print("Error during speech:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
