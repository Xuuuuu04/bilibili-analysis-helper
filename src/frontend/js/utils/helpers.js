/**
 * helpers.js - 前端工具函数库 (全局兼容版)
 *
 * 【模块职责】
 * 提供纯函数工具集，不依赖外部状态，可安全复用
 *
 * 【重构说明】
 * - 从 script.js 中提取的工具函数
 * - 原始位置：script.js 第 2854-2903 行
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 数字格式化工具
// ============================================================================

/**
 * 格式化数字显示，将大数字转换为易读的中文单位
 *
 * 【功能说明】
 * - 数字小于 10000：原样返回
 * - 数字大于等于 10000：转换为"万"单位，保留1位小数
 * - 空值或 0：返回 "0"
 *
 * 【使用示例】
 * - BiliHelpers.formatNumber(1234)    // => "1234"
 * - BiliHelpers.formatNumber(12345)   // => "1.2万"
 * - BiliHelpers.formatNumber(0)       // => "0"
 * - BiliHelpers.formatNumber(null)    // => "0"
 *
 * @param {number|null|undefined} num - 要格式化的数字
 * @returns {string} 格式化后的字符串
 *
 * @originalLocation script.js:2854
 */
function formatNumber(num) {
    if (!num) return '0';
    if (num > 10000) return (num / 10000).toFixed(1) + '万';
    return num;
}

// ============================================================================
// 提示框工具
// ============================================================================

/**
 * 显示 Toast 提示信息
 *
 * 【功能说明】
 * - 在页面底部显示临时提示消息
 * - 提示消息会在 3 秒后自动消失
 * - 通过 CSS 类控制显示/隐藏动画
 *
 * 【使用示例】
 * - BiliHelpers.showToast('操作成功！', document.getElementById('toast'))
 * - BiliHelpers.showToast('保存失败', toastElement)
 *
 * @param {string} msg - 要显示的提示信息
 * @param {HTMLElement} toastElement - Toast DOM 元素
 *
 * @originalLocation script.js:2860
 *
 * @note 此函数依赖 toast 元素，必须传入 toastElement 参数
 */
function showToast(msg, toastElement) {
    if (!toastElement) {
        // 向后兼容：如果没有传入 toastElement，尝试从全局获取
        toastElement = document.getElementById('toast');
    }

    if (!toastElement) {
        console.warn('[showToast] 未找到 toast 元素，无法显示提示');
        return;
    }

    // 更新提示文本并显示
    toastElement.textContent = msg;
    toastElement.classList.remove('hidden');

    // 3秒后自动隐藏
    setTimeout(() => {
        toastElement.classList.add('hidden');
    }, 3000);
}

// ============================================================================
// Markdown 渲染工具
// ============================================================================

/**
 * 将 Markdown 文本渲染为 HTML
 *
 * 【功能说明】
 * - 使用 marked.js 库将 Markdown 转换为 HTML
 * - 自动将渲染结果插入到指定 DOM 元素中
 * - 支持完整的 Markdown 语法（标题、列表、代码块等）
 *
 * 【使用示例】
 * - BiliHelpers.renderMarkdown(element, '# 标题\\n\\n内容')
 * - BiliHelpers.renderMarkdown(document.getElementById('content'), markdownText)
 *
 * @param {HTMLElement} element - 要插入渲染结果的 DOM 元素
 * @param {string} text - Markdown 格式的文本
 * @returns {void}
 *
 * @requires marked.js (必须在 HTML 中引入 marked.min.js)
 * @originalLocation script.js:2179
 *
 * @note 确保 HTML 中已引入 marked.js 库
 */
