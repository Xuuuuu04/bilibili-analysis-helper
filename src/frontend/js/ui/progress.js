/**
 * progress.js - 进度条与步骤条管理模块
 *
 * 【模块职责】
 * 封装所有进度条、步骤条的 UI 操作逻辑
 *
 * 【重构说明】
 * - 从 script.js 中提取的进度管理函数
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 UI 逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 步骤配置
// ============================================================================

/**
 * 不同模式的步骤配置
 *
 * 【说明】
 * 每个模式对应不同的分析步骤，用于显示在步骤条中
 */
const MODE_STEPS = {
    video: [
        { id: 'search', text: '搜索相关视频' },
        { id: 'info', text: '获取视频信息' },
        { id: 'content', text: '拉取文本与互动数据' },
        { id: 'frames', text: '提取视觉关键帧' },
        { id: 'ai', text: 'AI 深度建模分析' }
    ],
    article: [
        { id: 'search', text: '定位目标专栏' },
        { id: 'info', text: '拉取专栏元数据' },
        { id: 'content', text: '提取专栏核心文本' },
        { id: 'ai', text: '逻辑链路深度解析' }
    ],
    user: [
        { id: 'search', text: '搜索匹配用户' },
        { id: 'info', text: '检索用户基本资料' },
        { id: 'content', text: '分析近期作品趋势' },
        { id: 'ai', text: '生成 AI 深度画像' }
    ],
    research: [
        { id: 'ai', text: '深度研究 Agent 运行中' }
    ]
};

// ============================================================================
// 进度条管理
// ============================================================================

/**
 * 重置进度条状态
 *
 * 【功能说明】
 * 将进度条恢复到初始状态，包括：
 * - 进度条归零
 * - 加载文字重置
 * - 流式状态隐藏
 * - chunk 计数器归零
 * - 弹幕词云隐藏
 *
 * @param {Object} elements - DOM 元素集合
 * @param {HTMLElement} elements.progressBar - 进度条元素
 * @param {HTMLElement} elements.loadingText - 加载文字元素
 * @param {HTMLElement} elements.streamingStatus - 流式状态元素
 * @param {HTMLElement} elements.chunkCounter - chunk 计数器元素
 * @param {HTMLElement} elements.danmakuWordCloudContainer - 弹幕词云容器
 *
 * @originalLocation script.js:2145-2151
 */
function resetProgress(elements) {
    elements.progressBar.style.width = '0%';
    elements.loadingText.textContent = '准备就绪...';
    elements.streamingStatus.classList.add('hidden');
    elements.chunkCounter.textContent = '0';
    elements.danmakuWordCloudContainer.classList.add('hidden');
}

/**
 * 更新进度条
 *
 * 【功能说明】
 * 更新进度条的百分比和提示文字
 *
 * @param {Object} elements - DOM 元素集合
 * @param {HTMLElement} elements.progressBar - 进度条元素
 * @param {HTMLElement} elements.loadingText - 加载文字元素
 * @param {number} percent - 进度百分比 (0-100)
 * @param {string} [text] - 可选的提示文字
 *
 * @originalLocation script.js:2153-2156
 *
 * @example
 * updateProgress(elements, 50, '正在分析视频...');
 */
function updateProgress(elements, percent, text) {
    elements.progressBar.style.width = percent + '%';
    if (text) elements.loadingText.textContent = text;
}

// ============================================================================
// 步骤条管理
// ============================================================================

/**
 * 初始化步骤条
 *
 * 【功能说明】
 * 根据指定的模式创建并渲染步骤条
 *
 * @param {Object} elements - DOM 元素集合
 * @param {HTMLElement} elements.loadingStepper - 步骤条容器元素
 * @param {string} mode - 分析模式 ('video' | 'article' | 'user' | 'research')
 *
 * @originalLocation script.js:2130-2143
 *
 * @example
 * initStepper(elements, 'video');  // 创建视频分析的5个步骤
 */
function initStepper(elements, mode) {
    const steps = MODE_STEPS[mode] || MODE_STEPS.video;
    elements.loadingStepper.innerHTML = '';

    steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step';
        stepDiv.id = `step-${step.id}`;
        stepDiv.innerHTML = `
            <div class="step-icon">${index + 1}</div>
            <div class="step-text">${step.text}</div>
        `;
        elements.loadingStepper.appendChild(stepDiv);
    });
}

