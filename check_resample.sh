#!/bin/bash
# 检查重采样文件的实际采样率

echo "========================================="
echo "检查重采样文件采样率"
echo "=========================================
"

cd /home/pi/FT8PYCLI

# 找最新的重采样文件
RESAMPLED=$(ls -t temp/temp_*_resampled.wav 2>/dev/null | head -1)

if [ -z "$RESAMPLED" ]; then
    echo "❌ 没有找到重采样文件"
    echo "   请先运行主程序生成临时文件"
    exit 1
fi

echo "检查文件: $RESAMPLED"
echo ""

# 使用 Python 检查采样率
python3 << PYEOF
import wave
import sys

try:
    w = wave.open("$RESAMPLED", 'rb')
    rate = w.getframerate()
    channels = w.getnchannels()
    width = w.getsampwidth()
    frames = w.getnframes()
    w.close()
    
    print(f"采样率: {rate} Hz")
    print(f"声道数: {channels}")
    print(f"位深度: {width * 8} bit")
    print(f"帧数: {frames}")
    print(f"时长: {frames/rate:.2f} 秒")
    print("")
    
    if rate == 12000:
        print("✅ 采样率正确 (12000Hz)")
    else:
        print(f"❌ 采样率错误！应该是 12000Hz，实际是 {rate}Hz")
        print("   这就是 ft8.py 崩溃的原因！")
        
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "========================================="
