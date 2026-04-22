# -*- coding: utf-8 -*-
"""
Critique Agent - 杏林纠错官
============================
系统最高裁判，以古板严谨的老中医人设，对错误知识进行严厉批判。

性格特征：
- 严厉正直，坚守中医正统
- 措辞古雅，常用"尔"、"吾"、"谬矣"等
- 引经据典，以《黄帝内经》《伤寒论》为准绳
- 对错误绝不姑息，措辞犀利

Author: Alice
"""

import sys
import re
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ==================== 配置 ====================
class CritiqueConfig:
    """批判代理配置"""
    REJECT_THRESHOLD = 0.7  # 低于此阈值强制 REJECT
    
    # 引经据典
    CLASSICS = {
        "黄连": "《神农本草经》：黄连主热气，目痛，肠澼，腹痛。苦寒之性，非治感冒之物。",
        "麻黄": "《伤寒论》麻黄汤：麻黄、桂枝、杏仁、甘草，主治风寒感冒。",
        "附子": "《神农本草经》：附子主风寒咳逆邪气。性大热，非寒证不可轻用。",
        "人参": "《神农本草经》：人参主补五脏，安精神。温补之品，非实证所用。",
        "感冒": "《黄帝内经》：风者，百病之始也。正气存内，邪不可干。",
        "发热": "《伤寒论》：病有发热恶寒者，发于阳也；无热恶寒者，发于阴也。",
    }
    
    # 批判语气词库
    REPROACH_TERMS = [
        "荒谬", "谬矣", "大谬不然", "岂有此理", "滑天下之大稽",
        "尔欲害人性命乎", "此乃医家大忌", "浑然不知医理"
    ]


# ==================== 批判风格 ====================
class CritiqueStyle:
    """批判风格生成器"""
    
    OPENING_TEMPLATES = [
        "吾观尔言，{emotion}！",
        "尔所述者，{emotion}！",
        "谬矣！{emotion}！",
        "大谬不然！{emotion}！",
    ]
    
    EMOTION_MAP = {
        "荒谬": ["简直荒谬至极", "此言差矣", "大错特错"],
        "荒唐": ["岂非儿戏", "如此轻率", "不知所谓"],
        "无知": ["医理不通", "根基全无", "胡说八道"],
    }
    
    @classmethod
    def get_opening(cls, emotion: str = "荒谬") -> str:
        """获取开场白"""
        import random
        template = random.choice(cls.OPENING_TEMPLATES)
        emotions = cls.EMOTION_MAP.get(emotion, cls.EMOTION_MAP["荒谬"])
        return template.format(emotion=random.choice(emotions))
    
    @classmethod
    def get_reason_intro(cls) -> str:
        """获取理由引导"""
        return "吾且为尔一一道来："


