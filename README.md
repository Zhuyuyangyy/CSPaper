# CSPaper - 计算机类论文生成器

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**基于 AI 的智能计算机类论文生成系统**  
支持大纲生成、正文写作、参考文献、查重报告、DOCX/PDF导出

</div>

---

## 📖 项目简介

CSPaper 是一款面向计算机专业学生的智能论文生成工具，基于 AI 大模型技术，帮助学生快速生成符合学校毕设规范的论文框架和正文内容。

### 适用场景

- 📚 **本科毕业设计** - 计算机科学与技术、软件工程、人工智能等相关专业
- 🎓 **硕士课程论文** - 学术论文框架搭建
- 🏆 **计算机设计大赛** - 竞赛申报书生成
- 📝 **课题申报** - 研究框架与方案设计

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📋 **智能大纲生成** | 自动生成符合规范的论文大纲，支持 29+ 章节结构 |
| ✍️ **正文自动写作** | 基于大纲逐章生成完整正文内容，支持 8000+ 字 |
| 📚 **参考文献管理** | GB/T 7714 标准格式化，支持批量导入 |
| 🔍 **查重率模拟** | 仿知网/万方风格，展示查重率及降重建议 |
| 📄 **多格式导出** | 支持 DOCX、PDF 双格式导出，符合论文排版规范 |
| 📊 **图表生成** | 自动生成柱状图、折线图、饼图等，插入论文自动编号 |
| 🎨 **格式排版** | 符合学校毕设格式要求：封面、摘要、目录、页眉页脚 |

---

## 🛠️ 技术栈

**后端**
- Python 3.8+
- FastAPI (Web 框架)
- Pydantic (数据模型)
- python-docx (Word 导出)
- ReportLab (PDF 导出)

**前端**
- React 18
- TypeScript
- Vite (构建工具)
- Axios (HTTP 客户端)

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 安装部署

#### 方式一：一键启动（推荐）

```batch
# 克隆项目
git clone https://github.com/Zhuyuyangyy/CSPaper.git
cd CSPaper

# 双击运行
start_paper_system_v2.bat
```

#### 方式二：手动启动

**1. 安装后端依赖**

```bash
pip install -r requirements.txt
```

**2. 启动后端服务**

```bash
cd CSPaper
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动后访问：http://localhost:8000/docs (API 文档)

**3. 启动前端**

```bash
cd "DZYY ProjectCSPaper-计算机类论文生成器frontend"
npm install
npm run dev
```

前端访问：http://localhost:9091

---

## 📖 使用指南

### 1. 选择论文类型

进入系统后，选择 **计算机类论文** 作为论文类型。

### 2. 填写论文信息

- **论文标题** - 输入研究主题（建议 10-30 字）
- **学科专业** - 选择或输入专业名称
- **关键词** - 输入 3-5 个核心关键词
- **学位层次** - 本科 / 硕士 / 博士

### 3. 生成大纲

点击"生成大纲"，系统自动生成符合规范的论文框架。

### 4. 生成正文

确认大纲后，点击"生成全文"，系统逐章生成正文内容。

### 5. 导出论文

生成完成后，点击"导出论文"，选择 DOCX 或 PDF 格式下载。

---

## 📁 项目结构

```
CSPaper/
├── app/                          # 后端代码
│   ├── main.py                  # FastAPI 主入口
│   ├── models/                  # 数据模型
│   │   └── paper_models.py     # 论文相关模型
│   ├── routers/                 # API 路由
│   │   └── paper/
│   │       └── generate.py     # 生成接口
│   ├── services/               # 业务服务
│   │   ├── paper_generator.py  # 论文生成核心
│   │   ├── docx_exporter.py   # Word 导出
│   │   └── thesis_formats.py  # 论文格式配置
│   └── agents/                # AI 代理
│
├── DZYY ProjectCSPaper-*/      # 前端项目
│   ├── src/
│   │   ├── App.tsx           # 主组件
│   │   └── App.css           # 样式文件
│   └── package.json
│
├── docker-compose.yml          # Docker 部署配置
├── Dockerfile.backend          # 后端镜像
├── Dockerfile.frontend         # 前端镜像
├── requirements.txt           # Python 依赖
└── start_paper_system_v2.bat  # 一键启动脚本
```

---

## 🔌 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/paper/generate/outline` | POST | 生成论文大纲 |
| `/api/paper/generate/content` | POST | 生成论文正文 |
| `/api/paper/paper/{paper_id}` | GET | 获取论文详情 |
| `/api/paper/export` | POST | 导出论文 |
| `/api/paper/references/{paper_id}` | GET | 获取参考文献 |
| `/api/paper/plagiarism/{paper_id}` | GET | 获取查重报告 |

完整 API 文档：http://localhost:8000/docs

---

## 📊 输出示例

### 大纲生成

```
第1章 绪论
  1.1 研究背景与意义
  1.2 国内外研究现状
  1.3 研究内容与方法
  1.4 论文组织结构
第2章 相关技术与理论基础
  2.1 深度学习概述
  2.2 卷积神经网络
  ...
```

### 导出效果

- ✅ 封面页（标题、学院、专业、姓名）
- ✅ 中英文摘要 + 关键词
- ✅ 自动目录
- ✅ 正文（符合论文格式）
- ✅ 参考文献（GB/T 7714）
- ✅ 致谢页
- ✅ 页眉页脚 + 页码

---

## ⚠️ 声明

- 本项目仅供学习参考和研究使用
- 生成的论文内容为 AI 辅助创作，建议人工审核修改
- 请勿直接用于学术不端行为

---

## 📝 许可证

MIT License

---

## 👨‍💻 作者

**开发者**: OpenClaw AI Assistant  
**所属**: 全自主智能开发体

---

<div align="center">

**如果对你有帮助，请给个 ⭐ Star！**

</div>
