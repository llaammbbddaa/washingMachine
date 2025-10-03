Raspberry Pi Voice Synthesizer (Speaker: 4Ω, 3W)
===============================================

What this is
------------
A small Python helper (`synth.py`) that speaks text using locally-available TTS tools and routes audio to ALSA (via `aplay`). It is designed for a Raspberry Pi and a regular dynamic speaker (4Ω, 3W), but it intentionally DOES NOT drive the speaker directly from GPIO pins.

Key safety note
---------------
- A 4Ω, 3W speaker is low impedance and must be driven by a proper amplifier. Never connect the speaker directly to Raspberry Pi GPIO pins or the 3.3V/5V pins. Doing so will damage the Pi and/or the speaker.
- Use one of:
  - A small audio amplifier board (PAM8403, PAM8302, LM386-based, etc.) connected to the Pi's headphone or audio-out (or a DAC HAT).
  - A powered USB speaker.
  - A proper I2S DAC + amplifier HAT.
- Keep volumes reasonable and ensure common-ground wiring is correct between the Pi and any amplifier.

Install (system packages)
-------------------------
On Raspberry Pi OS / Debian-based systems you can install recommended packages:

sudo apt update
sudo apt install -y espeak alsa-utils libttspico-utils

- `espeak` provides the `espeak --stdout` pipeline option.
- `alsa-utils` provides `aplay` to play WAV from stdout.
- `pico2wave` (from `libttspico-utils`) is an alternate local TTS.

Optional Python packages
------------------------
A Python fallback is `pyttsx3` if you prefer a pure-Python route (offline):

pip3 install -r requirements.txt

Files
-----
- `synth.py` - the main script. Usage examples below.
- `requirements.txt` - optional Python packages (pyttsx3).

Usage examples
--------------
Speak a short phrase:

python3 synth.py "Hello from Raspberry Pi"

Simulate (don't actually play):

python3 synth.py --simulate "Test only"

Specify ALSA device (if you need a specific hardware output):

python3 synth.py --device plughw:0,0 "Speak to a specific device"

Notes and troubleshooting
-------------------------
- If you see errors about missing commands, install `espeak` and `alsa-utils` as shown above.
- If audio is present but the speaker is silent, double-check amplifier power, wiring, gain, and that the Pi's audio output is routed to the correct device. Use `aplay -l` to list ALSA devices.
- For better quality, consider using a DAC HAT or USB sound card and set `--device` to the appropriate `plughw:X,Y`.

Next steps / improvements
------------------------
- Add optional volume control (via `amixer` or ALSA APIs).
- Add a systemd service to start a simple IPC TTS server for other programs to call.
- Support network TTS (gTTS) as an optional online method.

Basic wiring guideline (textual)
--------------------------------
Below is a minimal wiring example. This is a text guide, not a PCB schematic. If you're unsure, consult amplifier or HAT documentation.

- Raspberry Pi audio output (3.5mm headphone jack or USB audio / HAT DAC line-out) -> amplifier input (line-in or AUX)
- Amplifier power supply -> as required by the amplifier board (do NOT power amp from Pi 5V pin unless the amp is explicitly designed for it)
- Amplifier speaker outputs -> speaker terminals (+ and -). Connect the speaker to these terminals.
- Ensure the amplifier and Pi share a common ground if required by the amplifier design (usually they do when using audio jacks or HATs).

Troubleshooting checklist
-------------------------
- No sound: check amplifier power and speaker wiring.
- Distorted sound: reduce amplifier gain/volume; verify speaker impedance and amplifier compatibility.
- Device not listed: run `aplay -l` to list ALSA playback devices and pass `--device plughw:X,Y`.
- Permission errors: ensure your user is in the `audio` group or run with sudo when testing audio devices.

License
-------
MIT