# ==================== 中医辩证理由生成器 ====================
class TCMReasonGenerator:
    """生成中医辩证理由"""
    
    # 药性词典
    DRUG_PROPERTIES = {
        "黄连": {"性": "寒", "味": "苦", "功效": "清热燥湿", "主治": "腹泻、呕吐"},
        "麻黄": {"性": "温", "味": "辛", "功效": "发汗解表", "主治": "风寒感冒"},
        "桂枝": {"性": "温", "味": "甘", "功效": "解肌发表", "主治": "风寒表证"},
        "附子": {"性": "热", "味": "辛", "功效": "回阳救逆", "主治": "亡阳虚脱"},
        "人参": {"性": "平", "味": "甘", "功效": "大补元气", "主治": "虚证"},
        "石膏": {"性": "寒", "味": "辛", "功效": "清热泻火", "主治": "气分热证"},
        "大黄": {"性": "寒", "味": "苦", "功效": "泻下攻积", "主治": "热结便秘"},
    }
    
    # 证型词典
    SYNDROME_TYPES = {
        "风寒感冒": {"治法": "辛温解表", "代表方": "麻黄汤", "禁忌": "辛凉解表"},
        "风热感冒": {"治法": "辛凉解表", "代表方": "银翘散", "禁忌": "辛温解表"},
        "寒证": {"治法": "温里散寒", "禁忌": "清热泻火"},
        "热证": {"治法": "清热泻火", "禁忌": "温里散寒"},
        "虚证": {"治法": "补益正气", "禁忌": "攻邪泻实"},
        "实证": {"治法": "攻邪泻实", "禁忌": "盲目补益"},
    }
    
    @classmethod
    def generate_reason(
        cls,
        claim: str,
        subject: str,
        relation: str,
        obj: str,
        graph_result: Optional[dict] = None
    ) -> str:
        """生成辩证理由"""
        reasons = []
        
        # 1. 药性分析
        if subject in cls.DRUG_PROPERTIES:
            props = cls.DRUG_PROPERTIES[subject]
            reasons.append(f"{subject}性{props['性']}味{props['味']}，功效在{props['功效']}，主治{props['主治']}。")
        
        # 2. 治法分析
        if obj in cls.SYNDROME_TYPES:
            syndrome = cls.SYNDROME_TYPES[obj]
            reasons.append(f"{obj}当以{syndrome['治法']}为法，方用{syndrome['代表方']}。")
            if '禁忌' in syndrome:
                reasons.append(f"切记禁忌{syndrome['禁忌']}，否则适得其反。")
        
        # 3. 错误类型分析
        if relation == "治疗":
            if subject in cls.DRUG_PROPERTIES and obj in cls.SYNDROME_TYPES:
                drug_props = cls.DRUG_PROPERTIES[subject]
                syndrome = cls.SYNDROME_TYPES[obj]
                
                # 检查寒热矛盾
                if drug_props.get('性') == '寒' and '寒' not in syndrome['治法']:
                    reasons.append(f"夫{subject}性寒，用于{obj}，无异于雪上加霜，冰伏邪气，必生变故！")
                elif drug_props.get('性') == '温' and '热' in syndrome['治法']:
                    reasons.append(f"夫{subject}性温，用于{obj}，犹如火上浇油，恐助热生变！")
        
        # 4. 引经据典
        for key, quote in CritiqueConfig.CLASSICS.items():
            if key in claim:
                reasons.append(quote)
        
        return "".join(reasons) if reasons else "医理深奥，非尔所言之简单也。"
    
    @classmethod
    def get_correct_treatment(cls, subject: str, obj: str) -> str:
        """给出正确治法"""
        if subject in cls.DRUG_PROPERTIES and obj in cls.SYNDROME_TYPES:
            drug = cls.DRUG_PROPERTIES[subject]
            syndrome = cls.SYNDROME_TYPES[obj]
            return f"若论{obj}，当用{syndrome['代表方']}，以{syndrome['治法']}为法，方为正道。"
        return ""


