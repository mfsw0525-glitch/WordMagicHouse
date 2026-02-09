#!/bin/bash
# 激活 conda 环境并运行 reset_learning.py

cd "$(dirname "$0")"
conda run -n word_magic python reset_learning.py
