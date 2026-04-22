# 3D 人体模型目录

> 本目录用于存放标准的 1.8 米男性/女性 GLTF 人体模型

## 📐 坐标系说明

### 坐标系定义

```
       ▲ Y (头正方向, +Y)
       │
       │
       │      X (右正方向)
       │    ↗
       │   /
       │  /
       │ /
       └────────────► Z (前正方向)
      /
     /
    ▼
  (背)
```

| 轴 | 方向 | 说明 |
|----|------|------|
| **X** | 左负右正 | 人体左右方向，左为负，右为正 |
| **Y** | 足负头正 | 人体上下方向，脚为负，头为正 |
| **Z** | 背负前正 | 人体前后方向，背为负，前为正 |

### 坐标单位

- **单位**: 标准化单位 (1 unit ≈ 1 米)
- **模型身高**: 1.8 米 (180cm)
- **坐标范围**: X ∈ [-0.5, 0.5], Y ∈ [0, 1.8], Z ∈ [-0.3, 0.3]

### 关键穴位坐标参考 (1.8米男性基准)

| 穴位 | 代码 | X | Y | Z | 说明 |
|------|------|-----|------|-----|------|
| 百会 | DU20 | 0 | 1.72 | 0.02 | 头顶正中央 |
| 印堂 | EX-HN3 | 0 | 1.62 | 0.05 | 两眉之间 |
| 人中 | DU26 | 0 | 1.55 | 0.03 | 人中沟上1/3 |
| 承浆 | RN24 | 0 | 1.50 | 0.03 | 下唇中央下方 |
| 膻中 | RN17 | 0 | 1.35 | 0.08 | 两乳头连线中点 |
| 中脘 | RN12 | 0 | 1.20 | 0.08 | 脐上4寸 |
| 神阙 | RN8 | 0 | 1.05 | 0.08 | 肚脐中央 |
| 关元 | RN4 | 0 | 0.90 | 0.08 | 脐下3寸 |
| 气海 | RN6 | 0 | 0.95 | 0.08 | 脐下1.5寸 |
| 足三里 | ST36 | 0.05 | 0.42 | 0.02 | 犊鼻下3寸 |
| 丰隆 | ST40 | 0.05 | 0.38 | 0.02 | 外踝尖上8寸 |
| 三阴交 | SP6 | 0.04 | 0.35 | 0.02 | 内踝尖上3寸 |
| 太溪 | KI3 | -0.04 | 0.28 | 0.02 | 内踝与跟腱之间 |
| 涌泉 | KI1 | 0 | 0.02 | 0.05 | 足心前1/3 |
| 合谷 | LI4 | 0.08 | 1.35 | 0.03 | 手背第1-2掌骨间 |
| 曲池 | LI11 | 0.05 | 1.08 | 0.02 | 肘横纹桡侧端 |
| 内关 | PC6 | -0.04 | 1.25 | 0.02 | 腕横纹上2寸 |
| 外关 | SJ5 | 0.04 | 1.25 | 0.02 | 腕背横纹上2寸 |
| 风池 | GB20 | 0.08 | 1.45 | 0.08 | 枕骨粗隆旁开 |
| 肩井 | GB21 | 0.06 | 1.30 | 0.02 | 大椎与肩峰连线中点 |

### 十四经络路径坐标 (简化)

#### 手太阴肺经 (LU)
```
LU1 (中府)  →  LU2 (云门)  →  LU3 (天府)  →  LU4 (侠白)
     ↓              ↓             ↓             ↓
[0.08,1.45] → [0.10,1.43] → [0.09,1.38] → [0.08,1.35]
     ↓              ↓             ↓             ↓
LU5 (尺泽)  →  LU6 (孔最)  →  LU7 (列缺)  →  LU9 (太渊)
[0.07,1.20] → [0.06,1.15] → [0.05,1.10] → [0.04,1.05]
```

