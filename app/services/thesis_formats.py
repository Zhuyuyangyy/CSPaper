# -*- coding: utf-8 -*-
"""
论文格式模板 - 符合学校毕设格式要求
支持：本科论文、硕士论文、博士论文、各学科格式
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class ThesisLevel(str, Enum):
    """论文学位等级"""
    BACHELOR = "bachelor"      # 本科
    MASTER = "master"          # 硕士
    DOCTOR = "doctor"         # 博士


class ThesisDiscipline(str, Enum):
    """学科门类"""
    COMPUTER = "computer"      # 计算机
    MEDICINE = "medicine"     # 医学
    ENGINEERING = "engineering"  # 工科
    LIBERAL_ARTS = "liberal_arts"  # 文科


@dataclass
class FormatConfig:
    """格式配置"""
    # 页面设置
    page_size: str = "A4"
    margin_top: float = 2.5      # 上边距 cm
    margin_bottom: float = 2.0  # 下边距
    margin_left: float = 3.0     # 左边界
    margin_right: float = 2.5     # 右边界
    line_spacing: float = 1.5    # 行间距
    
    # 字体设置
    font_title: str = "黑体"
    font_content: str = "宋体"
    font_english: str = "Times New Roman"
    font_size_title: int = 3      # 三号
    font_size_content: int = 5   # 五号
    font_size_chapter: int = 3   # 三号
    font_size_section: int = 5   # 五号
    
    # 标题层级
    chapter_numbering: str = "第X章"  # 第X章
    section_numbering: str = "X.X"     # 1.1
    subsection_numbering: str = "X.X.X"  # 1.1.1
    
    # 摘要要求
    abstract_words_limit: int = 300
    keywords_count: int = 3
    
    # 目录要求
    toc_depth: int = 3           # 目录深度
    toc_page_separator: str = ".........."  # 目录填充符号


# 各学科论文格式配置
THESIS_FORMATS: Dict[str, FormatConfig] = {
    # 计算机类本科论文格式
    "computer_bachelor": FormatConfig(
        page_size="A4",
        margin_top=2.5,
        margin_bottom=2.0,
        margin_left=3.0,
        margin_right=2.5,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=3,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X",
        abstract_words_limit=300,
        keywords_count=3
    ),
    
    # 医学类本科论文格式
    "medicine_bachelor": FormatConfig(
        page_size="A4",
        margin_top=2.5,
        margin_bottom=2.0,
        margin_left=2.5,
        margin_right=2.5,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=3,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X",
        abstract_words_limit=400,
        keywords_count=4
    ),
    
    # 工科类本科论文格式
    "engineering_bachelor": FormatConfig(
        page_size="A4",
        margin_top=2.5,
        margin_bottom=2.0,
        margin_left=3.0,
        margin_right=2.5,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=3,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X",
        abstract_words_limit=250,
        keywords_count=3
    ),
    
    # 文科类本科论文格式
    "liberal_arts_bachelor": FormatConfig(
        page_size="A4",
        margin_top=2.8,
        margin_bottom=2.3,
        margin_left=3.0,
        margin_right=2.8,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=3,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X",
        abstract_words_limit=500,
        keywords_count=5
    ),
    
    # 硕士论文格式
    "master": FormatConfig(
        page_size="A4",
        margin_top=2.5,
        margin_bottom=2.0,
        margin_left=3.0,
        margin_right=2.5,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=3,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X.X",
        abstract_words_limit=500,
        keywords_count=4
    ),
    
    # 博士论文格式
    "doctor": FormatConfig(
        page_size="A4",
        margin_top=3.0,
        margin_bottom=2.5,
        margin_left=3.0,
        margin_right=2.5,
        line_spacing=1.5,
        font_title="黑体",
        font_content="宋体",
        font_size_title=2,
        font_size_content=5,
        chapter_numbering="第X章",
        section_numbering="X.X.X.X",
        abstract_words_limit=800,
        keywords_count=5
    )
}


def get_format_config(discipline: str, level: str = "bachelor") -> FormatConfig:
    """获取格式配置"""
    key = f"{discipline}_{level}"
    return THESIS_FORMATS.get(key, THESIS_FORMATS["computer_bachelor"])


def format_chapter_title(chapter_num: int, title: str, config: FormatConfig) -> str:
    """格式化章标题"""
    if config.chapter_numbering == "第X章":
        return f"第{chapter_num}章 {title}"
    return f"{chapter_num} {title}"


def format_section_title(section_num: str, title: str, level: int = 1) -> str:
    """格式化节标题"""
    if level == 1:
        return f"{section_num} {title}"
    elif level == 2:
        return f"{section_num} {title}"
    return f"{section_num} {title}"


# 标准论文结构模板
STANDARD_THESIS_STRUCTURE = {
    # 计算机类
    "computer": [
        {"id": "abstract", "title": "摘要", "type": "chapter", "required": True},
        {"id": "abstract_en", "title": "Abstract", "type": "chapter", "required": True},
        {"id": "chapter1", "title": "绪论", "type": "chapter", "required": True},
        {"id": "chapter1_1", "title": "研究背景", "type": "section", "level": 1},
        {"id": "chapter1_2", "title": "研究意义", "type": "section", "level": 1},
        {"id": "chapter1_3", "title": "国内外研究现状", "type": "section", "level": 1},
        {"id": "chapter1_4", "title": "研究内容与目标", "type": "section", "level": 1},
        {"id": "chapter1_5", "title": "论文结构安排", "type": "section", "level": 1},
        {"id": "chapter2", "title": "相关技术与理论基础", "type": "chapter", "required": True},
        {"id": "chapter2_1", "title": "技术一", "type": "section", "level": 1},
        {"id": "chapter2_2", "title": "技术二", "type": "section", "level": 1},
        {"id": "chapter3", "title": "需求分析", "type": "chapter", "required": True},
        {"id": "chapter3_1", "title": "业务需求分析", "type": "section", "level": 1},
        {"id": "chapter3_2", "title": "功能需求分析", "type": "section", "level": 1},
        {"id": "chapter3_3", "title": "非功能需求分析", "type": "section", "level": 1},
        {"id": "chapter4", "title": "系统设计", "type": "chapter", "required": True},
        {"id": "chapter4_1", "title": "系统架构设计", "type": "section", "level": 1},
        {"id": "chapter4_2", "title": "功能模块设计", "type": "section", "level": 1},
        {"id": "chapter4_3", "title": "数据库设计", "type": "section", "level": 1},
        {"id": "chapter5", "title": "系统实现", "type": "chapter", "required": True},
        {"id": "chapter5_1", "title": "开发环境", "type": "section", "level": 1},
        {"id": "chapter5_2", "title": "主要功能实现", "type": "section", "level": 1},
        {"id": "chapter5_3", "title": "核心代码分析", "type": "section", "level": 1},
        {"id": "chapter6", "title": "系统测试", "type": "chapter", "required": True},
        {"id": "chapter6_1", "title": "测试环境", "type": "section", "level": 1},
        {"id": "chapter6_2", "title": "功能测试", "type": "section", "level": 1},
        {"id": "chapter6_3", "title": "性能测试", "type": "section", "level": 1},
        {"id": "chapter7", "title": "总结与展望", "type": "chapter", "required": True},
        {"id": "references", "title": "参考文献", "type": "chapter", "required": True},
        {"id": "thanks", "title": "致谢", "type": "chapter", "required": False},
        {"id": "appendix", "title": "附录", "type": "chapter", "required": False},
    ],
    
    # 医学类
    "medicine": [
        {"id": "abstract", "title": "摘要", "type": "chapter", "required": True},
        {"id": "abstract_en", "title": "Abstract", "type": "chapter", "required": True},
        {"id": "intro", "title": "前言", "type": "chapter", "required": True},
        {"id": "materials", "title": "资料与方法", "type": "chapter", "required": True},
        {"id": "materials_1", "title": "一般资料", "type": "section", "level": 1},
        {"id": "materials_2", "title": "纳入与排除标准", "type": "section", "level": 1},
        {"id": "materials_3", "title": "研究方法", "type": "section", "level": 1},
        {"id": "materials_4", "title": "统计学方法", "type": "section", "level": 1},
        {"id": "results", "title": "结果", "type": "chapter", "required": True},
        {"id": "results_1", "title": "基线资料比较", "type": "section", "level": 1},
        {"id": "results_2", "title": "主要结局指标", "type": "section", "level": 1},
        {"id": "results_3", "title": "安全性评价", "type": "section", "level": 1},
        {"id": "discussion", "title": "讨论", "type": "chapter", "required": True},
        {"id": "discussion_1", "title": "主要发现", "type": "section", "level": 1},
        {"id": "discussion_2", "title": "结果分析", "type": "section", "level": 1},
        {"id": "discussion_3", "title": "局限性", "type": "section", "level": 1},
        {"id": "conclusion", "title": "结论", "type": "chapter", "required": True},
        {"id": "references", "title": "参考文献", "type": "chapter", "required": True},
        {"id": "thanks", "title": "致谢", "type": "chapter", "required": False},
    ],
    
    # 工科类
    "engineering": [
        {"id": "abstract", "title": "摘要", "type": "chapter", "required": True},
        {"id": "abstract_en", "title": "Abstract", "type": "chapter", "required": True},
        {"id": "chapter1", "title": "绪论", "type": "chapter", "required": True},
        {"id": "chapter1_1", "title": "研究背景与意义", "type": "section", "level": 1},
        {"id": "chapter1_2", "title": "国内外研究进展", "type": "section", "level": 1},
        {"id": "chapter1_3", "title": "主要研究内容", "type": "section", "level": 1},
        {"id": "chapter2", "title": "理论基础", "type": "chapter", "required": True},
        {"id": "chapter3", "title": "问题分析", "type": "chapter", "required": True},
        {"id": "chapter4", "title": "方案设计", "type": "chapter", "required": True},
        {"id": "chapter4_1", "title": "设计目标", "type": "section", "level": 1},
        {"id": "chapter4_2", "title": "总体方案", "type": "section", "level": 1},
        {"id": "chapter4_3", "title": "详细设计", "type": "section", "level": 1},
        {"id": "chapter5", "title": "实现与验证", "type": "chapter", "required": True},
        {"id": "chapter5_1", "title": "实现方案", "type": "section", "level": 1},
        {"id": "chapter5_2", "title": "实验验证", "type": "section", "level": 1},
        {"id": "chapter6", "title": "结论与展望", "type": "chapter", "required": True},
        {"id": "references", "title": "参考文献", "type": "chapter", "required": True},
        {"id": "thanks", "title": "致谢", "type": "chapter", "required": False},
    ],
    
    # 文科类
    "liberal_arts": [
        {"id": "abstract", "title": "摘要", "type": "chapter", "required": True},
        {"id": "abstract_en", "title": "Abstract", "type": "chapter", "required": True},
        {"id": "intro", "title": "引言", "type": "chapter", "required": True},
        {"id": "chapter1", "title": "文献综述", "type": "chapter", "required": True},
        {"id": "chapter1_1", "title": "国内研究综述", "type": "section", "level": 1},
        {"id": "chapter1_2", "title": "国外研究综述", "type": "section", "level": 1},
        {"id": "chapter2", "title": "理论框架", "type": "chapter", "required": True},
        {"id": "chapter3", "title": "研究方法", "type": "chapter", "required": True},
        {"id": "chapter4", "title": "实证分析", "type": "chapter", "required": True},
        {"id": "chapter4_1", "title": "案例分析", "type": "section", "level": 1},
        {"id": "chapter4_2", "title": "数据论证", "type": "section", "level": 1},
        {"id": "chapter5", "title": "结论与讨论", "type": "chapter", "required": True},
        {"id": "references", "title": "参考文献", "type": "chapter", "required": True},
        {"id": "thanks", "title": "致谢", "type": "chapter", "required": False},
        {"id": "appendix", "title": "附录", "type": "chapter", "required": False},
    ]
}


def get_thesis_structure(paper_type: str) -> List[Dict]:
    """获取论文结构"""
    return STANDARD_THESIS_STRUCTURE.get(paper_type, STANDARD_THESIS_STRUCTURE["computer"])