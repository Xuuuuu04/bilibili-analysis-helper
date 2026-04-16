/**
 * research-api.js - 深度研究 API 封装
 *
 * 【模块职责】
 * 封装深度研究（Agent）相关的 API 调用，包括研究任务、历史记录、文件下载等
 *
 * 【重构说明】
 * - 从 script.js 中提取的深度研究 API 调用
 * - 提取日期：2025-12-24
 * - 功能：100% 保持原有 API 调用逻辑不变
 *
 * @author 幽浮喵 (mumu_xsy)
 * @version 1.0.0
 */

// ============================================================================
// 深度研究 API（流式）
// ============================================================================

/**
 * 启动深度研究任务（流式）
 *
 * 【功能说明】
 * 对指定课题进行自动化多轮深度研究
 * 使用 Server-Sent Events (SSE) 实时返回研究进度、工具调用和结果
 *
 * 【API 端点】 POST /api/research
 * 【请求格式】
 * {
 *   topic: string  // 研究课题
 * }
 * 【流式响应类型】
 * - round_start: 新一轮分析开始
 * - tool_start: 工具调用开始
 * - tool_progress: 工具执行进度
 * - tool_result: 工具执行结果
 * - thinking: Agent 思考过程
 * - content: 中间结论/报告内容
 * - report_start: 正式报告开始
 * - final: 最终完成
 * - error: 错误信息
 *
 * @param {string} topic - 研究课题
 * @param {Object} callbacks - 回调函数集合
 * @param {Function} callbacks.onRoundStart - 轮次开始回调 (round)
 * @param {Function} callbacks.onToolStart - 工具开始回调 (tool, args)
 * @param {Function} callbacks.onToolProgress - 工具进度回调 (tool, data)
 * @param {Function} callbacks.onToolResult - 工具结果回调 (tool, result)
 * @param {Function} callbacks.onThinking - 思考过程回调 (content)
 * @param {Function} callbacks.onContent - 内容追加回调 (content)
 * @param {Function} callbacks.onReportStart - 报告开始回调 ()
 * @param {Function} callbacks.onFinal - 完成回调 (data)
 * @param {Function} callbacks.onError - 错误回调 (error)
 * @returns {Promise<void>} 异步操作完成
 *
 * @originalLocation script.js:782-1433 (processResearchStream)
 *
 * @example
 * await startDeepResearch('2025年AI发展趋势', {
 *   onRoundStart: (round) => console.log(`第${round}轮开始`),
 *   onToolStart: (tool, args) => console.log(`调用工具: ${tool}`),
 *   onThinking: (content) => console.log('思考中...', content),
 *   onContent: (content) => console.log('报告内容:', content),
 *   onFinal: (data) => console.log('研究完成', data),
 *   onError: (error) => console.error('错误', error)
 * });
 */
async function startDeepResearch(topic, callbacks, signal = null) {
    const {
        onRoundStart,
        onToolStart,
        onToolProgress,
        onToolResult,
        onThinking,
        onContent,
        onReportStart,
        onFinal,
        onError
    } = callbacks;

    try {
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic }),
            signal: signal
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '深度研究请求失败');
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
                        console.error('[startDeepResearch] JSON 解析失败:', jsonStr);
                        continue;
                    }

                    // 根据消息类型调用对应回调
                    if (data.type === 'round_start') {
                        if (onRoundStart) onRoundStart(data.round);
                    } else if (data.type === 'tool_start') {
                        if (onToolStart) onToolStart(data.tool, data.args);
                    } else if (data.type === 'tool_progress') {
                        if (onToolProgress) onToolProgress(data.tool, data);
                    } else if (data.type === 'tool_result') {
                        if (onToolResult) onToolResult(data.tool, data.result);
                    } else if (data.type === 'thinking') {
                        if (onThinking) onThinking(data.content);
                    } else if (data.type === 'content') {
                        if (onContent) onContent(data.content);
                    } else if (data.type === 'report_start') {
                        if (onReportStart) onReportStart();
                    } else if (data.type === 'final') {
                        if (onFinal) onFinal(data.data);
                    } else if (data.type === 'error') {
                        if (onError) onError(new Error(data.error));
                    }
                }
            }
        }
    } catch (error) {
        console.error('[startDeepResearch] 请求失败:', error);
        if (onError) onError(error);
        throw error;
    }
}

// ============================================================================
// 研究历史 API
// ============================================================================

/**
 * 获取研究历史记录
 *
 * 【功能说明】
 * 获取所有已完成的研究报告列表
 *
 * 【API 端点】 GET /api/research/history
 * 【响应格式】
 * {
 *   success: true,
 *   data: [
 *     {
 *       id: string,
 *       topic: string,
 *       created_at: string,
 *       has_pdf: boolean
 *     },
 *     ...
 *   ]
 * }
 *
 * @returns {Promise<Array>} 研究历史列表，失败返回空数组
 *
 * @originalLocation script.js:2025-2046 (showResearchHistory)
 */
async function getResearchHistory() {
    try {
        const response = await fetch('/api/research/history');
        const data = await response.json();

        if (data.success) {
            return data.data || [];
        } else {
            console.error('[getResearchHistory] API 返回失败:', data.error);
            return [];
        }
    } catch (error) {
        console.error('[getResearchHistory] 请求失败:', error);
        return [];
    }
}

