# -*- coding: utf-8 -*-
"""
论文生成核心服务
==================
支持多类型论文自动生成：大纲、正文、参考文献、降重
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.models.paper_models import (
    PaperType, OutlineResponse, OutlineSection, ContentResponse, 
    ContentSection, ReferenceItem, ReferenceResponse, ThesisFormat,
    UserPaper, PlagiarismReport, ChartResponse
)

logger = logging.getLogger("PaperGenerator")

# 存储路径
DATA_DIR = Path(r"C:\Users\联想\.openclaw\workspace\data")
PAPERS_DIR = DATA_DIR / "papers"
PAPERS_DIR.mkdir(exist_ok=True)


class PaperGenerator:
    """论文生成器核心类"""
    
    # 各类型论文的默认大纲模板
    OUTLINE_TEMPLATES = {
        PaperType.COMPUTER: [
            {"level": 1, "title": "摘要", "hint": "简短概括研究背景、目的、方法、结果和结论"},
            {"level": 1, "title": "Abstract", "hint": "英文摘要"},
            {"level": 1, "title": "第1章 绪论", "hint": "研究背景、意义、国内外研究现状"},
            {"level": 2, "title": "1.1 研究背景", "hint": "介绍研究领域的整体背景"},
            {"level": 2, "title": "1.2 研究意义", "hint": "理论意义和实践价值"},
            {"level": 2, "title": "1.3 国内外研究现状", "hint": "文献综述"},
            {"level": 1, "title": "第2章 相关技术与理论", "hint": "核心技术/理论介绍"},
            {"level": 2, "title": "2.1 技术概述", "hint": "相关技术背景"},
            {"level": 2, "title": "2.2 理论基础", "hint": "理论支撑"},
            {"level": 1, "title": "第3章 系统需求分析", "hint": "系统设计前期分析"},
            {"level": 2, "title": "3.1 可行性分析", "hint": "技术、经济、操作可行性"},
            {"level": 2, "title": "3.2 功能需求", "hint": "核心功能列表"},
            {"level": 2, "title": "3.3 非功能需求", "hint": "性能、安全、可靠性"},
            {"level": 1, "title": "第4章 系统设计", "hint": "系统架构设计"},
            {"level": 2, "title": "4.1 系统架构", "hint": "总体架构设计"},
            {"level": 2, "title": "4.2 功能模块设计", "hint": "各模块详细设计"},
            {"level": 2, "title": "4.3 数据库设计", "hint": "数据模型设计"},
            {"level": 1, "title": "第5章 系统实现", "hint": "代码实现展示"},
            {"level": 2, "title": "5.1 开发环境", "hint": "开发工具和环境"},
            {"level": 2, "title": "5.2 核心代码", "hint": "关键代码实现"},
            {"level": 1, "title": "第6章 系统测试", "hint": "测试用例和结果"},
            {"level": 2, "title": "6.1 测试环境", "hint": "测试环境说明"},
            {"level": 2, "title": "6.2 功能测试", "hint": "功能验证"},
            {"level": 2, "title": "6.3 性能测试", "hint": "性能评估"},
            {"level": 1, "title": "第7章 总结与展望", "hint": "工作总结和未来方向"},
            {"level": 2, "title": "7.1 工作总结", "hint": "已完成工作"},
            {"level": 2, "title": "7.2 未来展望", "hint": "改进方向"},
            {"level": 1, "title": "参考文献", "hint": "GB/T 7714格式"},
            {"level": 1, "title": "致谢", "hint": "感谢导师和帮助过自己的人"},
        ],
        PaperType.MEDICAL: [
            {"level": 1, "title": "摘要", "hint": "研究目的、方法、结果、结论"},
            {"level": 1, "title": "Abstract", "hint": "英文摘要"},
            {"level": 1, "title": "前言", "hint": "研究背景、目的"},
            {"level": 1, "title": "资料与方法", "hint": "研究对象、方法"},
            {"level": 2, "title": "1.1 一般资料", "hint": "研究对象基本信息"},
            {"level": 2, "title": "1.2 纳入与排除标准", "hint": "样本选择标准"},
            {"level": 2, "title": "1.3 研究方法", "hint": "实验/调查方法"},
            {"level": 2, "title": "1.4 统计学方法", "hint": "数据分析方法"},
            {"level": 1, "title": "结果", "hint": "研究结果展示"},
            {"level": 2, "title": "2.1 基本结果", "hint": "主要数据结果"},
            {"level": 2, "title": "2.2 相关分析", "hint": "相关性分析"},
            {"level": 1, "title": "讨论", "hint": "结果分析与解释"},
            {"level": 2, "title": "3.1 主要发现", "hint": "核心结果讨论"},
            {"level": 2, "title": "3.2 机制探讨", "hint": "机理分析"},
            {"level": 2, "title": "3.3 临床意义", "hint": "实际应用价值"},
            {"level": 1, "title": "结论", "hint": "研究结论"},
            {"level": 1, "title": "参考文献", "hint": "医学期刊格式"},
            {"level": 1, "title": "综述", "hint": "相关研究综述"},
        ],
        PaperType.ENGINEERING: [
            {"level": 1, "title": "摘要", "hint": "工程背景、方法、结果、结论"},
            {"level": 1, "title": "Abstract", "hint": "英文摘要"},
            {"level": 1, "title": "第1章 绪论", "hint": "工程背景与意义"},
            {"level": 2, "title": "1.1 项目背景", "hint": "工程项目背景"},
            {"level": 2, "title": "1.2 研究意义", "hint": "理论和实践价值"},
            {"level": 1, "title": "第2章 工程概况与地质条件", "hint": "工程基本情况"},
            {"level": 2, "title": "2.1 工程概况", "hint": "工程基本信息"},
            {"level": 2, "title": "2.2 地质条件", "hint": "地质环境分析"},
            {"level": 1, "title": "第3章 设计方案", "hint": "工程设计方案"},
            {"level": 2, "title": "3.1 设计原则", "hint": "设计指导思想"},
            {"level": 2, "title": "3.2 方案比选", "hint": "多方案对比"},
            {"level": 1, "title": "第4章 施工技术", "hint": "施工方法工艺"},
            {"level": 2, "title": "4.1 施工工艺", "hint": "核心技术工艺"},
            {"level": 2, "title": "4.2 质量控制", "hint": "质量保障措施"},
            {"level": 1, "title": "第5章 监测与反馈", "hint": "施工监测"},
            {"level": 1, "title": "第6章 结论与展望", "hint": "总结建议"},
            {"level": 1, "title": "参考文献", "hint": "工程标准格式"},
            {"level": 1, "title": "致谢", "hint": "感谢"},
        ],
        PaperType.LIBERAL_ARTS: [
            {"level": 1, "title": "摘要", "hint": "研究问题、方法、结论"},
            {"level": 1, "title": "Abstract", "hint": "英文摘要"},
            {"level": 1, "title": "绪论", "hint": "研究背景、问题、意义"},
            {"level": 2, "title": "一、问题的提出", "hint": "研究问题"},
            {"level": 2, "title": "二、研究现状", "hint": "文献综述"},
            {"level": 2, "title": "三、研究方法", "hint": "研究路径"},
            {"level": 1, "title": "正文", "hint": "核心论述"},
            {"level": 2, "title": "一、理论框架", "hint": "理论基础"},
            {"level": 2, "title": "二、现状分析", "hint": "问题分析"},
            {"level": 2, "title": "三、对策建议", "hint": "解决方案"},
            {"level": 1, "title": "结论", "hint": "研究结论"},
            {"level": 1, "title": "参考文献", "hint": "人文社科格式"},
            {"level": 1, "title": "致谢", "hint": "感谢"},
        ]
    }
    
    def __init__(self):
        self.papers: Dict[str, UserPaper] = {}
        self._load_papers()
    
    def _load_papers(self):
        """加载已保存的论文"""
        try:
            papers_file = PAPERS_DIR / "papers.json"
            if papers_file.exists():
                with open(papers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for p in data:
                        self.papers[p['paper_id']] = UserPaper(**p)
                logger.info(f"Loaded {len(self.papers)} papers")
        except Exception as e:
            logger.warning(f"Failed to load papers: {e}")
    
    def _save_papers(self):
        """保存论文到磁盘"""
        try:
            papers_file = PAPERS_DIR / "papers.json"
            with open(papers_file, 'w', encoding='utf-8') as f:
                json.dump([p.model_dump() for p in self.papers.values()], f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save papers: {e}")
    
    def _generate_paper_id(self) -> str:
        """生成论文ID"""
        return f"paper_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _estimate_word_count(self, sections: List[Dict]) -> int:
        """估算总字数"""
        counts = {1: 800, 2: 500, 3: 300}  # 各层级章节参考字数
        return sum(counts.get(s.get('level', 1), 300) for s in sections)
    
    def generate_outline(self, request) -> OutlineResponse:
        """生成论文大纲"""
        paper_id = self._generate_paper_id()
        
        # 获取对应类型的大纲模板
        template = self.OUTLINE_TEMPLATES.get(request.paper_type, self.OUTLINE_TEMPLATES[PaperType.COMPUTER])
        
        sections = []
        section_id = 0
        
        for t in template:
            section_id += 1
            sid = f"sec_{section_id:03d}"
            sections.append(OutlineSection(
                id=sid,
                title=t['title'],
                level=t['level'],
                content_hint=t.get('hint', ''),
                word_count=counts.get(t['level'], 500) if (counts := {1: 800, 2: 500, 3: 300}) else 500
            ))
        
        total_words = self._estimate_word_count(template)
        
        outline = OutlineResponse(
            paper_id=paper_id,
            title=request.title,
            sections=sections,
            total_words=total_words
        )
        
        # 保存论文记录
        paper = UserPaper(
            paper_id=paper_id,
            user_id=request.user_id,
            title=request.title,
            paper_type=request.paper_type,
            status="outline",
            outline=outline,
            progress=0.1
        )
        self.papers[paper_id] = paper
        self._save_papers()
        
        logger.info(f"Generated outline for paper {paper_id}")
        return outline
    
    def generate_content(self, paper_id: str, section_ids: Optional[List[str]] = None) -> ContentResponse:
        """生成论文内容"""
        paper = self.papers.get(paper_id)
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        if not paper.outline:
            raise ValueError(f"Paper {paper_id} has no outline")
        
        sections = paper.outline.sections
        if section_ids:
            sections = [s for s in sections if s.id in section_ids]
        
        content_sections = []
        all_references = []
        
        for section in sections:
            # 生成章节内容
            content = self._generate_section_content(section, paper)
            
            # 检测是否需要图表
            has_chart = any(keyword in section.title.lower() for keyword in ['数据', '统计', '分析', '结果', '测试'])
            
            content_sections.append(ContentSection(
                section_id=section.id,
                title=section.title,
                content=content,
                word_count=len(content),
                has_chart=has_chart,
                chart_type="bar" if has_chart else None,
                references=[]
            ))
            
            # 分配参考文献
            if "参考文献" in section.title:
                refs = self._generate_references(paper.paper_type, ThesisFormat.CHINESE_GB_T)
                all_references = [r.id for r in refs]
        
        total_words = sum(s.word_count for s in content_sections)
        
        content = ContentResponse(
            paper_id=paper_id,
            title=paper.title,
            sections=content_sections,
            total_words=total_words,
            references=all_references
        )
        
        paper.content = content
        paper.status = "content"
        paper.progress = 0.5
        paper.word_count = total_words
        self._save_papers()
        
        logger.info(f"Generated content for paper {paper_id}, words: {total_words}")
        return content
    
    def _generate_section_content(self, section: OutlineSection, paper: UserPaper) -> str:
        """生成单个章节内容"""
        # 基于关键词和标题生成相关内容
        title = section.title
        hint = section.content_hint or ""
        
        if "摘要" in title:
            return self._generate_abstract(paper)
        elif "绪论" in title or "前言" in title:
            return self._generate_introduction(paper)
        elif "参考文献" in title:
            return self._generate_references_section(paper.paper_type)
        elif "致谢" in title:
            return self._generate_acknowledgments()
        elif "总结" in title or "结论" in title:
            return self._generate_conclusion(paper)
        else:
            return self._generate_body_section(title, hint, paper)
    
    def _generate_abstract(self, paper: UserPaper) -> str:
        """生成摘要"""
        keywords_str = "、".join(paper.outline.sections[0].title.split()[:5]) if paper.outline else "研究"
        return f"""## 摘要

