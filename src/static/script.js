document.addEventListener('DOMContentLoaded', () => {
    const eventSelect = document.getElementById('eventSelect');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const generateBtn = document.getElementById('generateBtn');
    
    const alertPanel = document.getElementById('alertPanel');
    const reportPanel = document.getElementById('reportPanel');
    
    let currentEvents = [];
    let currentAlert = null;

    // Load events
    fetch('/api/events')
        .then(res => res.json())
        .then(events => {
            currentEvents = events;
            eventSelect.innerHTML = '<option value="" disabled selected>Select a network event...</option>';
            events.forEach((evt, idx) => {
                const opt = document.createElement('option');
                opt.value = idx;
                opt.textContent = `Event [Pred: ${evt.predicted_label.toUpperCase()}, True: ${evt.true_label.toUpperCase()}] - ${evt.proto} / ${evt.service} / ${evt.src_bytes} bytes`;
                eventSelect.appendChild(opt);
            });
            eventSelect.addEventListener('change', () => {
                analyzeBtn.disabled = false;
                alertPanel.classList.add('hidden');
                reportPanel.classList.add('hidden');
            });
        });

    // Analyze Threat
    analyzeBtn.addEventListener('click', () => {
        const idx = eventSelect.value;
        if (idx === "") return;
        
        const event = currentEvents[idx];
        setLoading(analyzeBtn, true);
        
        fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event })
        })
        .then(res => res.json())
        .then(alert => {
            currentAlert = alert;
            renderAlert(alert);
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
        
        fetch('/api/generate_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert: currentAlert })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                document.getElementById('reportContent').innerHTML = `<p style="color:var(--danger)">Error: ${data.error}</p>`;
            } else {
                document.getElementById('reportContent').innerHTML = marked.parse(data.report);
            }
            reportPanel.classList.remove('hidden');
        })
        .catch(err => console.error(err))
        .finally(() => setLoading(generateBtn, false));
    });

    function renderAlert(alert) {
        // Basic info
        document.getElementById('threatBadge').textContent = alert.predicted_threat_class.toUpperCase();
        document.getElementById('trueBadge').textContent = alert.true_threat_class.toUpperCase();
        document.getElementById('reportTrueLabel').textContent = alert.true_threat_class.toUpperCase();
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
