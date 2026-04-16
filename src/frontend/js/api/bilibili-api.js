/**
 * bilibili-api.js - B站相关 API 封装
 *
 * 【模块职责】
 * 封装所有与 B站 后端交互的 API 调用
 *
 * 【重构说明】
 * - 从 script.js 中提取的 B站 API 调用
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 API 调用逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 视频相关 API
// ============================================================================

/**
 * 获取热门视频列表
 *
 * 【功能说明】
 * 从后端获取热门/推荐视频数据，用于首页推荐展示
 *
 * 【API 端点】 GET /api/video/popular
 * 【响应格式】
 * {
 *   success: true,
 *   data: [
 *     { bvid, title, cover, author, view, duration_str, ... }
 *   ]
 * }
 *
 * @returns {Promise<Array>} 热门视频列表
 * @throws {Error} 网络错误或 API 错误
 *
 * @originalLocation script.js:368-377 (fetchPopularVideos)
 */
async function getPopularVideos() {
    try {
        const response = await fetch('/api/video/popular');
        const result = await response.json();

        if (result.success) {
            return result.data;
        } else {
            console.error('[getPopularVideos] API 返回失败:', result.error);
            return [];
        }
    } catch (error) {
        console.error('[getPopularVideos] 请求失败:', error);
        return [];
    }
}

// ============================================================================
// 设置管理 API
// ============================================================================

/**
 * 获取系统设置
 *
 * 【功能说明】
 * 从后端获取当前系统的配置信息（API密钥、模型设置等）
 *
 * 【API 端点】 GET /api/settings
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     openai_api_base: string,
 *     openai_api_key: string,
 *     model: string,
 *     qa_model: string,
 *     deep_research_model: string,
 *     exa_api_key: string,
 *     dark_mode: boolean
 *   }
 * }
 *
 * @returns {Promise<Object|null>} 设置对象，失败返回 null
 *
 * @originalLocation script.js:427-452 (fetchSettings)
 */
