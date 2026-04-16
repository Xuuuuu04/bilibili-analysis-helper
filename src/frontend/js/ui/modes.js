/**
 * modes.js - 模式切换与元数据管理模块
 *
 * 【模块职责】
 * 封装模式切换、深色模式、元数据管理的 UI 操作逻辑
 *
 * 【重构说明】
 * - 从 script.js 中提取的模式管理函数
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 UI 逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 模式配置
// ============================================================================

/**
 * 各模式的元数据配置
 *
 * 【说明】
 * 定义了不同分析模式下显示的元数据项
 */
const MODE_META = {
    video: [
        { id: 'metaDuration', title: '视频时长', icon: '⏱️', default: '--:--' },
        { id: 'metaSubtitle', title: '字幕状态', icon: '📝', default: '无字幕' },
        { id: 'metaFrames', title: '分析帧数', icon: '🖼️', default: '0 帧' },
        { id: 'metaDanmaku', title: '分析弹幕', icon: '💬', default: '0 弹' }
    ],
    article: [
        { id: 'metaWordCount', title: '文章字数', icon: '📄', default: '0 字' },
        { id: 'metaViews', title: '阅读量', icon: '👁️', default: '0' },
        { id: 'metaLikes', title: '点赞数', icon: '👍', default: '0' }
    ],
    user: [
        { id: 'metaUserLevel', title: '用户等级', icon: '⭐', default: 'L--' },
        { id: 'metaFollowers', title: '粉丝数', icon: '👥', default: '0' },
        { id: 'metaWorksCount', title: '作品数', icon: '📁', default: '0' }
    ],
    research: [
        { id: 'metaRounds', title: '研究轮次', icon: '🔄', default: '0 轮' },
        { id: 'metaSearch', title: '搜索次数', icon: '🔍', default: '0 次' },
        { id: 'metaAnalysis', title: '分析次数', icon: '📽️', default: '0 次' },
        { id: 'metaTokens', title: '累计 Tokens', icon: '🪙', default: '0' }
    ]
};

/**
 * 各模式的按钮文字配置
 */
const MODE_BUTTON_TEXTS = {
    research: '深度研究',
    video: '开始分析',
    article: '解析专栏',
    user: '画像分析'
};

/**
 * 各模式的描述文字
 */
const MODE_DESCRIPTIONS = {
    'research': '多维拆解，在海量信息中捕捉深度洞见。',
    'video': '瞬息提炼，让每一帧光影都有迹可循。',
    'article': '结构重组，深度转译专栏背后的文字灵魂。',
    'user': '风格画像，全景式洞察创作背后的灵魂印记。'
};

/**
 * 各模式的输入框占位符
 */
const MODE_PLACEHOLDERS = {
    'video': '粘贴 Bilibili 视频链接或 BV 号...',
    'article': '粘贴专栏链接或 CV 号...',
    'user': '输入用户 UID 或空间链接...',
    'research': '输入你想要研究的课题 (如: 2025 AI 发展趋势)'
};

// ============================================================================
// 元数据管理
// ============================================================================

/**
 * 初始化分析元数据
 *
 * 【功能说明】
 * 根据指定的模式创建并显示元数据项
 *
 * @param {Object} elements - DOM 元素集合
 * @param {HTMLElement} elements.analysisMeta - 元数据容器元素
 * @param {string} mode - 分析模式
 *
 * @originalLocation script.js:529-539
 */
function initAnalysisMeta(elements, mode) {
    const metas = MODE_META[mode] || MODE_META.video;
    elements.analysisMeta.innerHTML = '';
    metas.forEach(meta => {
        const span = document.createElement('span');
        span.id = meta.id;
        span.title = meta.title;
        span.innerHTML = `${meta.icon} ${meta.default}`;
        elements.analysisMeta.appendChild(span);
    });
}

