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

    function loadEvents() {
        setLoading(refreshBtn, true);
        analyzeBtn.disabled = true;
        selectedEventIdx = null;
        cachedReports = { tldr: null, detailed: null };
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
                        cachedReports = { tldr: null, detailed: null };
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

    // Generate Report
    generateBtn.addEventListener('click', () => {
        if (!currentAlert) return;
        setLoading(generateBtn, true);
        
        cachedReports = { tldr: null, detailed: null };
        
        fetch('/api/generate_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert: currentAlert, mode: 'tldr' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                document.getElementById('reportContent').innerHTML = `<p style="color:var(--danger)">Error: ${data.error}</p>`;
            } else {
                cachedReports.tldr = data.report;
                document.getElementById('reportContent').innerHTML = marked.parse(data.report);
                
                tabTldr.classList.add('active');
                tabDetailed.classList.remove('active');
            }
            reportPanel.classList.remove('hidden');
        })
        .catch(err => console.error(err))
        .finally(() => setLoading(generateBtn, false));
    });

    // Tab Listeners
    tabTldr.addEventListener('click', () => {
        if (!cachedReports.tldr) return;
        tabTldr.classList.add('active');
        tabDetailed.classList.remove('active');
        document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.tldr);
    });

    tabDetailed.addEventListener('click', () => {
        if (tabDetailed.classList.contains('active')) return;
        
        tabTldr.classList.remove('active');
        tabDetailed.classList.add('active');
        
        if (cachedReports.detailed) {
            document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.detailed);
            return;
        }
        
        const tabText = tabDetailed.querySelector('.tab-text');
        const tabLoader = tabDetailed.querySelector('.tab-loader');
        
        tabText.classList.add('hidden');
        tabLoader.classList.remove('hidden');
        document.getElementById('reportContent').innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Generating detailed CTI report (running local model)...</p>`;
        
        fetch('/api/generate_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert: currentAlert, mode: 'detailed' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                document.getElementById('reportContent').innerHTML = `<p style="color:var(--danger)">Error: ${data.error}</p>`;
                tabTldr.classList.add('active');
                tabDetailed.classList.remove('active');
                if (cachedReports.tldr) {
                    document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.tldr);
                }
            } else {
                cachedReports.detailed = data.report;
                if (tabDetailed.classList.contains('active')) {
                    document.getElementById('reportContent').innerHTML = marked.parse(data.report);
                }
            }
        })
        .catch(err => {
            console.error(err);
            document.getElementById('reportContent').innerHTML = `<p style="color:var(--danger)">Failed to generate detailed report.</p>`;
            tabTldr.classList.add('active');
            tabDetailed.classList.remove('active');
            if (cachedReports.tldr) {
                document.getElementById('reportContent').innerHTML = marked.parse(cachedReports.tldr);
            }
        })
        .finally(() => {
            tabText.classList.remove('hidden');
            tabLoader.classList.add('hidden');
        });
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