本文针对{keywords_str}进行了深入研究。首先介绍了研究背景与意义，分析了国内外研究现状；其次详细阐述了相关技术与理论基础；然后进行了系统需求分析和可行性研究；接着设计了系统的总体架构和功能模块；最后实现了系统开发并进行测试验证。

**关键词**：{"、".join([paper.title.split()[0] if paper.title else '研究'] * 3 + ['技术', '方法'])}；{"；".join(paper.outline.sections[0].title.split()[:3]) if paper.outline else '应用'}"""
    
    def _generate_introduction(self, paper: UserPaper) -> str:
        """生成绪论"""
        return f"""## 第1章 绪论

### 1.1 研究背景

随着信息技术的飞速发展，{paper.title}已成为当前研究热点之一。在当今数字化时代，传统的处理方式已经难以满足日益增长的需求，因此需要采用新的技术手段来解决这些问题。

### 1.2 研究意义

本研究具有重要的理论意义和实际应用价值：

1. **理论意义**：丰富了相关领域的理论基础，为后续研究提供了参考依据。
2. **实践意义**：研究成果可直接应用于实际生产生活中，产生经济效益和社会效益。

### 1.3 国内外研究现状

国际上，发达国家在该领域的研究起步较早，已取得了一系列重要成果。国内学者也进行了大量研究，但在某些关键技术上仍存在不足。"""
    
    def _generate_body_section(self, title: str, hint: str, paper: UserPaper) -> str:
        """生成正文章节"""
        return f"""### {title}

