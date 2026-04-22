# -*- coding: utf-8 -*-
"""
Resource Generator - 资源生成专家
==================================
生成符合 Three.js 要求的 3D 经络穴位动画描述。

核心职责：
1. 根据 TCM 知识生成穴位动画描述 (animation_desc)
2. 输出标准 JSON 格式供 Three.js 直接调用
3. 坐标数据严格符合人体经络解剖学逻辑

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 坐标系参考 (详见 app/static/models/README.md)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

标准模型: 1.8米男性站立姿态

坐标轴:
  X: 左右 (左负右正)
  Y: 上下 (足负头正)  ← 身高约 1.8 单位
  Z: 前后 (前正后负)

坐标示例:
  百会 (DU20): [0.00, 1.72, 0.00]  ← 头顶
  涌泉 (KI1):  [0.00, 0.02, 0.08]  ← 脚心
  合谷 (LI4):  [0.05, 1.35, 0.03]  ← 手背

GLTF 模型放置位置: app/static/models/
  - human_male_180cm.glb (推荐)
  - human_female_170cm.glb (备选)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 置信度阈值配置 (可在 .env 中覆盖)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REJECT   < 0.50  → 强制拒绝，完全拦截
UNCERTAIN 0.50-0.69 → 老中医审核，可能拒绝
ACCEPT   ≥ 0.70  → 通过校验

调优建议:
  如需更严格: 降低 ACCEPT 阈值至 0.75-0.80
  如需更宽松: 提高 ACCEPT 阈值至 0.65
  老中医太严厉: 可在 critique_agent.py 中降低权重的严厉程度

JSON 输出格式：
{
    "target_point": "LI4",
    "coords": [x, y, z],  // 穴位坐标
    "meridian_path": [[x1,y1,z1], ...],  // 经络路径
    "animation_desc": "...",  // 动画描述
    "meridian_name": "手阳明大肠经",
    "point_name": "合谷",
    "anatomy_note": "第1、2掌骨之间",
    "stimulation": "直刺0.5-1寸",
    "compatible_points": ["LR3", "LI11"],  // 配穴
    "threejs_ready": true
}

Author: Alice 🌸
"""

import sys
import json
import random
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field, asdict


