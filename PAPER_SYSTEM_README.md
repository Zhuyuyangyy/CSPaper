# CSPaper & MedPaper 论文生成系统 v2.0

## 📋 项目概述

**全自主智能论文生成系统** - 支持医学/计算机/工科/文科多类型论文一键生成

### 核心功能
- ✅ 智能大纲生成（符合学校规范）
- ✅ 全文自动写作（各章节内容）
- ✅ 参考文献格式化（GB/T 7714）
- ✅ 查重率模拟（仿知网/万方风格）
- ✅ 数据图表生成（柱状图/折线图/饼图）
- ✅ DOCX/PDF双格式导出
- ✅ 用户历史记录
- ✅ 写作进度保存
- ✅ 主题切换（明/暗模式）

## 🚀 快速启动

### 方式一：一键启动（推荐）
```batch
双击运行 start_paper_system.bat
```

### 方式二：手动启动

**1. 启动后端**
```bash
cd C:\Users\联想\.openclaw\workspace
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**2. 启动CSPaper前端**
```batch
cd "C:\Users\联想\.openclaw\workspace\DZYY ProjectCSPaper-计算机类论文生成器frontend"
npm install
npm run dev -- --port 9091 --host
```

**3. 启动MedPaper前端**
```batch
cd "C:\Users\联想\.openclaw\workspace\DZYY ProjectMedPaper-医学生论文生成器frontend"
npm install
npm run dev -- --port 9090 --host
```

## 🌐 访问地址

| 服务 | 地址 |
|------|------|
| 后端API | http://localhost:8000 |
| CSPaper | http://localhost:9091 |
| MedPaper | http://localhost:9090 |
| API文档 | http://localhost:8000/docs |

## 📖 使用指南

### 1. 生成论文

1. 选择论文类型（医学/计算机/工科/文科）
2. 输入论文标题（必填）
3. 填写专业方向和关键词（可选）
4. 点击「生成论文大纲」
5. 等待大纲生成完成

### 2. 查看与编辑大纲

- 大纲包含标准论文结构（摘要、绪论、正文、结论等）
- 每个章节显示预估字数
- 支持二级、三级标题展开

### 3. 生成全文

1. 在大纲页面点击「生成全文」
2. 系统自动续写各章节内容
3. 可在内容页面查看完整论文
4. 支持图表自动插入

### 4. 查重报告

- 点击「查重报告」获取模拟查重结果
- 显示总体查重率和各章节分布
- 提供降重建议

### 5. 导出论文

- 支持 **DOCX** 和 **PDF** 两种格式
- 包含目录、摘要、关键词、参考文献
- 自动排版符合学校格式要求

## 📁 项目结构

```
workspace/
├── app/                          # 后端代码
│   ├── main.py                  # FastAPI入口
│   ├── models/
│   │   └── paper_models.py     # 数据模型
│   ├── routers/
│   │   └── paper/
│   │       └── generate.py     # 论文生成API
│   └── services/
│       ├── paper_generator.py  # 核心生成服务
│       └── docx_exporter.py    # 导出服务
├── DZYY ProjectCSPaper-*/      # 计算机论文前端
├── DZYY ProjectMedPaper-*/     # 医学论文前端
├── data/                        # 数据目录
│   ├── papers/                 # 论文存储
│   ├── exports/                # 导出文件
│   └── charts/                 # 图表缓存
└── start_paper_system.bat      # 一键启动脚本
```

## 🔧 API 接口

### 论文生成
```
POST /api/paper/generate/outline    - 生成大纲
POST /api/paper/generate/content    - 生成正文
GET  /api/paper/references/{id}     - 获取参考文献
GET  /api/paper/plagiarism/{id}    - 查重报告
POST /api/paper/export              - 导出论文
```

### 论文管理
```
GET  /api/paper/paper/{id}         - 获取论文详情
GET  /api/paper/papers/{user}      - 获取用户论文列表
DELETE /api/paper/paper/{id}        - 删除论文
GET  /api/paper/progress/{id}      - 获取进度
```

## 🎨 界面预览

### 主题特色
- **CSPaper**: 蓝色科技风格，适合计算机类论文
- **MedPaper**: 绿色医学风格，适合医学生论文

### 功能特色
- 响应式设计，适配电脑/平板
- 明暗主题切换
- 加载动画和进度显示
- 友好的错误提示

## 📊 输出示例

### 论文大纲结构（计算机类）
```
├── 摘要
├── Abstract
├── 第1章 绪论
│   ├── 1.1 研究背景
│   ├── 1.2 研究意义
│   └── 1.3 国内外研究现状
├── 第2章 相关技术与理论
├── 第3章 系统需求分析
├── 第4章 系统设计
├── 第5章 系统实现
├── 第6章 系统测试
├── 第7章 总结与展望
├── 参考文献
└── 致谢
```

### 论文大纲结构（医学类）
```
├── 摘要
├── Abstract
├── 前言
├── 资料与方法
│   ├── 1.1 一般资料
│   ├── 1.2 纳入与排除标准
│   ├── 1.3 研究方法
│   └── 1.4 统计学方法
├── 结果
├── 讨论
├── 结论
└── 参考文献
```

## ⚠️ 注意事项

1. **首次使用**请确保安装Node.js 18+和Python 3.9+
2. **导出功能**需要安装 python-docx 库
3. **PDF导出**需要安装 reportlab 库
4. 论文内容为AI模拟生成，仅供参考

## 📜 版本信息

- **Version**: 2.0.0
- **Build Date**: 2026-04-22
- **Author**: Alice 🌸

## 🆘 技术支持

如遇问题请检查：
1. 端口是否被占用（8000/9090/9091）
2. 依赖是否完整安装
3. Node.js 和 Python 版本是否正确

---

**全自主智能开发体 OpenClaw** 🚀
通宵开发，准时交付！
