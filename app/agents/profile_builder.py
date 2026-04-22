# -*- coding: utf-8 -*-
"""
Profile Builder - 画像专家
===========================
将用户口语化描述转化为标准中医画像标签。

核心职责：
1. 识别用户口语中的中医意图
2. 映射为标准 TCM 证型/体质标签
3. 构建用户健康画像

语义映射规则：
- "嗓子冒火" → 热证/肺火
- "手脚冰凉" → 阳虚/寒证
- "湿气重" → 痰湿/湿困
- "上火" → 热证/实火或虚火
- "脾虚" → 脾气虚/脾阳虚

Author: Alice
"""

import sys
import re
import logging
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# ==================== 日志配置 ====================
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("ProfileBuilder")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger


# ==================== 中医证型定义 ====================
class SyndromeType(Enum):
    """证型枚举"""
    # 八纲辨证
    阴虚 = "阴虚"
    阳虚 = "阳虚"
    气虚 = "气虚"
    血虚 = "血虚"
    热证 = "热证"
    寒证 = "寒证"
    实证 = "实证"
    虚证 = "虚证"
    
    # 病因辨证
    湿邪 = "湿邪"
    痰湿 = "痰湿"
    气郁 = "气郁"
    血瘀 = "血瘀"
    风邪 = "风邪"
    
    # 脏腑辨证
    肺热 = "肺热"
    肺火 = "肺火"
    心火 = "心火"
    肝火 = "肝火"
    肝郁 = "肝郁"
    胃热 = "胃热"
    脾虚 = "脾虚"
    肾虚 = "肾虚"
    
    # 体质类型
    阳虚质 = "阳虚质"
    阴虚质 = "阴虚质"
    气虚质 = "气虚质"
    痰湿质 = "痰湿质"
    湿热质 = "湿热质"
    血瘀质 = "血瘀质"
    气郁质 = "气郁质"
    特禀质 = "特禀质"


