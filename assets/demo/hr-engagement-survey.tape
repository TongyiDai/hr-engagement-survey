Output "hr-engagement-survey-demo.gif"
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 760
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms

Hide
Type "cd /path/to/hr-engagement-survey" Enter
Type "clear" Enter
Show
Sleep 600ms
Type "# 喂匿名聚合的敬业度结果（假数据），出洞察，不做个人识别" Sleep 400ms Enter
Sleep 1s
Type "sed -n '1,12p' tests/fixtures/results-q12.json" Sleep 300ms Enter
Sleep 2200ms
Type "python3 scripts/analyze_results.py --input tests/fixtures/results-q12.json --format markdown | head -28" Sleep 300ms Enter
Sleep 3500ms
Type "# 全程脱敏假数据 · 只产草稿/洞察，人工复核后再用 ✅" Enter
Sleep 2800ms