#### 足阳明胃经 (ST)
```
ST1 (承泣)  →  ST2 (四白)  →  ST3 (巨髎)  →  ST4 (地仓)
[0,1.60]   → [0.04,1.58] → [0.05,1.55] → [0.06,1.52]
     ↓                                           ↓
ST7 (下关)  ←                              ST8 (颊车)
[0.06,1.48]                                    [0.06,1.45]
     ↓
ST9 (人迎)  →  ST10 (水突)  →  ...  →  ST36 (足三里)
[0.08,1.40] → [0.08,1.35]            → [0.05,0.42]
```

## 📁 模型文件

### 推荐模型

请将以下模型文件放入本目录：

| 文件名 | 描述 | 格式 | 推荐比例 |
|--------|------|------|----------|
| `human_male_180cm.glb` | 1.8米男性标准模型 | GLB | 50% |
| `human_female_170cm.glb` | 1.7米女性标准模型 | GLB | 50% |
| `human_neutral.glb` | 中性人体模型 | GLB | 备用 |

### 模型要求

1. **格式**: GLB (GL Transmission Format) 或 GLTF
2. **骨架**: 绑定标准骨骼 (Mixamo 或 similar)
3. **UV**: 展开 UV 用于贴图
4. **LOD**: 建议包含多级别细节
5. **顶点**: 建议 10K-50K 面

### 免费模型来源

- [Mixamo](https://www.mixamo.com/) - 免费角色模型
- [CGTrader](https://www.cgtrader.com/) - 有免费选项
- [Sketchfab](https://sketchfab.com/) - CC 许可模型
- [Quaternius](https://quaternius.com/) - 低多边形免费

### 模型命名规范

```
human_{gender}_{height}cm_{variant}.glb

示例:
  human_male_180cm_standard.glb
  human_female_170cm_slim.glb
  human_neutral_175cm_athletic.glb
```

## 🔧 前端加载代码

```javascript
// 模型加载示例
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

class TCMHumanModel {
    constructor() {
        this.loader = new GLTFLoader();
        this.model = null;
        this.group = new THREE.Group();
    }
    
    async loadModel(modelPath = '/static/models/human_male_180cm.glb') {
        return new Promise((resolve, reject) => {
            this.loader.load(
                modelPath,
                (gltf) => {
                    this.model = gltf.scene;
                    
                    // 调整大小 (模型原尺寸可能不同)
                    this.model.scale.set(1, 1, 1);
                    
                    // 居中
                    const box = new THREE.Box3().setFromObject(this.model);
                    const center = box.getCenter(new THREE.Vector3());
                    this.model.position.sub(center);
                    
                    // Y 轴归零 (脚底对齐地面)
                    this.model.position.y = 0;
                    
                    this.group.add(this.model);
                    resolve(this.model);
                },
                (progress) => {
                    console.log(`Loading: ${(progress.loaded / progress.total * 100).toFixed(1)}%`);
                },
                reject
            );
        });
    }
    
    // 将相对坐标转换为世界坐标
    getWorldPosition(acupointLocalCoords) {
        const [x, y, z] = acupointLocalCoords;
        
        // 模型原点已在 (0, 0, 0)，脚底在 Y=0
        return new THREE.Vector3(x, y, z);
    }
    
    // 高亮穴位
    highlightAcupoint(worldPos, color = 0xff6600) {
        const marker = new THREE.Mesh(
            new THREE.SphereGeometry(0.02, 16, 16),
            new THREE.MeshStandardMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.5
            })
        );
        
        marker.position.copy(worldPos);
        this.group.add(marker);
        
        return marker;
    }
}
```

## 📊 坐标验证

### 基准测试点

| 测试 | 预期 | 验证方法 |
|------|------|----------|
| 百会 (DU20) | Y ≈ 1.72 | 手动测量头顶位置 |
| 涌泉 (KI1) | Y ≈ 0.02 | 手动测量脚心位置 |
| 左手合谷 (LI4) | X > 0, Y ≈ 1.35 | 确认左右侧 |

---

*最后更新: 2026-04-19*
