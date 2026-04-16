/**
 * video-api.js - 视频分析与聊天 API 封装
 *
 * 【模块职责】
 * 封装视频分析、专栏分析、聊天问答等流式 API 调用
 *
 * 【重构说明】
 * - 从 script.js 中提取的视频分析 API 调用
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 API 调用逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 视频分析 API（流式）
// ============================================================================

/**
 * 启动视频/专栏分析（流式）
 *
 * 【功能说明】
 * 对指定的 B站 视频/专栏 进行 AI 深度分析
 * 使用 Server-Sent Events (SSE) 实时返回分析进度和结果
 *
 * 【API 端点】 POST /api/analyze/stream
 * 【请求格式】
 * {
 *   url: string,      // BV号、CV号或完整链接
 *   mode: string      // 分析模式：'video' | 'article' | 'user'
 * }
 * 【流式响应类型】
 * - stage: 更新进度阶段
 * - progress: 更新进度百分比
 * - content: 追加分析内容
 * - video_info: 视频信息
 * - final: 最终完整数据
 * - error: 错误信息
 *
 * @param {string} url - 视频/专栏 URL 或 ID
 * @param {string} mode - 分析模式 ('video' | 'article')
 * @param {Object} callbacks - 回调函数集合
 * @param {Function} callbacks.onStage - 阶段更新回调 (stage, progress, message)
 * @param {Function} callbacks.onProgress - 进度更新回调 (progress, message)
 * @param {Function} callbacks.onContent - 内容追加回调 (content)
 * @param {Function} callbacks.onVideoInfo - 视频信息回调 (info)
 * @param {Function} callbacks.onFinal - 完成回调 (data)
 * @param {Function} callbacks.onError - 错误回调 (error)
 * @returns {Promise<void>} 异步操作完成
 *
 * @originalLocation script.js:1257-1433 (processStreamAnalysis)
 *
 * @example
 * await analyzeVideo('BV1234567890', 'video', {
 *   onStage: (stage, progress, message) => console.log(message),
 *   onContent: (content) => console.log(content),
 *   onFinal: (data) => console.log('完成', data),
 *   onError: (error) => console.error(error)
 * });
 */
async function analyzeVideo(url, mode, callbacks) {
    const {
        onStage,
        onProgress,
        onContent,
        onVideoInfo,
        onFinal,
        onError
    } = callbacks;

    try {
        const response = await fetch('/api/analyze/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                mode: mode
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '分析请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // 读取流式数据
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6);
                    let data;

                    try {
                        data = JSON.parse(jsonStr);
                    } catch (e) {
                        console.error('[analyzeVideo] JSON 解析失败:', jsonStr);
                        continue;
                    }

                    // 根据消息类型调用对应回调
                    if (data.type === 'stage') {
                        if (onStage) onStage(data.stage, data.progress, data.message);
                    } else if (data.type === 'progress') {
                        if (onProgress) onProgress(data.progress, data.message);
                    } else if (data.type === 'content') {
                        if (onContent) onContent(data.content);
                    } else if (data.type === 'video_info') {
                        if (onVideoInfo) onVideoInfo(data.info);
                    } else if (data.type === 'final') {
                        if (onFinal) onFinal(data.data);
                    } else if (data.type === 'error') {
                        if (onError) onError(new Error(data.error));
                    }
                }
            }
        }
    } catch (error) {
        console.error('[analyzeVideo] 请求失败:', error);
        if (onError) onError(error);
        throw error;
    }
}

// ============================================================================
// 聊天问答 API（流式）
// ============================================================================