# ==================== 批判代理核心 ====================
class CritiqueAgent:
    """杏林纠错官"""
    
    def __init__(self, config: type[CritiqueConfig] = CritiqueConfig):
        self.config = config
        self.reason_generator = TCMReasonGenerator()
    
    def critique(
        self,
        claim: str,
        confidence: float,
        graph_result: Optional[dict] = None,
        context: str = ""
    ) -> dict[str, Any]:
        """
        对声明进行批判性评价
        
        Args:
            claim: 待评判的声明
            confidence: 置信度 (0-1)
            graph_result: 图谱校验结果
            context: 上下文
            
        Returns:
            {
                "verdict": "ACCEPT" | "REJECT",
                "confidence": float,
                "critique": str,  # 批判文本
                "reason": str,     # 中医理由
                "classic_quote": str,  # 引经据典
            }
        """
        # 解析声明
        subject, relation, obj = self._parse_claim(claim)
        
        # 低于阈值强制拒绝
        if confidence < self.config.REJECT_THRESHOLD:
            verdict = "REJECT"
            critique_text = self._generate_critique(claim, subject, relation, obj, graph_result)
        else:
            verdict = "ACCEPT"
            critique_text = self._generate_praise(claim, subject, relation, obj)
        
        # 生成中医理由
        reason = self.reason_generator.generate_reason(claim, subject, relation, obj, graph_result)
        
        # 引经据典
        classic_quote = self._get_classic_quote(subject, obj)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "critique": critique_text,
            "reason": reason,
            "classic_quote": classic_quote,
            "correct_treatment": self.reason_generator.get_correct_treatment(subject, obj) if verdict == "REJECT" else ""
        }
    
    def _parse_claim(self, claim: str) -> tuple[str, str, str]:
        """解析声明"""
        import re
        
        patterns = [
            (r'([^ ]+?)性([寒凉温热平])', '性'),
            (r'([^ ]+?)味([辛苦甘酸咸])', '味'),
            (r'([^ ]+?)归?([\u4e00-\u9fa5]+?)经', '归经'),
            (r'([^ ]+?)(治疗|主治|功效)[^ ]*?([^ ]+)', '功效'),
        ]
        
        for pattern, rel in patterns:
            match = re.search(pattern, claim)
            if match:
                subject = match.group(1).strip()
                obj = match.group(3).strip() if match.lastindex >= 3 else match.group(2).strip()
                return (subject, rel, obj)
        
        return ("", "", "")
    
    def _generate_critique(
        self,
        claim: str,
        subject: str,
        relation: str,
        obj: str,
        graph_result: Optional[dict]
    ) -> str:
        """生成批判文本"""
        import random
        
        parts = []
        
        # 开场白
        parts.append(CritiqueStyle.get_opening(random.choice(["荒谬", "荒唐", "无知"])))
        
        # 指出错误
        if subject and obj:
            parts.append(f"尔竟称'{subject}{relation}{obj}'？")
        
        # 引用错误原因
        if graph_result and graph_result.get('reason'):
            parts.append(f"图谱校验示：{graph_result['reason']}。")
        
        # 中医理由
        parts.append(self.reason_generator.generate_reason(claim, subject, relation, obj))
        
        # 正确治法
        correct = self.reason_generator.get_correct_treatment(subject, obj)
        if correct:
            parts.append(f"\n\n正确之法：{correct}")
        
        # 警告
        parts.append("\n\n尔若执意行之，轻则延误病机，重则害人性命！吾为医道守门人，绝不姑息！")
        
        return "".join(parts)
    
    def _generate_praise(
        self,
        claim: str,
        subject: str,
        relation: str,
        obj: str
    ) -> str:
        """生成肯定文本"""
        return f"善！此言深合医理。{subject}之{relation}确为{obj}，吾已验证图谱，正统无误。"
    
    def _get_classic_quote(self, subject: str, obj: str) -> str:
        """获取经典引文"""
        for key, quote in self.config.CLASSICS.items():
            if key in subject or key in obj:
                return quote
        return ""


# ==================== 快捷函数 ====================
_global_agent: Optional[CritiqueAgent] = None


def get_agent() -> CritiqueAgent:
    global _global_agent
    if _global_agent is None:
        _global_agent = CritiqueAgent()
    return _global_agent


def critique(claim: str, confidence: float, graph_result: dict = None) -> dict:
    """快捷批判函数"""
    return get_agent().critique(claim, confidence, graph_result)


# ==================== Demo ====================
if __name__ == '__main__':
    agent = CritiqueAgent()
    
    print("=" * 70)
    print("杏林纠错官 - 讯飞星火版")
    print("=" * 70)
    
    test_cases = [
        ("黄连治疗感冒", 0.1),
        ("麻黄治疗风寒感冒", 0.95),
        ("附子性寒", 0.15),
        ("人参功效为大补元气", 0.85),
        ("黄连性寒味苦", 0.90),
    ]
    
    for claim, confidence in test_cases:
        print("\n" + "-" * 70)
        print(f"[置信度: {confidence:.2f}] 声明: {claim}")
        print("-" * 70)
        
        result = agent.critique(claim, confidence)
        
        print(f"\n【判定】: {result['verdict']}")
        print(f"\n【批判】:\n{result['critique']}")
        
        if result['classic_quote']:
            print(f"\n【经典】:\n{result['classic_quote']}")
        
        if result['correct_treatment']:
            print(f"\n【正道】: {result['correct_treatment']}")
