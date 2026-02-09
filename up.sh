#!/bin/bash
echo "🚀 正在同步代码到 GitHub..."
git add .
git commit -m "Update at $(date +'%Y-%m-%d %H:%M:%S')"
git push
echo "✅ 同步完成！Streamlit Cloud 正在自动更新..."