# ==================== 语义映射规则 ====================
class SemanticMappingRules:
    """口语 → 中医术语 映射规则"""
    
    # 层级1: 症状/感受 → 证型
    SYMPTOM_TO_SYNDROME = {
        # 热相关
        "嗓子冒火": ["热证", "肺火"],
        "嗓子疼": ["热证", "肺热"],
        "喉咙痛": ["热证", "肺热"],
        "口腔溃疡": ["热证", "心火", "胃热"],
        "长痘": ["热证", "肺热", "胃热"],
        "脸上起痘": ["热证", "肺热", "胃热"],
        "上火": ["热证"],
        "火气大": ["热证", "肝火"],
        "口干": ["热证", "阴虚"],
        "口渴": ["热证", "阴虚", "胃热"],
        "舌苔黄": ["热证", "湿热"],
        "尿黄": ["热证"],
        
        # 寒相关
        "手脚冰凉": ["寒证", "阳虚"],
        "手脚冰冷": ["寒证", "阳虚"],
        "怕冷": ["寒证", "阳虚"],
        "畏寒": ["寒证", "阳虚"],
        "肚子凉": ["寒证", "脾虚", "阳虚"],
        "宫寒": ["寒证", "血瘀", "阳虚"],
        "后背凉": ["寒证", "阳虚"],
        
        # 湿相关
        "湿气重": ["湿邪", "痰湿"],
        "湿气太重": ["湿邪", "痰湿"],
        "身体沉重": ["湿邪", "痰湿"],
        "头重": ["湿邪", "痰湿"],
        "大便粘": ["湿邪", "痰湿"],
        "舌苔厚": ["湿邪", "痰湿"],
        "脸上油腻": ["湿邪", "痰湿"],
        "长湿疹": ["湿邪", "血瘀"],
        
        # 虚相关
        "没力气": ["气虚"],
        "乏力": ["气虚"],
        "疲劳": ["气虚"],
        "累": ["气虚"],
        "气短": ["气虚"],
        "心慌": ["气虚", "血虚"],
        "头晕": ["血虚", "气虚"],
        "眼花": ["血虚"],
        "记忆力差": ["血虚", "肾虚"],
        "掉头发": ["血虚", "肾虚"],
        "失眠多梦": ["阴虚", "血虚"],
        "睡不着": ["阴虚", "血虚", "肝火"],
        
        # 气血相关
        "气血不足": ["气虚", "血虚"],
        "贫血": ["血虚"],
        "脸色差": ["血虚", "气虚"],
        "面色萎黄": ["血虚"],
        "面色苍白": ["血虚", "阳虚"],
        
        # 肝相关
        "爱生气": ["气郁", "肝郁"],
        "脾气大": ["肝火", "肝郁"],
        "心情不好": ["气郁", "肝郁"],
        "郁闷": ["气郁", "肝郁"],
        "压力大": ["气郁", "肝郁"],
        "乳房胀痛": ["气郁", "肝郁", "血瘀"],
        "月经前乳房胀痛": ["肝郁"],
        
        # 胃相关
        "胃不舒服": ["胃热", "脾虚"],
        "胃疼": ["胃热", "寒凝"],
        "胃胀": ["气郁", "胃热"],
        "消化不好": ["脾虚", "胃热"],
        "食欲不振": ["脾虚", "湿邪"],
        
        # 脾相关
        "脾虚": ["脾虚"],
        "大便稀": ["脾虚", "湿邪"],
        "拉肚子": ["脾虚", "湿邪"],
        "腹胀": ["气郁", "脾虚"],
        
        # 肾相关
        "肾虚": ["肾虚"],
        "腰酸": ["肾虚"],
        "腰疼": ["肾虚", "血瘀"],
        "性功能下降": ["肾虚"],
        "夜尿多": ["肾虚", "阳虚"],
        "耳鸣": ["肾虚"],
        
        # 其他
        "便秘": ["热证", "阴虚", "气郁"],
        "肥胖": ["痰湿", "气虚"],
        "水肿": ["湿邪", "肾虚"],
        "风湿": ["湿邪", "风邪"],
        "关节疼": ["湿邪", "血瘀", "风邪"],
        "痛经": ["血瘀", "寒凝", "肝郁"],
        "月经不调": ["血瘀", "肝郁", "肾虚"],
    }
    
    # 层级2: 证型 → 推荐体质标签
    SYNDROME_TO_CONSTITUTION = {
        "阳虚": ["阳虚质"],
        "阴虚": ["阴虚质"],
        "气虚": ["气虚质"],
        "痰湿": ["痰湿质"],
        "湿热": ["湿热质"],
        "血瘀": ["血瘀质"],
        "气郁": ["气郁质"],
        "肝火": ["湿热质", "阴虚质"],
        "肝郁": ["气郁质"],
        "肺热": ["湿热质"],
        "肺火": ["湿热质"],
    }
    
    # 层级3: 证型 → 推荐穴位/调理
    SYNDROME_TO_TIPS = {
        "热证": ["少吃辛辣", "多喝温水", "可按揉合谷、曲池"],
        "寒证": ["保暖避寒", "忌食生冷", "可艾灸关元、神阙"],
        "湿邪": ["健脾祛湿", "运动发汗", "可按揉阴陵泉、丰隆"],
        "气虚": ["补中益气", "适度运动", "可艾灸足三里、气海"],
        "血虚": ["养血补血", "规律作息", "可按揉血海、三阴交"],
        "阴虚": ["滋阴润燥", "忌熬夜", "可按揉太溪、照海"],
        "阳虚": ["温阳散寒", "适度晒太阳", "可艾灸命门、肾俞"],
        "肝郁": ["疏肝解郁", "调畅情志", "可按揉太冲、膻中"],
        "气郁": ["理气行气", "户外活动", "可按揉内关、足三里"],
        "痰湿": ["化痰祛湿", "清淡饮食", "可按揉丰隆、阴陵泉"],
        "血瘀": ["活血化瘀", "适度运动", "可按揉血海、地机"],
    }


