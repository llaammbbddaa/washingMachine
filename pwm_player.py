#!/usr/bin/env python3
"""
Simple PWM audio player using pigpio.

This script converts a mono WAV file (8k-48k sample rate, 8-16 bit) into PWM duty cycles
and streams them to a GPIO pin using pigpio waves. It is intended ONLY as a signal source.

IMPORTANT SAFETY: Do NOT connect the PWM GPIO pin directly to a speaker. The PWM output
must go into a proper amplifier input (line-in) or a class-D amp input. Driving a 4Ω
speaker directly from GPIO will damage the Pi and the speaker.

Usage:
    python3 pwm_player.py --wav speech.wav --gpio 18 --rate 8000

Notes:
- Requires pigpio daemon running (sudo pigpiod).
- Best used with a low-pass filter (RC) or a class-D amplifier that accepts PWM/PCM.
"""

import argparse
import wave
import sys
import os

try:
    import pigpio
except ImportError:
    print("pigpio module not found. Install with: pip3 install pigpio", file=sys.stderr)
    raise


def wav_to_samples(wav_path):
    wf = wave.open(wav_path, 'rb')
    channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    framerate = wf.getframerate()
    nframes = wf.getnframes()

    if channels != 1:
        raise ValueError('Only mono WAV supported for this simple player')

    raw = wf.readframes(nframes)
    wf.close()

    # Convert to 8-bit unsigned samples for PWM duty mapping
    if sampwidth == 1:
        # 8-bit unsigned
        samples = list(raw)
    elif sampwidth == 2:
        # 16-bit signed little endian -> convert to 8-bit unsigned
        import struct
        fmt = '<{}h'.format(nframes)
        vals = struct.unpack(fmt, raw)
        samples = [int((v + 32768) >> 8) for v in vals]
    else:
        raise ValueError('Unsupported sample width: {} bytes'.format(sampwidth))

    return samples, framerate


def stream_pwm(samples, sr, gpio, pi):
    # pigpio hardware PWM supports frequency and dutycycle (0-1e6)
    # We'll approximate by setting a carrier frequency and updating duty cycle rapidly.
    carrier = 25000  # 25 kHz carrier frequency
    pi.set_mode(gpio, pigpio.OUTPUT)
    # Start with 0 duty
    pi.hardware_PWM(gpio, carrier, 0)

    # Duty range for hardware_PWM is 0..1000000
    for s in samples:
        duty = int(s * 1000000 / 255)
        pi.hardware_PWM(gpio, carrier, duty)
    # Stop
    pi.hardware_PWM(gpio, 0, 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wav', required=True, help='Path to mono WAV file')
    parser.add_argument('--gpio', type=int, default=18, help='GPIO pin (BCM) to use for PWM (default 18)')
    parser.add_argument('--rate', type=int, default=None, help='Playback sample rate (optional)')
    args = parser.parse_args()

    if not os.path.exists(args.wav):
        print('WAV file not found:', args.wav, file=sys.stderr)
        sys.exit(2)

    samples, framerate = wav_to_samples(args.wav)
    if args.rate and args.rate != framerate:
        print('Warning: WAV sample rate {} differs from requested rate {}'.format(framerate, args.rate))

    pi = pigpio.pi()
    if not pi.connected:
        print('pigpio daemon not running. Start it with: sudo pigpiod', file=sys.stderr)
        sys.exit(3)

    try:
        stream_pwm(samples, framerate, args.gpio, pi)
    finally:
        pi.stop()


if __name__ == '__main__':
    main()
