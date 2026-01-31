@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║          🚀 一键推送到 GitHub                                     ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo [步骤 1/3] 检查 Git 状态...
git status
echo.

echo [步骤 2/3] 添加所有文件并提交...
git add -A
git commit -m "✨ 完整功能系统 - 基金估值 + 全球资产监控"
echo.

echo [步骤 3/3] 推送到 GitHub...
git push origin main
echo.

if errorlevel 1 (
    echo ╔═══════════════════════════════════════════════════════════════════╗
    echo ║                    ⚠️ 推送失败                                    ║
    echo ║                                                                   ║
    echo ║  可能的原因：                                                     ║
    echo ║  1. 网络连接问题（需要 VPN）                                     ║
    echo ║  2. 身份验证失败                                                  ║
    echo ║  3. 远程仓库冲突                                                  ║
    echo ║                                                                   ║
    echo ║  解决方案：                                                       ║
    echo ║  1. 检查网络连接                                                  ║
    echo ║  2. 使用 VPN 后重试                                               ║
    echo ║  3. 手动运行：git push origin main                               ║
    echo ╚═══════════════════════════════════════════════════════════════════╝
) else (
    echo ╔═══════════════════════════════════════════════════════════════════╗
    echo ║                    ✅ 推送成功！                                  ║
    echo ║                                                                   ║
    echo ║  接下来要做的：                                                   ║
    echo ║                                                                   ║
    echo ║  1. 启用 GitHub Pages                                            ║
    echo ║     https://github.com/better6666/fund-valuation-system/settings/pages
    echo ║                                                                   ║
    echo ║  2. 运行 GitHub Actions                                          ║
    echo ║     https://github.com/better6666/fund-valuation-system/actions  ║
    echo ║     点击 "Update All Assets" → "Run workflow"                    ║
    echo ║                                                                   ║
    echo ║  3. 访问网站                                                      ║
    echo ║     https://better6666.github.io/fund-valuation-system/         ║
    echo ║                                                                   ║
    echo ║  详细步骤请查看：🚀GitHub完整部署指南.txt                        ║
    echo ╚═══════════════════════════════════════════════════════════════════╝
    echo.
    echo 是否立即打开 GitHub 仓库？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        start https://github.com/better6666/fund-valuation-system
    )
)

echo.
pause
