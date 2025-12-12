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

    # Run existing decoder
    # Since we don't have a direct 'decode(samples)' method easily accessible without re-implementing 
    # the whole FT8 class logic, we will save the temp file (which we did) and let FT8.gowav read it.
    
    # We need to pass the FILENAME to gowav, not the samples.
    # The current run_decoder function takes samples, but we already saved them to 'out_name' in main().
    # Let's change the logic to use the saved file.
    pass

def run_decoder_on_file(filename):
    """Run the existing Python FT8 decoder on a file."""
    logger.info(f"Running Decoder on {filename}...")
    
    try:
        decoder = FT8()
        # gowav reads the file itself
        decoder.gowav(filename, 0) # 0 = channel
            
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
        run_decoder_on_file(out_name)
    else:
        # If not saving, we must save temporarily to decode
        temp_name = "temp_sniper_decode.wav"
        save_wav(temp_name, filtered_samples, rate)
        run_decoder_on_file(temp_name)
        try:
            os.remove(temp_name)
        except:
            pass

if __name__ == "__main__":
    main()
