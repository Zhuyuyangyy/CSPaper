# -*- coding: utf-8 -*-
"""
Complete Dialogue Simulation Log
================================
Demonstration: Elderly TCM Doctor Critiques + 3D Coordinate JSON Output + User Profile

Author: Alice
"""

import json
import sys
import os
from datetime import datetime

# Force UTF-8 output on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(r'C:\Users\联想\.openclaw\workspace')

from app.agents.critique_agent import CritiqueAgent, critique
from app.agents.resource_generator import ResourceGenerator, generate_3d_resource
from app.agents.profile_builder import ProfileBuilder, build_profile


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    print(f"\n### {title}")
    print("-" * 70)


def simulate_dialogue():
    """Simulate complete dialogue flow"""
    
    print_header("TCM Knowledge Q&A System - Multi-Agent Demo")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Roles:")
    print("  [USER] - Ordinary patient")
    print("  [CRITIC] - Elderly TCM critique agent")
    print("  [GENERATOR] - 3D acupuncture point data generator")
    print("  [BUILDER] - User health profile builder")
    print("  [GRAPHRAG] - Knowledge graph verification")
    
    # ==================== Scene 1: User asks about 黄连 ====================
    print_header("Scene 1: User asks 'Can Huanglian treat colds?'")
    
    user_question = "黄连可以治感冒吗？"
    print(f"\n[USER] Question: {user_question}")
    
    # GraphRAG verification
    print_section("[GRAPHRAG] Knowledge Graph Verification")
    
    graph_result = {
        "verdict": "REJECT",
        "confidence": 0.15,
        "reason": "黄连功效为清热燥湿，主治腹泻。感冒属风寒/风热，需解表散邪。黄连苦寒，不治感冒。",
        "levels_passed": 1,
        "evidence": [
            {"type": "direct_edge", "data": {"relations": ["功效"], "object": "清热燥湿"}},
            {"type": "contradiction", "data": ["寒热属性不匹配"]}
        ]
    }
    
    print(f"Confidence: {graph_result['confidence']:.2f}")
    print(f"Verdict: {graph_result['verdict']}")
    print(f"Reason: {graph_result['reason']}")
    
    # Critique agent
    print_section("[CRITIC] Elderly TCM Doctor Critique")
    
    critique_agent = CritiqueAgent()
    critique_result = critique_agent.critique(
        claim="黄连治疗感冒",
        confidence=graph_result['confidence'],
        graph_result=graph_result
    )
    
    print(f"\n[VERDICT]: {critique_result['verdict']}")
    print(f"\n[CRITIQUE TEXT]:")
    print(critique_result['critique'])
    
    if critique_result['classic_quote']:
        print(f"\n[CLASSIC QUOTE]:")
        print(critique_result['classic_quote'])
    
    if critique_result['correct_treatment']:
        print(f"\n[CORRECT TREATMENT]: {critique_result['correct_treatment']}")
    
    # ==================== Scene 2: User asks about acupuncture point ====================
    print_header("Scene 2: User asks 'Where is Hegu point?'")
    
    user_question2 = "合谷穴在哪？我想了解一下"
    print(f"\n[USER] Question: {user_question2}")
    
    # Generate 3D acupuncture data
    print_section("[GENERATOR] 3D Acupuncture Resource Generation")
    
    resource_gen = ResourceGenerator()
    try:
        json_output = resource_gen.generate_json(
            target="LI4",
            treatment="针刺",
            disease="头痛"
        )
        
        print("\n[JSON DATA for Three.js]:")
        print("-" * 70)
        
        data = json.loads(json_output)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        print("\n" + "-" * 70)
        print("[VISUALIZATION PARAMS]:")
        print(f"   Point: {data['point_name']} ({data['target_point']})")
        print(f"   Coords: [{data['coords'][0]:.2f}, {data['coords'][1]:.2f}, {data['coords'][2]:.2f}]")
        print(f"   Meridian: {data['meridian_name']}")
        print(f"   Anatomy: {data['anatomy_note']}")
        print(f"   Stimulation: {data['stimulation']}")
        print(f"   Compatible Points: {', '.join(data['compatible_points']) if data['compatible_points'] else 'None'}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # ==================== Scene 3: User describes symptoms ====================
    print_header("Scene 3: User describes symptoms 'Throat is burning, insomnia, fatigue'")
    
    user_symptoms = "最近嗓子冒火，还失眠多梦，白天没力气"
    print(f"\n[USER] Description: {user_symptoms}")
    
    # Build profile
    print_section("[BUILDER] User Health Profile")
    
    profile_builder = ProfileBuilder()
    profile = profile_builder.build(user_symptoms, user_id="user_001")
    result = profile.to_dict()
    
    print(f"\n[PROFILE SUMMARY] {result['summary']}")
    
    print(f"\n[SYNDROME ANALYSIS]")
    for s in result['syndromes'][:4]:
        print(f"   {s['type']}: {s['score']:.1f} (weight:{s['weight']:.2f})")
    
    print(f"\n[CONSTITUTION]")
    print(f"   Primary: {result['constitution'][0] if result['constitution'] else 'TBD'}")
    if len(result['constitution']) > 1:
        print(f"   Secondary: {result['constitution'][1]}")
    
    print(f"\n[HEALTH TIPS]")
    for i, tip in enumerate(result['tips'], 1):
        print(f"   {i}. {tip}")
    
    if result['warnings']:
        print(f"\n[WARNINGS]")
        for w in result['warnings']:
            print(f"   ! {w}")
    
    print(f"\n[CONFIDENCE]: {result['confidence']:.2f}")
    
    # ==================== Scene 4: Full dialogue ====================
    print_header("Scene 4: Full Dialogue Flow - Multi-Agent Collaboration")
    
    print("""
[USER] Doctor, I have dry mouth, sore throat, and constipation. Am I having internal fire?

[SYSTEM] Hello! Let me analyze for you. Building your health profile first...
""")
    
    symptom_text = "口干舌燥，嗓子疼，便秘"
    profile_result = build_profile(symptom_text, user_id="user_001")
    
    print(f"""
[PROFILE ANALYSIS]
   Primary Syndrome: {profile_result['syndromes'][0]['type']} (weight:{profile_result['syndromes'][0]['weight']:.2f})
   Constitution: {profile_result['constitution'][0] if profile_result['constitution'] else 'TBD'}
   
   Health Tips:
   {' '.join(['   ' + t for t in profile_result['tips'][:3]])}

[SYSTEM] Based on your symptoms, you do have heat syndrome. But we need to differentiate
between excess fire and deficiency fire. Recommend seeing a doctor for proper diagnosis.
""")
    
    print("""
[USER] Can I take Huanglian Shangqing Wan by myself?

[SYSTEM] Let me verify through GraphRAG...
""")
    
    critique_result = critique(
        claim="黄连治疗便秘",
        confidence=0.65,
        graph_result={
            "reason": "黄连清热燥湿，可治热结便秘，但需对证。体虚者慎用。",
            "levels_passed": 2
        }
    )
    
    print(f"""
[GRAPHRAG] Verdict: {critique_result['verdict']}, Confidence: {critique_result['confidence']:.2f}

[CRITIC] "Huanglian is bitter and cold, can clear heat and relieve constipation.
If your constipation is due to excess heat, Huanglian Shangqing Wan is appropriate.
However, for those with deficiency, use with caution as it may damage spleen and stomach.
Start with half dose and observe your body's response."

[3D POINT RECOMMENDATION] For constipation, recommended acupoints:
""")
    
    try:
        for point in ["ST25", "SP6", "KI3"]:
            json_out = generate_3d_resource(point, treatment="按摩", disease="便秘")
            point_data = json.loads(json_out)
            print(f"   - {point_data['point_name']}({point_data['target_point']}): "
                  f"[{point_data['coords'][0]:.2f}, {point_data['coords'][1]:.2f}, {point_data['coords'][2]:.2f}]")
    except Exception as e:
        print(f"   [Loading...]")
    
    print("""
[USER] I heard that needling Hegu point can treat toothache. Is that true?

[SYSTEM] Hegu is indeed an important point for pain relief. Let me generate 3D positioning data...
""")
    
    json_out = generate_3d_resource("LI4", treatment="针刺", disease="牙痛")
    point_data = json.loads(json_out)
    
    print(f"""
[ACUPOINT 3D DATA]

{json.dumps(point_data, ensure_ascii=False, indent=2)}

[3D RENDER PARAMS]:
   - target_point: Hegu standard code (LI4)
   - coords: Human relative coordinate system [X(left/right), Y(up/down), Z(front/back)]
   - meridian_path: Meridian pathway for Three.js to draw meridian lines
   - compatible_points: [JIACHE, XIAGUAN] for synergistic effect
""")
    
    print_header("Demo Complete")
    print("\n[NOTE] This demo showed multi-agent collaboration:")
    print("   1. ProfileBuilder: Converts user speech to TCM syndromes")
    print("   2. GraphRAG: Verifies knowledge accuracy")
    print("   3. CritiqueAgent: Elderly TCM style critique of misconceptions")
    print("   4. ResourceGenerator: Generates Three.js compatible 3D acupoint data")


if __name__ == '__main__':
    simulate_dialogue()