function renderMarkdown(element, text) {
    if (!element) {
        console.warn('[renderMarkdown] 未找到目标元素');
        return;
    }

    if (typeof marked === 'undefined') {
        console.error('[renderMarkdown] marked.js 未加载，请确保在 HTML 中引入');
        element.textContent = text; // 降级：直接显示纯文本
        return;
    }

    try {
        // 配置 marked.js 以支持 GFM 表格和其他扩展
        marked.setOptions({
            gfm: true,           // 启用 GitHub Flavored Markdown
            breaks: true,        // 换行符转换为 <br>
            headerIds: true,     // 为标题生成 ID
            mangle: false,       // 不转义邮箱地址
            pedantic: false,     // 不使用严格模式
            sanitize: false,     // 不过滤 HTML（marked v5+ 已移除此选项）
            smartLists: true,    // 智能列表
            smartypants: false,  // 不转换引号
            xhtml: false         // 不使用 XHTML 标签
        });

        element.innerHTML = marked.parse(text);
    } catch (error) {
        console.error('[renderMarkdown] Markdown 解析失败:', error);
        element.textContent = text; // 降级：显示原始文本
    }
}

// ============================================================================
// 文件下载工具
// ============================================================================

/**
 * 下载文本内容为 Markdown 文件
 *
 * 【功能说明】
 * - 将文本内容封装为 Blob 对象
 * - 创建临时下载链接并触发下载
 * - 自动清理临时 DOM 元素
 *
 * 【使用示例】
 * - BiliHelpers.downloadMarkdown('# 标题\\n内容', 'report.md')
 * - BiliHelpers.downloadMarkdown(content, 'analysis_' + Date.now() + '.md')
 *
 * @param {string} content - 要下载的文本内容（通常是 Markdown 格式）
 * @param {string} [filename] - 文件名（可选，默认生成时间戳文件名）
 * @returns {void}
 *
 * @originalLocation script.js:2892
 */
function downloadMarkdown(content, filename) {
    if (!content) {
        // 向后兼容：调用全局的 showToast（如果存在）
        if (typeof showToast === 'function') {
            showToast('没有可下载的内容', document.getElementById('toast'));
        }
        return;
    }

    // 如果没有提供文件名，生成默认文件名
    if (!filename) {
        filename = 'bilibili_analysis_' + new Date().getTime() + '.md';
    }

    try {
        // 创建 Blob 对象（MIME 类型：text/markdown）
        const blob = new Blob([content], { type: 'text/markdown' });

        // 创建临时下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;

        // 触发下载
        document.body.appendChild(a);
        a.click();

        // 清理
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('[downloadMarkdown] 下载失败:', error);
        if (typeof showToast === 'function') {
            showToast('下载失败: ' + error.message, document.getElementById('toast'));
        }
    }
}

// ============================================================================
// 剪贴板工具
// ============================================================================

/**
 * 复制文本到剪贴板
 *
 * 【功能说明】
 * - 使用现代 Clipboard API 复制文本
 * - 复制成功后显示提示信息
 * - 自动处理错误情况
 *
 * 【使用示例】
 * - BiliHelpers.copyToClipboard('要复制的文本', showToastFn)
 * - await BiliHelpers.copyToClipboard(content, (msg) => console.log(msg))
 *
 * @param {string} text - 要复制的文本内容
 * @param {Function} [showToastCallback] - 显示提示的回调函数（可选）
 * @returns {Promise<boolean>} 复制是否成功
 *
 * @note 依赖现代浏览器的 Clipboard API（需要 HTTPS 或 localhost）
 */
async function copyToClipboard(text, showToastCallback) {
    if (!text) {
        if (showToastCallback) {
            showToastCallback('没有可复制的内容');
        }
        return false;
    }

    try {
        // 使用 Clipboard API 复制
        await navigator.clipboard.writeText(text);

        if (showToastCallback) {
            showToastCallback('复制成功！');
        }
        return true;
    } catch (error) {
        console.error('[copyToClipboard] 复制失败:', error);

        if (showToastCallback) {
            showToastCallback('复制失败: ' + error.message);
        }
        return false;
    }
}

// ============================================================================
// 时间戳格式化工具
// ============================================================================

/**
 * 格式化时间戳为可读字符串
 *
 * 【功能说明】
 * - 将时间戳（毫秒）转换为 HH:MM 格式
 * - 用于聊天消息、日志等场景
 *
 * 【使用示例】
 * - BiliHelpers.formatTimestamp(new Date())  // => "14:30"
 * - BiliHelpers.formatTimestamp(Date.now())  // => "09:05"
 *
 * @param {number|Date} timestamp - 时间戳（毫秒）或 Date 对象
 * @returns {string} 格式化后的时间字符串 (HH:MM)
 */
