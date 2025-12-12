#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sniper Mode Prototype (Deep Decoder Verification)

This script demonstrates the "Sniper Mode" concept:
1. Reads a raw audio file.
2. Applies a strict Bandpass Filter allowing only a narrowband (e.g., 50Hz) around a target frequency.
3. Attempts to decode the filtered signal.

Concept: By removing out-of-band noise *before* decoding, we improve the effective SNR.
"""

import sys
import os
import wave
import numpy as np
from scipy import signal
import logging
import argparse

# Ensure src path is available
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

try:
    from src.ft8 import FT8
    from src import ft8
except ImportError:
    print("Error: Could not import 'src.ft8'. Make sure you are running this from the repo root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SniperVerify')

def load_wav(filename):
    """Load WAV file and return samples and parameters."""
    if not os.path.exists(filename):
        logger.error(f"File not found: {filename}")
        return None, None, None

    logger.info(f"Loading {filename}...")
    try:
        w = wave.open(filename, 'rb')
        channels = w.getnchannels()
        width = w.getsampwidth()
        framerate = w.getframerate()
        nframes = w.getnframes()
        data = w.readframes(nframes)
        w.close()
        
        # Convert to numpy array
        if width == 1:
            dtype = np.uint8
        elif width == 2:
            dtype = np.int16
        else:
            raise ValueError("Only 8 or 16 bit audio supported")

        samples = np.frombuffer(data, dtype=dtype)
        
        # Convert to float normalized -1..1
        if width == 1:
            samples = (samples.astype(float) - 128) / 128.0
        else:
            samples = samples.astype(float) / 32768.0
            
        # If stereo, take left channel only for now
        if channels == 2:
            samples = samples[::2]
            
        return samples, framerate, nframes
    except Exception as e:
        logger.error(f"Error loading wav: {e}")
        return None, None, None

def apply_bandpass_filter(samples, rate, center_freq, bandwidth=60):
    """
    Apply a Butterworth Bandpass Filter.
    Target: center_freq +/- (bandwidth/2)
    """
    nyquist = 0.5 * rate
    low = (center_freq - bandwidth/2) / nyquist
    high = (center_freq + bandwidth/2) / nyquist
    
    # Ensure bounds
    if low <= 0: low = 0.001
    if high >= 1: high = 0.999
    
    logger.info(f"Applying Bandpass Filter: {center_freq}Hz +/- {bandwidth/2}Hz (Order 4)")
    
    # Design filter
    b, a = signal.butter(4, [low, high], btype='band')
    
    # Apply filter
    filtered_samples = signal.filtfilt(b, a, samples)
    return filtered_samples

def save_wav(filename, samples, rate):
    """Save samples to WAV for verification."""
    try:
        # Convert back to int16
        samples_int16 = (samples * 32767).astype(np.int16)
        
        w = wave.open(filename, 'wb')
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples_int16.tobytes())
        w.close()
        logger.info(f"Saved filtered audio to {filename}")
    except Exception as e:
        logger.error(f"Error saving wav: {e}")

def run_decoder(samples, rate):
    """Run the existing Python FT8 decoder on samples."""
    # The pure python decoder expects 12000Hz usually
    # But ft8.py's extract() handles resampling natively via decimate logic if needed,
    # or expects 12000. Let's check.
    # Actually src/ft8.py extract() usually expects ~12000 samples/sec for the symbols to align.
    
    logger.info("Running Decoder...")
    
    # We might need to resample to 12000 if input is 44100/48000
    if rate != 12000:
        logger.info(f"Resampling from {rate} to 12000...")
        num_samples = int(len(samples) * 12000 / rate)
        samples = signal.resample(samples, num_samples)
        rate = 12000
        
    # FT8 decoder expects int16 buffer or float?
    # extract() takes 'samples'. Let's see how it uses them.
    # It usually does FFT.
    
    # Try using the Decoder class logic
    decoder = FT8()
    
    # We need to simulate the 'extract' behavior
    # Assuming samples is float array
    
    try:
        # This calls the full search
        # Note: We need to adapt this because valid_candidates etc might be empty if we filter too much?
        # No, if we filter, the FFT just shows silence elsewhere.
        
        # We need to convert back to what ft8.py expects (usually raw bytes or Audio object?)
        # Actually ft8.py's main decoder loop often works on a list/array of floats.
        
        # Let's call the low-level extract function if accessible, or wrap it.
        # Looking at ft8.py, we might simply call:
        # messages = decoder.decode(samples, rate) # Hypothetical
        
        # ft8.py is a bit script-like. Let's try to reuse the 'Audio' class wrapper or call extract directly.
        # But wait, ft8.py doesn't have a clean 'decode(samples)' API exposed easily.
        # It has 'extract(s, ...)'
        
        # Let's define a minimal processing flow using peak finding
        # For now, let's use the simplest entry point:
        
        messages = ft8.extract(samples, 0, len(samples), 0) # 0=log_level
        
        print(f"\n--- Decoding Results ({len(messages)} messages) ---")
        for msg in messages:
            print(msg)
            
    except Exception as e:
        logger.error(f"Decoder error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Sniper Mode Prototype")
    parser.add_argument("wav_file", help="Input WAV file")
    parser.add_argument("-f", "--freq", type=int, default=1000, help="Target Center Frequency (Hz)")
    parser.add_argument("-b", "--bw", type=int, default=100, help="Bandwidth (Hz)")
    parser.add_argument("--save-filtered", action="store_true", help="Save the filtered audio to wav")
    
    args = parser.parse_args()
    
    # 1. Load Audio
    samples, rate, nframes = load_wav(args.wav_file)
    if samples is None:
        return
        
    logger.info(f"Loaded {nframes} frames at {rate}Hz ({nframes/rate:.2f}s)")
    
    # 2. Bandpass Filter
    filtered_samples = apply_bandpass_filter(samples, rate, args.freq, args.bw)
    
    # 3. Save if requested
    if args.save_filtered:
        out_name = args.wav_file.replace(".wav", f"_filtered_{args.freq}Hz.wav")
        save_wav(out_name, filtered_samples, rate)
    
    # 4. Decode
    # Compare: Full Band vs Filtered?
    # For prototype, just decode Filtered.
    run_decoder(filtered_samples, rate)

if __name__ == "__main__":
    main()