# ==================== 穴位坐标数据 (标准化) ====================
class AcupuncturePointDatabase:
    """穴位坐标数据库 (简化版，单位为相对人体比例)"""
    
    # 坐标系: X=左右(左负右正), Y=上下(足负头正), Z=前后(前正后负)
    # 基于标准解剖学姿态 (站立，手臂下垂，掌心朝前)
    
    POINTS = {
        # 手阳明大肠经
        "LI1": {"name": "商阳", "coords": [0.08, 1.62, 0.02], "meridian": "大肠经"},
        "LI4": {"name": "合谷", "coords": [0.05, 1.35, 0.03], "meridian": "大肠经"},
        "LI10": {"name": "手三里", "coords": [0.06, 1.20, 0.02], "meridian": "大肠经"},
        "LI11": {"name": "曲池", "coords": [0.07, 1.08, 0.02], "meridian": "大肠经"},
        
        # 足阳明胃经
        "ST1": {"name": "承泣", "coords": [0.03, 1.75, 0.08], "meridian": "胃经"},
        "ST36": {"name": "足三里", "coords": [0.10, 0.40, -0.05], "meridian": "胃经"},
        "ST40": {"name": "丰隆", "coords": [0.12, 0.60, -0.04], "meridian": "胃经"},
        
        # 足太阴脾经
        "SP6": {"name": "三阴交", "coords": [-0.10, 0.45, -0.04], "meridian": "脾经"},
        "SP10": {"name": "血海", "coords": [-0.12, 0.70, -0.03], "meridian": "脾经"},
        
        # 手太阴肺经
        "LU1": {"name": "中府", "coords": [-0.08, 1.55, 0.05], "meridian": "肺经"},
        "LU7": {"name": "列缺", "coords": [-0.06, 1.55, 0.03], "meridian": "肺经"},
        "LU9": {"name": "太渊", "coords": [-0.08, 1.52, 0.02], "meridian": "肺经"},
        
        # 足少阴肾经
        "KI1": {"name": "涌泉", "coords": [0.00, -0.95, -0.08], "meridian": "肾经"},
        "KI3": {"name": "太溪", "coords": [-0.08, 0.00, -0.06], "meridian": "肾经"},
        "KI6": {"name": "照海", "coords": [-0.10, 0.00, -0.07], "meridian": "肾经"},
        
        # 任脉
        "RN3": {"name": "中极", "coords": [0.00, 0.95, 0.06], "meridian": "任脉"},
        "RN4": {"name": "关元", "coords": [0.00, 0.85, 0.06], "meridian": "任脉"},
        "RN6": {"name": "气海", "coords": [0.00, 0.75, 0.06], "meridian": "任脉"},
        "RN12": {"name": "中脘", "coords": [0.00, 0.55, 0.05], "meridian": "任脉"},
        "RN17": {"name": "膻中", "coords": [0.00, 0.90, 0.05], "meridian": "任脉"},
        
        # 督脉
        "DU1": {"name": "长强", "coords": [0.00, -0.60, -0.08], "meridian": "督脉"},
        "DU4": {"name": "命门", "coords": [0.00, 0.50, -0.06], "meridian": "督脉"},
        "DU14": {"name": "大椎", "coords": [0.00, 1.25, -0.04], "meridian": "督脉"},
        "DU20": {"name": "百会", "coords": [0.00, 1.70, 0.00], "meridian": "督脉"},
        
        # 经外奇穴
        "EX-HN1": {"name": "印堂", "coords": [0.00, 1.77, 0.05], "meridian": "奇穴"},
        "EX-HN5": {"name": "太阳", "coords": [0.10, 1.72, 0.06], "meridian": "奇穴"},
        "EX-CA1": {"name": "子宫", "coords": [0.00, 0.60, -0.08], "meridian": "奇穴"},
    }
    
    # 经络路径 (简化版，每条经选取主要穴位)
    MERIDIAN_PATHS = {
        "大肠经": ["LI1", "LI4", "LI10", "LI11"],
        "胃经": ["ST1", "ST36", "ST40"],
        "脾经": ["SP6", "SP10"],
        "肺经": ["LU1", "LU7", "LU9"],
        "肾经": ["KI1", "KI3", "KI6"],
        "任脉": ["RN3", "RN4", "RN6", "RN12", "RN17"],
        "督脉": ["DU1", "DU4", "DU14", "DU20"],
    }
    
    @classmethod
    def get_point(cls, code: str) -> Optional[dict]:
        """获取穴位信息"""
        return cls.POINTS.get(code.upper())
    
    @classmethod
    def get_meridian_path(cls, meridian: str) -> list[list[float]]:
        """获取经络路径坐标"""
        path_codes = cls.MERIDIAN_PATHS.get(meridian, [])
        coords = []
        for code in path_codes:
            if code in cls.POINTS:
                coords.append(cls.POINTS[code]["coords"])
        return coords
    
    @classmethod
    def get_all_points(cls) -> dict:
        """获取所有穴位"""
        return cls.POINTS.copy()


