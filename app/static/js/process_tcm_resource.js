/**
 * process_tcm_resource.js
 * ==========================
 * 前端 Three.js 消费模块 - 处理 SSE 中医3D资源
 * 
 * 功能：
 * 1. 接收 SSE animation_desc 事件
 * 2. 解析 coords 坐标数组
 * 3. 在 GLTF 人体模型上高亮穴位
 * 4. 实现脉冲光效和经络游走动画
 * 
 * @author Alice
 * @version 1.0.0
 */

// ==================== 导入 Three.js ====================
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// ==================== 配置 ====================
const TCM_CONFIG = {
    // 坐标系说明：
    // X: 左右 (左负右正)
    // Y: 上下 (足负头正)
    // Z: 前后 (前正后负)
    coordinateScale: 1.0,  // 坐标系缩放
    
    // 穴位高亮配置
    acupointHighlight: {
        color: 0xff6600,      // 橙色光效
        emissiveColor: 0xff3300,
        pulseSpeed: 2.0,     // 脉冲速度 (Hz)
        pulseMin: 0.3,       // 脉冲最小强度
        pulseMax: 1.0,        // 脉冲最大强度
        glowRadius: 0.08,     // 光晕半径
    },
    
    // 经络动画配置
    meridianAnimation: {
        color: 0x00ff88,      // 绿色游走
        speed: 0.5,           // 游走速度
        particleCount: 50,     // 粒子数量
        trailLength: 20,       // 轨迹长度
    },
    
    // 相机配置
    camera: {
        fov: 45,
        near: 0.1,
        far: 1000,
        initialPosition: { x: 0, y: 0.8, z: 2.5 }
    }
};

