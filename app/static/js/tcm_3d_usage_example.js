/**
 * TCM 3D 模块使用示例
 * ======================
 * 演示如何在 HTML 页面中集成 SSE + Three.js 的完整流程
 */

// ==================== 示例1: 基础使用 ====================
async function basicUsageExample() {
    // 1. 初始化 3D 场景
    const processor = new TCM3DResourceProcessor('threejs-container');
    
    // 可选: 加载人体模型
    await processor.loadBodyModel('/models/human_body.glb');
    
    // 2. 连接 SSE
    const sseClient = new TCMSSEClient('http://localhost:8000');
    sseClient.setProcessor(processor);
    
    // 3. 注册事件处理器
    sseClient.on('thought', (data) => {
        updateThinkingIndicator(data);
    });
    
    sseClient.on('fact_check', (data) => {
        showFactCheckResult(data);
    });
    
    sseClient.on('critique', (data) => {
        showCritiquePanel(data);
    });
    
    sseClient.on('resource_3d', (data) => {
        // 3D 资源已由 processor 自动处理
        showResourceInfo(data);
    });
    
    sseClient.on('verdict', (data) => {
        showFinalVerdict(data);
    });
    
    // 4. 发送请求
    sseClient.connect({
        message: '黄连可以治感冒吗？',
        user_id: 'user_001',
        enable_3d: true,
        enable_critique: true
    });
    
    // 5. 断开连接
    // sseClient.disconnect();
}

// ==================== 示例2: 处理 [REJECT] 状态 ====================
async function rejectHandlingExample() {
    const processor = new TCM3DResourceProcessor('threejs-container');
    const sseClient = new TCMSSEClient('http://localhost:8000');
    
    // UI 元素
    const uiElements = {
        messageContainer: document.getElementById('messages'),
        loadingIndicator: document.getElementById('loading'),
        critiquePanel: document.getElementById('critique-panel'),
        rejectOverlay: document.getElementById('reject-overlay')
    };
    
    // 使用拒绝状态处理器
    TCMRejectStateHandler.handle(sseClient, uiElements);
    
    // 连接并发送请求
    sseClient.connect({
        message: '我自己吃点黄连上清丸可以吗？',
        user_id: 'user_001',
        enable_3d: true,
        enable_critique: true
    });
}

// ==================== 示例3: 手动操作 3D 场景 ====================
function manual3DManipulationExample() {
    const processor = new TCM3DResourceProcessor('threejs-container');
    
    // 手动添加穴位
    processor.addAcupointMarker({
        code: 'LI4',
        name: '合谷',
        coords: [0.05, 1.35, 0.03],
        meridianName: '手阳明大肠经'
    });
    
    // 手动添加经络
    processor.addMeridianLine('大肠经', [
        [0.08, 1.62, 0.02],  // LI1 商阳
        [0.05, 1.35, 0.03],  // LI4 合谷
        [0.06, 1.20, 0.02],  // LI10 手三里
        [0.07, 1.08, 0.02],  // LI11 曲池
    ]);
    
    // 聚焦穴位
    processor.focusOnAcupoint('LI4');
    
    // 3秒后清除
    setTimeout(() => {
        processor.clearAll();
    }, 5000);
    
    // 导出图片
    const imageData = processor.exportAsImage();
    console.log('Exported image:', imageData);
}

