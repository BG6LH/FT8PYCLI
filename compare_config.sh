#!/bin/bash
# 对比 WSJT-X 和 FT8PYCLI 的配置

echo "========================================="
echo "WSJT-X vs FT8PYCLI 配置对比"
echo "========================================="
echo ""

cd /home/pi/FT8PYCLI

echo "1. FT8PYCLI 配置:"
echo "----------------------------------------"
cat config/ft8pycli.json | grep -A 5 "audio\|device"
echo ""

echo "2. FT8PYCLI 实际使用的音频设备:"
echo "----------------------------------------"
python3 << 'PYEOF'
import json
with open('config/ft8pycli.json') as f:
    config = json.load(f)
    device = config.get('device') or config.get('audio', {}).get('device')
    print(f"设备配置: {device}")
PYEOF
echo ""

echo "3. 可用音频设备列表:"
echo "----------------------------------------"
python3 -c "
import sys
sys.path.insert(0, 'src')
from audio_recorder import AudioRecorder
recorder = AudioRecorder()
recorder.list_devices()
"
echo ""

echo "4. 检查最新录音文件:"
echo "----------------------------------------"
LATEST=$(ls -t recordings/recording_*.wav 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    echo "文件: $LATEST"
    python3 check_audio_level.py "$LATEST" 2>/dev/null || echo "运行 check_audio_level.py 检查详情"
else
    echo "没有录音文件"
fi
echo ""

echo "========================================="
echo "建议:"
echo "========================================="
echo "1. 确认 WSJT-X 使用的音频设备"
echo "2. 确保 FT8PYCLI 使用相同的设备"
echo "3. 检查音频电平是否正常"
echo "========================================="
