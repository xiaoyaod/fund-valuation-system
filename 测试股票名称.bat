@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║          🔍 测试股票名称获取                                      ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo 正在运行增强版数据抓取脚本...
echo 这个版本会获取真实的股票名称而不是"股票1"、"股票2"
echo.

python scripts/fetch_data_enhanced.py

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    ✅ 完成！                                      ║
echo ║                                                                   ║
echo ║  数据已保存到：                                                   ║
echo ║  - data/funds.json                                               ║
echo ║  - public/data/funds.json                                        ║
echo ║                                                                   ║
echo ║  现在可以打开 index.html 查看效果                                ║
echo ║  股票名称应该显示真实名称（如"贵州茅台"而不是"股票1"）           ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo 是否立即打开网页查看？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    start index.html
)

pause