/**
 * 更新步骤条状态
 *
 * 【功能说明】
 * 设置指定步骤的状态（激活或完成）
 *
 * @param {string} stepId - 步骤ID（如 'search', 'info', 'ai' 等）
 * @param {string} status - 状态类型
 *   - 'active': 激活状态（当前正在执行的步骤）
 *   - 'completed': 完成状态（已完成的步骤）
 *
 * @originalLocation script.js:2158-2171
 *
 * @example
 * updateStepper('info', 'active');      // 激活"获取视频信息"步骤
 * updateStepper('search', 'completed'); // 标记"搜索"步骤为完成
 */
function updateStepper(stepId, status) {
    const step = document.getElementById(`step-${stepId}`);
    if (!step) return;

    if (status === 'active') {
        // 移除其他步骤的激活状态
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        step.classList.add('active');
        step.classList.remove('completed');
    } else if (status === 'completed') {
        step.classList.add('completed');
        step.classList.remove('active');
    }
}

/**
 * 重置步骤条
 *
 * 【功能说明】
 * 清除所有步骤的状态，恢复到初始状态
 *
 * @originalLocation script.js:2173-2177
 *
 * @example
 * resetStepper();  // 重置所有步骤
 */
function resetStepper() {
    document.querySelectorAll('.step').forEach(s => {
        s.className = 'step';
    });
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有进度管理函数挂载到全局对象 ProgressUI 上
 * 这样可以在任何地方通过 ProgressUI.functionName() 调用
 *
 * 【使用方式】
 * - ProgressUI.resetProgress(elements)
 * - ProgressUI.updateProgress(elements, 50, '正在分析...')
 * - ProgressUI.initStepper(elements, 'video')
 * - ProgressUI.updateStepper('info', 'active')
 * - ProgressUI.resetStepper()
 */
window.ProgressUI = {
    // 配置
    MODE_STEPS,

    // 进度条管理
    resetProgress,
    updateProgress,

    // 步骤条管理
    initStepper,
    updateStepper,
    resetStepper
};

// ============================================================================
// 使用说明
// ============================================================================

/**
 * 【使用方式】
 *
 * 1. 在 HTML 中引入此文件（在 script.js 之前）：
 *    <script src="js/utils/helpers.js"></script>
 *    <script src="js/api/bilibili-api.js"></script>
 *    <script src="js/api/video-api.js"></script>
 *    <script src="js/api/research-api.js"></script>
 *    <script src="js/ui/progress.js"></script>
 *    <script src="script.js"></script>
 *
 * 2. 使用进度条：
 *    // 重置进度
 *    ProgressUI.resetProgress(elements);
 *
 *    // 更新进度
 *    ProgressUI.updateProgress(elements, 50, '正在分析视频...');
 *
 * 3. 使用步骤条：
 *    // 初始化步骤条（视频模式）
 *    ProgressUI.initStepper(elements, 'video');
 *
 *    // 激活某个步骤
 *    ProgressUI.updateStepper('info', 'active');
 *
 *    // 标记步骤完成
 *    ProgressUI.updateStepper('search', 'completed');
 *
 *    // 重置所有步骤
 *    ProgressUI.resetStepper();
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【依赖说明】
 * - 需要传入正确的 elements 对象
 * - elements 对象必须包含以下属性：
 *   - progressBar
 *   - loadingText
 *   - loadingStepper
 *   - streamingStatus
 *   - chunkCounter
 *   - danmakuWordCloudContainer
 *
 * 【测试清单】
 * - ✅ resetProgress: 测试进度条归零、文字重置、状态隐藏
 * - ✅ updateProgress: 测试进度更新、文字更新、边界值
 * - ✅ initStepper: 测试各模式步骤创建、步骤顺序
 * - ✅ updateStepper: 测试激活状态、完成状态、无效ID
 * - ✅ resetStepper: 测试重置所有步骤状态
 *
 * 【注意事项】
 * - 进度条操作需要传入完整的 elements 对象
 * - 步骤条操作直接操作 DOM，不需要 elements 对象
 * - updateStepper 的 stepId 必须与 MODE_STEPS 中定义的 ID 一致
 */
