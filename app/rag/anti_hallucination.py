# -*- coding: utf-8 -*-
"""
Anti-Hallucination Module - 置信度评估与幻觉检测
================================================
基于多层校验的置信度计算，专门针对中医知识的准确性验证。

核心机制：
1. 实体一致性校验 (Entity Consistency)
2. 关系合理性校验 (Relation Plausibility)  
3. 图谱匹配评分 (Graph Match Score)
4. 上下文相关性 (Context Relevance)

Author: Alice 🌸
"""

import sys
import re
import logging
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ==================== 日志 ====================
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("AntiHallucination")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger


# ==================== 枚举定义 ====================
class Verdict(Enum):
    """判定结果"""
    ACCEPT = "ACCEPT"      # 高置信度，接受
    UNCERTAIN = "UNCERTAIN"  # 中等置信度，需人工确认
    REJECT = "REJECT"      # 低置信度，拒绝


class EntityType(Enum):
    """实体类型"""
    TCM_HERB = "中药"       # 必须100%匹配
    TCM_FORMULA = "方剂"    # 必须100%匹配
    TCM_ACUPUNCTURE = "经络穴位"  # 必须100%匹配
    TCM_DISEASE = "病证"    # 允许一定模糊
    GENERAL = "通用"        # 通用实体


# ==================== 数据类 ====================
@dataclass
class ConfidenceConfig:
    """置信度配置参数"""
    # 基础分数
    base_score: float = 0.3
    
    # 权重配置
    entity_exact_match_weight: float = 0.30  # 专有名词精确匹配
    entity_fuzzy_match_weight: float = 0.10   # 模糊匹配
    relation_validity_weight: float = 0.20    # 关系有效性
    graph_match_weight: float = 0.25         # 图谱匹配
    context_relevance_weight: float = 0.15    # 上下文相关
    
    # 阈值
    accept_threshold: float = 0.70
    uncertain_threshold: float = 0.50
    
    # 惩罚项
    contradiction_penalty: float = 0.40
    impossible_relation_penalty: float = 0.30
    entity_type_mismatch_penalty: float = 0.25
    
    # TCM 专用配置
    tcm_exact_match_bonus: float = 0.20  # 中医专有名词100%匹配额外加分


@dataclass
class ConfidenceResult:
    """置信度评估结果"""
    verdict: Verdict
    confidence: float
    
    # 分项得分
    entity_score: float = 0.0
    relation_score: float = 0.0
    graph_score: float = 0.0
    context_score: float = 0.0
    
    # 详细信息
    matched_entities: list[str] = field(default_factory=list)
    matched_relations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # 原始数据
    claim: str = ""
    context: str = ""