// ==================== 示例4: 处理 SSE 数据而不使用 Three.js ====================
function sseOnlyExample() {
    const sseClient = new TCMSSEClient('http://localhost:8000');
    
    const eventLog = [];
    
    sseClient.on('thought', (data) => {
        eventLog.push({ type: 'thought', ...data });
        console.log('思考进度:', data.progress, data.thought);
    });
    
    sseClient.on('fact_check', (data) => {
        eventLog.push({ type: 'fact_check', ...data });
        console.log('图谱校验:', data.verdict, '置信度:', data.confidence);
        
        if (data.confidence < 0.7) {
            console.warn('置信度较低，需要老中医审核');
        }
    });
    
    sseClient.on('critique', (data) => {
        eventLog.push({ type: 'critique', ...data });
        
        if (data.verdict === 'REJECT') {
            console.error('老中医拒绝:', data.critique_text);
            showRejectUI(data);
        } else {
            console.log('老中医认可:', data.critique_text);
        }
    });
    
    sseClient.on('resource_3d', (data) => {
        eventLog.push({ type: 'resource_3d', ...data });
        console.log('3D资源:', data.point_name, '坐标:', data.coords);
        
        // 可用于非 Three.js 的其他可视化
        renderAcupointToSVG(data);
    });
    
    sseClient.on('complete', (data) => {
        eventLog.push({ type: 'complete', ...data });
        console.log('对话完成，共处理事件:', eventLog.length);
        
        // 可将完整日志发送给服务器进行调试分析
        sendEventLogToServer(eventLog);
    });
    
    // 发送请求
    sseClient.connect({
        message: document.getElementById('user-input').value,
        user_id: 'anonymous',
        enable_3d: true,
        enable_critique: true
    });
}

// ==================== 示例5: 完整 HTML 页面模板 ====================
/*
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>中医知识问答 - 3D可视化</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        #threejs-container {
            width: 100%;
            height: 60vh;
            border-bottom: 1px solid #333;
        }
        
        #chat-panel {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 12px;
            max-width: 80%;
        }
        
        .user-message {
            background: #4a90e2;
            margin-left: auto;
        }
        
        .assistant-message {
            background: #2d3748;
        }
        
        #critique-panel {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 350px;
            background: rgba(0,0,0,0.9);
            border: 2px solid #ff6600;
            border-radius: 12px;
            padding: 20px;
            display: none;
        }
        
        #critique-panel.active { display: block; }
        
        .reject-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .reject-overlay.active { display: flex; }
        
        .rewrite-loader {
            text-align: center;
            color: #fff;
        }
        
        .progress-bar {
            width: 200px;
            height: 4px;
            background: #333;
            border-radius: 2px;
            margin-top: 20px;
            overflow: hidden;
        }
        
        .progress-bar::after {
            content: '';
            display: block;
            width: 0;
            height: 100%;
            background: #ff6600;
            transition: width 0.3s ease;
        }
        
        #user-input {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 600px;
            padding: 15px 20px;
            border-radius: 25px;
            border: none;
            background: #2d3748;
            color: #fff;
            font-size: 16px;
        }
        
        #user-input:focus {
            outline: none;
            box-shadow: 0 0 0 2px #4a90e2;
        }
    </style>
</head>
<body>
    <div id="threejs-container"></div>
    
    <div id="chat-panel">
        <!-- 消息将在这里显示 -->
    </div>
    
    <div id="critique-panel">
        <!-- 老中医批判内容 -->
    </div>
    
    <div class="reject-overlay" id="reject-overlay">
        <div class="rewrite-loader">
            <div class="rewrite-icon">🔄</div>
            <h3>正在重新组织答案</h3>
            <p>老中医已驳回原答案</p>
            <div class="progress-bar"></div>
        </div>
    </div>
    
    <input type="text" id="user-input" placeholder="输入您的问题..." />
    
    <script type="module">
        import { 
            TCM3DResourceProcessor, 
            TCMSSEClient, 
            TCMRejectStateHandler 
        } from './process_tcm_resource.js';
        
        const processor = new TCM3DResourceProcessor('threejs-container');
        const sseClient = new TCMSSEClient('http://localhost:8000');
        
        // 设置处理器
        sseClient.setProcessor(processor);
        
        // 设置拒绝处理
        TCMRejectStateHandler.handle(sseClient, {
            messageContainer: document.getElementById('chat-panel'),
            critiquePanel: document.getElementById('critique-panel'),
            rejectOverlay: document.getElementById('reject-overlay')
        });
        
        // 监听输入
        document.getElementById('user-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.value.trim()) {
                sseClient.connect({
                    message: e.target.value,
                    user_id: 'user_' + Date.now(),
                    enable_3d: true,
                    enable_critique: true
                });
                e.target.value = '';
            }
        });
    </script>
</body>
</html>
*/

// ==================== 导出示例函数 ====================
export {
    basicUsageExample,
    rejectHandlingExample,
    manual3DManipulationExample,
    sseOnlyExample
};
