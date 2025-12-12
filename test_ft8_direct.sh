#!/bin/bash
# 直接测试 ft8.py 解码器输出

echo "========================================="
echo "FT8.py 直接解码测试"
echo "========================================="
echo ""

cd /home/pi/FT8PYCLI

# 找最新的录音
RECORDING=$(ls -t recordings/recording_*.wav 2>/dev/null | head -1)

if [ -z "$RECORDING" ]; then
    echo "❌ 没有录音文件"
    exit 1
fi

echo "测试文件: $RECORDING"
echo ""
echo "========================================="
echo "ft8.py 原始输出:"
echo "========================================="

# 直接运行 ft8.py 并显示所有输出
cd src
python3 ft8.py -file "../$RECORDING" 2>&1

echo ""
echo "========================================="
echo "测试完成"
echo ""
echo "如果看到以 'P' 开头的行，说明解码成功"
echo "如果没有任何输出，说明解码器有问题"
echo "========================================="