# ==================== 3D 资源生成器 ====================
@dataclass
class AnimationResource3D:
    """3D 动画资源"""
    target_point: str = ""
    point_name: str = ""
    coords: list[float] = field(default_factory=list)
    meridian_path: list[list[float]] = field(default_factory=list)
    meridian_name: str = ""
    animation_desc: str = ""
    anatomy_note: str = ""
    stimulation: str = ""
    compatible_points: list[str] = field(default_factory=list)
    threejs_ready: bool = True
    
    def to_json(self) -> str:
        """输出 Three.js 可用 JSON"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class ResourceGenerator:
    """资源生成专家"""
    
    # 动画描述模板
    ANIMATION_TEMPLATES = {
        "针刺": [
            "银针自表皮缓缓刺入，深度约{depth}寸，得气后小幅度捻转，酸麻胀感沿经传导。",
            "持针以押手配合，快速破皮后缓慢推进，达到适当深度后施以平补平泻法。",
        ],
        "艾灸": [
            "艾炷置于穴位之上，温热感逐渐渗透，约{time}分钟后更换新炷。",
            "手持艾条悬灸，距离皮肤约3-5cm，以局部红晕为度。",
        ],
        "按摩": [
            "拇指按于穴位，施以揉法，力度由轻渐重，每分钟约{rate}次。",
            "用掌根或鱼际部按揉穴位，配合点按，以酸胀为度。",
        ],
        "拔罐": [
            "将罐具扣于穴位，用火排除空气，罐内负压使皮肤微微隆起。",
            "闪罐法：吸拔后立即起下，再拔，反复数次至局部潮红。",
        ],
    }
    
    # 配穴规则
    POINT_COMBINATIONS = {
        "感冒": ["LI4", "DU14", "LU7"],
        "头痛": ["EX-HN5", "GB20", "DU20"],
        "失眠": ["EX-HN1", "HT7", "SP6"],
        "腰痛": ["DU4", "BL23", "BL40"],
        "胃痛": ["RN12", "ST36", "PC6"],
        "痛经": ["RN4", "SP10", "LR3"],
    }
    
    def __init__(self):
        self.point_db = AcupuncturePointDatabase()
    
    def generate(
        self,
        target: str,
        treatment: str = "针刺",
        disease: str = ""
    ) -> AnimationResource3D:
        """
        生成 3D 动画资源
        
        Args:
            target: 目标穴位代码 (如 "LI4") 或穴位名
            treatment: 治疗方式 (针刺/艾灸/按摩/拔罐)
            disease: 病症 (用于配穴)
            
        Returns:
            AnimationResource3D 对象
        """
        # 查找穴位
        point_info = self._lookup_point(target)
        
        if not point_info:
            raise ValueError(f"Unknown point: {target}")
        
        # 获取经络路径
        meridian = point_info["meridian"]
        meridian_path = self.point_db.get_meridian_path(meridian)
        
        # 生成动画描述
        animation_desc = self._generate_animation_desc(treatment, point_info, disease)
        
        # 获取配穴
        compatible = self._get_compatible_points(disease)
        
        # 组装资源
        resource = AnimationResource3D(
            target_point=target.upper() if isinstance(target, str) else target,
            point_name=point_info["name"],
            coords=point_info["coords"],
            meridian_path=meridian_path,
            meridian_name=f"足{meridian}" if meridian in ["胃经", "脾经", "肾经", "膀胱经", "肝经", "胆经"] else f"手{meridian}" if meridian in ["大肠经", "小肠经", "肺经", "心经", "心包经", "三焦经"] else meridian,
            animation_desc=animation_desc,
            anatomy_note=self._get_anatomy_note(target.upper()),
            stimulation=self._get_stimulation_method(treatment),
            compatible_points=compatible,
            threejs_ready=True
        )
        
        return resource
    
    def generate_json(
        self,
        target: str,
        treatment: str = "针刺",
        disease: str = ""
    ) -> str:
        """直接生成 JSON 字符串 (供 Three.js 调用)"""
        resource = self.generate(target, treatment, disease)
        return resource.to_json()
    
    def _lookup_point(self, target: str) -> Optional[dict]:
        """查找穴位"""
        # 先按代码查找
        upper_target = target.upper()
        if upper_target in self.point_db.POINTS:
            return self.point_db.POINTS[upper_target]
        
        # 按名称查找
        for code, info in self.point_db.POINTS.items():
            if info["name"] == target:
                return info
        
        return None
    
    def _generate_animation_desc(
        self,
        treatment: str,
        point_info: dict,
        disease: str
    ) -> str:
        """生成动画描述"""
        import random
        
        templates = self.ANIMATION_TEMPLATES.get(treatment, self.ANIMATION_TEMPLATES["针刺"])
        template = random.choice(templates)
        
        # 填充参数
        desc = template.format(
            depth=random.choice(["0.5", "1", "1.5"]),
            time=random.choice(["10", "15", "20"]),
            rate=random.choice(["60", "80", "100", "120"])
        )
        
        # 添加病症相关描述
        if disease:
            disease_desc = self._get_disease_desc(disease)
            if disease_desc:
                desc += f"\n\n此穴为{disease}之常用穴，{disease_desc}"
        
        # 添加经络循行描述
        meridian = point_info["meridian"]
        desc += f"\n\n属{meridian}，经气汇聚之所。"
        
        return desc
    
    def _get_disease_desc(self, disease: str) -> str:
        """获取病症描述"""
        descriptions = {
            "感冒": "主解表散邪，宣肺止咳。",
            "头痛": "可疏风通络，止痛安神。",
            "失眠": "能宁心安神，调和阴阳。",
            "腰痛": "可通经活络，缓急止痛。",
            "胃痛": "能理气和胃，消食导滞。",
            "痛经": "可温经散寒，调经止痛。",
        }
        return descriptions.get(disease, "")
    
    def _get_anatomy_note(self, code: str) -> str:
        """获取解剖学备注"""
        notes = {
            "LI4": "第1、2掌骨之间，约第2掌骨中点桡侧",
            "ST36": "胫骨前肌外侧缘，犊鼻下3寸",
            "SP6": "胫骨内侧后缘，内踝尖上3寸",
            "DU20": "头部正中线，两耳尖连线中点",
            "DU14": "第7颈椎棘突下凹陷中",
            "RN17": "胸部正中线，两乳头连线中点",
            "RN12": "上腹部正中线，脐上4寸",
            "RN4": "下腹部正中线，脐下3寸",
            "EX-HN1": "额部，两眉头连线中点",
            "EX-HN5": "颞部，眉梢与目外眦连线中点后1寸",
        }
        return notes.get(code, "常规解剖位置")
    
    def _get_stimulation_method(self, treatment: str) -> str:
        """获取刺激方式"""
        methods = {
            "针刺": "直刺或斜刺0.3-1.5寸，得气为度",
            "艾灸": "艾炷灸3-5壮，或艾条悬灸10-15分钟",
            "按摩": "揉法、点按，以酸胀为度，每穴2-3分钟",
            "拔罐": "留罐5-10分钟，或闪罐、走罐",
        }
        return methods.get(treatment, methods["针刺"])
    
    def _get_compatible_points(self, disease: str) -> list[str]:
        """获取配穴"""
        if disease and disease in self.POINT_COMBINATIONS:
            return self.POINT_COMBINATIONS[disease]
        return []


# ==================== 快捷函数 ====================
_generator: Optional[ResourceGenerator] = None


def get_generator() -> ResourceGenerator:
    global _generator
    if _generator is None:
        _generator = ResourceGenerator()
    return _generator


def generate_3d_resource(target: str, treatment: str = "针刺", disease: str = "") -> str:
    """快捷生成 3D 资源 JSON"""
    return get_generator().generate_json(target, treatment, disease)


# ==================== Demo ====================
if __name__ == '__main__':
    generator = ResourceGenerator()
    
    print("=" * 70)
    print("3D 经络穴位资源生成器 - 讯飞星火版")
    print("=" * 70)
    
    test_targets = ["LI4", "足三里", "百会", "合谷"]
    
    for target in test_targets:
        print(f"\n{'='*70}")
        print(f"穴位: {target}")
        print("=" * 70)
        
        try:
            json_output = generator.generate_json(target, treatment="针刺", disease="腰痛")
            print(json_output)
        except ValueError as e:
            print(f"Error: {e}")
