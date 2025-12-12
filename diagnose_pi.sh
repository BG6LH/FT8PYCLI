#!/bin/bash
# FT8PYCLI 诊断脚本 - 检查 libldpc C 库状态

echo "========================================="
echo "FT8PYCLI libldpc 诊断工具"
echo "========================================="
echo ""

# 1. 检查 C 库文件是否存在
echo "1. 检查 libldpc.so 文件..."
if [ -f "src/libldpc/libldpc.so" ]; then
    echo "✅ 找到 libldpc.so"
    ls -lh src/libldpc/libldpc.so
else
    echo "❌ 未找到 libldpc.so"
    echo "   需要编译: cd src/libldpc && make"
fi
echo ""

# 2. 检查编译工具
echo "2. 检查编译环境..."
if command -v gcc &> /dev/null; then
    echo "✅ GCC 已安装: $(gcc --version | head -1)"
else
    echo "❌ GCC 未安装"
    echo "   安装命令: sudo apt-get install build-essential"
fi
echo ""

# 3. 测试 Python 加载 C 库
echo "3. 测试 Python 加载 libldpc.so..."
python3 << 'PYEOF'
import sys
import ctypes
import os

# 切换到项目根目录
os.chdir('/home/pi/FT8PYCLI')

try:
    # 尝试加载 C 库
    lib = ctypes.cdll.LoadLibrary("src/libldpc/libldpc.so")
    print("✅ Python 成功加载 libldpc.so")
    print(f"   库对象: {lib}")
except Exception as e:
    print(f"❌ Python 加载失败: {e}")
    print("   可能原因:")
    print("   1. 文件不存在")
    print("   2. 文件权限问题")
    print("   3. 架构不匹配")
PYEOF
echo ""

# 4. 检查 ft8.py 中的加载逻辑
echo "4. 检查 ft8.py 的 libldpc 加载代码..."
grep -n "LoadLibrary.*libldpc" src/ft8.py
echo ""

# 5. 运行简单解码测试
echo "5. 测试解码器启动信息..."
echo "   运行: python3 src/ft8.py -h 2>&1 | head -5"
timeout 3 python3 src/ft8.py -h 2>&1 | head -5
echo ""

echo "========================================="
echo "诊断完成"
echo "========================================="
