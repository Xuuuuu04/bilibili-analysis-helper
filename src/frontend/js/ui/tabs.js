/**
 * tabs.js - Tab 切换与侧边栏管理模块
 *
 * 【模块职责】
 * 封装 Tab 切换和侧边栏更新的 UI 操作逻辑
 *
 * 【重构说明】
 * - 从 script.js 中提取的 Tab 管理函数
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 UI 逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// Tab 切换管理
// ============================================================================

/**
 * 切换到指定的 Tab
 *
 * 【功能说明】
 * 隐藏所有 Tab 面板，显示目标 Tab 面板，并更新导航按钮状态
 *
 * 【特殊情况处理】
 * - 分析中禁止切换到 chat Tab
 * - 研究模式分析中禁止切换到 research_report Tab
 * - 弹幕 Tab 切换时自动生成词云
 * - 聊天 Tab 切换时自动滚动到底部
 *
 * @param {string} tabName - 目标 Tab 名称
 * @param {Object} params - 参数对象
 * @param {Object} params.elements - DOM 元素集合
 * @param {string} params.currentMode - 当前模式
 * @param {boolean} params.isAnalyzing - 是否正在分析
 * @param {Object} params.currentData - 当前数据对象
 * @param {Function} params.showToast - Toast 提示函数（可选）
 * @param {Function} params.generateWordCloud - 词云生成函数（可选）
 *
 * @originalLocation script.js:1969-2016
 *
 * @example
 * switchTab('summary', {
 *   elements,
 *   currentMode: 'video',
 *   isAnalyzing: false,
 *   currentData,
 *   showToast: (msg) => console.log(msg),
 *   generateWordCloud: (data) => renderWordCloud(data)
 * });
 */
function switchTab(tabName, params) {
    const {
        elements,
        currentMode,
        isAnalyzing,
        currentData,
        showToast,
        generateWordCloud
    } = params;

    // 特殊情况：分析中禁止切换到 chat
    if (isAnalyzing && tabName === 'chat') {
        const msg = '分析尚未结束，请耐心等待 AI 建模完成。在此期间请勿刷新或退出界面。';
        if (showToast) {
            showToast(msg);
        } else {
            console.warn('[switchTab]', msg);
        }
        return;
    }

    // 特殊情况：研究模式分析中禁止切换到报告
    if (isAnalyzing && tabName === 'research_report' && currentMode === 'research') {
        const msg = '研究正在进行中，请在"思考过程"中查看进度，完成后将自动展示报告';
        if (showToast) {
            showToast(msg);
        } else {
            console.warn('[switchTab]', msg);
        }
        return;
    }

    // 更新导航按钮状态
    elements.navBtns.forEach(btn => {
        if (btn.dataset.tab === tabName) btn.classList.add('active');
        else btn.classList.remove('active');
    });

    // 强制移除所有面板的 active 状态，确保互斥
    elements.tabContents.forEach(pane => {
        pane.classList.remove('active');
    });

    // 特别处理：确保聊天面板互斥
    if (elements.chatContent) elements.chatContent.classList.remove('active');

    // 显示目标面板
    if (tabName === 'summary') {
        elements.summaryContent.classList.add('active');
    } else if (tabName === 'danmaku') {
        elements.danmakuContent.classList.add('active');
        // 自动生成词云
        if (currentData.danmakuPreview && currentData.danmakuPreview.length > 0 && generateWordCloud) {
            setTimeout(() => generateWordCloud(currentData.danmakuPreview), 50);
        }
    } else if (tabName === 'comments') {
        elements.commentsContent.classList.add('active');
    } else if (tabName === 'subtitle') {
        elements.subtitleContent.classList.add('active');
    } else if (tabName === 'article_analysis') {
        elements.articleAnalysisContent.classList.add('active');
    } else if (tabName === 'article_content') {
        elements.articleOriginalContent.classList.add('active');
    } else if (tabName === 'user_portrait') {
        elements.userPortraitContentPane.classList.add('active');
    } else if (tabName === 'user_works') {
        elements.userWorksContent.classList.add('active');
    } else if (tabName === 'research_report') {
        elements.researchReportContent.classList.add('active');
    } else if (tabName === 'research_process') {
        elements.researchProcessContent.classList.add('active');
    } else if (tabName === 'chat') {
        elements.chatContent.classList.add('active');
        // 自动滚动到底部
        if (elements.chatMessages) {
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        }
    }
}

