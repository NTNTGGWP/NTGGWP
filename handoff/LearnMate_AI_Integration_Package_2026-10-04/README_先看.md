# LearnMate AI 診斷＋補救練習整合包

這份資料夾是提供嘉倫整合到「已有完整 AWS S3 課程影片」版本的交接包。

## 目標流程

學生看 AWS S3 影片 → 做一般章節測驗 → 儲存真實作答 → AI 分析學習狀況 → AI 依錯題產生補救練習 → 回去重做一般測驗 → Power BI 比較前後分數。

本包不會取代既有的課程、影片、會員或 AWS 設定，只加入 Quiz、AI 診斷、補救練習與 Power BI 匯出能力。

## 重要觀念

- Django 可以在本機執行，同時播放 AWS S3 影片並呼叫 Azure OpenAI；不必先部署新版網站到 AWS。
- 所有觀看進度、一般測驗作答及 Power BI 匯出必須使用同一個資料庫。
- AI 補救題目前是即時產生的網頁練習，不會另存補救題成績。前後成效以學生重做「一般章節測驗」的兩次 `QuizAttempt` 比較。
- 不要把 `.env`、API Key、AWS Secret 或資料庫密碼提交到 Git。

## 資料夾內容

- `django/main/ai_assistant.py`：Azure OpenAI 呼叫層（也保留原專案的 Gemini／Claude fallback）。
- `django/main/ai_diagnosis.py`：依觀看、完成率、Quiz 錯題進行學習診斷；並把結構化弱點寫入 `QuizAttempt`。
- `django/main/ai_remedial.py`：依最近一次錯題產生 4 題補救練習。
- `django/main/templates/main/`：一般 Quiz 與結果／AI 操作頁。
- `django/main/migrations/0028...`、`0029...`：目前專案的資料表變更参考。
- `integration_reference/`：需要合併進嘉倫既有 `models.py`、`views.py`、`urls.py`、`admin.py`、`settings.py` 的精簡片段。
- `powerbi/`：真實資料匯出、Excel 建置器與現有 PBIX。
- `test_evidence/`：本次真實測試的補救前與第二次測驗快照。

## 建議整合順序

1. 在嘉倫專案建立新 Git 分支或備份。
2. 確認 app 名稱；本包假設 Django app 叫 `main`。若名稱不同，調整 import、template path 及 migration dependency。
3. 把三個 `ai_*.py` 放進嘉倫 app。
4. 依 `integration_reference/models_to_merge.py` 合併 Quiz models 與必要的進度欄位。
5. **若嘉倫已有 0028／0029 migration，不要直接覆蓋。** 合併 models 後執行 `python manage.py makemigrations` 產生他自己的新 migration。只有 migration 編號與 dependency 完全相容時才可直接使用本包 migration。
6. 合併 `views_to_merge.py`、`urls_to_merge.py`、`admin_to_merge.py`。
7. 複製兩個 template，並依嘉倫的 base template／CSS 做小幅調整。
8. 在課程章節清單加入 `course_page_entry_example.html` 的 Quiz 入口。
9. 依 `.env.ai.example` 私下設定 Azure OpenAI；不要把真实值放进此資料夾或 Git。
10. 執行检查、migration、建立题目并完成整套测试。

## 必要套件

见 `integration_reference/requirements_ai.txt`。Azure OpenAI 模式最少需要 `requests` 与 `python-dotenv`。

## 环境变量

把 `.env.ai.example` 的四个名称加入嘉伦专案根目录 `.env`。程式实际读取的是 `AZURE_OPENAI_DEPLOYMENT`，不是 `AZURE_OPENAI_DEPLOYMENT_NAME`。

## 整合后检查

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py runserver
```

后台建立 Quiz 时，每题务必填写 `topic_tag`，否则虽然能评分，Power BI 的知识点弱点统计会缺少该题。

## Demo 验收清单

1. 用测试学生加入一门有 AWS 影片的课程。
2. 播放影片一小段，确认 `LessonProgress` 有更新。
3. 第一次测验故意答错，确认结果页显示分数与错题。
4. 按「分析我的学习状况」，确认产生弱点与建议。
5. 按「产生补救练习」，确认产生 4 题与解析。
6. 回一般测验重做，确认显示上次／这次分数与进步值。
7. 执行 Power BI 匯出，确认 `weak_topics`、`remedial_comparisons`、`student_course_metrics` 有资料。

## Power BI 更新

```powershell
cd myproject
python manage.py export_powerbi_json --output ../outputs/learnmate/learnmate_powerbi_data.json
cd ../powerbi
python build_workbook.py --input ../outputs/learnmate/learnmate_powerbi_data.json --output dashboard/LearnMate_PowerBI_Data.xlsx
```

打开 PBIX 后按「重新整理」。不需要重做图表，也不需要每次重新指定档案；只要 Excel 输出路径维持相同。

## Power BI 嵌入位置

学生版建议放在 `/student/analytics/`，也就是学生专区的「学习分析」。若使用 Power BI「发布至 Web」，链接属于公开访问，只能放匿名 Demo 资料。正式学生资料要使用 Power BI Embedded + RLS，或其他有登入权限的嵌入方式。

