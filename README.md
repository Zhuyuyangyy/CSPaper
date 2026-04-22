# CSPaper - 计算机类论文生成器

基于 AI 的计算机类论文生成系统，支持大纲生成、正文写作、参考文献、查重报告、DOCX/PDF导出。

## 快速启动

```bash
# 启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端 (另一个终端)
cd "DZYY ProjectCSPaper-*"
npm install
npm run dev
```

访问 http://localhost:9091

## 功能

- 智能大纲生成
- 正文自动写作
- 参考文献格式化 (GB/T 7714)
- 查重率模拟
- DOCX/PDF导出
- 图表自动生成