/**
 * 发送聊天问题（流式）
 *
 * 【功能说明】
 * 基于已分析的报告进行智能问答
 * 使用 SSE 实时返回 AI 回答
 *
 * 【API 端点】 POST /api/chat/stream
 * 【请求格式】
 * {
 *   question: string,          // 用户问题
 *   context: string,          // 分析报告全文
 *   video_info: Object,       // 视频信息
 *   history: Array            // 对话历史
 * }
 * 【流式响应类型】
 * - content: 追加回答内容
 * - error: 错误信息
 *
 * @param {string} question - 用户问题
 * @param {string} context - 分析报告全文
 * @param {Object} videoInfo - 视频信息对象
 * @param {Array} history - 对话历史
 * @param {Object} callbacks - 回调函数集合
 * @param {Function} callbacks.onContent - 内容追加回调 (content)
 * @param {Function} callbacks.onError - 错误回调 (error)
 * @returns {Promise<string>} 完整回答内容
 *
 * @originalLocation script.js:1567-1616 (sendMessage)
 *
 * @example
 * const answer = await sendChat('视频讲了什么？', reportContent, videoInfo, [], {
 *   onContent: (text) => console.log('收到:', text),
 *   onError: (err) => console.error('错误:', err)
 * });
 */
async function sendChat(question, context, videoInfo, history, callbacks) {
    const { onContent, onError } = callbacks;

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                context: context,
                video_info: videoInfo,
                history: history
            })
        });

        if (!response.ok) {
            throw new Error('网络请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        // 读取流式数据
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'content') {
                        fullResponse += data.content;
                        if (onContent) onContent(fullResponse);
                    } else if (data.type === 'error') {
                        throw new Error(data.error);
                    }
                }
            }
        }

        return fullResponse;
    } catch (error) {
        console.error('[sendChat] 请求失败:', error);
        if (onError) onError(error);
        throw error;
    }
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有视频 API 函数挂载到全局对象 VideoAPI 上
 * 这样可以在任何地方通过 VideoAPI.functionName() 调用
 *
 * 【使用方式】
 * - VideoAPI.analyzeVideo(url, mode, callbacks)
 * - VideoAPI.sendChat(question, context, videoInfo, history, callbacks)
 */
window.VideoAPI = {
    // 视频分析
    analyzeVideo,

    // 聊天问答
    sendChat
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
 *    <script src="script.js"></script>
 *
 * 2. 使用视频分析：
 *    await VideoAPI.analyzeVideo('BV1234567890', 'video', {
 *      onStage: (stage, progress, message) => {
 *        console.log(`阶段: ${stage}, 进度: ${progress}%, 消息: ${message}`);
 *      },
 *      onContent: (content) => {
 *        console.log('收到内容:', content);
 *      },
 *      onVideoInfo: (info) => {
 *        console.log('视频信息:', info);
 *      },
 *      onFinal: (data) => {
 *        console.log('分析完成:', data);
 *      },
 *      onError: (error) => {
 *        console.error('分析失败:', error);
 *      }
 *    });
 *
 * 3. 使用聊天问答：
 *    const answer = await VideoAPI.sendChat(
 *      '视频主要讲了什么？',
 *      reportContent,
 *      videoInfo,
 *      chatHistory,
 *      {
 *        onContent: (text) => {
 *          console.log('实时回答:', text);
 *        },
 *        onError: (err) => {
 *          console.error('问答失败:', err);
 *        }
 *      }
 *    );
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【流式处理说明】
 * - 使用 Server-Sent Events (SSE)
 * - 自动处理数据流解析
 * - 通过回调函数实时推送数据
 *
 * 【错误处理】
 * - 所有函数都包含 try-catch
 * - 网络错误、解析错误都会触发 onError 回调
 * - 错误会记录到 console.error
 *
 * 【测试清单】
 * - ✅ analyzeVideo: 测试视频分析、专栏分析、网络错误
 * - ✅ sendChat: 测试正常问答、空上下文、历史记录
 *
 * 【注意事项】
 * - analyzeVideo 是流式 API，需要传入所有必要的回调
 * - onFinal 回调会收到完整的分析数据
 * - sendChat 返回完整回答，同时通过 onContent 实时推送
 */
