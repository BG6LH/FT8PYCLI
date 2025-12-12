#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音频电平检查工具"""

import sys
import wave
import numpy as np

def check_level(filename):
    """检查音频文件电平"""
    try:
        w = wave.open(filename, 'rb')
        channels = w.getnchannels()
        width = w.getsampwidth()
        framerate = w.getframerate()
        nframes = w.getnframes()
        
        print(f"文件: {filename}")
        print(f"采样率: {framerate} Hz, 声道: {channels}, 位深: {width*8} bit")
        print(f"时长: {nframes/framerate:.2f} 秒")
        
        data = w.readframes(nframes)
        w.close()
        
        if width == 2:
            samples = np.frombuffer(data, dtype=np.int16).astype(float) / 32768.0
        else:
            samples = np.frombuffer(data, dtype=np.uint8).astype(float) / 128.0 - 1.0
            
        if channels == 2:
            samples = samples[::2]
            
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        
        print(f"\nRMS: {rms:.6f}, 峰值: {peak:.6f}")
        
        if peak < 0.01:
            print("❌ 音频电平太低！")
        elif peak > 0.95:
            print("⚠️  音频电平太高，可能削波！")
        else:
            print("✅ 音频电平正常")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 check_audio_level.py <wav文件>")
        sys.exit(1)
    check_level(sys.argv[1])
