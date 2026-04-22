# -*- coding: utf-8 -*-
"""
论文生成API路由
================
支持：大纲生成、正文写作、参考文献、查重、导出
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.paper_models import (
    GenerationRequest, OutlineResponse, ContentResponse,
    ReferenceResponse, ReferenceItem, ExportRequest, ExportResponse,
    PlagiarismReport, ChartRequest, ChartResponse, UserPaper,
    PaperType, ThesisFormat
)
from app.services.paper_generator import paper_generator
from app.services.docx_exporter import docx_exporter, pdf_exporter

router = APIRouter(prefix="/api/paper", tags=["paper"])
logger = logging.getLogger("PaperRouter")


# ==================== 论文生成 ====================
@router.post("/generate/outline", response_model=OutlineResponse)
async def generate_outline(request: GenerationRequest):
    """生成论文大纲"""
    try:
        outline = paper_generator.generate_outline(request)
        return outline
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/content", response_model=ContentResponse)
async def generate_content(paper_id: str, section_ids: str = None):
    """生成论文正文内容
    
    Args:
        paper_id: 论文ID
        section_ids: 要生成的章节ID列表，逗号分隔；None表示全部
    """
    try:
        section_list = section_ids.split(",") if section_ids else None
        content = paper_generator.generate_content(paper_id, section_list)
        return content
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/full", response_model=ContentResponse)
async def generate_full_paper(paper_id: str, background_tasks: BackgroundTasks):
    """一键生成完整论文（后台运行）"""
    try:
        # 更新状态
        paper_generator.update_progress(paper_id, 0.2)
        
        # 生成内容
        content = paper_generator.generate_content(paper_id)
        paper_generator.update_progress(paper_id, 0.8)
        
        return content
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Full paper generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 参考文献 ====================
@router.get("/references/{paper_id}", response_model=ReferenceResponse)
async def get_references(paper_id: str, format: ThesisFormat = ThesisFormat.CHINESE_GB_T):
    """获取论文参考文献"""
    try:
        paper = paper_generator.get_paper(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # 生成参考文献
        from app.services.paper_generator import paper_generator
        refs = paper_generator._generate_references(paper.paper_type, format)
        
        return ReferenceResponse(
            paper_id=paper_id,
            references=refs,
            format=format,
            count=len(refs)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get references failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 查重报告 ====================
@router.get("/plagiarism/{paper_id}", response_model=PlagiarismReport)
async def get_plagiarism_report(paper_id: str):
    """获取查重报告（模拟）"""
    try:
        report = paper_generator.generate_plagiarism_report(paper_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Plagiarism report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 图表生成 ====================
@router.post("/chart", response_model=ChartResponse)
async def generate_chart(request: ChartRequest):
    """生成图表"""
    import uuid
    import random
    
    chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    
    # 生成图表Markdown表示
    chart_markdown = f"![{request.title}](data:image/svg+xml;base64,...)"
    
    # 生成SVG图表
    svg_content = generate_svg_chart(request.chart_type, request.title, request.data_description)
    
    # 保存图表
    from pathlib import Path
    charts_dir = Path(r"C:\Users\联想\.openclaw\workspace\data\charts")
    charts_dir.mkdir(exist_ok=True)
    
    chart_file = charts_dir / f"{chart_id}.svg"
    with open(chart_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    return ChartResponse(
        chart_id=chart_id,
        chart_type=request.chart_type,
        markdown_image=chart_markdown,
        standalone_url=f"/api/paper/chart/{chart_id}",
        insert_code=f'<figure>\n  <img src="/api/paper/chart/{chart_id}" alt="{request.title}"/>\n  <figcaption>图1: {request.title}</figcaption>\n</figure>'
    )


def generate_svg_chart(chart_type: str, title: str, data_desc: str) -> str:
    """生成SVG图表"""
    import random
    
    width, height = 600, 400
    padding = 60
    
    if chart_type == "bar":
        # 柱状图
        bars = 6
        bar_width = (width - 2 * padding) / bars - 20
        max_val = 100
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="{width}" height="{height}" fill="white"/>
    <text x="{width/2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
    <g transform="translate({padding}, {padding})">
'''
        for i in range(bars):
            val = random.randint(20, 95)
            x = i * ((width - 2 * padding) / bars) + 10
            bar_height = val / max_val * (height - 2 * padding - 40)
            y = height - 2 * padding - bar_height - 20
            color = f"hsl({200 + i * 20}, 70%, 50%)"
            svg += f'''        <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="3"/>
        <text x="{x + bar_width/2}" y="{height - 2 * padding}" text-anchor="middle" font-size="11">类{i+1}</text>
        <text x="{x + bar_width/2}" y="{y - 8}" text-anchor="middle" font-size="10">{val}%</text>
'''
        svg += '''    </g>
</svg>'''
        return svg
    
    elif chart_type == "line":
        # 折线图
        points = []
        for i in range(8):
            x = i * ((width - 2 * padding) / 7) + padding
            y = height - padding - random.randint(50, 300)
            points.append(f"{x},{y}")
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="{width}" height="{height}" fill="white"/>
    <text x="{width/2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
    <polyline points="{' '.join(points)}" fill="none" stroke="#4A90D9" stroke-width="3"/>
'''
        for p in points:
            x, y = p.split(',')
            svg += f'    <circle cx="{x}" cy="{y}" r="5" fill="#4A90D9"/>\n'
        svg += '''</svg>'''
        return svg
    
    elif chart_type == "pie":
        # 饼图
        slices = [(25, "#FF6B6B"), (30, "#4ECDC4"), (20, "#45B7D1"), (15, "#96CEB4"), (10, "#FFEAA7")]
        start_angle = 0
        
        cx, cy = width // 2, height // 2 + 20
        r = 120
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="{width}" height="{height}" fill="white"/>
    <text x="{width/2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
'''
        
        for pct, color in slices:
            end_angle = start_angle + pct * 3.6
            x1 = cx + r * np.cos(np.radians(start_angle - 90))
            y1 = cy + r * np.sin(np.radians(start_angle - 90))
            x2 = cx + r * np.cos(np.radians(end_angle - 90))
            y2 = cy + r * np.sin(np.radians(end_angle - 90))
            
            large_arc = 1 if pct > 50 else 0
            path = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
            svg += f'    <path d="{path}" fill="{color}"/>\n'
            svg += f'    <text x="{cx + r*0.6*np.cos(np.radians((start_angle + end_angle)/2 - 90))}" y="{cy + r*0.6*np.sin(np.radians((start_angle + end_angle)/2 - 90))}" text-anchor="middle" fill="white" font-size="11">{pct}%</text>\n'
            start_angle = end_angle
        
        svg += '</svg>'
        return svg
    
    else:
        # 默认返回表格
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="{width}" height="{height}" fill="white"/>
    <text x="{width/2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
    <rect x="{padding}" y="{padding+20}" width="{width-2*padding}" height="{height-2*padding-40}" fill="none" stroke="#333" stroke-width="1"/>
    <text x="{width/2}" y="{height-20}" text-anchor="middle" fill="#666" font-size="12">{data_desc}</text>
</svg>'''


@router.get("/chart/{chart_id}")
async def get_chart(chart_id: str):
    """获取图表文件"""
    from pathlib import Path
    chart_file = Path(rf"C:\Users\联想\.openclaw\workspace\data\charts\{chart_id}.svg")
    if not chart_file.exists():
        raise HTTPException(status_code=404, detail="Chart not found")
    return FileResponse(chart_file, media_type="image/svg+xml")


# ==================== 导出功能 ====================
@router.post("/export", response_model=ExportResponse)
async def export_paper(request: ExportRequest):
    """导出论文为DOCX或PDF"""
    try:
        paper = paper_generator.get_paper(request.paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        if request.format == "docx":
            result = docx_exporter.export(paper, request)
        elif request.format == "pdf":
            result = pdf_exporter.export(paper, request)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        # 更新状态
        paper.status = "exported"
        paper_generator._save_papers()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{paper_id}")
async def download_paper(paper_id: str, format: str = "docx"):
    """下载论文文件"""
    from pathlib import Path
    
    paper = paper_generator.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    export_dir = Path(r"C:\Users\联想\.openclaw\workspace\data\exports")
    
    # 查找最新的导出文件
    files = list(export_dir.glob(f"*{paper.title[:20]}*"))
    if not files:
        raise HTTPException(status_code=404, detail="Export file not found")
    
    latest = max(files, key=lambda p: p.stat().st_mtime)
    return FileResponse(latest, filename=latest.name)


# ==================== 论文管理 ====================
@router.get("/paper/{paper_id}", response_model=UserPaper)
async def get_paper(paper_id: str):
    """获取论文详情"""
    paper = paper_generator.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.get("/papers/{user_id}")
async def get_user_papers(user_id: str):
    """获取用户的所有论文"""
    papers = paper_generator.get_user_papers(user_id)
    return {
        "user_id": user_id,
        "papers": papers,
        "total_count": len(papers)
    }


@router.delete("/paper/{paper_id}")
async def delete_paper(paper_id: str):
    """删除论文"""
    if paper_id in paper_generator.papers:
        del paper_generator.papers[paper_id]
        paper_generator._save_papers()
        return {"message": "Paper deleted"}
    raise HTTPException(status_code=404, detail="Paper not found")


# ==================== 进度管理 ====================
@router.get("/progress/{paper_id}")
async def get_progress(paper_id: str):
    """获取论文生成进度"""
    paper = paper_generator.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "paper_id": paper_id,
        "progress": paper.progress,
        "status": paper.status,
        "word_count": paper.word_count
    }


@router.post("/progress/{paper_id}")
async def update_progress(paper_id: str, progress: float):
    """更新论文进度"""
    paper_generator.update_progress(paper_id, progress)
    return {"message": "Progress updated"}