// ============================================================================
// 侧边栏管理
// ============================================================================

/**
 * 更新侧边栏 UI
 *
 * 【功能说明】
 * 根据当前模式显示/隐藏相关的导航按钮和侧边栏
 * - 深度研究模式隐藏相关推荐侧边栏
 * - 根据模式自动切换到第一个可用 Tab
 *
 * @param {Object} params - 参数对象
 * @param {Object} params.elements - DOM 元素集合
 * @param {string} params.currentMode - 当前模式
 * @param {Function} params.switchTab - Tab 切换函数
 *
 * @originalLocation script.js:1876-1899
 *
 * @example
 * updateSidebarUI({
 *   elements,
 *   currentMode: 'video',
 *   switchTab: (tabName) => console.log('切换到', tabName)
 * });
 */
function updateSidebarUI(params) {
    const { elements, currentMode, switchTab: switchTabFn } = params;

    const navBtns = elements.sidebarNav.querySelectorAll('.nav-btn, .nav-btn-action');
    let firstVisibleTab = '';

    navBtns.forEach(btn => {
        const showOn = btn.dataset.showOn;
        const showOnModes = showOn ? showOn.split(/\s+/).filter(Boolean) : [];
        if (!showOn || showOnModes.includes(currentMode)) {
            btn.classList.remove('hidden');
            if (!firstVisibleTab && btn.classList.contains('nav-btn')) {
                firstVisibleTab = btn.dataset.tab;
            }
        } else {
            btn.classList.add('hidden');
        }
    });

    // 自动切换到第一个可用的 Tab
    if (firstVisibleTab && switchTabFn) {
        switchTabFn(firstVisibleTab);
    }

    // 特殊处理：深度研究模式隐藏相关推荐侧边栏
    if (currentMode === 'research') {
        elements.relatedSection.classList.add('hidden');
    } else {
        elements.relatedSection.classList.remove('hidden');
    }
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有 Tab 管理函数挂载到全局对象 TabUI 上
 * 这样可以在任何地方通过 TabUI.functionName() 调用
 *
 * 【使用方式】
 * - TabUI.switchTab(tabName, params)
 * - TabUI.updateSidebarUI(params)
 */
window.TabUI = {
    // Tab 切换
    switchTab,

    // 侧边栏管理
    updateSidebarUI
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
 *    <script src="script.js"></script>
 *
 * 2. 切换 Tab：
 *    TabUI.switchTab('summary', {
 *      elements,
 *      currentMode: 'video',
 *      isAnalyzing: false,
 *      currentData,
 *      showToast: (msg) => BiliHelpers.showToast(msg, toastElement),
 *      generateWordCloud: (data) => renderWordCloud(data)
 *    });
 *
 * 3. 更新侧边栏：
 *    TabUI.updateSidebarUI({
 *      elements,
 *      currentMode: 'video',
 *      switchTab: (tabName) => TabUI.switchTab(tabName, params)
 *    });
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【依赖说明】
 * elements 对象必须包含：
 * - navBtns: 所有导航按钮
 * - tabContents: 所有 Tab 内容面板
 * - sidebarNav: 侧边栏导航容器
 * - relatedSection: 相关推荐区域
 * - 各种特定内容区域（summaryContent, danmakuContent 等）
 *
 * 【测试清单】
 * - ✅ switchTab: 测试所有 Tab 切换、互斥显示、边界情况
 * - ✅ updateSidebarUI: 测试各模式按钮显示/隐藏、自动切换
 * - ✅ 特殊情况: 测试分析中禁止切换、自动滚动、词云触发
 *
 * 【注意事项】
 * - switchTab 需要传入完整的状态参数
 * - 切换到 chat 会自动滚动到底部
 * - 切换到 danmaku 会自动触发词云生成（如果提供了函数）
 * - 深度研究模式会隐藏相关推荐侧边栏
 */
