(function () {
    const TOOL_LABELS = {
        search_videos: '搜索相关视频',
        web_search: '全网深度搜索',
        analyze_video: '分析视频',
        search_users: '搜索 UP 主',
        get_user_recent_videos: '获取 UP 主作品集',
        finish_research_and_write_report: '撰写深度研究报告'
    };
    const TOOL_ICONS = {
        search_videos: '🔍',
        web_search: '🌐',
        analyze_video: '📽️',
        search_users: '👤',
        get_user_recent_videos: '🗂️',
        finish_research_and_write_report: '✍️'
    };
    const STATUS_LABELS = {
        running: '进行中',
        done: '已完成',
        error: '失败'
    };
    const STATUS_TONES = {
        running: 'accent',
        done: 'success',
        error: 'danger'
    };
    const state = {
        timelineEl: null,
        reportEl: null,
        onReportChange: null,
        autoScroll: true,
        collapseCompleted: false,
        run: {
            topic: '',
            runId: null,
            startedAt: null
        },
        rounds: new Map(),
        currentRound: null,
        toolCards: new Map(),
        thinkingCards: new Map(),
        reportCardKey: null,
        completionCardKey: null,
        reportBuffer: '',
        reportRenderTimer: null,
        reportStarted: false
    };
    function nowTs() {
        return Date.now();
    }
    function toMillis(ts) {
        if (!ts) return nowTs();
        if (typeof ts === 'number') return ts;
        const t = Date.parse(ts);
        return Number.isFinite(t) ? t : nowTs();
    }
    function pad2(n) {
        return String(n).padStart(2, '0');
    }
    function formatClock(ms) {
        const d = new Date(ms);
        return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
    }
    function formatDuration(ms) {
        if (!Number.isFinite(ms) || ms < 0) return '';
        const s = Math.floor(ms / 1000);
        const m = Math.floor(s / 60);
        const r = s % 60;
        if (m <= 0) return `${r}s`;
        return `${m}m${pad2(r)}s`;
    }
    function stableStringify(obj) {
        if (obj === null || obj === undefined) return '';
        if (typeof obj !== 'object') return JSON.stringify(obj);
        if (Array.isArray(obj)) return `[${obj.map(stableStringify).join(',')}]`;
        const keys = Object.keys(obj).sort();
        return `{${keys.map(k => `${JSON.stringify(k)}:${stableStringify(obj[k])}`).join(',')}}`;
    }
    function ensureEl(value, name) {
        if (!value) throw new Error(`DeepResearchUI missing ${name}`);
        return value;
    }
    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = String(text);
        return node;
    }
    function setAutoScroll(enabled) {
        state.autoScroll = !!enabled;
        if (!state.timelineEl) return;
        state.timelineEl.dataset.autoscroll = state.autoScroll ? 'on' : 'off';
        const btn = document.getElementById('drAutoScrollBtn');
        if (btn) {
            btn.dataset.state = state.autoScroll ? 'on' : 'off';
            btn.textContent = state.autoScroll ? '自动滚动：开' : '自动滚动：关';
        }
    }
    function setCollapseCompleted(enabled) {
        state.collapseCompleted = !!enabled;
        if (!state.timelineEl) return;
        state.timelineEl.dataset.collapseCompleted = state.collapseCompleted ? 'on' : 'off';
        const btn = document.getElementById('drCollapseCompletedBtn');
        if (btn) {
            btn.dataset.state = state.collapseCompleted ? 'on' : 'off';
            btn.textContent = state.collapseCompleted ? '折叠已完成：开' : '折叠已完成：关';
        }
    }
    function scrollToBottom() {
        if (!state.autoScroll || !state.timelineEl) return;
        state.timelineEl.scrollTop = state.timelineEl.scrollHeight;
    }
    function resolveToolLabel(tool) {
        return TOOL_LABELS[tool] || tool || '工具调用';
    }
    function resolveToolIcon(tool) {
        return TOOL_ICONS[tool] || '🧩';
    }
    function buildToolKey(tool, args, extra) {
        if (extra && typeof extra === 'string' && extra.length > 0) return `${tool || 'tool'}:${extra}`;
        const argsKey = args ? stableStringify(args) : '';
        return `${tool || 'tool'}:${argsKey}`;
    }
    function ensureRound(roundNumber, tsMs) {
        const round = Number.isFinite(roundNumber) && roundNumber > 0 ? roundNumber : 1;
        const existing = state.rounds.get(round);
        if (existing) {
            state.currentRound = round;
            return existing;
        }
        const wrapper = el('div', 'dr-round');
        wrapper.dataset.round = String(round);
        const header = el('div', 'dr-round-header');
        const title = el('div', 'dr-round-title');
        const left = el('div', 'dr-round-title-left');
        const roundTag = el('span', 'dr-round-badge ui-badge');
        roundTag.textContent = `Round ${round}`;
        left.appendChild(roundTag);
        const startedAt = el('span', 'dr-round-time ui-kbd', formatClock(tsMs));
        left.appendChild(startedAt);
        title.appendChild(left);
        const right = el('div', 'dr-round-title-right');
        const duration = el('span', 'dr-round-duration ui-kbd', '');
        duration.dataset.role = 'duration';
        right.appendChild(duration);
        title.appendChild(right);
        header.appendChild(title);
        const list = el('div', 'dr-round-list');
        wrapper.appendChild(header);
        wrapper.appendChild(list);
        ensureEl(state.timelineEl, 'timelineEl').appendChild(wrapper);
        state.rounds.set(round, { wrapper, header, list, createdAt: tsMs });
        state.currentRound = round;
        scrollToBottom();
        return state.rounds.get(round);
    }
    function updateRoundDurations(tsMs) {
        state.rounds.forEach((value) => {
            const durationEl = value.wrapper.querySelector('[data-role="duration"]');
            if (!durationEl) return;
            durationEl.textContent = value.createdAt ? `耗时 ${formatDuration(tsMs - value.createdAt)}` : '';
        });
    }
    function createCardBase({ titleText, subtitleText, tone, icon, tsMs, collapsible }) {
        const card = el('div', 'dr-card');
        card.dataset.tone = tone || 'default';
        const timeEl = el('div', 'dr-card-time ui-kbd', formatClock(tsMs));
        const header = el('div', 'dr-card-header');
        const titleArea = el('div', 'dr-card-title');
        if (icon) titleArea.appendChild(el('span', 'dr-card-icon', icon));
        const textWrap = el('div', 'dr-card-title-text');
        textWrap.appendChild(el('div', 'dr-card-title-main', titleText || ''));
        if (subtitleText) textWrap.appendChild(el('div', 'dr-card-title-sub', subtitleText));
        titleArea.appendChild(textWrap);
        header.appendChild(titleArea);
        const meta = el('div', 'dr-card-meta');
        const status = el('span', `dr-status ui-badge ${tone === 'success' ? 'dr-status-success' : tone === 'danger' ? 'dr-status-danger' : ''}`);
        status.textContent = STATUS_LABELS[tone] || '';
        status.style.display = 'none';
        meta.appendChild(status);
        if (collapsible) {
            const btn = el('button', 'dr-card-toggle ui-focusable');
            btn.type = 'button';
            btn.textContent = '收起';
            btn.addEventListener('click', () => {
                const collapsed = card.classList.toggle('collapsed');
                btn.textContent = collapsed ? '展开' : '收起';
            });
            meta.appendChild(btn);
        }
        header.appendChild(meta);
        const body = el('div', 'dr-card-body');
        card.appendChild(timeEl);
        card.appendChild(header);
        card.appendChild(body);
        return { card, body, statusEl: status };
    }
    function appendCardToRound(roundNumber, card) {
        const round = ensureRound(roundNumber, toMillis(state.run.startedAt || nowTs()));
        round.list.appendChild(card);
        scrollToBottom();
    }
    function markCardState(card, stateName) {
        card.classList.remove('active', 'completed', 'failed');
        if (stateName === 'active') card.classList.add('active');
        if (stateName === 'completed') card.classList.add('completed');
        if (stateName === 'failed') card.classList.add('failed');
    }
    function renderArgsChips(args) {
        if (!args || typeof args !== 'object') return null;
        const keys = ['keyword', 'query', 'mid', 'bvid'];
        const chips = el('div', 'dr-chips');
        let count = 0;
        keys.forEach((k) => {
            if (args[k] === undefined || args[k] === null || args[k] === '') return;
            const chip = el('span', 'ui-chip accent');
            chip.textContent = `${k}: ${args[k]}`;
            chips.appendChild(chip);
            count += 1;
        });
        if (!count) return null;
        return chips;
    }
    function renderSourcesList(items) {
        const wrap = el('div', 'dr-sources');
        const list = el('div', 'dr-sources-list');
        const max = Math.min(items.length, 8);
        for (let i = 0; i < max; i += 1) {
            const it = items[i];
            const row = el('div', 'dr-source-row');
            const a = el('a', 'dr-source-link');
            a.href = it.url;
            a.target = '_blank';
            a.rel = 'noreferrer';
            a.textContent = it.title || it.url;
            row.appendChild(a);
            const meta = el('div', 'dr-source-meta');
            let hostname = '';
            try {
                hostname = new URL(it.url).hostname;
            } catch (e) {
                hostname = '';
            }
            if (!hostname && typeof it.url === 'string') hostname = it.url.replace(/^https?:\/\//, '').split('/')[0];
            const domain = el('span', 'ui-kbd', hostname || 'source');
            meta.appendChild(domain);
            if (it.published_date) meta.appendChild(el('span', 'ui-kbd', it.published_date));
            row.appendChild(meta);
            list.appendChild(row);
        }
        wrap.appendChild(list);
        if (items.length > max) {
            const more = el('div', 'dr-sources-more');
            more.textContent = `还有 ${items.length - max} 条结果未展示`;
            wrap.appendChild(more);
        }
        return wrap;
    }
    function setToolStatus(statusEl, status, startedAtMs) {
        if (!statusEl) return;
        const label = STATUS_LABELS[status] || '';
        statusEl.textContent = label;
        statusEl.style.display = label ? 'inline-flex' : 'none';
        statusEl.dataset.tone = STATUS_TONES[status] || 'accent';
        if (startedAtMs) statusEl.title = `开始于 ${formatClock(startedAtMs)}`;
    }
    function upsertToolCard({ tool, args, tsMs, roundNumber, toolCallId, extraKey }) {
        const key = toolCallId || buildToolKey(tool, args, extraKey);
        const existing = state.toolCards.get(key);
        if (existing) return existing;
        const icon = resolveToolIcon(tool);
        const title = resolveToolLabel(tool);
        const { card, body, statusEl } = createCardBase({
            titleText: `${icon} ${title}`,
            subtitleText: '',
            tone: 'default',
            icon: '',
            tsMs,
            collapsible: true
        });
        card.classList.add('dr-card--tool');
        markCardState(card, 'active');
        const chips = renderArgsChips(args);
        if (chips) body.appendChild(chips);
        const summary = el('div', 'dr-card-summary');
        summary.dataset.role = 'summary';
        body.appendChild(summary);
        const preview = el('div', 'dr-preview');
        preview.dataset.role = 'preview';
        body.appendChild(preview);
        const raw = el('details', 'dr-raw');
        const rawSummary = el('summary', '', '查看原始数据');
        raw.appendChild(rawSummary);
        const pre = el('pre', 'dr-pre', '');
        raw.appendChild(pre);
        body.appendChild(raw);
        state.toolCards.set(key, { key, tool, args, card, body, statusEl, summaryEl: summary, previewEl: preview, rawPreEl: pre, startedAt: tsMs, round: roundNumber });
        appendCardToRound(roundNumber, card);
        return state.toolCards.get(key);
    }
    function updateToolCardRaw(toolCard, data) {
        if (!toolCard || !toolCard.rawPreEl) return;
        toolCard.rawPreEl.textContent = JSON.stringify(data, null, 2);
    }
    function updateToolCardSummary(toolCard, text) {
        if (!toolCard || !toolCard.summaryEl) return;
        toolCard.summaryEl.textContent = text || '';
    }
    function appendToolCardPreview(toolCard, delta) {
        if (!toolCard || !toolCard.previewEl || !delta) return;
        
        // 保存原始文本以支持累加渲染
        if (!toolCard.rawContent) toolCard.rawContent = '';
        toolCard.rawContent += String(delta);
        
        // 使用 Markdown 渲染
        BiliHelpers.renderMarkdown(toolCard.previewEl, toolCard.rawContent);
        
        toolCard.previewEl.scrollTop = toolCard.previewEl.scrollHeight;
    }
    function upsertThinkingCard({ roundNumber, tsMs }) {
        const key = `thinking:${roundNumber}`;
        const existing = state.thinkingCards.get(key);
        if (existing) return existing;
        const { card, body } = createCardBase({
            titleText: '🧠 思考中',
            subtitleText: '',
            tone: 'default',
            icon: '',
            tsMs,
            collapsible: true
        });
        card.classList.add('dr-card--thinking');
        markCardState(card, 'active');
        const text = el('div', 'dr-thinking');
        text.dataset.role = 'thinking';
        body.appendChild(text);
        state.thinkingCards.set(key, { key, card, body, textEl: text, round: roundNumber, startedAt: tsMs });
        appendCardToRound(roundNumber, card);
        return state.thinkingCards.get(key);
    }
    function appendThinking(roundNumber, tsMs, delta) {
        const card = upsertThinkingCard({ roundNumber, tsMs });
        if (!card || !delta) return;
        card.textEl.textContent += String(delta);
        scrollToBottom();
    }
    function completeThinking(roundNumber) {
        const key = `thinking:${roundNumber}`;
        const card = state.thinkingCards.get(key);
        if (!card) return;
        markCardState(card.card, 'completed');
    }
    function scheduleReportRender() {
        if (state.reportRenderTimer) return;
        state.reportRenderTimer = window.setTimeout(() => {
            state.reportRenderTimer = null;
            if (!state.reportEl) return;
            window.BiliHelpers.renderMarkdown(state.reportEl, state.reportBuffer);
            if (typeof state.onReportChange === 'function') state.onReportChange(state.reportBuffer);
        }, 180);
    }
    function appendReport(tsMs, delta) {
        if (!delta) return;
        state.reportBuffer += String(delta);
        scheduleReportRender();
        updateRoundDurations(tsMs);

        // 更新时间线中的报告卡片状态
        if (state.reportCardKey) {
            const card = state.toolCards.get(state.reportCardKey);
            if (card && card.summaryEl) {
                const count = state.reportBuffer.length;
                card.summaryEl.textContent = `已生成 ${count} 字，报告同步写入“研究报告”面板`;
            }
            if (card && card.previewEl) {
                // 对于报告预览，显示最后一段完整的内容或截断显示
                const previewText = state.reportBuffer.length > 500 ? '...' + state.reportBuffer.slice(-500) : state.reportBuffer;
                BiliHelpers.renderMarkdown(card.previewEl, previewText);
                card.previewEl.scrollTop = card.previewEl.scrollHeight;
            }
        }
    }
    function setReportStarted(tsMs) {
        state.reportStarted = true;
        state.reportBuffer = '';
        if (state.reportEl) state.reportEl.innerHTML = '';
        const roundNumber = state.currentRound || 1;
        const key = `report:${state.run.runId || 'run'}`;
        state.reportCardKey = key;
        const { card, body, statusEl } = createCardBase({
            titleText: '🧾 正在生成研究报告',
            subtitleText: '内容较多时会持续输出，请耐心等待',
            tone: 'default',
            icon: '',
            tsMs,
            collapsible: true
        });
        card.classList.add('dr-card--report');
        markCardState(card, 'active');
        const tips = el('div', 'dr-card-summary', '报告正在生成，同步写入“研究报告”面板');
        body.appendChild(tips);

        const preview = el('div', 'dr-preview markdown-body');
        preview.dataset.role = 'preview';
        body.appendChild(preview);

        setToolStatus(statusEl, 'running', tsMs);
        statusEl.classList.add('dr-status-accent');
        appendCardToRound(roundNumber, card);
        state.toolCards.set(key, { 
            key, tool: 'report', args: null, card, body, statusEl, 
            summaryEl: tips, previewEl: preview, rawPreEl: null, 
            startedAt: tsMs, round: roundNumber 
        });
    }
    function setDone(tsMs) {
        const roundNumber = state.currentRound || 1;
        const key = `done:${state.run.runId || 'run'}`;
        state.completionCardKey = key;
        const { card, body, statusEl } = createCardBase({
            titleText: '✨ 研究完成',
            subtitleText: '已持久化，可在历史记录中查看/下载',
            tone: 'default',
            icon: '',
            tsMs,
            collapsible: false
        });
        card.classList.add('dr-card--system');
        markCardState(card, 'completed');
        setToolStatus(statusEl, 'done', tsMs);
        statusEl.classList.add('dr-status-success');
        const actions = el('div', 'dr-actions');
        const openHistory = el('button', 'btn-mini btn-outline-mini ui-focusable', '查看历史');
        openHistory.type = 'button';
        openHistory.addEventListener('click', () => {
            if (typeof window.showResearchHistory === 'function') window.showResearchHistory();
        });
        actions.appendChild(openHistory);
        body.appendChild(actions);
        appendCardToRound(roundNumber, card);
        state.toolCards.set(key, { key, tool: 'done', args: null, card, body, statusEl, actionsEl: actions, startedAt: tsMs, round: roundNumber });
    }
    function setArtifact(fileId) {
        if (!fileId) return;
        const key = state.completionCardKey;
        if (!key) return;
        const card = state.toolCards.get(key);
        if (!card || !card.actionsEl) return;
        if (card.actionsEl.querySelector('[data-role="artifact"]')) return;
        const wrap = el('div', '');
        wrap.dataset.role = 'artifact';
        const md = el('a', 'btn-mini btn-outline-mini ui-focusable', '下载 MD');
        md.href = `/api/research/download/${encodeURIComponent(fileId)}/md`;
        md.download = `${fileId}.md`;
        const pdf = el('a', 'btn-mini btn-primary-mini ui-focusable', '下载 PDF');
        pdf.href = `/api/research/download/${encodeURIComponent(fileId)}/pdf`;
        pdf.download = `${fileId}.pdf`;
        const openReport = el('button', 'btn-mini btn-outline-mini ui-focusable', '打开报告');
        openReport.type = 'button';
        openReport.addEventListener('click', () => {
            const btn = document.querySelector('.nav-btn[data-tab="research_report"]');
            if (btn) btn.click();
        });
        wrap.appendChild(md);
        wrap.appendChild(pdf);
        wrap.appendChild(openReport);
        card.actionsEl.appendChild(wrap);
    }
    function addError(tsMs, message) {
        const roundNumber = state.currentRound || 1;
        const { card, body, statusEl } = createCardBase({
            titleText: '⛔ 出现错误',
            subtitleText: '',
            tone: 'default',
            icon: '',
            tsMs,
            collapsible: true
        });
        card.classList.add('dr-card--error');
        markCardState(card, 'failed');
        setToolStatus(statusEl, 'error', tsMs);
        statusEl.classList.add('dr-status-danger');
        body.appendChild(el('div', 'dr-error', message || '未知错误'));
        appendCardToRound(roundNumber, card);
    }
    function clear() {
        if (state.reportRenderTimer) {
            window.clearTimeout(state.reportRenderTimer);
            state.reportRenderTimer = null;
        }
        state.rounds.clear();
        state.toolCards.clear();
        state.thinkingCards.clear();
        state.reportCardKey = null;
        state.completionCardKey = null;
        state.reportBuffer = '';
        state.reportStarted = false;
        if (state.timelineEl) state.timelineEl.innerHTML = '';
        if (state.reportEl) {
            state.reportEl.innerHTML = '<div class="empty-state"><p>等待深度研究开始...</p></div>';
        }
    }
    function init(options) {
        state.timelineEl = ensureEl(options.timelineEl, 'timelineEl');
        state.reportEl = ensureEl(options.reportEl, 'reportEl');
        state.onReportChange = options.onReportChange || null;
        const collapseBtn = document.getElementById('drCollapseCompletedBtn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => setCollapseCompleted(!state.collapseCompleted));
        }
        const expandBtn = document.getElementById('drExpandAllBtn');
        if (expandBtn) {
            expandBtn.addEventListener('click', () => {
                if (!state.timelineEl) return;
                state.timelineEl.querySelectorAll('.dr-card.collapsed').forEach((node) => node.classList.remove('collapsed'));
                state.timelineEl.querySelectorAll('.dr-card-toggle').forEach((node) => { node.textContent = '收起'; });
            });
        }
        const autoscrollBtn = document.getElementById('drAutoScrollBtn');
        if (autoscrollBtn) {
            autoscrollBtn.addEventListener('click', () => setAutoScroll(!state.autoScroll));
        }
        const clearBtn = document.getElementById('drClearBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => clear());
        }
        setAutoScroll(true);
        setCollapseCompleted(false);
    }
    function startRun(topic, runId) {
        clear();
        state.run.topic = topic || '';
        state.run.runId = runId || null;
        state.run.startedAt = nowTs();
        if (state.reportEl) state.reportEl.innerHTML = '<div class="empty-state"><p>AI 正在分析并搜集资料...</p></div>';
        const r = ensureRound(1, state.run.startedAt);
        const { card, body } = createCardBase({
            titleText: '🚀 深度研究已启动',
            subtitleText: state.run.topic ? `课题：${state.run.topic}` : '',
            tone: 'default',
            icon: '',
            tsMs: state.run.startedAt,
            collapsible: true
        });
        card.classList.add('dr-card--system');
        markCardState(card, 'active');
        body.appendChild(el('div', 'dr-card-summary', 'Agent 将拆解问题、调用工具搜集资料并生成结构化报告'));
        r.list.appendChild(card);
        scrollToBottom();
    }
    function handleEvent(data) {
        if (!data || typeof data !== 'object') return;
        const tsMs = toMillis(data.ts);
        updateRoundDurations(tsMs);
        const type = data.type;
        if (type === 'round_start') {
            ensureRound(data.round || 1, tsMs);
            return;
        }
        const roundNumber = state.currentRound || 1;
        if (type === 'thinking') {
            appendThinking(roundNumber, tsMs, data.content || '');
            return;
        }
        if (type === 'report_start') {
            setReportStarted(tsMs);
            completeThinking(roundNumber);
            return;
        }
        if (type === 'content') {
            if (state.reportStarted) {
                appendReport(tsMs, data.content || '');
            }
            completeThinking(roundNumber);
            return;
        }
        if (type === 'tool_start') {
            const tool = data.tool;
            const args = data.args || null;
            const toolCallId = data.tool_call_id || null;
            const extraKey = args && args.bvid ? `bvid:${args.bvid}` : null;
            const card = upsertToolCard({ tool, args, tsMs, roundNumber, toolCallId, extraKey });
            setToolStatus(card.statusEl, 'running', tsMs);
            updateToolCardSummary(card, '准备执行...');
            updateToolCardRaw(card, data);
            return;
        }
        if (type === 'tool_progress') {
            const tool = data.tool;
            const toolCallId = data.tool_call_id || null;
            const extraKey = data.bvid ? `bvid:${data.bvid}` : null;
            const card = upsertToolCard({ tool, args: null, tsMs, roundNumber, toolCallId, extraKey });
            setToolStatus(card.statusEl, 'running', card.startedAt);
            if (data.message) updateToolCardSummary(card, data.message);
        if (data.title && tool === 'analyze_video') updateToolCardSummary(card, `正在分析：${data.title}`);
        if (tool === 'analyze_video' && data.content) {
            appendToolCardPreview(card, data.content);
            // 同时更新摘要显示已提取字数
            const currentText = card.previewEl.textContent || '';
            updateToolCardSummary(card, `正在提取视频文案... (已提取 ${currentText.length} 字)`);
        }
            updateToolCardRaw(card, data);
            return;
        }
        if (type === 'tool_result') {
            const tool = data.tool;
            const toolCallId = data.tool_call_id || null;
            const result = data.result;
            const extraKey = result && result.bvid ? `bvid:${result.bvid}` : null;
            const card = upsertToolCard({ tool, args: null, tsMs, roundNumber, toolCallId, extraKey });
            markCardState(card.card, 'completed');
            setToolStatus(card.statusEl, 'done', card.startedAt);
            if (tool === 'web_search' && Array.isArray(result) && result.length && result[0].url) {
                card.body.appendChild(renderSourcesList(result));
                updateToolCardSummary(card, `已返回 ${result.length} 条来源`);
            } else if (tool === 'search_users' && Array.isArray(result) && result.length && result[0].mid) {
                updateToolCardSummary(card, `已找到 ${result.length} 位相关 UP 主`);
            } else if ((tool === 'search_videos' || tool === 'get_user_recent_videos') && Array.isArray(result) && result.length && result[0].bvid) {
                updateToolCardSummary(card, `已获取 ${result.length} 条视频素材`);
            } else if (tool === 'analyze_video' && result && result.bvid) {
                updateToolCardSummary(card, `✅ ${result.title || result.bvid} 分析完成`);
            } else if (tool === 'finish_research_and_write_report') {
                updateToolCardSummary(card, '已进入报告生成阶段');
            } else if (typeof result === 'string') {
                updateToolCardSummary(card, result);
            } else {
                updateToolCardSummary(card, '工具调用完成');
            }
            updateToolCardRaw(card, data);
            return;
        }
        if (type === 'done') {
            setDone(tsMs);
            if (state.reportCardKey) {
                const reportCard = state.toolCards.get(state.reportCardKey);
                if (reportCard) {
                    markCardState(reportCard.card, 'completed');
                    setToolStatus(reportCard.statusEl, 'done', reportCard.startedAt);
                }
            }
            return;
        }
        if (type === 'error') {
            addError(tsMs, data.error || '未知错误');
        }
    }
    window.DeepResearchUI = {
        init,
        startRun,
        handleEvent,
        setArtifact,
        clear
    };
})();