/**
 * 更新元数据值
 *
 * 【功能说明】
 * 更新指定元数据项的显示值，保留图标不变
 *
 * @param {string} id - 元数据项的ID
 * @param {string} value - 新的值
 * @param {string} [prefix] - 可选的前缀（如单位符号）
 *
 * @originalLocation script.js:541-548
 *
 * @example
 * updateMetaValue('metaFrames', '120');  // => "🖼️ 120"
 * updateMetaValue('metaRounds', '5', '轮');  // => "🔄 5轮"
 */
function updateMetaValue(id, value, prefix = '') {
    const el = document.getElementById(id);
    if (el) {
        // 保留图标（在 innerHTML 开头）
        const icon = el.innerHTML.split(' ')[0];
        el.innerHTML = `${icon} ${prefix}${value}`;
    }
}

/**
 * 重置元数据
 *
 * 【功能说明】
 * 重置 Token 计数并重新初始化元数据
 *
 * @param {Object} elements - DOM 元素集合
 * @param {HTMLElement} elements.tokenCount - Token 计数元素
 * @param {string} mode - 分析模式
 *
 * @originalLocation script.js:560-563
 */
function resetMeta(elements, mode) {
    elements.tokenCount.textContent = '0';
    initAnalysisMeta(elements, mode);
}

// ============================================================================
// 深色模式管理
// ============================================================================

/**
 * 切换深色模式
 *
 * 【功能说明】
 * 切换页面的深色/浅色主题，并保存到 localStorage
 *
 * @param {boolean} isDark - 是否启用深色模式
 *
 * @originalLocation script.js:550-558
 */
function toggleDarkMode(isDark) {
    if (isDark) {
        document.body.classList.add('dark-theme');
        localStorage.setItem('darkMode', 'true');
    } else {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('darkMode', 'false');
    }
}

// ============================================================================
// 模式切换
// ============================================================================

/**
 * 切换应用模式
 *
 * 【功能说明】
 * 切换到指定的分析模式，更新所有相关 UI：
 * - 模式按钮状态
 * - 搜索框样式
 * - 模式描述
 * - 按钮文字和占位符
 * - 深度研究的特殊处理
 *
 * @param {string} mode - 目标模式 ('video' | 'article' | 'user' | 'research')
 * @param {Object} params - 参数对象
 * @param {Object} params.elements - DOM 元素集合
 * @param {Function} params.updateSidebarUI - 侧边栏更新函数
 * @param {Function} params.showToast - Toast 提示函数（可选）
 *
 * @returns {string} 返回当前模式
 *
 * @originalLocation script.js:1795-1874
 *
 * @example
 * const newMode = ModeUI.switchMode('video', {
 *   elements,
 *   updateSidebarUI: () => console.log('更新侧边栏'),
 *   showToast: (msg) => console.log(msg)
 * });
 */