# ==================== 用户画像 ====================
@dataclass
class UserProfile:
    """用户中医画像"""
    user_id: str = ""
    
    # 主要证型 (按权重排序)
    syndromes: list[dict] = field(default_factory=list)
    
    # 体质判定
    constitution: list[str] = field(default_factory=list)
    
    # 主要症状
    symptoms: list[str] = field(default_factory=list)
    
    # 调理建议
    tips: list[str] = field(default_factory=list)
    
    # 风险提示
    warnings: list[str] = field(default_factory=list)
    
    # 画像置信度
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "syndromes": self.syndromes,
            "constitution": self.constitution,
            "symptoms": self.symptoms,
            "tips": self.tips,
            "warnings": self.warnings,
            "confidence": self.confidence,
            "summary": self.generate_summary()
        }
    
    def generate_summary(self) -> str:
        """生成画像摘要"""
        if not self.syndromes:
            return "信息不足，无法生成画像"
        
        top_syndrome = self.syndromes[0]["type"]
        
        constitutions = "、".join(self.constitution[:2]) if self.constitution else "待判定"
        
        return f"主要证型：{top_syndrome}；体质倾向：{constitutions}。"


# ==================== 画像构建器 ====================
class ProfileBuilder:
    """画像专家"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.mapping = SemanticMappingRules()
    
    def build(
        self,
        user_input: str,
        user_id: str = "",
        context: dict = None
    ) -> UserProfile:
        """
        从用户输入构建中医画像
        
        Args:
            user_input: 用户口语化描述
            user_id: 用户ID
            context: 额外上下文 (年龄、性别等)
            
        Returns:
            UserProfile 对象
        """
        self.logger.info("Building profile from input: %s", user_input)
        
        profile = UserProfile(user_id=user_id)
        
        # Step 1: 语义解析
        parsed_symptoms = self._parse_symptoms(user_input)
        profile.symptoms = list(set(parsed_symptoms.keys()))
        
        self.logger.info("Parsed symptoms: %s", profile.symptoms)
        
        # Step 2: 证型推断
        syndromes = self._infer_syndromes(parsed_symptoms)
        profile.syndromes = syndromes
        
        # Step 3: 体质判定
        constitution = self._infer_constitution(syndromes)
        profile.constitution = constitution
        
        # Step 4: 调理建议
        tips = self._generate_tips(syndromes)
        profile.tips = tips
        
        # Step 5: 风险提示
        warnings = self._check_warnings(syndromes, context)
        profile.warnings = warnings
        
        # Step 6: 计算置信度
        profile.confidence = self._calculate_confidence(syndromes, len(parsed_symptoms))
        
        self.logger.info("Profile confidence: %.2f", profile.confidence)
        
        return profile
    
    def _parse_symptoms(self, user_input: str) -> dict[str, float]:
        """
        解析用户输入，提取症状及匹配度
        
        Returns:
            {症状: 匹配度}
        """
        symptoms = {}
        
        # 精确匹配
        for phrase, syndrome_list in self.mapping.SYMPTOM_TO_SYNDROME.items():
            if phrase in user_input:
                symptoms[phrase] = 1.0
        
        # 模糊匹配 (同义词/近义词)
        fuzzy_map = {
            "疼": "痛",
            "不舒服": "不适",
            "胃部不适": "胃不舒服",
            "脸上长痘": "长痘",
            "睡眠不好": "失眠多梦",
        }
        
        for fuzzy, standard in fuzzy_map.items():
            if fuzzy in user_input and standard in self.mapping.SYMPTOM_TO_SYNDROME:
                symptoms[fuzzy] = 0.8
        
        return symptoms
    
    def _infer_syndromes(self, symptoms: dict[str, float]) -> list[dict]:
        """从症状推断证型"""
        syndrome_scores = {}
        
        for symptom, match_score in symptoms.items():
            if symptom in self.mapping.SYMPTOM_TO_SYNDROME:
                related_syndromes = self.mapping.SYMPTOM_TO_SYNDROME[symptom]
                
                for syndrome in related_syndromes:
                    if syndrome not in syndrome_scores:
                        syndrome_scores[syndrome] = 0.0
                    syndrome_scores[syndrome] += match_score
        
        # 排序
        sorted_syndromes = sorted(
            syndrome_scores.items(),
            key=lambda x: -x[1]
        )
        
        # 转换为列表格式
        result = []
        for syndrome, score in sorted_syndromes[:5]:  # 取前5个
            result.append({
                "type": syndrome,
                "score": score,
                "weight": min(1.0, score / 3.0)  # 归一化
            })
        
        return result
    
    def _infer_constitution(self, syndromes: list[dict]) -> list[str]:
        """从证型推断体质"""
        constitution_scores = {}
        
        for syndrome_item in syndromes:
            syndrome = syndrome_item["type"]
            weight = syndrome_item["weight"]
            
            if syndrome in self.mapping.SYNDROME_TO_CONSTITUTION:
                constitutions = self.mapping.SYNDROME_TO_CONSTITUTION[syndrome]
                for constitution in constitutions:
                    if constitution not in constitution_scores:
                        constitution_scores[constitution] = 0.0
                    constitution_scores[constitution] += weight
        
        # 排序，取前2
        sorted_const = sorted(
            constitution_scores.items(),
            key=lambda x: -x[1]
        )
        
        return [c[0] for c in sorted_const[:2]]
    
    def _generate_tips(self, syndromes: list[dict]) -> list[str]:
        """生成调理建议"""
        tips_set = set()
        
        for syndrome_item in syndromes[:3]:  # 取前3证型
            syndrome = syndrome_item["type"]
            
            if syndrome in self.mapping.SYNDROME_TO_TIPS:
                tips_set.update(self.mapping.SYNDROME_TO_TIPS[syndrome][:2])
        
        return list(tips_set)[:5]  # 最多5条
    
    def _check_warnings(
        self,
        syndromes: list[dict],
        context: dict = None
    ) -> list[str]:
        """检查风险提示"""
        warnings = []
        
        for syndrome_item in syndromes:
            syndrome = syndrome_item["type"]
            score = syndrome_item["score"]
            
            # 高风险证型
            if syndrome in ["血瘀", "痰湿"] and score >= 2:
                warnings.append(f"{syndrome}较重，建议就医详细检查")
            
            if syndrome in ["阳虚", "阴虚"] and score >= 3:
                warnings.append(f"{syndrome}明显，需长期调理，切勿自行用药")
        
        return warnings
    
    def _calculate_confidence(
        self,
        syndromes: list[dict],
        symptom_count: int
    ) -> float:
        """计算画像置信度"""
        if symptom_count == 0:
            return 0.0
        
        # 基于证型一致性
        if len(syndromes) == 0:
            return 0.1
        
        # 证型越多，置信度应越高 (信息丰富)
        syndrome_confidence = min(1.0, len(syndromes) / 3.0)
        
        # 症状数量加成
        symptom_confidence = min(1.0, symptom_count / 3.0)
        
        return (syndrome_confidence * 0.6 + symptom_confidence * 0.4)


# ==================== 快捷函数 ====================
_builder: Optional[ProfileBuilder] = None


def get_builder() -> ProfileBuilder:
    global _builder
    if _builder is None:
        _builder = ProfileBuilder()
    return _builder


def build_profile(user_input: str, user_id: str = "") -> dict:
    """快捷构建画像"""
    profile = get_builder().build(user_input, user_id)
    return profile.to_dict()


# ==================== Demo ====================
if __name__ == '__main__':
    builder = ProfileBuilder()
    
    print("=" * 70)
    print("中医画像专家 - 讯飞星火版")
    print("=" * 70)
    
    test_inputs = [
        "最近嗓子冒火，嘴里还长溃疡，失眠多梦",
        "感觉湿气太重了，身体沉重，脸上油腻",
        "我老公老是手脚冰凉，还腰疼，是不是肾虚啊",
        "女，35岁，最近压力大，乳房胀痛，月经前更明显",
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*70}")
        print(f"用户输入: {user_input}")
        print("=" * 70)
        
        profile = builder.build(user_input, user_id="demo_user")
        result = profile.to_dict()
        
        print(f"\n【画像摘要】{result['summary']}")
        print(f"\n【证型】")
        for s in result['syndromes'][:3]:
            print(f"  - {s['type']} (得分:{s['score']:.1f})")
        
        print(f"\n【体质】{'、'.join(result['constitution']) if result['constitution'] else '待判定'}")
        
        print(f"\n【调理建议】")
        for tip in result['tips']:
            print(f"  - {tip}")
        
        if result['warnings']:
            print(f"\n【风险提示】")
            for w in result['warnings']:
                print(f"  ! {w}")
        
        print(f"\n【置信度】{result['confidence']:.2f}")
