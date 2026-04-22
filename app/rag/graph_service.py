# -*- coding: utf-8 -*-
"""
GraphRAG Service - TCM Knowledge Graph Service
=============================================
Based on NetworkX directed graph, supports triplet loading and multi-level fact verification.

Functions:
1. Load triplets from JSON and build directed graph
2. Multi-level fact verification (verify_fact)
3. Graph query and reasoning
4. Hybrid RAG with vector retrieval

Author: Alice
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

import networkx as nx

# ==================== Configuration ====================
class GraphConfig:
    """Graph configuration"""
    GRAPH_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw_graph_data.json"
    KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base"
    
    # TCM entity dictionary (must match 100%)
    TCM_ENTITY_TYPES = {
        "中药": ["麻黄", "黄连", "人参", "当归", "附子", "甘草", "石膏", "柴胡", "白芍", "川芎",
                "桂枝", "茯苓", "白术", "生姜", "大黄", "芒硝", "细辛", "半夏", "陈皮",
                "枳壳", "厚朴", "大枣", "山药", "熟地", "生地", "山茱萸", "泽泻", "丹皮", "知母",
                "黄芩", "黄柏", "栀子", "连翘", "薄荷", "荆芥", "防风", "羌活", "独活", "藁本"],
        "方剂": ["麻黄汤", "桂枝汤", "银翘散", "桑菊饮", "败毒散", "补中益气汤", "四君子汤", "四物汤",
                "八珍汤", "六味地黄丸", "金匮肾气丸", "逍遥散", "柴胡疏肝散", "归脾汤", "天王补心丹"],
        "经络穴位": ["足太阳膀胱经", "足阳明胃经", "足少阳胆经", "足太阴脾经", "足少阴肾经", "足厥阴肝经",
                    "手太阴肺经", "手阳明大肠经", "手少阳三焦经", "手太阳小肠经", "手少阴心经", "手厥阴心包经",
                    "百会", "风池", "合谷", "足三里", "涌泉", "关元", "气海", "神阙", "中脘", "天枢"],
        "病证": ["感冒", "咳嗽", "发热", "头痛", "失眠", "便秘", "腹泻", "胃痛", "胁痛", "腰痛",
                "风湿", "痹证", "痿证", "中风", "眩晕", "耳鸣", "鼻炎", "咽炎", "肺炎", "肝炎"]
    }
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLD = 0.6
    ENTITY_EXACT_MATCH_BONUS = 0.3
    
    # Relation weights
    RELATION_WEIGHTS = {
        "属于": 1.0,
        "归经": 1.0,
        "性": 1.0,
        "味": 1.0,
        "治疗": 0.9,
        "主治": 0.9,
        "功效": 0.85,
        "位于": 0.8,
        "分布": 0.8,
    }


# ==================== Logging ====================
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("GraphService")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger


# ==================== Graph Service ====================
class GraphRAGService:
    """TCM Knowledge Graph Service"""
    
    def __init__(self, config: type[GraphConfig] = GraphConfig):
        self.config = config
        self.logger = setup_logging()
        self.graph: nx.DiGraph = nx.DiGraph()
        self._node_metadata: dict[str, dict] = {}
        self._entity_index: dict[str, set[str]] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration"""
        self.logger.info("Graph configuration loaded")
        self.logger.info("  TCM entity types: %d categories", len(self.config.TCM_ENTITY_TYPES))
        total_entities = sum(len(v) for v in self.config.TCM_ENTITY_TYPES.values())
        self.logger.info("  Total entities: %d", total_entities)
    
    # ==================== Graph Building ====================
    def load_from_json(self, file_path: Optional[str] = None) -> int:
        """
        Load triplets from JSON file and build directed graph.
        
        Args:
            file_path: Path to triplet JSON file
            
        Returns:
            Number of edges loaded
        """
        if file_path is None:
            file_path = str(self.config.GRAPH_DATA_PATH)
        
        path = Path(file_path)
        if not path.exists():
            self.logger.warning("Graph file not found: %s", path)
            return 0
        
        self.logger.info("Loading graph: %s", path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                triples = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error("JSON parse failed: %s", e)
            return 0
        
        edges_added = 0
        nodes_seen = set()
        
        for triple in triples:
            try:
                subject = str(triple.get('subject', '')).strip()
                relation = str(triple.get('relation', '')).strip()
                obj = str(triple.get('object', '')).strip()
                source = triple.get('source', '')
                extracted_at = triple.get('extracted_at', '')
                
                if not all([subject, relation, obj]):
                    continue
                
                # Add edge
                if self.graph.has_edge(subject, obj):
                    existing_data = self.graph[subject][obj]
                    existing_data['relations'].append(relation)
                    existing_data['sources'].append(source)
                else:
                    self.graph.add_edge(subject, obj, 
                        relations=[relation],
                        sources=[source],
                        weight=self.config.RELATION_WEIGHTS.get(relation, 0.8)
                    )
                    edges_added += 1
                
                # Record node metadata
                self._node_metadata[subject] = {
                    'type': self._classify_entity(subject),
                    'first_seen': extracted_at or datetime.now().isoformat()
                }
                self._node_metadata[obj] = {
                    'type': self._classify_entity(obj),
                    'first_seen': extracted_at or datetime.now().isoformat()
                }
                
                nodes_seen.update([subject, obj])
                self._update_entity_index(subject, relation, obj)
                
            except Exception as e:
                self.logger.warning("Triplet processing failed: %s", e)
                continue
        
        self.logger.info("Graph loaded: %d nodes, %d edges", self.graph.number_of_nodes(), self.graph.number_of_edges())
        return edges_added
    
    def _classify_entity(self, entity: str) -> str:
        """Auto-classify entity type"""
        for etype, keywords in self.config.TCM_ENTITY_TYPES.items():
            if entity in keywords:
                return etype
        return "通用"
    
    def _update_entity_index(self, subject: str, relation: str, obj: str):
        """Update entity inverted index"""
        if subject not in self._entity_index:
            self._entity_index[subject] = set()
        self._entity_index[subject].add(f"{relation}->{obj}")
        
        if obj not in self._entity_index:
            self._entity_index[obj] = set()
        self._entity_index[obj].add(f"<-{relation}--{subject}")
    
    # ==================== Graph Query ====================
    def get_outgoing(self, node: str) -> list[tuple[str, dict]]:
        """Get all outgoing edges of a node"""
        if node not in self.graph:
            return []
        return list(self.graph.out_edges(node, data=True))
    
    def get_incoming(self, node: str) -> list[tuple[str, dict]]:
        """Get all incoming edges of a node"""
        if node not in self.graph:
            return []
        return list(self.graph.in_edges(node, data=True))
    
    def get_neighbors(self, node: str, depth: int = 1) -> dict[str, list]:
        """Get neighbor nodes"""
        if depth == 1:
            return {
                'out': [target for _, target in self.graph.out_edges(node)],
                'in': [source for source, _ in self.graph.in_edges(node)]
            }
        
        out_nodes = set()
        in_nodes = set()
        current_out = {node}
        current_in = {node}
        
        for _ in range(depth):
            next_out = set()
            next_in = set()
            
            for n in current_out:
                next_out.update(self.graph.successors(n))
            for n in current_in:
                next_in.update(self.graph.predecessors(n))
            
            out_nodes.update(next_out)
            in_nodes.update(next_in)
            current_out = next_out
            current_in = next_in
        
        return {'out': list(out_nodes), 'in': list(in_nodes)}
    
    def find_path(self, source: str, target: str, max_length: int = 3) -> list[list[str]]:
        """Find shortest path between two nodes"""
        if source not in self.graph or target not in self.graph:
            return []
        
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_length))
            return paths
        except nx.NetworkXError:
            return []
    
    def get_subgraph(self, center_node: str, radius: int = 1) -> nx.DiGraph:
        """Get subgraph centered on a node"""
        if center_node not in self.graph:
            return nx.DiGraph()
        
        nodes = {center_node}
        current = {center_node}
        
        for _ in range(radius):
            next_layer = set()
            for n in current:
                next_layer.update(self.graph.successors(n))
                next_layer.update(self.graph.predecessors(n))
            nodes.update(next_layer)
            current = next_layer
        
        return self.graph.subgraph(nodes).copy()
    
    # ==================== Fact Verification (Multi-level) ====================
    def verify_fact(self, claim: str, context: str = "") -> dict[str, Any]:
        """
        Multi-level fact verification.
        
        Levels:
        1. Direct graph match (A --R--> B)
        2. Reverse graph match (B <--R-- A)
        3. Path inference
        4. Contradiction detection
        5. Entity type consistency
        
        Args:
            claim: Claim to verify (e.g., "黄连治疗感冒")
            context: Additional context
            
        Returns:
            {
                "verdict": "ACCEPT" | "REJECT" | "UNCERTAIN",
                "confidence": 0.0-1.0,
                "reason": str,
                "evidence": [{"type": str, "data": Any}],
                "levels_passed": int,
            }
        """
        self.logger.info("[verify_fact] Verifying claim: %s", claim)
        
        result = {
            "verdict": "UNCERTAIN",
            "confidence": 0.0,
            "reason": "",
            "evidence": [],
            "levels_passed": 0,
            "claim": claim
        }
        
        # Parse claim
        parsed = self._parse_claim(claim)
        if not parsed:
            result["reason"] = "Cannot parse claim format"
            return result
        
        subject, relation, obj = parsed
        self.logger.info("  Parsed: %s --[%s]--> %s", subject, relation, obj)
        
        # ===== Level 1: Direct Match =====
        if self.graph.has_edge(subject, obj):
            edge_data = self.graph[subject][obj]
            relations = edge_data.get('relations', [])
            
            if relation in relations or any(r in relations for r in self._related_relations(relation)):
                result["levels_passed"] = 1
                result["confidence"] = 0.85
                result["reason"] = f"Direct graph match: {relations} (TCM entity bonus)"
                result["evidence"].append({
                    "type": "direct_edge",
                    "data": {"relations": relations, "weight": edge_data.get('weight', 1.0)}
                })
                
                # TCM exact match bonus
                if self._is_tcm_entity(subject) or self._is_tcm_entity(obj):
                    result["confidence"] = min(1.0, result["confidence"] + 0.15)
                    result["reason"] += " (TCM entity bonus)"
                
                self.logger.info("  [PASS] Level 1 passed: confidence=%.2f", result['confidence'])
                return self._finalize_verdict(result)
        
        # ===== Level 2: Reverse Match =====
        reverse_relation = self._get_reverse_relation(relation)
        
        if self.graph.has_edge(obj, subject):
            edge_data = self.graph[obj][subject]
            relations = edge_data.get('relations', [])
            
            if any(r in relations for r in [reverse_relation, relation]):
                result["levels_passed"] = 2
                result["confidence"] = 0.6
                result["reason"] = f"Reverse graph match: {obj} -> {subject} ({relations})"
                result["evidence"].append({
                    "type": "reverse_edge",
                    "data": {"relations": relations}
                })
                self.logger.info("  [PASS] Level 2 passed: confidence=%.2f", result['confidence'])
        
        # ===== Level 3: Path Inference =====
        paths = self.find_path(subject, obj, max_length=2)
        if paths:
            result["levels_passed"] = max(result["levels_passed"], 3)
            path_bonus = min(0.2, len(paths) * 0.05)
            result["confidence"] = max(result["confidence"], 0.4 + path_bonus)
            result["evidence"].append({
                "type": "path_inference",
                "data": {"paths": paths[:5]}
            })
            result["reason"] += f" | Path inference: {len(paths)} paths"
            self.logger.info("  [PASS] Level 3 passed: %d paths, confidence=%.2f", len(paths), result['confidence'])
        
        # ===== Level 4: Contradiction Detection =====
        contradictions = self._detect_contradiction(subject, relation, obj)
        if contradictions:
            result["evidence"].append({
                "type": "contradiction",
                "data": contradictions
            })
            result["confidence"] *= 0.3
            result["reason"] += f" | Contradiction detected: {contradictions}"
            result["verdict"] = "REJECT"
            self.logger.warning("  [FAIL] Level 4 contradiction: %s", contradictions)
            return result
        
        # ===== Level 5: Entity Type Consistency =====
        type_check = self._check_entity_type_consistency(subject, relation, obj)
        if not type_check["consistent"]:
            result["confidence"] *= type_check["penalty"]
            result["reason"] += f" | Entity type mismatch: {type_check['reason']}"
        
        return self._finalize_verdict(result)
    
    def _parse_claim(self, claim: str) -> Optional[tuple[str, str, str]]:
        """Parse claim into (subject, relation, obj)"""
        import re
        
        relation_keywords = {
            "属于": ["属于", "归于"],
            "治疗": ["治疗", "主治", "用于"],
            "功效": ["功效", "具有", "能够"],
            "归经": ["归肺", "归膀胱", "归经"],
            "性": ["性"],
            "味": ["味"],
            "位于": ["位于"]
        }
        
        # Special handling for gui jing pattern: 麻黄归肺膀胱经 or 麻黄归经
        guijing_match = re.search(r'([^ ]+?)归([\u4e00-\u9fa5]*?)经$', claim)
        if guijing_match:
            subject = guijing_match.group(1).strip()
            obj = guijing_match.group(2).strip()
            if obj:
                obj = obj + '经'
            else:
                obj = '肺膀胱经'  # default
            if subject:
                return (subject, "归经", obj)
        
        # Sort keywords by length descending to match longer patterns first
        all_keywords = []
        for rel, keywords in relation_keywords.items():
            for kw in keywords:
                all_keywords.append((len(kw), kw, rel))
        all_keywords.sort(key=lambda x: -x[0])
        
        for _, kw, rel in all_keywords:
            if kw in claim:
                parts = claim.split(kw, 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    obj = parts[1].strip().rstrip('。.,，、')
                    if subject and obj:
                        return (subject, rel, obj)
        
        return None
    
    def _related_relations(self, relation: str) -> list[str]:
        """Get related relation types"""
        related = {
            "治疗": ["主治", "功效", "用于"],
            "属于": ["归经", "性"],
            "归经": ["属于", "性"],
        }
        return related.get(relation, [])
    
    def _get_reverse_relation(self, relation: str) -> str:
        """Get reverse relation"""
        reverse_map = {
            "治疗": "被治疗",
            "属于": "包含",
            "功效": "主治",
        }
        return reverse_map.get(relation, f"被{relation}")
    
    def _is_tcm_entity(self, entity: str) -> bool:
        """Check if entity is a TCM-specific entity"""
        for entities in self.config.TCM_ENTITY_TYPES.values():
            if entity in entities:
                return True
        return False
    
    def _detect_contradiction(self, subject: str, relation: str, obj: str) -> list[str]:
        """Detect contradictions"""
        contradictions = []
        
        if relation in ["性", "味"]:
            opposite = {
                "寒": ["温", "热"], "凉": ["温", "热"],
                "温": ["寒", "凉"], "热": ["寒", "凉"],
                "辛": ["酸", "苦"], "苦": ["甘", "辛"],
                "甘": ["苦", "酸"], "酸": ["甘", "辛"]
            }
            
            if subject in self.graph:
                for _, other_obj, data in self.graph.out_edges(subject, data=True):
                    if data.get('relations') and relation in data['relations']:
                        if other_obj in opposite and opposite[other_obj] == obj:
                            contradictions.append(f"Property contradiction: {obj} vs {other_obj}")
        
        return contradictions
    
    def _check_entity_type_consistency(self, subject: str, relation: str, obj: str) -> dict:
        """Check entity type consistency"""
        result = {"consistent": True, "penalty": 1.0, "reason": ""}
        
        subj_type = self._node_metadata.get(subject, {}).get('type', '通用')
        obj_type = self._node_metadata.get(obj, {}).get('type', '通用')
        
        constraints = {
            "性": {"subject": ["中药"], "object": ["通用"]},
            "味": {"subject": ["中药"], "object": ["通用"]},
            "归经": {"subject": ["中药", "方剂"], "object": ["经络穴位"]},
            "治疗": {"subject": ["中药", "方剂", "经络穴位"], "object": ["病证"]},
            "功效": {"subject": ["中药", "方剂"], "object": ["通用"]},
        }
        
        if relation in constraints:
            constraint = constraints[relation]
            
            if subj_type not in constraint["subject"] and subj_type != "通用":
                result["consistent"] = False
                result["penalty"] = 0.7
                result["reason"] = f"{subject}({subj_type}) invalid for relation {relation}"
            
            if obj_type not in constraint["object"] and obj_type != "通用":
                result["consistent"] = False
                result["penalty"] = 0.7
                result["reason"] += f" | {obj}({obj_type}) is not a valid object"
        
        return result
    
    def _finalize_verdict(self, result: dict) -> dict:
        """Finalize verdict"""
        confidence = result["confidence"]
        
        # TCM exact match bonus
        claim = result.get("claim", "")
        for entity_list in self.config.TCM_ENTITY_TYPES.values():
            for entity in entity_list:
                if entity in claim:
                    result["confidence"] = min(1.0, confidence + 0.1)
                    break
        
        # Final verdict
        if result["confidence"] >= self.config.CONFIDENCE_THRESHOLD:
            if result["levels_passed"] >= 2:
                result["verdict"] = "ACCEPT"
            else:
                result["verdict"] = "UNCERTAIN"
        else:
            result["verdict"] = "REJECT"
        
        self.logger.info("  Final verdict: [%s] confidence=%.2f", result['verdict'], result['confidence'])
        return result
    
    # ==================== Graph Statistics ====================
    def get_stats(self) -> dict:
        """Get graph statistics"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "entity_types": {k: len(v) for k, v in self.config.TCM_ENTITY_TYPES.items()},
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(1, self.graph.number_of_nodes()),
            "config": {
                "confidence_threshold": self.config.CONFIDENCE_THRESHOLD,
                "entity_exact_match_bonus": self.config.ENTITY_EXACT_MATCH_BONUS,
            }
        }
    
    def export_to_json(self, file_path: Optional[str] = None) -> int:
        """Export graph to JSON"""
        if file_path is None:
            file_path = str(self.config.GRAPH_DATA_PATH)
        
        path = Path(file_path)
        
        triples = []
        for subject, obj, data in self.graph.edges(data=True):
            for relation in data.get('relations', []):
                triples.append({
                    "subject": subject,
                    "relation": relation,
                    "object": obj,
                    "sources": data.get('sources', []),
                    "weight": data.get('weight', 1.0)
                })
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(triples, f, ensure_ascii=False, indent=2)
        
        self.logger.info("Exported %d triplets to %s", len(triples), path)
        return len(triples)


# ==================== Quick Functions ====================
_global_service: Optional[GraphRAGService] = None


def get_service() -> GraphRAGService:
    """Get global graph service instance"""
    global _global_service
    if _global_service is None:
        _global_service = GraphRAGService()
        _global_service.load_from_json()
    return _global_service


def verify_fact(claim: str, context: str = "") -> dict:
    """Quick verification function"""
    return get_service().verify_fact(claim, context)


# ==================== Demo ====================
if __name__ == '__main__':
    service = GraphRAGService()
    
    # Add mock triplets
    mock_triples = [
        {"subject": "麻黄", "relation": "性", "object": "温", "source": "本草纲目"},
        {"subject": "麻黄", "relation": "味", "object": "辛", "source": "本草纲目"},
        {"subject": "麻黄", "relation": "归经", "object": "肺", "source": "本草纲目"},
        {"subject": "麻黄", "relation": "归经", "object": "膀胱经", "source": "本草纲目"},
        {"subject": "麻黄", "relation": "功效", "object": "发汗解表", "source": "伤寒论"},
        {"subject": "麻黄", "relation": "功效", "object": "宣肺平喘", "source": "伤寒论"},
        {"subject": "麻黄", "relation": "治疗", "object": "风寒感冒", "source": "伤寒论"},
        {"subject": "麻黄", "relation": "治疗", "object": "咳嗽", "source": "伤寒论"},
        {"subject": "黄连", "relation": "性", "object": "寒", "source": "本草纲目"},
        {"subject": "黄连", "relation": "味", "object": "苦", "source": "本草纲目"},
        {"subject": "黄连", "relation": "功效", "object": "清热燥湿", "source": "本草纲目"},
        {"subject": "黄连", "relation": "治疗", "object": "腹泻", "source": "本草纲目"},
        {"subject": "感冒", "relation": "属于", "object": "外感病", "source": "中医基础理论"},
    ]
    
    for triple in mock_triples:
        s, r, o = triple['subject'], triple['relation'], triple['object']
        service.graph.add_edge(s, o, relations=[r], sources=[triple['source']], weight=0.9)
        service._node_metadata[s] = {'type': service._classify_entity(s), 'first_seen': ''}
        service._node_metadata[o] = {'type': service._classify_entity(o), 'first_seen': ''}
    
    print("\n" + "=" * 60)
    print("TCM Knowledge Graph GraphRAG Demo")
    print("=" * 60)
    
    stats = service.get_stats()
    print("\nGraph stats: %d nodes, %d edges", stats['nodes'], stats['edges'])
    
    print("\n" + "-" * 60)
    print("Test: Verification Results")
    print("-" * 60)
    
    for claim in [
        "麻黄性温",
        "麻黄味辛",
        "麻黄归经",
        "麻黄治疗感冒",
        "黄连治疗感冒",
    ]:
        result = service.verify_fact(claim)
        print(f"\nClaim: {claim}")
        print(f"  Verdict: [{result['verdict']}] Confidence: {result['confidence']:.2f}")
        print(f"  Reason: {result['reason']}")
        if result['evidence']:
            print(f"  Evidence: {result['evidence'][:2]}")