# ==================== TCM 实体词典 ====================
class TCMEntityDictionary:
    """中医实体词典"""
    
    # 中药 (按功效分类)
    HERBS = {
        # 解表药
        "麻黄", "桂枝", "紫苏", "荆芥", "防风", "羌活", "独活", "白芷", "苍耳", "辛夷",
        "薄荷", "牛蒡", "桑叶", "菊花", "葛根", "柴胡", "升麻",
        # 清热药
        "石膏", "知母", "芦根", "天花粉", "淡竹叶", "栀子", "黄连", "黄芩", "黄柏", "龙胆",
        "苦参", "金银花", "连翘", "蒲公英", "紫花地丁", "板蓝根", "大青叶", "青黛", "贯众",
        # 温里药
        "附子", "干姜", "肉桂", "吴茱萸", "小茴香", "丁香", "花椒", "高良姜", "胡椒",
        # 补虚药
        "人参", "党参", "黄芪", "白术", "山药", "甘草", "大枣", "蜂蜜",
        "鹿茸", "肉苁蓉", "杜仲", "续断", "菟丝子", "沙苑子", "益智仁", "冬虫夏草", "蛤蚧",
        "当归", "熟地", "生地", "白芍", "川芎", "阿胶", "何首乌", "龙眼肉", "枸杞子",
        # 化痰止咳平喘药
        "半夏", "天南星", "白芥子", "旋覆花", "白前", "桔梗", "苦杏仁", "百部", "紫菀", "款冬花",
        # 理气药
        "陈皮", "青皮", "枳实", "枳壳", "木香", "香附", "乌药", "沉香", "檀香", "川楝子", "荔枝核",
        # 活血化瘀药
        "川芎", "延胡索", "郁金", "姜黄", "乳香", "没药", "丹参", "红花", "桃仁", "益母草",
        "牛膝", "鸡血藤", "王不留行", "三棱", "莪术", "水蛭", "虻虫", "地鳖虫",
        # 利水渗湿药
        "茯苓", "猪苓", "泽泻", "薏苡仁", "车前子", "滑石", "木通", "通草", "金钱草", "茵陈",
    }
    
    # 方剂
    FORMULAS = {
        "麻黄汤", "桂枝汤", "桑菊饮", "银翘散", "败毒散", "参苏饮",
        "补中益气汤", "四君子汤", "四物汤", "八珍汤", "归脾汤", "天王补心丹",
        "六味地黄丸", "知柏地黄丸", "杞菊地黄丸", "金匮肾气丸",
        "逍遥散", "柴胡疏肝散", "龙胆泻肝汤", "藿香正气散",
        "平胃散", "藿香正气散", "三仁汤", "茵陈蒿汤",
        "二陈汤", "清气化痰丸", "贝母瓜蒌散", "止嗽散",
        "四逆汤", "回阳救急汤", "当归四逆汤", "黄芪桂枝五物汤",
        "血府逐瘀汤", "膈下逐瘀汤", "少腹逐瘀汤", "身痛逐瘀汤",
        "镇肝熄风汤", "天麻钩藤饮", "大定风珠", "地黄饮子",
    }
    
    # 经络穴位
    ACUPUNCTURE_POINTS = {
        "十二正经": {
            "手太阴肺经": ["中府", "云门", "天府", "侠白", "尺泽", "孔最", "列缺", "经渠", "太渊", "鱼际", "少商"],
            "手阳明大肠经": ["商阳", "二间", "三间", "合谷", "阳溪", "偏历", "温溜", "下廉", "上廉", "手三里", "曲池"],
            "足阳明胃经": ["承泣", "四白", "巨髎", "地仓", "大迎", "颊车", "下关", "头维", "人迎", "水突", "气舍", "缺盆", "气户", "库房", "屋翳", "膺窗", "乳中", "乳根", "不容", "承满", "梁门", "关门", "太乙", "滑肉门", "天枢", "外陵", "大巨", "水道", "归来", "气冲", "髀关", "伏兔", "阴市", "梁丘", "犊鼻", "足三里", "上巨虚", "条口", "下巨虚", "丰隆", "解溪", "冲阳", "陷谷", "内庭", "厉兑"],
            "足太阴脾经": ["隐白", "大都", "太白", "公孙", "商丘", "三阴交", "漏谷", "地机", "阴陵泉", "血海", "箕门", "冲门", "府舍", "腹结", "大横", "腹哀", "食窦", "天溪", "胸乡", "周荣", "大包"],
            "手少阴心经": ["极泉", "青灵", "少海", "灵道", "通里", "阴郄", "神门", "少府", "少冲"],
            "手太阳小肠经": ["少泽", "前谷", "后溪", "腕骨", "阳谷", "养老", "支正", "小海", "肩贞", "臑俞", "天宗", "秉风", "曲垣", "肩外俞", "肩中俞", "天窗", "天容", "颧髎", "听宫"],
            "足太阳膀胱经": ["睛明", "攒竹", "眉冲", "曲差", "五处", "承光", "通天", "络却", "玉枕", "天柱", "大杼", "风门", "肺俞", "厥阴俞", "心俞", "督俞", "膈俞", "肝俞", "胆俞", "脾俞", "胃俞", "三焦俞", "肾俞", "气海俞", "大肠俞", "关元俞", "小肠俞", "膀胱俞", "中膂俞", "白环俞", "上髎", "次髎", "中髎", "下髎", "会阳", "承扶", "殷门", "浮郄", "委阳", "委中", "附分", "魄户", "膏肓", "神堂", "譩譆", "膈关", "魂门", "阳纲", "意舍", "胃仓", "肓门", "志室", "胞肓", "秩边", "合阳", "承筋", "承山", "飞扬", "跗阳", "昆仑", "仆参", "申脉", "金门", "京骨", "束骨", "足通谷", "至阴"],
            "足少阴肾经": ["涌泉", "然谷", "太溪", "大钟", "照海", "复溜", "交信", "筑宾", "阴谷", "横骨", "大赫", "气穴", "四满", "中注", "肓俞", "商曲", "石关", "阴都", "腹通谷", "幽门", "步廊", "神封", "灵墟", "神藏", "彧中", "俞府"],
            "手厥阴心包经": ["天池", "天泉", "曲泽", "郄门", "间使", "内关", "大陵", "劳宫", "中冲"],
            "手少阳三焦经": ["关冲", "液门", "中渚", "阳池", "外关", "支沟", "会宗", "三阳络", "四渎", "天井", "清冷渊", "消泺", "臑会", "肩髎", "天髎", "天牖", "翳风", "瘈脉", "颅息", "角孙", "耳门", "耳和髎", "丝竹空"],
            "足少阳胆经": ["瞳子髎", "听会", "上关", "颔厌", "悬颅", "悬厘", "曲鬓", "率谷", "天冲", "浮白", "头窍阴", "完骨", "本神", "阳白", "头临泣", "目窗", "正营", "承灵", "脑空", "风池", "肩井", "渊腋", "辄筋", "日月", "京门", "带脉", "五枢", "维道", "居髎", "环跳", "风市", "中渎", "膝阳关", "阳陵泉", "阳交", "外丘", "光明", "阳辅", "悬钟", "丘墟", "足临泣", "地五会", "侠溪", "足窍阴"],
            "足厥阴肝经": ["大敦", "行间", "太冲", "中封", "蠡沟", "中都", "膝关", "曲泉", "阴包", "足五里", "阴廉", "急脉", "章门", "期门"],
        },
        # 奇经八脉
        "奇经八脉": {
            "督脉": ["长强", "腰俞", "腰阳关", "命门", "悬枢", "脊中", "中枢", "筋缩", "至阳", "灵台", "神道", "身柱", "陶道", "大椎", "哑门", "风府", "脑户", "强间", "后顶", "百会", "前顶", "囟会", "上星", "神庭", "素髎", "水沟", "兑端", "龈交"],
            "任脉": ["会阴", "曲骨", "中极", "关元", "石门", "气海", "阴交", "神阙", "水分", "下脘", "建里", "中脘", "上脘", "巨阙", "鸠尾", "中庭", "膻中", "玉堂", "紫宫", "华盖", "璇玑", "天突", "廉泉", "承浆"],
            "冲脉": ["幽门", "通谷", "阴都", "石关", "商曲", "肓俞", "中注", "四满", "气穴", "大赫", "横骨"],
            "带脉": ["带脉", "五枢", "维道"],
            "阳跷脉": ["申脉", "仆参", "跗阳", "居髎", "臑俞", "肩髎", "巨骨", "天髎", "地仓", "巨髎", "承泣", "睛明"],
            "阴跷脉": ["照海", "交信", "晴明"],
            "阳维脉": ["金门", "阳交", "臑俞", "天髎", "肩井", "本神", "阳白", "头临泣", "目窗", "正营", "承灵", "脑空", "风池", "风府", "哑门"],
            "阴维脉": ["筑宾", "冲门", "府舍", "大横", "腹哀", "期门", "天突", "廉泉"],
        },
        # 常用奇穴
        "常用奇穴": {
            "头颈部": ["四神聪", "印堂", "鱼腰", "太阳", "球后", "鼻通", "金津", "玉液", "夹承浆", "牵正", "翳明", "安眠"],
            "项背部": ["定喘", "夹脊", "胃脘下俞", "腰眼", "十七椎", "腰奇"],
            "上肢部": ["肩前", "肘尖", "手逆注", "中泉", "大骨空", "小骨空", "腰痛点", "外劳宫", "八邪", "四缝", "十宣"],
            "下肢部": ["环中", "鹤顶", "百虫窝", "膝眼", "胆囊", "阑尾", "内踝尖", "外踝尖", "八风", "独阴"],
        }
    }
    
    # 病证
    DISEASES = {
        "外感病": ["感冒", "发热", "咳嗽", "哮喘", "鼻塞", "流涕", "咽喉肿痛"],
        "肺系病证": ["感冒", "咳嗽", "哮喘", "肺痈", "肺痿", "咯血"],
        "心系病证": ["心悸", "胸痹", "不寐", "健忘", "痴呆", "癫狂", "痫证"],
        "脾胃病证": ["胃痛", "痞满", "腹痛", "呕吐", "呃逆", "噎膈", "泄泻", "便秘"],
        "肝胆病证": ["胁痛", "黄疸", "积聚", "眩晕", "头痛", "中风", "瘿病"],
        "肾系病证": ["水肿", "淋证", "癃闭", "关格", "遗精", "阳痿", "耳鸣", "耳聋"],
        "气血津液病证": ["郁证", "血证", "汗证", "消渴", "内伤发热", "虚劳", "痞证"],
        "经络病证": ["头痛", "痹证", "腰痛", "肩凝证", "落枕", "痿证"],
        "五官科病证": ["目赤肿痛", "近视", "耳鸣耳聋", "鼻渊", "咽喉肿痛", "牙痛"],
        "妇科病证": ["月经不调", "痛经", "崩漏", "带下病", "妊娠恶阻", "产后腹痛"],
    }
    
    @classmethod
    def is_tcm_herb(cls, text: str) -> bool:
        return text in cls.HERBS
    
    @classmethod
    def is_tcm_formula(cls, text: str) -> bool:
        return text in cls.FORMULAS
    
    @classmethod
    def is_tcm_acupuncture(cls, text: str) -> bool:
        for category in cls.ACUPUNCTURE_POINTS.values():
            if isinstance(category, dict):
                for points in category.values():
                    if text in points:
                        return True
            elif text in category:
                return True
        return False
    
    @classmethod
    def is_tcm_disease(cls, text: str) -> bool:
        for diseases in cls.DISEASES.values():
            if text in diseases:
                return True
        return False
    
    @classmethod
    def is_tcm_entity(cls, text: str, require_exact: bool = True) -> tuple[bool, str]:
        """
        检查是否为中医实体
        
        Returns:
            (is_tcm, entity_type)
        """
        if cls.is_tcm_herb(text):
            return (True, "中药")
        if cls.is_tcm_formula(text):
            return (True, "方剂")
        if cls.is_tcm_acupuncture(text):
            return (True, "经络穴位")
        if cls.is_tcm_disease(text):
            return (True, "病证")
        return (False, "通用")