/**
 * 获取历史研究报告内容
 *
 * 【功能说明】
 * 根据文件名加载历史研究报告的完整内容
 *
 * 【API 端点】 GET /api/research/report/:filename
 * 【响应格式】
 * {
 *   success: true,
 *   data: {
 *     filename: string,
 *     content: string  // Markdown 格式的报告内容
 *   }
 * }
 *
 * @param {string} filename - 报告文件名（如：research_20251224_143000.md）
 * @returns {Promise<Object|null>} 报告数据对象，失败返回 null
 *
 * @originalLocation script.js:2057-2092 (loadReport)
 */
async function getResearchReport(filename) {
    try {
        const response = await fetch(`/api/research/report/${filename}`);
        const data = await response.json();

        if (data.success) {
            return data.data;
        } else {
            console.error('[getResearchReport] API 返回失败:', data.error);
            return null;
        }
    } catch (error) {
        console.error('[getResearchReport] 请求失败:', error);
        return null;
    }
}

/**
 * 下载研究报告文件
 *
 * 【功能说明】
 * 下载指定格式的报告文件（PDF 或 Markdown）
 * 会直接触发浏览器下载
 *
 * 【API 端点】 GET /api/research/download/:fileId/:format
 * 【参数】
 * - fileId: 文件ID
 * - format: 'pdf' | 'md'
 *
 * @param {string} fileId - 文件ID
 * @param {string} format - 文件格式 ('pdf' | 'md')
 * @returns {void} 直接触发下载
 *
 * @originalLocation script.js:2049-2051 (downloadFile)
 */
function downloadResearchFile(fileId, format) {
    window.open(`/api/research/download/${fileId}/${format}`);
}

// ============================================================================
// 导出为全局对象（兼容模式）
// ============================================================================

/**
 * 将所有深度研究 API 函数挂载到全局对象 ResearchAPI 上
 * 这样可以在任何地方通过 ResearchAPI.functionName() 调用
 *
 * 【使用方式】
 * - ResearchAPI.startDeepResearch(topic, callbacks)
 * - ResearchAPI.getResearchHistory()
 * - ResearchAPI.getResearchReport(filename)
 * - ResearchAPI.downloadResearchFile(fileId, format)
 */
window.ResearchAPI = {
    // 深度研究
    startDeepResearch,

    // 历史管理
    getResearchHistory,
    getResearchReport,
    downloadResearchFile
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
 *    <script src="script.js"></script>
 *
 * 2. 启动深度研究：
 *    await ResearchAPI.startDeepResearch('2025年AI发展趋势', {
 *      onRoundStart: (round) => {
 *        console.log(`开始第${round}轮分析`);
 *      },
 *      onToolStart: (tool, args) => {
 *        console.log(`执行工具: ${tool}`, args);
 *      },
 *      onToolProgress: (tool, data) => {
 *        console.log(`工具进度: ${tool}`, data);
 *      },
 *      onThinking: (content) => {
 *        console.log('Agent 思考:', content);
 *      },
 *      onContent: (content) => {
 *        console.log('报告内容:', content);
 *      },
 *      onReportStart: () => {
 *        console.log('开始撰写正式报告');
 *      },
 *      onFinal: (data) => {
 *        console.log('研究完成', data);
 *      },
 *      onError: (error) => {
 *        console.error('研究失败', error);
 *      }
 *    });
 *
 * 3. 获取研究历史：
 *    const history = await ResearchAPI.getResearchHistory();
 *    console.log('历史记录:', history);
 *
 * 4. 加载历史报告：
 *    const report = await ResearchAPI.getResearchReport('research_20251224.md');
 *    console.log('报告内容:', report.content);
 *
 * 5. 下载报告文件：
 *    ResearchAPI.downloadResearchFile('research_20251224', 'pdf');
 *    ResearchAPI.downloadResearchFile('research_20251224', 'md');
 *
 * 【兼容性】
 * - 完全向后兼容
 * - 不使用 ES6 模块（使用全局对象）
 * - 可与原有代码共存
 *
 * 【流式处理说明】
 * - 使用 Server-Sent Events (SSE)
 * - 自动处理数据流解析
 * - 通过回调函数实时推送研究进度
 *
 * 【错误处理】
 * - 所有函数都包含 try-catch
 * - 网络错误、解析错误都会触发 onError 回调
 * - 错误会记录到 console.error
 *
 * 【测试清单】
 * - ✅ startDeepResearch: 测试正常研究、网络错误、无效课题
 * - ✅ getResearchHistory: 测试获取历史、空历史
 * - ✅ getResearchReport: 测试加载报告、文件不存在
 * - ✅ downloadResearchFile: 测试下载 PDF、下载 MD
 *
 * 【注意事项】
 * - startDeepResearch 是流式 API，需要传入所有必要的回调
 * - 研究过程可能较长时间，需要 UI 显示进度
 * - 工具调用链（search_videos → analyze_video → web_search）会通过回调依次触发
 * - onReportStart 表示开始撰写最终报告，此前的内容可能是中间分析
 */