// ==================== TCM 3D 资源处理器 ====================
class TCM3DResourceProcessor {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`[TCM3D] Container #${containerId} not found`);
            return;
        }
        
        // Three.js 核心对象
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;
        
        // 人体模型
        this.bodyModel = null;
        this.bodyGroup = new THREE.Group();
        
        // 穴位标记
        this.acupointMarkers = new Map();  // code -> marker
        this.acupointGroup = new THREE.Group();
        
        // 经络线
        this.meridianLines = new Map();    // meridianName -> line
        this.meridianGroup = new THREE.Group();
        
        // 动画状态
        this.animationState = {
            isPlaying: false,
            currentTime: 0,
            pulsePhase: 0,
        };
        
        // 事件回调
        this.eventCallbacks = {
            onResourceReceived: [],
            onAcupointHighlight: [],
            onMeridianAnimate: [],
            onError: []
        };
        
        this._init();
    }
    
    // ==================== 初始化 ====================
    _init() {
        console.log('[TCM3D] Initializing...');
        
        // 创建场景
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);
        
        // 创建相机
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(
            TCM_CONFIG.camera.fov,
            aspect,
            TCM_CONFIG.camera.near,
            TCM_CONFIG.camera.far
        );
        this.camera.position.set(
            TCM_CONFIG.camera.initialPosition.x,
            TCM_CONFIG.camera.initialPosition.y,
            TCM_CONFIG.camera.initialPosition.z
        );
        
        // 创建渲染器
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.container.appendChild(this.renderer.domElement);
        
        // 创建轨道控制器
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.target.set(0, 0.8, 0);
        
        // 添加光源
        this._setupLights();
        
        // 添加地面网格
        this._setupGrid();
        
        // 后处理 - Bloom 效果
        this._setupPostProcessing();
        
        // 添加到场景
        this.scene.add(this.bodyGroup);
        this.scene.add(this.acupointGroup);
        this.scene.add(this.meridianGroup);
        
        // 开始渲染循环
        this._animate();
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => this._onResize());
        
        console.log('[TCM3D] Initialized successfully');
    }
    
    _setupLights() {
        // 环境光
        const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
        this.scene.add(ambientLight);
        
        // 主光源
        const mainLight = new THREE.DirectionalLight(0xffffff, 1);
        mainLight.position.set(5, 10, 5);
        mainLight.castShadow = true;
        this.scene.add(mainLight);
        
        // 补光
        const fillLight = new THREE.DirectionalLight(0x8888ff, 0.3);
        fillLight.position.set(-5, 5, -5);
        this.scene.add(fillLight);
    }
    
    _setupGrid() {
        // 地面网格帮助定位
        const gridHelper = new THREE.GridHelper(3, 30, 0x444444, 0x222222);
        gridHelper.position.y = -1;
        this.scene.add(gridHelper);
    }
    
    _setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);
        
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);
        
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            0.5,   // strength
            0.4,   // radius
            0.85   // threshold
        );
        this.composer.addPass(bloomPass);
    }
    
    // ==================== 渲染循环 ====================
    _animate() {
        requestAnimationFrame(() => this._animate());
        
        const delta = 0.016; // ~60fps
        
        // 更新控制器
        this.controls.update();
        
        // 更新脉冲动画
        this._updatePulseAnimation(delta);
        
        // 更新经络游走动画
        this._updateMeridianAnimation(delta);
        
        // 渲染
        this.composer.render();
    }
    
    _updatePulseAnimation(delta) {
        if (!this.animationState.isPlaying) return;
        
        this.animationState.pulsePhase += delta * TCM_CONFIG.acupointHighlight.pulseSpeed;
        const phase = this.animationState.pulsePhase;
        
        const intensity = TCM_CONFIG.acupointHighlight.pulseMin + 
            (Math.sin(phase * Math.PI * 2) + 1) / 2 * 
            (TCM_CONFIG.acupointHighlight.pulseMax - TCM_CONFIG.acupointHighlight.pulseMin);
        
        // 更新所有穴位标记的 emissive 强度
        this.acupointMarkers.forEach((marker) => {
            if (marker.material) {
                marker.material.emissiveIntensity = intensity;
            }
        });
    }
    
    _updateMeridianAnimation(delta) {
        // 经络游走动画 - 沿路径移动的高亮粒子
        this.meridianLines.forEach((lineData, meridianName) => {
            if (!lineData.isAnimating) return;
            
            lineData.animPhase = (lineData.animPhase || 0) + delta * TCM_CONFIG.meridianAnimation.speed;
            if (lineData.animPhase > 1) lineData.animPhase = 0;
            
            // 更新粒子位置
            if (lineData.particles) {
                const positions = lineData.particles.geometry.attributes.position;
                const path = lineData.path;
                
                for (let i = 0; i < positions.count; i++) {
                    const t = (lineData.animPhase + i / positions.count) % 1;
                    const point = this._getPointOnPath(path, t);
                    positions.setXYZ(i, point.x, point.y, point.z);
                }
                positions.needsUpdate = true;
            }
        });
    }
    
    _getPointOnPath(path, t) {
        // 根据t值获取路径上的点 (t: 0-1)
        if (!path || path.length < 2) return new THREE.Vector3();
        
        const totalSegments = path.length - 1;
        const segmentIndex = Math.min(Math.floor(t * totalSegments), totalSegments - 1);
        const segmentT = (t * totalSegments) - segmentIndex;
        
        const p1 = new THREE.Vector3(...path[segmentIndex]);
        const p2 = new THREE.Vector3(...path[segmentIndex + 1]);
        
        return p1.clone().lerp(p2, segmentT);
    }
    
    _onResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
        this.composer.setSize(width, height);
    }
    
    // ==================== 公开 API ====================
    
    /**
     * 加载人体 GLTF 模型
     * @param {string} modelUrl - 模型URL
     */
    async loadBodyModel(modelUrl) {
        console.log(`[TCM3D] Loading body model: ${modelUrl}`);
        
        return new Promise((resolve, reject) => {
            const loader = new GLTFLoader();
            
            loader.load(
                modelUrl,
                (gltf) => {
                    this.bodyModel = gltf.scene;
                    
                    // 调整模型大小和位置
                    this.bodyModel.scale.set(1, 1, 1);
                    this.bodyModel.position.set(0, -0.9, 0);
                    
                    // 启用阴影
                    this.bodyModel.traverse((child) => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                        }
                    });
                    
                    this.bodyGroup.add(this.bodyModel);
                    console.log('[TCM3D] Body model loaded successfully');
                    resolve(this.bodyModel);
                },
                (progress) => {
                    console.log(`[TCM3D] Loading progress: ${(progress.loaded / progress.total * 100).toFixed(1)}%`);
                },
                (error) => {
                    console.error('[TCM3D] Failed to load body model:', error);
                    this._emit('onError', { type: 'model_load', error });
                    reject(error);
                }
            );
        });
    }
    
    /**
     * 处理 SSE 接收到的 3D 资源数据
     * @param {Object} data - SSE event data
     */
    processResourceData(data) {
        console.log('[TCM3D] Processing resource data:', data);
        
        // 触发回调
        this._emit('onResourceReceived', data);
        
        if (data.type === 'acupoint' || data.type === 'acupoint_recommendation') {
            this.addAcupointMarker({
                code: data.point_code,
                name: data.point_name,
                coords: data.coords,
                meridianName: data.meridian_name,
                animationDesc: data.animation_desc,
                anatomyNote: data.anatomy_note,
                stimulation: data.stimulation
            });
        }
        
        if (data.meridian_path && data.meridian_path.length > 0) {
            this.addMeridianLine(data.meridian_name, data.meridian_path);
        }
    }
    
    /**
     * 添加穴位标记
     * @param {Object} acupoint - 穴位数据
     */
    addAcupointMarker(acupoint) {
        console.log(`[TCM3D] Adding acupoint marker: ${acupoint.name} (${acupoint.code})`);
        
        const { code, name, coords, meridianName } = acupoint;
        
        // 检查是否已存在
        if (this.acupointMarkers.has(code)) {
            console.log(`[TCM3D] Acupoint ${code} already exists, skipping`);
            return;
        }
        
        // 创建穴位标记球体
        const geometry = new THREE.SphereGeometry(TCM_CONFIG.acupointHighlight.glowRadius, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: TCM_CONFIG.acupointHighlight.color,
            emissive: TCM_CONFIG.acupointHighlight.emissiveColor,
            emissiveIntensity: 0.5,
            metalness: 0.3,
            roughness: 0.4,
        });
        
        const marker = new THREE.Mesh(geometry, material);
        
        // 设置位置 (coords 是 [x, y, z])
        marker.position.set(
            coords[0] * TCM_CONFIG.coordinateScale,
            coords[1] * TCM_CONFIG.coordinateScale,
            coords[2] * TCM_CONFIG.coordinateScale
        );
        
        // 添加标签
        const label = this._createLabel(name, code);
        label.position.copy(marker.position);
        label.position.x += 0.05;
        this.acupointGroup.add(label);
        
        // 添加到组
        marker.userData = { code, name, meridianName, acupoint };
        this.acupointGroup.add(marker);
        this.acupointMarkers.set(code, marker);
        
        // 创建光晕效果
        this._createGlowEffect(marker);
        
        // 触发回调
        this._emit('onAcupointHighlight', { code, name, coords, meridianName });
        
        // 开始脉冲动画
        this.animationState.isPlaying = true;
    }
    
    /**
     * 创建穴位标签精灵
     */
    _createLabel(name, code) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;
        
        // 绘制背景
        context.fillStyle = 'rgba(0, 0, 0, 0.7)';
        context.roundRect(0, 0, canvas.width, canvas.height, 8);
        context.fill();
        
        // 绘制文字
        context.fillStyle = '#ffffff';
        context.font = 'bold 24px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(name, canvas.width / 2, canvas.height / 2 - 8);
        
        context.font = '16px Arial';
        context.fillStyle = '#aaaaaa';
        context.fillText(code, canvas.width / 2, canvas.height / 2 + 16);
        
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({ 
            map: texture,
            transparent: true 
        });
        
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.scale.set(0.15, 0.04, 1);
        
        return sprite;
    }
    
    /**
     * 创建光晕效果
     */
    _createGlowEffect(marker) {
        // 外层光晕
        const glowGeometry = new THREE.SphereGeometry(
            TCM_CONFIG.acupointHighlight.glowRadius * 2, 32, 32
        );
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: TCM_CONFIG.acupointHighlight.color,
            transparent: true,
            opacity: 0.3,
            side: THREE.BackSide
        });
        
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        marker.add(glow);
    }
    
    /**
     * 添加经络线
     */
    addMeridianLine(meridianName, path) {
        console.log(`[TCM3D] Adding meridian line: ${meridianName}`);
        
        if (this.meridianLines.has(meridianName)) {
            console.log(`[TCM3D] Meridian ${meridianName} already exists`);
            return;
        }
        
        // 转换路径为 Vector3 数组
        const points = path.map(coord => new THREE.Vector3(
            coord[0] * TCM_CONFIG.coordinateScale,
            coord[1] * TCM_CONFIG.coordinateScale,
            coord[2] * TCM_CONFIG.coordinateScale
        ));
        
        // 创建曲线
        const curve = new THREE.CatmullRomCurve3(points);
        const curvePoints = curve.getPoints(100);
        
        // 创建线条几何体
        const geometry = new THREE.BufferGeometry().setFromPoints(curvePoints);
        const material = new THREE.LineBasicMaterial({
            color: TCM_CONFIG.meridianAnimation.color,
            linewidth: 2,
            transparent: true,
            opacity: 0.8
        });
        
        const line = new THREE.Line(geometry, material);
        this.meridianGroup.add(line);
        
        // 创建游走粒子
        const particleGeometry = new THREE.BufferGeometry();
        const particlePositions = new Float32Array(TCM_CONFIG.meridianAnimation.particleCount * 3);
        
        for (let i = 0; i < TCM_CONFIG.meridianAnimation.particleCount; i++) {
            particlePositions[i * 3] = 0;
            particlePositions[i * 3 + 1] = 0;
            particlePositions[i * 3 + 2] = 0;
        }
        
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
        
        const particleMaterial = new THREE.PointsMaterial({
            color: TCM_CONFIG.meridianAnimation.color,
            size: 0.02,
            transparent: true,
            opacity: 0.8
        });
        
        const particles = new THREE.Points(particleGeometry, particleMaterial);
        this.meridianGroup.add(particles);
        
        // 保存数据
        this.meridianLines.set(meridianName, {
            line,
            particles,
            path: points,
            curve,
            isAnimating: true,
            animPhase: 0
        });
        
        // 触发回调
        this._emit('onMeridianAnimate', { meridianName, path });
    }
    
    /**
     * 移除穴位标记
     */
    removeAcupointMarker(code) {
        const marker = this.acupointMarkers.get(code);
        if (marker) {
            this.acupointGroup.remove(marker);
            this.acupointMarkers.delete(code);
        }
    }
    
    /**
     * 清除所有标记
     */
    clearAll() {
        this.acupointMarkers.forEach((marker) => {
            this.acupointGroup.remove(marker);
        });
        this.acupointMarkers.clear();
        
        this.meridianLines.forEach((data) => {
            this.meridianGroup.remove(data.line);
            this.meridianGroup.remove(data.particles);
        });
        this.meridianLines.clear();
        
        this.animationState.isPlaying = false;
    }
    
    /**
     * 聚焦到指定穴位
     */
    focusOnAcupoint(code) {
        const marker = this.acupointMarkers.get(code);
        if (marker) {
            this.controls.target.copy(marker.position);
        }
    }
    
    /**
     * 聚焦到经络
     */
    focusOnMeridian(meridianName) {
        const data = this.meridianLines.get(meridianName);
        if (data && data.path.length > 0) {
            const center = data.path[Math.floor(data.path.length / 2)];
            this.controls.target.copy(center);
        }
    }
    
    /**
     * 导出当前场景为图片
     */
    exportAsImage() {
        this.composer.render();
        return this.renderer.domElement.toDataURL('image/png');
    }
    
    // ==================== 事件系统 ====================
    on(event, callback) {
        if (this.eventCallbacks[event]) {
            this.eventCallbacks[event].push(callback);
        }
    }
    
    off(event, callback) {
        if (this.eventCallbacks[event]) {
            const index = this.eventCallbacks[event].indexOf(callback);
            if (index > -1) {
                this.eventCallbacks[event].splice(index, 1);
            }
        }
    }
    
    _emit(event, data) {
        if (this.eventCallbacks[event]) {
            this.eventCallbacks[event].forEach(cb => cb(data));
        }
    }
    
    // ==================== 销毁 ====================
    dispose() {
        this.clearAll();
        
        if (this.bodyModel) {
            this.bodyGroup.remove(this.bodyModel);
        }
        
        this.renderer.dispose();
        this.controls.dispose();
        
        if (this.renderer.domElement.parentElement) {
            this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
        }
    }
}