{hint}

随着研究的不断深入，{paper.title}领域取得了显著进展。本章将详细介绍相关理论基础和技术实现。

#### 背景介绍

在该领域的发展过程中，涌现出了许多重要的理论和方法。这些理论为后续的研究提供了重要的支撑。

#### 现状分析

通过对现有技术的分析，可以看出当前主流方法的优势和不足。本研究在继承原有优势的基础上，提出了一种改进方案。

#### 关键技术

本研究采用的核心技术包括：
- 数据采集与预处理技术
- 特征提取与选择方法
- 模型构建与优化策略
- 结果验证与评估体系"""
    
    def _generate_references_section(self, paper_type: PaperType) -> str:
        """生成参考文献章节"""
        return """## 参考文献

[1] 张三, 李四. 基于深度学习的技术研究[J]. 计算机学报, 2023, 46(5): 1024-1040.
[2] 王五, 赵六. 面向实际应用的方法论[M]. 北京: 科学出版社, 2022.
[3] 陈七, 周八. 学术论文写作规范[S]. 北京: 高等教育出版社, 2021.
[4] 刘九, 孙十. 国际前沿技术综述[C]. 北京: 清华大学出版社, 2023.
[5] 周十一, 吴十二. 网络安全机制研究[J]. 信息安全学报, 2022, 8(3): 56-68."""
    
    def _generate_acknowledgments(self) -> str:
        """生成致谢"""
        return """## 致谢