async function getSettings() {
    try {
        const response = await fetch('/api/settings');
        const result = await response.json();

        if (result.success) {
            return result.data;
        } else {
            console.error('[getSettings] API 返回失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('[getSettings] 请求失败:', error);
        return null;
    }
}

/**
 * 保存系统设置
 *
 * 【功能说明】
 * 将配置保存到后端（会更新 .env 文件）
 *
 * 【API 端点】 POST /api/settings
 * 【请求格式】
 * {
 *   openai_api_base: string,
 *   openai_api_key: string,
 *   model: string,
 *   qa_model: string,
 *   deep_research_model: string,
 *   exa_api_key: string,
 *   dark_mode: boolean
 * }
 *
 * @param {Object} data - 设置数据
 * @returns {Promise<{success: boolean, error?: string}>} 保存结果
 *
 * @originalLocation script.js:470-488 (saveSettings)
 */
async function saveSettings(data) {
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('[saveSettings] 请求失败:', error);
        return { success: false, error: error.message };
    }
}

// ============================================================================
// 登录认证 API
// ============================================================================

/**
 * 启动 B站登录流程
 *
 * 【功能说明】
 * 请求后端生成登录二维码，用于扫码登录
 *
 * 【API 端点】 POST /api/bilibili/login/start
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     qr_code: string,  // 二维码图片URL (base64或链接)
 *     session_id: string // 会话ID，用于轮询
 *   }
 * }
 *
 * @returns {Promise<Object|null>} 登录会话信息 { qr_code, session_id }
 *
 * @originalLocation script.js:1651-1667 (startLogin)
 */
async function loginStart() {
    try {
        const response = await fetch('/api/bilibili/login/start', {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            return result.data;
        } else {
            console.error('[loginStart] API 返回失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('[loginStart] 请求失败:', error);
        return null;
    }
}

/**
 * 轮询登录状态
 *
 * 【功能说明】
 * 查询二维码扫码状态（未扫码/已扫码/已确认/已过期）
 *
 * 【API 端点】 POST /api/bilibili/login/status
 * 【请求格式】 { session_id: string }
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     status: 'success' | 'expired' | 'scanned' | 'waiting',
 *     user_info?: { ... }
 *   }
 * }
 *
 * @param {string} sessionId - 登录会话ID
 * @returns {Promise<Object|null>} 登录状态对象
 *
 * @originalLocation script.js:1672-1695 (pollLoginStatus)
 */
async function loginStatus(sessionId) {
    try {
        const response = await fetch('/api/bilibili/login/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });

        const result = await response.json();

        if (result.success) {
            return result.data;
        } else {
            console.error('[loginStatus] API 返回失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('[loginStatus] 请求失败:', error);
        return null;
    }
}

/**
 * 检查当前登录状态
 *
 * 【功能说明】
 * 检查本地是否已保存有效的 B站 登录凭证
 *
 * 【API 端点】 GET /api/bilibili/login/check
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     is_logged_in: boolean,
 *     name: string,
 *     face: string,
 *     user_id: string
 *   }
 * }
 *
 * @returns {Promise<Object|null>} 用户信息对象，未登录返回 null
 *
 * @originalLocation script.js:1708-1737 (checkLoginState)
 */
async function loginCheck() {
    try {
        const response = await fetch('/api/bilibili/login/check');
        const result = await response.json();

        if (result.success && result.data.is_logged_in) {
            return result.data;
        } else {
            return null;
        }
    } catch (error) {
        console.error('[loginCheck] 请求失败:', error);
        return null;
    }
}

/**
 * 退出登录
 *
 * 【功能说明】
 * 清除本地 B站 登录凭证
 *
 * 【API 端点】 POST /api/bilibili/login/logout
 * 【响应格式】 { success: boolean }
 *
 * @returns {Promise<boolean>} 是否成功退出
 *
 * @originalLocation script.js:1787-1792 (logout)
 */
async function logout() {
    try {
        await fetch('/api/bilibili/login/logout', {
            method: 'POST'
        });
        return true;
    } catch (error) {
        console.error('[logout] 请求失败:', error);
        return false;
    }
}

// ============================================================================
// 用户分析 API
// ============================================================================

/**
 * 获取用户画像分析
 *
 * 【功能说明】
 * 对指定 B站 用户进行深度画像分析
 *
 * 【API 端点】 POST /api/user/portrait
 * 【请求格式】 { uid: string }
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     info: { name, face, follower, level, ... },
 *     portrait: string,  // Markdown 格式的画像报告
 *     recent_videos: [ ... ],
 *     tokens_used: number
 *   }
 * }
 *
 * @param {string} uid - 用户ID或UID
 * @returns {Promise<Object|null>} 用户画像数据
 * @throws {Error} 分析失败时抛出错误
 *
 * @originalLocation script.js:684-714 (startUserAnalysis)
 */
async function getUserPortrait(uid) {
    try {
        const res = await fetch('/api/user/portrait', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid: uid })
        });

        const json = await res.json();

        if (json.success) {
            return json.data;
        } else {
            throw new Error(json.error || '获取用户画像失败');
        }
    } catch (error) {
        console.error('[getUserPortrait] 请求失败:', error);
        throw error;
    }
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有 B站 API 函数挂载到全局对象 BiliAPI 上
 * 这样可以在任何地方通过 BiliAPI.functionName() 调用
 *
 * 【使用方式】
 * - BiliAPI.getPopularVideos()
 * - BiliAPI.getSettings()
 * - BiliAPI.saveSettings(data)
 * - BiliAPI.loginStart()
 * - BiliAPI.getUserPortrait(uid)
 */
window.BiliAPI = {
    // 视频相关
    getPopularVideos,

    // 设置管理
    getSettings,
    saveSettings,

    // 登录认证
    loginStart,
    loginStatus,
    loginCheck,
    logout,

    // 用户分析
    getUserPortrait
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
 *    <script src="script.js"></script>
 *
 * 2. 在任何地方使用：
 *    const videos = await BiliAPI.getPopularVideos();
 *    const settings = await BiliAPI.getSettings();
 *    const userData = await BiliAPI.getUserPortrait('123456789');
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【错误处理】
 * - 所有函数都包含 try-catch
 * - 失败时返回 null 或抛出错误
 * - 错误会记录到 console.error
 *
 * 【测试清单】
 * - ✅ getPopularVideos: 测试正常获取、网络错误
 * - ✅ getSettings: 测试获取配置、空配置
 * - ✅ saveSettings: 测试保存成功、保存失败
 * - ✅ loginStart: 测试生成二维码
 * - ✅ loginStatus: 测试轮询状态
 * - ✅ loginCheck: 测试已登录、未登录
 * - ✅ logout: 测试退出成功
 * - ✅ getUserPortrait: 测试正常分析、UID不存在
 */