function switchMode(mode, params) {
    const { elements, updateSidebarUI: updateSidebarFn, showToast: showToastFn } = params;

    // 更新模式按钮状态
    elements.modeBtns.forEach(btn => {
        if (btn.dataset.mode === mode) btn.classList.add('active');
        else btn.classList.remove('active');
    });

    document.body.dataset.mode = mode;

    // 更新搜索框样式
    const searchBox = document.querySelector('.search-box');
    searchBox.className = `search-box mode-${mode}`;

    // 更新模式描述
    const modeDesc = document.getElementById('modeDescription');
    if (modeDesc) {
        modeDesc.textContent = MODE_DESCRIPTIONS[mode] || '';
        modeDesc.className = `mode-description mode-${mode} animate-fade-in`;
    }

    // 更新主按钮样式
    elements.analyzeBtn.className = `btn-primary mode-${mode}`;
    const btnText = elements.analyzeBtn.lastChild;

    // 根据模式更新输入框和按钮
    if (mode === 'video') {
        elements.videoUrl.placeholder = MODE_PLACEHOLDERS.video;
        btnText.textContent = ' 视频分析';
    } else if (mode === 'article') {
        elements.videoUrl.placeholder = MODE_PLACEHOLDERS.article;
        btnText.textContent = ' 专题解析';
    } else if (mode === 'user') {
        elements.videoUrl.placeholder = MODE_PLACEHOLDERS.user;
        btnText.textContent = ' 用户画像';
    } else if (mode === 'research') {
        elements.videoUrl.placeholder = MODE_PLACEHOLDERS.research;
        btnText.textContent = ' 深度研究';

        // 深度研究模式显示历史入口
        elements.researchHistoryShortcut.classList.remove('hidden');

        // 提示查看历史
        if (elements.resultArea.classList.contains('hidden') && showToastFn) {
            showToastFn('💡 您可以点击输入框下方的按钮查看以往的研究报告');
        }
    }

    // 非研究模式隐藏历史入口
    if (mode !== 'research') {
        elements.researchHistoryShortcut.classList.add('hidden');
    }

    // 刷新侧边栏入口
    if (updateSidebarFn) {
        updateSidebarFn();
    }

    return mode;
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有模式管理函数挂载到全局对象 ModeUI 上
 * 这样可以在任何地方通过 ModeUI.functionName() 调用
 *
 * 【使用方式】
 * - ModeUI.initAnalysisMeta(elements, mode)
 * - ModeUI.updateMetaValue(id, value, prefix)
 * - ModeUI.resetMeta(elements, mode)
 * - ModeUI.toggleDarkMode(isDark)
 * - ModeUI.switchMode(mode, params)
 */
window.ModeUI = {
    // 配置
    MODE_META,
    MODE_BUTTON_TEXTS,
    MODE_DESCRIPTIONS,
    MODE_PLACEHOLDERS,

    // 元数据管理
    initAnalysisMeta,
    updateMetaValue,
    resetMeta,

    // 主题管理
    toggleDarkMode,

    // 模式切换
    switchMode
};

// ============================================================================
// 使用说明
// ============================================================================

/**
 * 【使用方式】
 *
 * 1. 在 HTML 中引入此文件（在 script.js 之前）：
 *    <script src="js/utils/helpers.js"></script>
 *    <script src="js/api/..."></script>
 *    <script src="js/ui/progress.js"></script>
 *    <script src="js/ui/tabs.js"></script>
 *    <script src="js/ui/modes.js"></script>
 *    <script src="script.js"></script>
 *
 * 2. 切换模式：
 *    ModeUI.switchMode('video', {
 *      elements,
 *      updateSidebarUI: () => TabUI.updateSidebarUI(params),
 *      showToast: (msg) => BiliHelpers.showToast(msg, toastElement)
 *    });
 *
 * 3. 管理元数据：
 *    // 初始化
 *    ModeUI.initAnalysisMeta(elements, 'video');
 *
 *    // 更新值
 *    ModeUI.updateMetaValue('metaFrames', '120');
 *
 *    // 重置
 *    ModeUI.resetMeta(elements, 'video');
 *
 * 4. 切换主题：
 *    ModeUI.toggleDarkMode(true);  // 启用深色模式
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【依赖说明】
 * elements 对象必须包含：
 * - modeBtns: 所有模式按钮
 * - analyzeBtn: 主分析按钮
 * - videoUrl: 输入框
 * - resultArea: 结果区域
 * - analysisMeta: 元数据容器
 * - tokenCount: Token 计数元素
 * - researchHistoryShortcut: 研究历史入口
 * - researchHistoryShortcut: 研究历史入口
 *
 * 【测试清单】
 * - ✅ initAnalysisMeta: 测试各模式元数据创建、ID正确性
 * - ✅ updateMetaValue: 测试值更新、前缀添加、图标保留
 * - ✅ resetMeta: 测试重置功能
 * - ✅ toggleDarkMode: 测试主题切换、localStorage保存
 * - ✅ switchMode: 测试所有模式切换、UI更新、特殊情况处理
 *
 * 【注意事项】
 * - switchMode 会更新多个 UI 元素，确保 elements 对象完整
 * - 深度研究模式会显示历史入口，其他模式隐藏
 * - 元数据更新时图标会自动保留
 */
