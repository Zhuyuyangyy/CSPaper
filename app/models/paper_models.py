# -*- coding: utf-8 -*-
"""
论文生成数据模型
==================
支持医学/计算机/工科/文科多类型论文生成
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PaperType(str, Enum):
    """论文类型"""
    MEDICAL = "medical"       # 医学
    COMPUTER = "computer"     # 计算机
    ENGINEERING = "engineering"  # 工科
    LIBERAL_ARTS = "liberal_arts"  # 文科


class ThesisFormat(str, Enum):
    """论文格式标准"""
    CHINESE_GB_T = "gb_t"        # GB/T 7714 国标
    IEEE = "ieee"
    ACM = "acm"
    CHICAGO = "chicago"


class GenerationRequest(BaseModel):
    """论文生成请求"""
    paper_type: PaperType = Field(default=PaperType.COMPUTER, description="论文类型")
    title: str = Field(..., description="论文标题", min_length=5, max_length=200)
    subject: str = Field(..., description="学科专业", min_length=2, max_length=100)
    keywords: List[str] = Field(..., description="关键词", min_length=3, max_length=8)
    outline_type: str = Field(default="standard", description="大纲类型: standard/detailed/brief")
    language: str = Field(default="zh", description="语言: zh/en")
    thesis_format: ThesisFormat = Field(default=ThesisFormat.CHINESE_GB_T, description="参考文献格式")
    user_id: str = Field(default="default_user", description="用户ID")
    requirements: Optional[str] = Field(None, description="其他要求")


class OutlineSection(BaseModel):
    """大纲章节"""
    id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    level: int = Field(default=1, description="层级: 1=一级, 2=二级, 3=三级")
    content_hint: Optional[str] = Field(None, description="内容提示")
    word_count: int = Field(default=0, description="预估字数")


class OutlineResponse(BaseModel):
    """大纲响应"""
    paper_id: str = Field(..., description="论文ID")
    title: str = Field(..., description="论文标题")
    sections: List[OutlineSection] = Field(..., description="章节列表")
    total_words: int = Field(default=0, description="总字数预估")
    created_at: datetime = Field(default_factory=datetime.now)


class ContentSection(BaseModel):
    """内容章节"""
    section_id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容(Markdown)")
    word_count: int = Field(0, description="字数")
    has_chart: bool = Field(default=False, description="是否包含图表")
    chart_type: Optional[str] = Field(None, description="图表类型")
    references: List[str] = Field(default_factory=list, description="引用的参考文献")


class ContentResponse(BaseModel):
    """内容响应"""
    paper_id: str
    title: str
    sections: List[ContentSection]
    total_words: int
    references: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


class ReferenceItem(BaseModel):
    """参考文献条目"""
    id: str = Field(..., description="序号")
    type: str = Field(..., description="类型: journal/conference/book/website")
    title: str = Field(..., description="标题")
    authors: List[str] = Field(..., description="作者列表")
    year: int = Field(..., description="年份")
    journal: Optional[str] = Field(None, description="期刊/会议")
    volume: Optional[str] = Field(None, description="卷")
    issue: Optional[str] = Field(None, description="期")
    pages: Optional[str] = Field(None, description="页码")
    doi: Optional[str] = Field(None, description="DOI")
    url: Optional[str] = Field(None, description="URL")
    abstract: Optional[str] = Field(None, description="摘要")


class ReferenceResponse(BaseModel):
    """参考文献响应"""
    paper_id: str
    references: List[ReferenceItem]
    format: ThesisFormat
    count: int


class ChartRequest(BaseModel):
    """图表生成请求"""
    paper_id: str
    chart_type: str = Field(..., description="图表类型: bar/line/pie/scatter/table/flowchart")
    title: str
    data_description: str = Field(..., description="数据描述")
    section_id: Optional[str] = Field(None, description="要插入的章节")


class ChartResponse(BaseModel):
    """图表响应"""
    chart_id: str
    chart_type: str
    markdown_image: str = Field(..., description="Markdown格式的图片引用")
    standalone_url: str = Field(..., description="独立访问URL")
    insert_code: str = Field(..., description="插入论文的代码")


class UserPaper(BaseModel):
    """用户论文记录"""
    paper_id: str
    user_id: str
    title: str
    subject: str = Field(default="计算机科学与技术", description="学科专业")
    paper_type: PaperType
    status: str = Field(default="draft", description="draft/outline/content/complete/exported")
    outline: Optional[OutlineResponse] = None
    content: Optional[ContentResponse] = None
    references: Optional[ReferenceResponse] = None
    progress: float = Field(default=0.0, description="完成进度 0-1")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    word_count: int = Field(default=0)


class ExportRequest(BaseModel):
    """导出请求"""
    paper_id: str
    format: str = Field(..., description="导出格式: docx/pdf")
    include_toc: bool = Field(default=True, description="包含目录")
    include_ref: bool = Field(default=True, description="包含参考文献")
    include_abstract: bool = Field(default=True, description="包含摘要")


class ExportResponse(BaseModel):
    """导出响应"""
    paper_id: str
    file_path: str
    file_name: str
    file_size: int
    download_url: str
    created_at: datetime = Field(default_factory=datetime.now)


class PlagiarismReport(BaseModel):
    """查重报告"""
    paper_id: str
    overall_rate: float = Field(..., description="总体查重率")
    section_rates: Dict[str, float] = Field(default_factory=dict, description="各章节查重率")
    matched_sources: List[Dict[str, Any]] = Field(default_factory=list, description="匹配来源")
    suggestions: List[str] = Field(default_factory=list, description="降重建议")


class UserHistory(BaseModel):
    """用户历史"""
    user_id: str
    papers: List[UserPaper]
    total_count: int