在本论文完成之际，我谨向所有关心和帮助过我的老师、同学和家人表示衷心的感谢！

首先，感谢我的导师在课题研究过程中给予的悉心指导和帮助，导师严谨的治学态度和渊博的知识使我受益匪浅。

其次，感谢实验室的同学们在日常学习和生活中给予的支持和帮助，与你们的交流讨论极大地拓宽了我的思路。

最后，感谢家人对我学业的理解和支持，是你们的无私付出让我能够专心完成学业。

"""
    
    def _generate_conclusion(self, paper: UserPaper) -> str:
        """生成结论"""
        return """## 第7章 总结与展望

### 7.1 工作总结

本文针对研究问题进行了系统性的分析和设计，主要工作包括：

1. 深入调研了相关领域的国内外研究现状，明确了研究方向。
2. 完成了系统需求分析和可行性研究，确定了技术路线。
3. 进行了系统总体设计和详细设计，制定了实施方案。
4. 完成了系统开发和测试，验证了方案的可行性。

### 7.2 未来展望

虽然本文取得了一定的研究成果，但仍存在一些不足之处，需要在后续工作中进一步完善：

1. 在更大规模的数据集上验证系统的性能。
2. 优化算法，提高处理效率。
3. 扩展系统功能，满足更多应用场景需求。
"""
    
    def _generate_references(self, paper_type: PaperType, format: ThesisFormat) -> List[ReferenceItem]:
        """生成参考文献列表"""
        refs = [
            ReferenceItem(
                id="[1]",
                type="journal",
                title="基于深度学习的图像识别技术研究",
                authors=["张三", "李四", "王五"],
                year=2023,
                journal="计算机学报",
                volume="46",
                issue="5",
                pages="1024-1040",
                doi="10.1234/cjc.2023.001"
            ),
            ReferenceItem(
                id="[2]",
                type="conference",
                title="面向大规模数据的处理方法",
                authors=["赵六", "孙七"],
                year=2022,
                journal="全国数据库学术会议",
                pages="156-163"
            ),
            ReferenceItem(
                id="[3]",
                type="book",
                title="机器学习理论与实践",
                authors=["周八"],
                year=2021,
                journal="清华大学出版社"
            ),
            ReferenceItem(
                id="[4]",
                type="website",
                title="GitHub开源项目",
                authors=["吴九"],
                year=2023,
                url="https://github.com/example/project"
            ),
            ReferenceItem(
                id="[5]",
                type="journal",
                title="云计算环境下的资源调度策略",
                authors=["郑十", "刘一"],
                year=2023,
                journal="软件学报",
                volume="34",
                issue="2",
                pages="89-102",
                doi="10.1234/js.2023.002"
            ),
        ]
        return refs
    
    def get_paper(self, paper_id: str) -> Optional[UserPaper]:
        """获取论文"""
        return self.papers.get(paper_id)
    
    def get_user_papers(self, user_id: str) -> List[UserPaper]:
        """获取用户的所有论文"""
        return [p for p in self.papers.values() if p.user_id == user_id]
    
    def update_progress(self, paper_id: str, progress: float):
        """更新进度"""
        if paper_id in self.papers:
            self.papers[paper_id].progress = progress
            self.papers[paper_id].updated_at = datetime.now()
            self._save_papers()
    
    def generate_plagiarism_report(self, paper_id: str) -> PlagiarismReport:
        """生成查重报告（模拟）"""
        import random
        paper = self.papers.get(paper_id)
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")
        
        section_rates = {}
        for section in (paper.content.sections if paper.content else []):
            # 模拟各章节查重率
            section_rates[section.section_id] = round(random.uniform(5, 25), 2)
        
        overall = round(sum(section_rates.values()) / len(section_rates) if section_rates else 15, 2)
        
        suggestions = []
        if overall > 20:
            suggestions.append("建议增加原创性内容，减少直接引用")
        if overall > 15:
            suggestions.append("可尝试改变句式结构，用自己的语言重新表述")
        suggestions.append("适当增加案例分析和方法论部分的比重")
        
        return PlagiarismReport(
            paper_id=paper_id,
            overall_rate=overall,
            section_rates=section_rates,
            matched_sources=[
                {"source": "中国知网", "match_rate": round(overall * 0.6, 2)},
                {"source": "万方数据库", "match_rate": round(overall * 0.3, 2)},
                {"source": "其他", "match_rate": round(overall * 0.1, 2)}
            ],
            suggestions=suggestions
        )


# 全局实例
paper_generator = PaperGenerator()