// ==================== SSE 连接管理器 ====================
class TCMSSEClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.eventSource = null;
        this.processor = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        this.eventHandlers = {
            thought: [],
            fact_check: [],
            critique: [],
            resource_3d: [],
            verdict: [],
            heartbeat: [],
            complete: [],
            error: []
        };
    }
    
    /**
     * 设置 3D 处理器
     */
    setProcessor(processor) {
        this.processor = processor;
    }
    
    /**
     * 连接 SSE
     */
    connect(requestData) {
        if (this.eventSource) {
            this.disconnect();
        }
        
        const url = `${this.baseUrl}/api/chat/stream`;
        
        console.log('[TCMSSE] Connecting to:', url);
        
        this.eventSource = new EventSource(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        // 注意: 标准 EventSource 不支持 POST
        // 这里需要使用 fetch + ReadableStream 或者封装
        
        // 替代方案: 使用 fetch 进行轮询或使用 WebSocket
        this._connectWithFetch(requestData);
    }
    
    /**
     * 使用 Fetch + ReadableStream 实现 SSE
     */
    async _connectWithFetch(requestData) {
        try {
            const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // 处理缓冲区中的完整事件
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 保留不完整的行
                
                for (const line of lines) {
                    this._processSSEEvent(line);
                }
            }
            
            this.isConnected = false;
            
        } catch (error) {
            console.error('[TCMSSE] Connection error:', error);
            this.isConnected = false;
            this._handleError(error);
            
            // 自动重连
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`[TCMSSE] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                setTimeout(() => this.connect(requestData), this.reconnectDelay);
            }
        }
    }
    
    /**
     * 处理 SSE 事件行
     */
    _processSSEEvent(line) {
        if (!line.trim() || line.startsWith(':')) return; // 跳过注释和空行
        
        // 解析事件类型
        let eventType = 'message';
        let eventData = '';
        
        if (line.startsWith('event:')) {
            eventType = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
            eventData = line.slice(5).trim();
        }
        
        // 解析下一个 data: 行 (如果有)
        // 简化处理: 假设 data 在同一行
        
        if (!eventData) return;
        
        try {
            const data = JSON.parse(eventData);
            
            console.log(`[TCMSSE] Event: ${eventType}`, data);
            
            // 触发处理器
            if (this.processor && eventType === 'resource_3d') {
                this.processor.processResourceData(data);
            }
            
            // 触发事件处理器
            if (this.eventHandlers[eventType]) {
                this.eventHandlers[eventType].forEach(handler => handler(data));
            }
            
            // 通用处理器
            if (this.eventHandlers['message']) {
                this.eventHandlers['message'].forEach(handler => handler(eventType, data));
            }
            
        } catch (e) {
            console.warn('[TCMSSE] Failed to parse event data:', e);
        }
    }
    
    /**
     * 断开连接
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
    }
    
    /**
     * 注册事件处理器
     */
    on(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].push(handler);
        }
    }
    
    /**
     * 移除事件处理器
     */
    off(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }
    
    /**
     * 处理错误
     */
    _handleError(error) {
        if (this.eventHandlers['error']) {
            this.eventHandlers['error'].forEach(handler => handler(error));
        }
    }
}

// ==================== [REJECT] 状态处理 ====================
class TCMRejectStateHandler {
    /**
     * 处理 [REJECT] 状态 - 显示重写加载动画
     */
    static handle(sseClient, uiElements) {
        const { 
            messageContainer, 
            loadingIndicator, 
            critiquePanel,
            rejectOverlay 
        } = uiElements;
        
        // 监听 critique 事件
        sseClient.on('critique', (data) => {
            if (data.verdict === 'REJECT') {
                this._showRejectAnimation(data, uiElements);
            }
        });
        
        // 监听 verdict 事件
        sseClient.on('verdict', (data) => {
            if (data.is_rejected) {
                this._handleRewriteState(data, uiElements);
            }
        });
    }
    
    /**
     * 显示拒绝动画
     */
    static _showRejectAnimation(data, uiElements) {
        const { critiquePanel, rejectOverlay } = uiElements;
        
        // 1. 显示老中医批判面板
        if (critiquePanel) {
            critiquePanel.classList.add('active');
            critiquePanel.innerHTML = `
                <div class="critique-content">
                    <div class="critique-avatar">🧓</div>
                    <div class="critique-text">
                        <div class="verdict-badge reject">REJECT</div>
                        <p class="critique-main">${this._escapeHtml(data.critique_text || '')}</p>
                        ${data.classic_quote ? `<blockquote class="classic-quote">${this._escapeHtml(data.classic_quote)}</blockquote>` : ''}
                        ${data.correct_treatment ? `<div class="correct-treatment">${this._escapeHtml(data.correct_treatment)}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        // 2. 显示"正在重写"遮罩
        if (rejectOverlay) {
            rejectOverlay.classList.add('active');
            rejectOverlay.innerHTML = `
                <div class="rewrite-loader">
                    <div class="rewrite-icon">🔄</div>
                    <div class="rewrite-text">
                        <h3>正在重新组织答案</h3>
                        <p>老中医已驳回原答案，系统正在结合正确知识重新生成...</p>
                    </div>
                    <div class="rewrite-progress">
                        <div class="progress-bar"></div>
                    </div>
                    <div class="rewrite-tips">
                        <span class="tip-label">提示：</span>
                        <span class="tip-text">${this._escapeHtml(data.correct_treatment || '请参考正确的中医辨证论治')}</span>
                    </div>
                </div>
            `;
            
            // 添加进度动画
            const progressBar = rejectOverlay.querySelector('.progress-bar');
            if (progressBar) {
                let progress = 0;
                const interval = setInterval(() => {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90; // 留出等待空间
                    progressBar.style.width = `${progress}%`;
                }, 300);
                
                // 保存 interval 以便后续清除
                rejectOverlay._progressInterval = interval;
            }
        }
        
        // 3. 播放音效 (可选)
        this._playSound('reject');
    }
    
    /**
     * 处理重写状态完成
     */
    static _handleRewriteState(data, uiElements) {
        const { rejectOverlay, messageContainer } = uiElements;
        
        // 完成进度条
        if (rejectOverlay) {
            const progressBar = rejectOverlay.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            
            // 延迟关闭遮罩
            setTimeout(() => {
                rejectOverlay.classList.remove('active');
                if (rejectOverlay._progressInterval) {
                    clearInterval(rejectOverlay._progressInterval);
                }
            }, 1500);
        }
        
        // 添加新消息
        if (messageContainer) {
            const newMessage = document.createElement('div');
            newMessage.className = 'message assistant-message rewrite-complete';
            newMessage.innerHTML = `
                <div class="message-content">
                    <div class="message-avatar">🤖</div>
                    <div class="message-body">
                        <p>${this._escapeHtml(data.summary || '根据老中医的指导，我为您重新整理了答案：')}</p>
                        ${data.syndromes && data.syndromes.length > 0 ? `
                            <div class="syndrome-tags">
                                ${data.syndromes.map(s => `<span class="syndrome-tag">${this._escapeHtml(s)}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${data.recommendations && data.recommendations.length > 0 ? `
                            <div class="recommendations">
                                <strong>调理建议：</strong>
                                <ul>
                                    ${data.recommendations.map(r => `<li>${this._escapeHtml(r)}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
            messageContainer.appendChild(newMessage);
            newMessage.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    /**
     * 播放音效
     */
    static _playSound(type) {
        // 可扩展: 添加音效
        console.log(`[TCMRejHandler] Playing sound: ${type}`);
    }
    
    /**
     * HTML 转义
     */
    static _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ==================== 导出 ====================
export {
    TCM3DResourceProcessor,
    TCMSSEClient,
    TCMRejectStateHandler,
    TCM_CONFIG
};