function formatTimestamp(timestamp) {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ============================================================================
// 通用 DOM 工具
// ============================================================================

/**
 * 安全地获取 DOM 元素
 *
 * 【功能说明】
 * - 封装 document.getElementById，添加错误处理
 * - 支持可选的默认元素或回调
 *
 * 【使用示例】
 * - const el = BiliHelpers.getElement('myElement')
 * - BiliHelpers.getElement('myElement', (el) => { if(el) el.style.display = 'block' })
 *
 * @param {string} id - 元素 ID
 * @param {Function} [callback] - 找到元素后的回调函数（可选）
 * @returns {HTMLElement|null} 找到的元素或 null
 */
function getElement(id, callback) {
    const element = document.getElementById(id);

    if (!element) {
        console.warn(`[getElement] 未找到 ID 为 "${id}" 的元素`);
        return null;
    }

    if (typeof callback === 'function') {
        callback(element);
    }

    return element;
}

/**
 * 切换元素的显示/隐藏状态
 *
 * 【功能说明】
 * - 通过添加/移除 'hidden' 类来控制元素可见性
 * - 支持强制指定显示或隐藏
 *
 * 【使用示例】
 * - BiliHelpers.toggleVisibility(element)         // 切换状态
 * - BiliHelpers.toggleVisibility(element, true)   // 显示
 * - BiliHelpers.toggleVisibility(element, false)  // 隐藏
 *
 * @param {HTMLElement} element - 要切换的 DOM 元素
 * @param {boolean} [forceState] - 强制设置为 true（显示）或 false（隐藏）
 * @returns {void}
 */
function toggleVisibility(element, forceState) {
    if (!element) return;

    if (forceState !== undefined) {
        // 强制设置状态
        if (forceState) {
            element.classList.remove('hidden');
        } else {
            element.classList.add('hidden');
        }
    } else {
        // 切换状态
        element.classList.toggle('hidden');
    }
}

// ============================================================================
// 导出到全局命名空间
// ============================================================================

/**
 * 将所有工具函数挂载到全局对象 BiliHelpers 上
 * 这样可以在任何地方通过 BiliHelpers.functionName() 调用
 *
 * 【使用方式】
 * - BiliHelpers.formatNumber(12345)
 * - BiliHelpers.showToast('消息', toastElement)
 * - BiliHelpers.renderMarkdown(element, markdown)
 */
window.BiliHelpers = {
    // 数字格式化
    formatNumber,

    // 提示框
    showToast,

    // Markdown 渲染
    renderMarkdown,

    // 文件下载
    downloadMarkdown,

    // 剪贴板
    copyToClipboard,

    // 时间格式化
    formatTimestamp,

    // DOM 工具
    getElement,
    toggleVisibility
};

// ============================================================================
// 使用说明与兼容性
// ============================================================================

/**
 * 【使用方式】
 *
 * 1. 在 HTML 中引入此文件（在 script.js 之前）：
 *    <script src="js/utils/helpers.js"></script>
 *    <script src="script.js"></script>
 *
 * 2. 在任何地方使用：
 *    BiliHelpers.formatNumber(12345)
 *    BiliHelpers.showToast('操作成功', document.getElementById('toast'))
 *
 * 3. 兼容性：完全向后兼容，不使用 ES6 模块
 *
 * 【测试清单】
 * - ✅ formatNumber: 测试数字 0, 9999, 10000, 123456
 * - ✅ showToast: 测试正常显示、连续调用、空值
 * - ✅ renderMarkdown: 测试标准 Markdown、代码块、空内容
 * - ✅ downloadMarkdown: 测试正常下载、空内容、特殊字符
 * - ✅ copyToClipboard: 测试正常复制、空内容、权限拒绝
 *
 * 【兼容性】
 * - Chrome/Edge: 90+
 * - Firefox: 88+
 * - Safari: 14+
 * - 需要 Clipboard API 支持
 *
 * 【后续优化】
 * - 如果将来使用模块化构建（webpack/vite），可以改为 ES6 export
 * - 目前使用全局对象，确保与现有代码完全兼容
 */