# ==================== 置信度评估器 ====================
class ConfidenceEvaluator:
    """置信度评估器"""
    
    def __init__(self, config: Optional[ConfidenceConfig] = None):
        self.config = config or ConfidenceConfig()
        self.logger = setup_logging()
        self.entity_dict = TCMEntityDictionary()
    
    def evaluate(
        self, 
        claim: str, 
        context: str = "",
        graph_service: Any = None
    ) -> ConfidenceResult:
        """
        评估声明的置信度
        
        Args:
            claim: 待评估的声明
            context: 上下文
            graph_service: 图谱服务实例 (用于图谱匹配)
        """
        self.logger.info(f"[evaluate] 评估声明: {claim}")
        
        result = ConfidenceResult(
            verdict=Verdict.UNCERTAIN,
            confidence=0.0,
            claim=claim,
            context=context
        )
        
        # Step 1: 解析声明
        parsed = self._parse_claim(claim)
        if not parsed:
            result.reasons.append("无法解析声明格式")
            result.verdict = Verdict.REJECT
            result.confidence = 0.0
            return result
        
        subject, relation, obj = parsed
        self.logger.info(f"  解析: {subject} --[{relation}]--> {obj}")
        
        # Step 2: 实体一致性评分
        entity_score = self._score_entity_consistency(subject, obj, result)
        result.entity_score = entity_score
        
        # Step 3: 关系有效性评分
        relation_score = self._score_relation_validity(subject, relation, obj, result)
        result.relation_score = relation_score
        
        # Step 4: 图谱匹配评分
        graph_score = 0.0
        if graph_service:
            graph_score = self._score_graph_match(subject, relation, obj, graph_service, result)
        result.graph_score = graph_score
        
        # Step 5: 上下文相关性
        context_score = self._score_context_relevance(claim, context, result)
        result.context_score = context_score
        
        # ===== 综合计算 =====
        confidence = self._calculate_overall_confidence(
            entity_score, relation_score, graph_score, context_score, result
        )
        result.confidence = confidence
        
        # ===== 最终判定 =====
        result.verdict = self._determine_verdict(confidence, result)
        
        self.logger.info(f"  置信度: {confidence:.3f} -> [{result.verdict.value}]")
        self.logger.info(f"  分项: entity={entity_score:.2f}, relation={relation_score:.2f}, graph={graph_score:.2f}, context={context_score:.2f}")
        
        return result
    
    def _parse_claim(self, claim: str) -> Optional[tuple[str, str, str]]:
        """解析声明为三元组"""
        # 中医声明常见格式
        patterns = [
            # A 性温/性寒/味辛
            (r'([^ ]+?)性([寒凉温热平])', '性'),
            (r'([^ ]+?)味([辛苦甘酸咸])', '味'),
            # A 归 B 经
            (r'([^ ]+?)归?([\u4e00-\u9fa5]+?)经', '归经'),
            # A 属于 B
            (r'([^ ]+?)属于([^ ]+)', '属于'),
            # A 治疗/主治/功效 B
            (r'([^ ]+?)(治疗|主治|功效|用于|具有)([^ ]+)', '功效'),
        ]
        
        for pattern, rel in patterns:
            import re
            match = re.search(pattern, claim)
            if match:
                subject = match.group(1).strip()
                obj = match.group(3).strip() if match.lastindex >= 3 else match.group(2).strip()
                # 清理末尾标点
                obj = re.sub(r'[。,，、.。]+$', '', obj)
                if subject and obj:
                    return (subject, rel, obj)
        
        return None
    
    def _score_entity_consistency(
        self, 
        subject: str, 
        obj: str, 
        result: ConfidenceResult
    ) -> float:
        """实体一致性评分"""
        score = 0.0
        
        # 检查 subject 是否为 TCM 专有实体
        subj_is_tcm, subj_type = self.entity_dict.is_tcm_entity(subject)
        if subj_is_tcm:
            score += self.config.entity_exact_match_weight
            result.matched_entities.append(f"{subject}({subj_type})")
            result.reasons.append(f"Subject '{subject}' 是已知的{subj_type}")
            
            # TCM 精确匹配额外加分
            if subj_type in ["中药", "方剂", "经络穴位"]:
                score += self.config.tcm_exact_match_bonus
                result.reasons.append(f"TCM 实体 {subject} 必须100%匹配")
        else:
            # 模糊匹配
            score += self.config.entity_fuzzy_match_weight
        
        # 检查 object
        obj_is_tcm, obj_type = self.entity_dict.is_tcm_entity(obj)
        if obj_is_tcm:
            score += self.config.entity_exact_match_weight * 0.8  # object 加成稍低
            result.matched_entities.append(f"{obj}({obj_type})")
        else:
            score += self.config.entity_fuzzy_match_weight * 0.5
        
        return min(score, 1.0)
    
    def _score_relation_validity(
        self,
        subject: str,
        relation: str,
        obj: str,
        result: ConfidenceResult
    ) -> float:
        """关系有效性评分"""
        score = 0.0
        
        # 关系类型有效性
        valid_relations = {
            "中药": ["性", "味", "归经", "功效", "治疗", "属于"],
            "方剂": ["功效", "治疗", "组成", "主治", "属于"],
            "经络穴位": ["位于", "分布", "主治"],
            "病证": ["属于", "症状", "病因"],
        }
        
        subj_is_tcm, subj_type = self.entity_dict.is_tcm_entity(subject)
        
        if subj_is_tcm:
            if relation in valid_relations.get(subj_type, []):
                score += self.config.relation_validity_weight
                result.matched_relations.append(f"{relation}(适用于{subj_type})")
            else:
                # 关系与实体类型不匹配
                result.warnings.append(f"关系 '{relation}' 可能不适用于 {subj_type}")
                score += self.config.relation_validity_weight * 0.3
        else:
            score += self.config.relation_validity_weight * 0.5
        
        # 检查矛盾
        contradictions = self._check_contradictions(subject, relation, obj)
        if contradictions:
            result.contradictions.extend(contradictions)
            score -= self.config.contradiction_penalty
            result.reasons.append(f"检测到矛盾: {contradictions}")
        
        return max(0.0, min(score, 1.0))
    
    def _check_contradictions(
        self, 
        subject: str, 
        relation: str, 
        obj: str
    ) -> list[str]:
        """检测矛盾"""
        contradictions = []
        
        # 性味矛盾
        opposite_properties = {
            ("性", "寒"): ["温", "热"],
            ("性", "凉"): ["温", "热"],
            ("性", "温"): ["寒", "凉"],
            ("性", "热"): ["寒", "凉"],
        }
        
        if (relation, obj) in opposite_properties:
            # 检查 subject 是否已有矛盾属性 (这里简化处理)
            pass
        
        return contradictions
    
    def _score_graph_match(
        self,
        subject: str,
        relation: str,
        obj: str,
        graph_service: Any,
        result: ConfidenceResult
    ) -> float:
        """图谱匹配评分"""
        try:
            # 直接查询
            if graph_service.graph.has_edge(subject, obj):
                edge_data = graph_service.graph[subject][obj]
                relations = edge_data.get('relations', [])
                
                if relation in relations:
                    score = self.config.graph_match_weight * 1.0
                    result.reasons.append(f"图谱直接匹配: {relations}")
                    return score
                elif any(r in relations for r in graph_service._related_relations(relation)):
                    score = self.config.graph_match_weight * 0.8
                    result.reasons.append(f"图谱近似匹配: {relations}")
                    return score
            
            # 反向匹配
            if graph_service.graph.has_edge(obj, subject):
                score = self.config.graph_match_weight * 0.5
                result.reasons.append("图谱反向匹配")
                return score
            
            # 路径推理
            paths = graph_service.find_path(subject, obj, max_length=2)
            if paths:
                score = self.config.graph_match_weight * 0.4 * min(len(paths), 3) / 3
                result.reasons.append(f"通过路径推理找到 {len(paths)} 条路径")
                return score
            
        except Exception as e:
            self.logger.warning(f"图谱查询失败: {e}")
        
        return 0.0
    
    def _score_context_relevance(
        self,
        claim: str,
        context: str,
        result: ConfidenceResult
    ) -> float:
        """上下文相关性评分"""
        if not context:
            return self.config.context_relevance_weight * 0.5
        
        # 简单关键词重叠
        claim_words = set(claim)
        context_words = set(context)
        overlap = len(claim_words & context_words)
        
        if overlap > 3:
            return self.config.context_relevance_weight * 1.0
        elif overlap > 0:
            return self.config.context_relevance_weight * 0.6
        else:
            return self.config.context_relevance_weight * 0.3
    
    def _calculate_overall_confidence(
        self,
        entity_score: float,
        relation_score: float,
        graph_score: float,
        context_score: float,
        result: ConfidenceResult
    ) -> float:
        """综合计算置信度"""
        # 加权求和
        weighted = (
            entity_score * (self.config.entity_exact_match_weight + self.config.entity_fuzzy_match_weight) +
            relation_score * self.config.relation_validity_weight +
            graph_score * self.config.graph_match_weight +
            context_score * self.config.context_relevance_weight
        )
        
        # 归一化 (因为权重之和不等于1)
        total_weight = (
            self.config.entity_exact_match_weight + 
            self.config.entity_fuzzy_match_weight +
            self.config.relation_validity_weight +
            self.config.graph_match_weight +
            self.config.context_relevance_weight
        )
        
        confidence = weighted / total_weight
        
        # TCM 专有实体额外加成
        for entity in result.matched_entities:
            if any(et in entity for et in ["中药", "方剂", "经络穴位"]):
                confidence = min(1.0, confidence + 0.05)
        
        # 矛盾惩罚
        if result.contradictions:
            confidence *= (1 - self.config.contradiction_penalty)
        
        return max(0.0, min(1.0, confidence))
    
    def _determine_verdict(self, confidence: float, result: ConfidenceResult) -> Verdict:
        """判定结果"""
        if result.contradictions:
            return Verdict.REJECT
        
        if confidence >= self.config.accept_threshold:
            return Verdict.ACCEPT
        elif confidence >= self.config.uncertain_threshold:
            return Verdict.UNCERTAIN
        else:
            return Verdict.REJECT


