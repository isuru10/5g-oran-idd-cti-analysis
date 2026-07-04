document.addEventListener('DOMContentLoaded', () => {
    const eventTableBody = document.getElementById('eventTableBody');
    const refreshBtn = document.getElementById('refreshBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const generateBtn = document.getElementById('generateBtn');
    
    const alertPanel = document.getElementById('alertPanel');
    const reportPanel = document.getElementById('reportPanel');
    const tabTldr = document.getElementById('tabTldr');
    const tabDetailed = document.getElementById('tabDetailed');
    
    let currentEvents = [];
    let currentAlert = null;
    let selectedEventIdx = null;
    let cachedReports = { tldr: null, detailed: null };
    let activeStreamController = null;
    let chatHistory = [];

    function resetChat() {
        chatHistory = [];
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="chat-message assistant">
                    Hello! I am your 5G O-RAN CTI Analyst assistant. Ask me anything about this incident, target components, or the contributing SHAP features.
                </div>
            `;
        }
    }

    function loadEvents() {
        setLoading(refreshBtn, true);
        analyzeBtn.disabled = true;
        selectedEventIdx = null;
        if (activeStreamController) activeStreamController.abort();
        cachedReports = { tldr: null, detailed: null };
        resetChat();
        alertPanel.classList.add('hidden');
        reportPanel.classList.add('hidden');
        
        eventTableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Loading network events...</td>
            </tr>
        `;
        
        fetch('/api/events')
            .then(res => res.json())
            .then(events => {
                currentEvents = events;
                eventTableBody.innerHTML = '';
                
                events.forEach((evt, idx) => {
                    const row = document.createElement('tr');
                    row.dataset.idx = idx;
                    
                    const predBadge = `<span class="badge ${evt.predicted_label}">${evt.predicted_label}</span>`;
                    const trueBadge = `<span class="badge ${evt.true_label}">${evt.true_label}</span>`;
                    
                    row.innerHTML = `
                        <td style="text-align: center;"><span class="select-radio"></span></td>
                        <td>${predBadge}</td>
                        <td>${trueBadge}</td>
                        <td><code>${evt.proto}</code></td>
                        <td><code>${evt.service || 'none'}</code></td>
                        <td>${evt.src_bytes.toLocaleString()}</td>
                        <td>${evt.dst_bytes.toLocaleString()}</td>
                    `;
                    
                    row.addEventListener('click', () => {
                        const previouslySelected = eventTableBody.querySelector('tr.selected');
                        if (previouslySelected) {
                            previouslySelected.classList.remove('selected');
                        }
                        
                        row.classList.add('selected');
                        selectedEventIdx = idx;
                        analyzeBtn.disabled = false;
                        
                        alertPanel.classList.add('hidden');
                        reportPanel.classList.add('hidden');
                        if (activeStreamController) activeStreamController.abort();
                        cachedReports = { tldr: null, detailed: null };
                        resetChat();
                    });
                    
                    eventTableBody.appendChild(row);
                });
            })
            .catch(err => {
                console.error(err);
                eventTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; color: var(--danger); padding: 2rem;">Error loading events. Please try again.</td>
                    </tr>
                `;
            })
            .finally(() => setLoading(refreshBtn, false));
    }

    // Initial Load
    loadEvents();

    // Refresh Button Click
    refreshBtn.addEventListener('click', loadEvents);

    // Analyze Threat
    analyzeBtn.addEventListener('click', () => {
        if (selectedEventIdx === null || selectedEventIdx === undefined) return;
        
        const event = { ...currentEvents[selectedEventIdx] };
        const trueLabel = event.true_label;
        delete event.true_label;
        delete event._id;
        
        setLoading(analyzeBtn, true);
        
        fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event })
        })
        .then(res => res.json())
        .then(alert => {
            currentAlert = alert;
            renderAlert(alert, trueLabel);
            alertPanel.classList.remove('hidden');
            reportPanel.classList.add('hidden');
        })
        .catch(err => console.error(err))
        .finally(() => setLoading(analyzeBtn, false));
    });

    async function streamReport(mode) {
        if (!currentAlert) return;
        
        if (activeStreamController) {
            activeStreamController.abort();
        }
        activeStreamController = new AbortController();
        const signal = activeStreamController.signal;
        
        const reportContentDiv = document.getElementById('reportContent');
        reportContentDiv.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Generating ${mode === 'tldr' ? 'executive TLDR' : 'detailed CTI report'} (running local model)...</p>`;
        
        if (mode === 'tldr') {
            setLoading(generateBtn, true);
        } else {
            const tabText = tabDetailed.querySelector('.tab-text');
            const tabLoader = tabDetailed.querySelector('.tab-loader');
            if (tabText && tabLoader) {
                tabText.classList.add('hidden');
                tabLoader.classList.remove('hidden');
            }
        }
        
        try {
            const response = await fetch('/api/generate_report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert: currentAlert, mode: mode }),
                signal: signal
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let receivedText = '';
            
            reportContentDiv.innerHTML = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunkText = decoder.decode(value, { stream: true });
                receivedText += chunkText;
                
                if ((mode === 'tldr' && tabTldr.classList.contains('active')) || 
                    (mode === 'detailed' && tabDetailed.classList.contains('active'))) {
                    reportContentDiv.innerHTML = marked.parse(receivedText);
                }
            }
            
            cachedReports[mode] = receivedText;
            
        } catch (err) {
            if (err.name === 'AbortError') {
                console.log(`Stream generation for ${mode} was aborted.`);
                return;
            }
            console.error(err);
            reportContentDiv.innerHTML = `<p style="color:var(--danger)">Error: ${err.message || err}</p>`;
            if (mode === 'detailed') {
                tabTldr.classList.add('active');
                tabDetailed.classList.remove('active');
                if (cachedReports.tldr) {
                    reportContentDiv.innerHTML = marked.parse(cachedReports.tldr);
                }
            }
        } finally {
            if (mode === 'tldr') {
                setLoading(generateBtn, false);
            } else {
                const tabText = tabDetailed.querySelector('.tab-text');
                const tabLoader = tabDetailed.querySelector('.tab-loader');
                if (tabText && tabLoader) {
                    tabText.classList.remove('hidden');
                    tabLoader.classList.add('hidden');
                }
            }
            activeStreamController = null;
        }
    }

    // Generate Report
    generateBtn.addEventListener('click', () => {
        cachedReports = { tldr: null, detailed: null };
        resetChat();
        tabTldr.classList.add('active');
        tabDetailed.classList.remove('active');
        reportPanel.classList.remove('hidden');
        streamReport('tldr');
    });

    // Tab Listeners
    tabTldr.addEventListener('click', () => {
        if (tabTldr.classList.contains('active')) return;
        
        tabTldr.classList.add('active');
        tabDetailed.classList.remove('active');
        
        if (activeStreamController) {
            activeStreamController.abort();
        }
        
        if (cachedReports.tldr) {
            document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.tldr);
        } else {
            streamReport('tldr');
        }
    });

    tabDetailed.addEventListener('click', () => {
        if (tabDetailed.classList.contains('active')) return;
        
        tabTldr.classList.remove('active');
        tabDetailed.classList.add('active');
        
        if (activeStreamController) {
            activeStreamController.abort();
        }
        
        if (cachedReports.detailed) {
            document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.detailed);
        } else {
            streamReport('detailed');
        }
    });

    function renderAlert(alert, trueLabel) {
        // Basic info
        document.getElementById('threatBadge').textContent = alert.predicted_threat_class.toUpperCase();
        document.getElementById('trueBadge').textContent = trueLabel.toUpperCase();
        document.getElementById('targetComponent').textContent = alert.affected_network_component;
        
        // Confidence bar
        const confPercent = (alert.prediction_confidence * 100).toFixed(2);
        document.getElementById('confValue').textContent = `${confPercent}%`;
        setTimeout(() => {
            document.getElementById('confFill').style.width = `${confPercent}%`;
        }, 100);

        // SHAP evidence
        document.getElementById('evidenceSummary').textContent = alert.shap_evidence.evidence_summary;
        
        const shapBarsContainer = document.getElementById('shapBars');
        shapBarsContainer.innerHTML = '';
        
        // Find max absolute value to scale bars
        const maxShap = Math.max(...alert.shap_evidence.top_features.map(f => Math.abs(f.shap_value)));
        
        alert.shap_evidence.top_features.forEach(f => {
            const width = (Math.abs(f.shap_value) / maxShap) * 100;
            const cls = f.direction === 'positive_contribution' ? 'positive' : 'negative';
            const sign = f.direction === 'positive_contribution' ? '+' : '';
            
            const row = document.createElement('div');
            row.className = 'shap-bar-row';
            row.innerHTML = `
                <div class="feature-name">${f.feature}</div>
                <div class="bar-container">
                    <div class="shap-fill ${cls}" style="width: 0%">
                        ${sign}${f.shap_value.toFixed(4)}
                    </div>
                </div>
            `;
            shapBarsContainer.appendChild(row);
            
            // Animate
            setTimeout(() => {
                row.querySelector('.shap-fill').style.width = `${Math.max(width, 15)}%`;
            }, 100);
        });
        
        // Display JSON structured alert
        document.getElementById('jsonAlertContent').textContent = JSON.stringify(alert, null, 2);
    }

    // Chat functionality
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');

    async function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text || !currentAlert) return;

        // Add user message to UI
        appendChatMessage('user', text);
        chatInput.value = '';

        // Add user message to local history
        chatHistory.push({ role: 'user', content: text });

        // Disable input and send button
        chatInput.disabled = true;
        chatSendBtn.disabled = true;

        // Append assistant loading message bubble with pulsing indicator
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'chat-message assistant';
        assistantBubble.innerHTML = `
            <span class="chat-pulse"></span>
            <span class="chat-pulse"></span>
            <span class="chat-pulse"></span>
        `;
        chatMessages.appendChild(assistantBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert: currentAlert, history: chatHistory })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let receivedText = '';

            // Clear parsing pulse indicator
            assistantBubble.innerHTML = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunkText = decoder.decode(value, { stream: true });
                receivedText += chunkText;

                // Render streaming response as HTML/Markdown
                assistantBubble.innerHTML = marked.parse(receivedText);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Save assistant message to local history
            chatHistory.push({ role: 'assistant', content: receivedText });

        } catch (err) {
            console.error(err);
            assistantBubble.innerHTML = `<span style="color: var(--danger)">Error: ${err.message || err}</span>`;
        } finally {
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    }

    function appendChatMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${role}`;
        msgDiv.textContent = content;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    function setLoading(btn, isLoading) {
        const text = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loader');
        if (isLoading) {
            text.classList.add('hidden');
            loader.classList.remove('hidden');
            btn.disabled = true;
        } else {
            text.classList.remove('hidden');
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    }
});