# ==================== 快捷函数 ====================
_evaluator: Optional[ConfidenceEvaluator] = None


def get_evaluator() -> ConfidenceEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = ConfidenceEvaluator()
    return _evaluator


def evaluate_confidence(claim: str, context: str = "", graph_service: Any = None) -> ConfidenceResult:
    """快捷置信度评估"""
    return get_evaluator().evaluate(claim, context, graph_service)


# ==================== Demo ====================
if __name__ == '__main__':
    print("=" * 60)
    print("🌿 中医知识置信度评估演示")
    print("=" * 60)
    
    evaluator = ConfidenceEvaluator()
    
    test_claims = [
        ("麻黄性温", ""),
        ("麻黄味辛", ""),
        ("麻黄归肺膀胱经", ""),
        ("麻黄治疗感冒", ""),
        ("黄连治疗感冒", ""),  # 应该 REJECT (黄连清热燥湿，不治感冒)
        ("附子性寒", ""),  # 应该 REJECT (附子性热)
        ("人参功效为大补元气", ""),
    ]
    
    for claim, context in test_claims:
        print(f"\n{'='*50}")
        print(f"声明: {claim}")
        print("-" * 50)
        
        result = evaluator.evaluate(claim, context)
        
        print(f"判定: [{result.verdict.value}]")
        print(f"置信度: {result.confidence:.3f}")
        print(f"分项得分: entity={result.entity_score:.2f}, relation={result.relation_score:.2f}, graph={result.graph_score:.2f}, context={result.context_score:.2f}")
        
        if result.matched_entities:
            print(f"匹配实体: {result.matched_entities}")
        if result.matched_relations:
            print(f"匹配关系: {result.matched_relations}")
        if result.contradictions:
            print(f"矛盾: {result.contradictions}")
        if result.reasons:
            print(f"原因: {result.reasons}")
        if result.warnings:
            print(f"警告: {result.warnings}")
