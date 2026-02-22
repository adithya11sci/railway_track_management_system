/**
 * Train Management System — Multi-Train Dashboard
 * Manages multiple trains, SVG track diagram, per-train drill-down.
 */

const API = '';

// ══════════════════════════════════════════════════════════════════
//  TRAIN MANAGER — holds all scheduled trains & results
// ══════════════════════════════════════════════════════════════════

const TrainManager = {
    trains: {},       // train_id -> { config, result, status }
    activeDetail: null,

    add(config, result) {
        this.trains[config.train_id] = {
            config,
            result,
            status: result.disaster_triggered ? 'disaster' :
                (result.results?.monitoring?.status === 'Delayed' ? 'delayed' : 'on-time'),
            trainType: config.train_type || 'Express',
        };
    },

    get(id) { return this.trains[id]; },
    getAll() { return Object.values(this.trains); },
    count() { return Object.keys(this.trains).length; },
};

// ══════════════════════════════════════════════════════════════════
//  TRAIN TYPE CONFIG
// ══════════════════════════════════════════════════════════════════

const TRAIN_TYPES = [
    { value: 'Superfast', label: '⚡ Superfast', color: '#8b5cf6' },
    { value: 'Express', label: '🚂 Express', color: '#3b82f6' },
    { value: 'Passenger', label: '🚃 Passenger', color: '#10b981' },
    { value: 'Freight', label: '📦 Freight', color: '#f59e0b' },
];

const STATIONS = [
    'Bangalore', 'New Delhi', 'Mumbai', 'Chennai', 'Kolkata',
    'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow',
    'Bhopal', 'Nagpur', 'Visakhapatnam', 'Yesvantpur', 'Secunderabad'
];

// ══════════════════════════════════════════════════════════════════
//  WIZARD — Dynamic Train Rows
// ══════════════════════════════════════════════════════════════════

let trainRowCounter = 0;

function addTrainRow(preset) {
    trainRowCounter++;
    const id = trainRowCounter;
    const p = preset || {
        trainId: `${10000 + Math.floor(Math.random() * 90000)}`,
        source: 'Bangalore',
        destination: 'New Delhi',
        trainType: 'Express',
        departureTime: '08:00',
        speed: 80,
        distance: 500,
        stops: 4,
        weather: 'clear',
        congestion: 'low',
        currentSpeed: 75,
        remainingDist: 10,
    };

    const row = document.createElement('div');
    row.className = 'train-row';
    row.id = `train-row-${id}`;
    row.innerHTML = `
        <div class="train-row-header">
            <span class="train-row-number">#${id}</span>
            <button class="btn-remove-row" onclick="removeTrainRow(${id})" title="Remove">✕</button>
        </div>
        <div class="train-row-fields">
            <div class="field">
                <label>Train ID</label>
                <input type="text" data-field="trainId" value="${p.trainId}">
            </div>
            <div class="field">
                <label>Source</label>
                <select data-field="source">
                    ${STATIONS.map(s => `<option value="${s}" ${s === p.source ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </div>
            <div class="field">
                <label>Destination</label>
                <select data-field="destination">
                    ${STATIONS.map(s => `<option value="${s}" ${s === p.destination ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </div>
            <div class="field">
                <label>Type</label>
                <select data-field="trainType">
                    ${TRAIN_TYPES.map(t => `<option value="${t.value}" ${t.value === p.trainType ? 'selected' : ''}>${t.label}</option>`).join('')}
                </select>
            </div>
            <div class="field">
                <label>Depart</label>
                <input type="text" data-field="departureTime" value="${p.departureTime}">
            </div>
            <div class="field">
                <label>Speed km/h</label>
                <input type="number" data-field="speed" value="${p.speed}">
            </div>
            <div class="field">
                <label>Dist km</label>
                <input type="number" data-field="distance" value="${p.distance}">
            </div>
            <div class="field">
                <label>Stops</label>
                <input type="number" data-field="stops" value="${p.stops}">
            </div>
            <div class="field">
                <label>Weather</label>
                <select data-field="weather">
                    <option value="clear" ${p.weather === 'clear' ? 'selected' : ''}>☀️ Clear</option>
                    <option value="rain" ${p.weather === 'rain' ? 'selected' : ''}>🌧️ Rain</option>
                    <option value="heavy_rain" ${p.weather === 'heavy_rain' ? 'selected' : ''}>⛈️ Heavy Rain</option>
                    <option value="fog" ${p.weather === 'fog' ? 'selected' : ''}>🌫️ Fog</option>
                    <option value="storm" ${p.weather === 'storm' ? 'selected' : ''}>🌪️ Storm</option>
                </select>
            </div>
            <div class="field">
                <label>Congestion</label>
                <select data-field="congestion">
                    <option value="low" ${p.congestion === 'low' ? 'selected' : ''}>🟢 Low</option>
                    <option value="moderate" ${p.congestion === 'moderate' ? 'selected' : ''}>🟡 Moderate</option>
                    <option value="high" ${p.congestion === 'high' ? 'selected' : ''}>🔴 High</option>
                    <option value="very_high" ${p.congestion === 'very_high' ? 'selected' : ''}>⛔ Very High</option>
                </select>
            </div>
            <div class="field">
                <label>Cur. Speed</label>
                <input type="number" data-field="currentSpeed" value="${p.currentSpeed}">
            </div>
            <div class="field">
                <label>Remain km</label>
                <input type="number" data-field="remainingDist" value="${p.remainingDist}">
            </div>
        </div>
    `;
    document.getElementById('trainRows').appendChild(row);
}
window.addTrainRow = addTrainRow;

function removeTrainRow(id) {
    const row = document.getElementById(`train-row-${id}`);
    if (row) row.remove();
}
window.removeTrainRow = removeTrainRow;

function getTrainRowData() {
    const rows = document.querySelectorAll('.train-row');
    const trains = [];
    rows.forEach(row => {
        const get = (f) => row.querySelector(`[data-field="${f}"]`)?.value || '';
        trains.push({
            train_id: get('trainId'),
            source: get('source'),
            destination: get('destination'),
            train_type: get('trainType'),
            departure_time: get('departureTime'),
            speed_kmh: parseFloat(get('speed')) || 80,
            distance_km: parseFloat(get('distance')) || 500,
            stops: parseInt(get('stops')) || 4,
            weather: get('weather'),
            congestion: get('congestion'),
            current_speed_kmh: parseFloat(get('currentSpeed')) || 75,
            remaining_distance_km: parseFloat(get('remainingDist')) || 10,
        });
    });
    return trains;
}

// ══════════════════════════════════════════════════════════════════
//  RUN ALL TRAINS
// ══════════════════════════════════════════════════════════════════

async function runAllTrains() {
    const trainData = getTrainRowData();
    if (trainData.length === 0) {
        alert('Add at least one train first!');
        return;
    }

    const btn = document.getElementById('btnRunAll');
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loading').style.display = 'inline';
    btn.disabled = true;

    try {
        const res = await fetch(`${API}/api/train/batch-flow`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trains: trainData }),
        });
        const data = await res.json();

        if (!data.success) {
            alert('Error: ' + (data.error || 'Unknown error'));
            return;
        }

        const results = data.data.trains;
        const pendingApprovals = data.data.pending_approvals || [];

        for (const [trainId, result] of Object.entries(results)) {
            const config = trainData.find(t => t.train_id === trainId) || {};
            TrainManager.add(config, result);
        }

        // Update badge
        document.getElementById('trainCountBadge').textContent = `${TrainManager.count()} Trains`;

        // Show results sections
        document.getElementById('trackSection').style.display = 'block';
        document.getElementById('trainsTableSection').style.display = 'block';

        renderTrainsGrid();
        renderTrackDiagram();

        // Check for disaster trains needing approval
        if (pendingApprovals.length > 0) {
            // Queue approval modals for each disaster train
            for (const trainId of pendingApprovals) {
                const train = TrainManager.get(trainId);
                if (train) {
                    const dr = train.result.results?.disaster_recovery || {};
                    await showApprovalModal(trainId, dr, train.config);
                }
            }
        }

    } catch (err) {
        alert('Connection error: ' + err.message);
    } finally {
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loading').style.display = 'none';
        btn.disabled = false;
    }
}
window.runAllTrains = runAllTrains;

// ══════════════════════════════════════════════════════════════════
//  DISASTER APPROVAL MODAL
// ══════════════════════════════════════════════════════════════════

let approvalState = {
    trainId: null,
    selectedOption: null,
    timer: null,
    remaining: 60,
    resolve: null,
};

const APPROVAL_TIMEOUT = 60; // seconds

function showApprovalModal(trainId, disasterData, config) {
    return new Promise((resolve) => {
        approvalState = {
            trainId,
            selectedOption: null,
            timer: null,
            remaining: APPROVAL_TIMEOUT,
            resolve,
        };

        const rc = disasterData.root_cause || {};
        const options = disasterData.options_presented || [];
        const recommended = disasterData.recommended_option;

        // Subtitle
        document.getElementById('approvalSubtitle').textContent =
            `Train ${trainId} — ${(rc.failure_type || 'unknown').replace(/_/g, ' ')} at ${rc.location || 'unknown location'}`;

        // Incident info
        document.getElementById('approvalIncident').innerHTML = `
            <div class="incident-grid">
                <div class="incident-item">
                    <span class="incident-label">Train</span>
                    <span class="incident-value">${trainId}</span>
                </div>
                <div class="incident-item">
                    <span class="incident-label">Failure</span>
                    <span class="incident-value danger">${(rc.failure_type || '—').replace(/_/g, ' ').toUpperCase()}</span>
                </div>
                <div class="incident-item">
                    <span class="incident-label">Severity</span>
                    <span class="incident-value danger">${(rc.severity || '—').toUpperCase()}</span>
                </div>
                <div class="incident-item">
                    <span class="incident-label">Location</span>
                    <span class="incident-value">${rc.location || '—'}</span>
                </div>
            </div>
        `;

        // Options
        const optionsHtml = options.map(opt => {
            const isRec = opt.option_id === recommended;
            const impact = opt.impact_analysis || {};
            const sc = opt.new_schedule || {};
            const scoreClass = opt.recommendation_score >= 7 ? 'score-high' : opt.recommendation_score >= 5 ? 'score-mid' : 'score-low';

            return `
            <div class="approval-option ${isRec ? 'recommended' : ''}" data-option-id="${opt.option_id}" onclick="selectApprovalOption(${opt.option_id})">
                ${isRec ? '<span class="rec-badge">★ RECOMMENDED</span>' : ''}
                <div class="option-top">
                    <span class="option-name">${opt.option_name || 'Option ' + opt.option_id}</span>
                    <span class="option-score ${scoreClass}">${opt.recommendation_score}/10</span>
                </div>
                <div class="option-stats">
                    <div class="opt-stat">
                        <span class="opt-label">Delay Added</span>
                        <span class="opt-value">+${sc.delay_added_minutes || 0}m</span>
                    </div>
                    <div class="opt-stat">
                        <span class="opt-label">Trains Disturbed</span>
                        <span class="opt-value ${(impact.trains_disturbed || 0) > 0 ? 'val-warning' : ''}">${impact.trains_disturbed || 0}</span>
                    </div>
                    <div class="opt-stat">
                        <span class="opt-label">Passengers</span>
                        <span class="opt-value">~${impact.total_passengers_affected || 0}</span>
                    </div>
                    <div class="opt-stat">
                        <span class="opt-label">Safety</span>
                        <span class="opt-value">${(opt.safety_score || '—').toUpperCase()}</span>
                    </div>
                </div>
                <div class="option-proscons">
                    ${(opt.pros || []).map(p => `<span class="pro-tag">✅ ${p}</span>`).join('')}
                    ${(opt.cons || []).map(c => `<span class="con-tag">❌ ${c}</span>`).join('')}
                </div>
                ${impact.affected_trains ? `
                <div class="affected-list">
                    <span class="opt-label">Affected Trains:</span>
                    ${impact.affected_trains.map(at => `<span class="affected-chip">${at.train_id} (+${at.delay_minutes}m)</span>`).join('')}
                </div>` : ''}
            </div>`;
        }).join('');

        document.getElementById('approvalOptions').innerHTML = optionsHtml;

        // Safety notes
        document.getElementById('approvalSafety').textContent =
            '🛡️ ' + (disasterData.safety_notes || 'All options verified for safety.');

        // Reset approve button
        document.getElementById('btnApprove').disabled = true;

        // Show modal
        document.getElementById('approvalOverlay').style.display = 'flex';

        // Start countdown
        startCountdown(trainId, recommended);
    });
}

function selectApprovalOption(optionId) {
    approvalState.selectedOption = optionId;

    // Update UI
    document.querySelectorAll('.approval-option').forEach(el => {
        el.classList.toggle('selected', parseInt(el.dataset.optionId) === optionId);
    });
    document.getElementById('btnApprove').disabled = false;
}
window.selectApprovalOption = selectApprovalOption;

function startCountdown(trainId, recommendedOption) {
    approvalState.remaining = APPROVAL_TIMEOUT;
    const circumference = 2 * Math.PI * 34; // 213.6
    const progressEl = document.getElementById('countdownProgress');
    const textEl = document.getElementById('countdownText');

    // Reset
    progressEl.setAttribute('stroke-dashoffset', '0');
    textEl.textContent = APPROVAL_TIMEOUT;
    progressEl.setAttribute('stroke', 'var(--warning)');

    approvalState.timer = setInterval(() => {
        approvalState.remaining--;
        const fraction = 1 - (approvalState.remaining / APPROVAL_TIMEOUT);
        const offset = circumference * fraction;
        progressEl.setAttribute('stroke-dashoffset', offset.toString());
        textEl.textContent = approvalState.remaining;

        // Color transitions
        if (approvalState.remaining <= 10) {
            progressEl.setAttribute('stroke', 'var(--danger)');
        } else if (approvalState.remaining <= 30) {
            progressEl.setAttribute('stroke', 'var(--warning)');
        }

        if (approvalState.remaining <= 0) {
            clearInterval(approvalState.timer);
            // Auto-approve recommended
            showToast(`⏱️ Time expired — auto-approving recommended route for Train ${trainId}`, 'warning');
            doApproval(trainId, recommendedOption, true);
        }
    }, 1000);
}

async function submitApproval() {
    if (!approvalState.selectedOption) return;
    clearInterval(approvalState.timer);
    await doApproval(approvalState.trainId, approvalState.selectedOption, false);
}
window.submitApproval = submitApproval;

async function doApproval(trainId, optionId, isAuto) {
    const endpoint = isAuto ? '/api/train/auto-approve-disaster' : '/api/train/approve-disaster';

    try {
        const res = await fetch(`${API}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ train_id: trainId, option_id: optionId }),
        });
        const data = await res.json();

        if (!data.success) {
            showToast(`❌ Approval failed: ${data.error}`, 'danger');
            return;
        }

        const result = data.data;
        const approvalType = isAuto ? 'Auto-approved' : 'Admin-approved';
        const approvedOpt = result.approved_option || {};

        // Success toast
        showToast(
            `✅ ${approvalType}: Train ${trainId} rerouted via ${approvedOpt.option_name || 'Option ' + optionId}`,
            'success'
        );

        // Cascade notification toasts
        const cascades = result.cascade_updates || [];
        cascades.forEach((cu, i) => {
            setTimeout(() => {
                showToast(
                    `🔄 Train ${cu.train_id}: ${cu.impact} (+${cu.delay_minutes}m delay, ~${cu.passengers_affected} passengers affected) — caused by reroute of Train ${trainId}`,
                    'info'
                );
            }, 500 * (i + 1));
        });

        // Update TrainManager with fresh data
        if (result.updated_train) {
            const train = TrainManager.get(trainId);
            if (train) {
                train.result = result.updated_train;
                train.status = 'disaster';  // keep as disaster (rerouted)
            }
        }

        // Re-render everything
        renderTrainsGrid();
        renderTrackDiagram();
        if (TrainManager.activeDetail === trainId) {
            openTrainDetail(trainId);
        }

    } catch (err) {
        showToast(`❌ Error: ${err.message}`, 'danger');
    }

    // Close modal
    document.getElementById('approvalOverlay').style.display = 'none';
    clearInterval(approvalState.timer);

    // Resolve the promise so next approval can proceed
    if (approvalState.resolve) approvalState.resolve();
}

// ══════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ══════════════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(toast);

    // Auto-remove after 8 seconds
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 400);
    }, 8000);
}

// ══════════════════════════════════════════════════════════════════
//  TRAINS GRID — overview cards
// ══════════════════════════════════════════════════════════════════

function renderTrainsGrid() {
    const grid = document.getElementById('trainsGrid');
    grid.innerHTML = '';

    TrainManager.getAll().forEach(train => {
        const r = train.result;
        const sched = r.results?.scheduling || {};
        const pred = r.results?.time_prediction || {};
        const mon = r.results?.monitoring || {};
        const route = sched.assigned_route || {};
        const typeInfo = TRAIN_TYPES.find(t => t.value === train.trainType) || TRAIN_TYPES[1];

        const statusClass = train.status === 'disaster' ? 'status-disaster' :
            train.status === 'delayed' ? 'status-delayed' : 'status-ontime';
        const statusText = train.status === 'disaster' ? '🚨 Disaster' :
            train.status === 'delayed' ? '⚠️ Delayed' : '✅ On-Time';

        const card = document.createElement('div');
        card.className = `train-card ${statusClass}`;
        card.onclick = () => openTrainDetail(r.train_id);
        card.innerHTML = `
            <div class="train-card-top">
                <div class="train-card-id">
                    <span class="train-type-dot" style="background:${typeInfo.color}"></span>
                    <span class="train-id-text">${r.train_id}</span>
                    <span class="train-type-label">${typeInfo.label}</span>
                </div>
                <span class="train-status-badge ${statusClass}">${statusText}</span>
            </div>
            <div class="train-card-route">
                <span class="route-station">${route.source || '—'}</span>
                <span class="route-arrow">━━━━►</span>
                <span class="route-station">${route.destination || '—'}</span>
            </div>
            <div class="train-card-stats">
                <div class="mini-stat">
                    <div class="mini-label">Depart</div>
                    <div class="mini-value">${sched.departure_time || '—'}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-label">ETA</div>
                    <div class="mini-value">${pred.predicted_arrival_time || '—'}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-label">Delay</div>
                    <div class="mini-value ${(mon.delay_minutes || 0) > 0 ? 'val-danger' : 'val-success'}">${mon.delay_minutes || 0}m</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-label">Platform</div>
                    <div class="mini-value">#${sched.platform_number || '—'}</div>
                </div>
            </div>
            <div class="train-card-footer">Click to view full pipeline →</div>
        `;
        grid.appendChild(card);
    });
}

// ══════════════════════════════════════════════════════════════════
//  SVG TRACK DIAGRAM
// ══════════════════════════════════════════════════════════════════

function renderTrackDiagram() {
    const svg = document.getElementById('trackSvg');
    const container = document.getElementById('trackContainer');
    const allTrains = TrainManager.getAll();
    if (allTrains.length === 0) return;

    // Collect unique stations in order
    const stationSet = new Set();
    allTrains.forEach(t => {
        const sched = t.result.results?.scheduling || {};
        const stops = sched.stops || [];
        stops.forEach(s => stationSet.add(s.station || s));
        const route = sched.assigned_route || {};
        if (route.source) stationSet.add(route.source);
        if (route.destination) stationSet.add(route.destination);
    });
    const stations = [...stationSet];

    const width = Math.max(container.clientWidth - 40, 800);
    const height = 60 + allTrains.length * 80;
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.innerHTML = '';

    const pad = 80;
    const trackW = width - pad * 2;

    // Station positions across the top
    const stationX = {};
    stations.forEach((s, i) => {
        stationX[s] = pad + (i / Math.max(stations.length - 1, 1)) * trackW;
    });

    // Draw station markers at top
    const ns = 'http://www.w3.org/2000/svg';

    stations.forEach((s, i) => {
        const x = stationX[s];
        // Vertical guide line
        const guideLine = document.createElementNS(ns, 'line');
        guideLine.setAttribute('x1', x); guideLine.setAttribute('x2', x);
        guideLine.setAttribute('y1', 35); guideLine.setAttribute('y2', height);
        guideLine.setAttribute('stroke', 'rgba(100,116,139,0.12)');
        guideLine.setAttribute('stroke-dasharray', '3,4');
        svg.appendChild(guideLine);

        // Station dot
        const dot = document.createElementNS(ns, 'circle');
        dot.setAttribute('cx', x); dot.setAttribute('cy', 28);
        dot.setAttribute('r', 6);
        dot.setAttribute('fill', '#64748b');
        dot.setAttribute('stroke', '#1e293b'); dot.setAttribute('stroke-width', 2);
        svg.appendChild(dot);

        // Station label
        const label = document.createElementNS(ns, 'text');
        label.setAttribute('x', x); label.setAttribute('y', 14);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('fill', '#94a3b8');
        label.setAttribute('font-size', '10');
        label.setAttribute('font-family', 'Inter, sans-serif');
        label.textContent = s.length > 10 ? s.substring(0, 9) + '…' : s;
        svg.appendChild(label);
    });

    // Draw each train's track
    allTrains.forEach((train, idx) => {
        const y = 70 + idx * 80;
        const sched = train.result.results?.scheduling || {};
        const route = sched.assigned_route || {};
        const stops = sched.stops || [];
        const src = route.source || '';
        const dst = route.destination || '';

        const srcX = stationX[src] || pad;
        const dstX = stationX[dst] || (pad + trackW);

        const statusColor = train.status === 'disaster' ? '#ef4444' :
            train.status === 'delayed' ? '#f59e0b' : '#10b981';

        const typeInfo = TRAIN_TYPES.find(t => t.value === train.trainType) || TRAIN_TYPES[1];

        // Track line (glow effect)
        const trackGlow = document.createElementNS(ns, 'line');
        trackGlow.setAttribute('x1', srcX); trackGlow.setAttribute('x2', dstX);
        trackGlow.setAttribute('y1', y); trackGlow.setAttribute('y2', y);
        trackGlow.setAttribute('stroke', statusColor);
        trackGlow.setAttribute('stroke-width', 4);
        trackGlow.setAttribute('stroke-opacity', 0.2);
        trackGlow.setAttribute('stroke-linecap', 'round');
        svg.appendChild(trackGlow);

        // Track line
        const track = document.createElementNS(ns, 'line');
        track.setAttribute('x1', srcX); track.setAttribute('x2', dstX);
        track.setAttribute('y1', y); track.setAttribute('y2', y);
        track.setAttribute('stroke', statusColor);
        track.setAttribute('stroke-width', 2);
        track.setAttribute('stroke-linecap', 'round');
        svg.appendChild(track);

        // Stop dots on the track
        stops.forEach(s => {
            const st = s.station || s;
            if (stationX[st] !== undefined) {
                const stopDot = document.createElementNS(ns, 'circle');
                stopDot.setAttribute('cx', stationX[st]); stopDot.setAttribute('cy', y);
                stopDot.setAttribute('r', 4);
                stopDot.setAttribute('fill', '#1a2235');
                stopDot.setAttribute('stroke', statusColor);
                stopDot.setAttribute('stroke-width', 1.5);
                svg.appendChild(stopDot);
            }
        });

        // Train icon — positioned based on progress
        const mon = train.result.results?.monitoring || {};
        const remainDist = train.config.remaining_distance_km || 10;
        const totalDist = train.config.distance_km || 500;
        const progress = Math.min(1, Math.max(0, 1 - remainDist / totalDist));
        const trainX = srcX + (dstX - srcX) * progress;

        // Train group (clickable)
        const g = document.createElementNS(ns, 'g');
        g.setAttribute('class', 'track-train-icon');
        g.setAttribute('cursor', 'pointer');
        g.onclick = () => openTrainDetail(train.result.train_id);

        // Pulse circle
        const pulse = document.createElementNS(ns, 'circle');
        pulse.setAttribute('cx', trainX); pulse.setAttribute('cy', y);
        pulse.setAttribute('r', 14);
        pulse.setAttribute('fill', statusColor);
        pulse.setAttribute('fill-opacity', 0.15);
        pulse.innerHTML = `<animate attributeName="r" values="12;18;12" dur="2s" repeatCount="indefinite"/>`;
        g.appendChild(pulse);

        // Train dot
        const trainDot = document.createElementNS(ns, 'circle');
        trainDot.setAttribute('cx', trainX); trainDot.setAttribute('cy', y);
        trainDot.setAttribute('r', 10);
        trainDot.setAttribute('fill', statusColor);
        trainDot.setAttribute('stroke', '#0a0e17'); trainDot.setAttribute('stroke-width', 2);
        g.appendChild(trainDot);

        // Train emoji
        const emoji = document.createElementNS(ns, 'text');
        emoji.setAttribute('x', trainX); emoji.setAttribute('y', y + 4);
        emoji.setAttribute('text-anchor', 'middle');
        emoji.setAttribute('font-size', '11');
        emoji.textContent = '🚆';
        g.appendChild(emoji);

        svg.appendChild(g);

        // Train label to the left
        const trainLabel = document.createElementNS(ns, 'text');
        trainLabel.setAttribute('x', srcX - 12); trainLabel.setAttribute('y', y + 4);
        trainLabel.setAttribute('text-anchor', 'end');
        trainLabel.setAttribute('fill', typeInfo.color);
        trainLabel.setAttribute('font-size', '11');
        trainLabel.setAttribute('font-weight', '600');
        trainLabel.setAttribute('font-family', 'Inter, sans-serif');
        trainLabel.textContent = train.result.train_id;
        svg.appendChild(trainLabel);

        // Status label
        const statusLabel = document.createElementNS(ns, 'text');
        statusLabel.setAttribute('x', dstX + 12);
        statusLabel.setAttribute('y', y + 4);
        statusLabel.setAttribute('text-anchor', 'start');
        statusLabel.setAttribute('fill', statusColor);
        statusLabel.setAttribute('font-size', '10');
        statusLabel.setAttribute('font-weight', '500');
        statusLabel.setAttribute('font-family', 'Inter, sans-serif');
        const statusText = train.status === 'disaster' ? 'DISASTER' :
            train.status === 'delayed' ? 'DELAYED' : 'ON-TIME';
        statusLabel.textContent = `${statusText} · ${mon.delay_minutes || 0}m`;
        svg.appendChild(statusLabel);
    });
}

// ══════════════════════════════════════════════════════════════════
//  PER-TRAIN DETAIL DRILL-DOWN
// ══════════════════════════════════════════════════════════════════

function openTrainDetail(trainId) {
    const train = TrainManager.get(trainId);
    if (!train) return;

    TrainManager.activeDetail = trainId;
    const r = train.result;

    // Show section
    const section = document.getElementById('trainDetailSection');
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Title
    const typeInfo = TRAIN_TYPES.find(t => t.value === train.trainType) || TRAIN_TYPES[1];
    document.getElementById('detailTrainTitle').innerHTML =
        `<span class="train-type-dot" style="background:${typeInfo.color}"></span> Train ${trainId} · ${typeInfo.label}`;

    // Animate pipeline
    animateDetailPipeline(train);

    // Render result cards
    renderDetailCards(r);

    // Highlight in grid
    document.querySelectorAll('.train-card').forEach(c => c.classList.remove('active'));
    const cards = document.querySelectorAll('.train-card');
    cards.forEach(c => {
        if (c.querySelector('.train-id-text')?.textContent === trainId) {
            c.classList.add('active');
        }
    });
}
window.openTrainDetail = openTrainDetail;

function closeDetail() {
    document.getElementById('trainDetailSection').style.display = 'none';
    TrainManager.activeDetail = null;
    document.querySelectorAll('.train-card').forEach(c => c.classList.remove('active'));
}
window.closeDetail = closeDetail;

async function animateDetailPipeline(train) {
    const nodes = ['schedule', 'predict', 'monitor', 'disaster'];
    nodes.forEach(n => {
        const el = document.getElementById(`detail-node-${n}`);
        el.className = 'pipeline-node' + (n === 'disaster' ? ' disaster-node' : '');
        el.querySelector('.node-status').textContent = 'Idle';
    });

    const disasterTriggered = train.result.disaster_triggered;
    const mon = train.result.results?.monitoring || {};
    const isDelayed = mon.status === 'Delayed';

    // Schedule
    await setDetailNode('schedule', 'active', 'Running…');
    await sleep(300);
    await setDetailNode('schedule', 'done', '✓ Done');

    // Predict
    await setDetailNode('predict', 'active', 'Running…');
    await sleep(300);
    await setDetailNode('predict', 'done', '✓ Done');

    // Monitor
    await setDetailNode('monitor', 'active', 'Running…');
    await sleep(300);
    if (disasterTriggered) {
        await setDetailNode('monitor', 'done', '⚠ Delayed');
        await sleep(200);
        await setDetailNode('disaster', 'active', 'Triggered!');
        await sleep(400);
        await setDetailNode('disaster', 'done', '✓ Resolved');
    } else if (isDelayed) {
        await setDetailNode('monitor', 'done', '⚠ Delayed');
    } else {
        await setDetailNode('monitor', 'done', '✓ On-Time');
    }
}

function setDetailNode(name, state, text) {
    const el = document.getElementById(`detail-node-${name}`);
    el.className = 'pipeline-node' + (state ? ` ${state}` : '') +
        (name === 'disaster' ? ' disaster-node' : '');
    el.querySelector('.node-status').textContent = text || 'Idle';
    return sleep(100);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ══════════════════════════════════════════════════════════════════
//  RENDER DETAIL CARDS
// ══════════════════════════════════════════════════════════════════

function renderDetailCards(result) {
    const r = result.results;

    // ── Scheduling ──
    const sched = r.scheduling || {};
    document.getElementById('detailSchedBadge').textContent = sched.platform_number ? `P${sched.platform_number}` : '—';
    document.getElementById('detailSchedBadge').className = 'card-badge badge-success';
    const route = sched.assigned_route || {};
    const stops = sched.stops || [];
    document.getElementById('detailScheduleBody').innerHTML = `
        <div class="kv-grid">
            <div class="kv-item">
                <div class="kv-label">Route</div>
                <div class="kv-value">${route.source || '—'} → ${route.destination || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Departure</div>
                <div class="kv-value large">${sched.departure_time || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Platform</div>
                <div class="kv-value large">#${sched.platform_number || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Base Travel</div>
                <div class="kv-value">${(sched.estimated_base_travel_time_hours || 0).toFixed(1)}h</div>
            </div>
        </div>
        ${stops.length ? `
        <div style="margin-top:12px">
            <div class="kv-label">Stops (${stops.length})</div>
            <div class="stops-list">
                ${stops.map(s => `<span class="stop-chip">${s.station || s} · P${s.platform || '?'} · ${s.halt_duration_minutes || '?'}m</span>`).join('')}
            </div>
        </div>` : ''}
    `;

    // ── Prediction ──
    const pred = r.time_prediction || {};
    const isRePred = pred.is_re_prediction;
    document.getElementById('detailPredBadge').textContent = isRePred ? 'RE-PREDICTED' : 'PREDICTED';
    document.getElementById('detailPredBadge').className = 'card-badge ' + (isRePred ? 'badge-warning' : 'badge-success');
    const adj = pred.adjustments || {};
    document.getElementById('detailPredictBody').innerHTML = `
        <div class="kv-grid">
            <div class="kv-item">
                <div class="kv-label">Predicted Arrival</div>
                <div class="kv-value large ${isRePred ? 'warning' : 'success'}">${pred.predicted_arrival_time || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Total Travel</div>
                <div class="kv-value large">${(pred.total_travel_hours || 0).toFixed(1)}h</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Delay Prob.</div>
                <div class="kv-value ${(pred.delay_probability_percent || 0) > 40 ? 'danger' : 'success'}">${(pred.delay_probability_percent || 0).toFixed(0)}%</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Confidence</div>
                <div class="kv-value">${((pred.confidence_score || 0) * 100).toFixed(0)}%</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Weather Factor</div>
                <div class="kv-value">${adj.weather_factor || '—'}x</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Congestion Factor</div>
                <div class="kv-value">${adj.congestion_factor || '—'}x</div>
            </div>
        </div>
        ${pred.notes ? `<p style="margin-top:12px;font-size:12px;color:var(--text-muted);line-height:1.5">💬 ${pred.notes}</p>` : ''}
    `;

    // ── Monitoring ──
    const mon = r.monitoring || {};
    const isDelayed = mon.status === 'Delayed';
    document.getElementById('detailMonBadge').textContent = mon.status || '—';
    document.getElementById('detailMonBadge').className = 'card-badge ' + (isDelayed ? 'badge-danger' : 'badge-success');
    document.getElementById('detailMonitorBody').innerHTML = `
        <div class="kv-grid">
            <div class="kv-item">
                <div class="kv-label">Status</div>
                <div class="kv-value large ${isDelayed ? 'danger' : 'success'}">${mon.status || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Delay</div>
                <div class="kv-value large ${isDelayed ? 'danger' : 'success'}">${mon.delay_minutes || 0} min</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Risk Level</div>
                <div class="kv-value ${mon.risk_level === 'High' ? 'danger' : 'success'}">${mon.risk_level || '—'}</div>
            </div>
            <div class="kv-item">
                <div class="kv-label">Current Speed</div>
                <div class="kv-value">${mon.current_speed_kmh || '—'} km/h</div>
            </div>
        </div>
        ${mon.flag_disaster_recovery ? '<p style="margin-top:10px;font-size:12px;color:var(--danger)">🚨 Disaster Recovery flagged</p>' : ''}
        ${mon.recommended_actions ? `
        <div style="margin-top:10px">
            <div class="kv-label">Recommended Actions</div>
            ${mon.recommended_actions.map(a => `<p style="font-size:12px;color:var(--text-secondary);margin:3px 0">• ${a}</p>`).join('')}
        </div>` : ''}
    `;

    // ── Disaster ──
    if (result.disaster_triggered) {
        document.getElementById('detailDisasterCard').style.display = 'block';
        const dr = r.disaster_recovery || {};
        const rc = dr.root_cause || {};
        const approved = dr.approved_option || {};
        const options = dr.options_presented || [];

        document.getElementById('detailDisasterBody').innerHTML = `
            <div style="margin-bottom:14px;padding:12px;background:var(--danger-bg);border-radius:8px">
                <div class="kv-grid">
                    <div class="kv-item">
                        <div class="kv-label">Failure Type</div>
                        <div class="kv-value danger">${(rc.failure_type || '—').replace(/_/g, ' ').toUpperCase()}</div>
                    </div>
                    <div class="kv-item">
                        <div class="kv-label">Severity</div>
                        <div class="kv-value danger">${(rc.severity || '—').toUpperCase()}</div>
                    </div>
                    <div class="kv-item">
                        <div class="kv-label">Location</div>
                        <div class="kv-value">${rc.location || '—'}</div>
                    </div>
                    <div class="kv-item">
                        <div class="kv-label">Approval Status</div>
                        <div class="kv-value success">${(dr.approval_status || '—').toUpperCase()}</div>
                    </div>
                </div>
            </div>
            <h4 style="font-size:12px;color:var(--text-muted);text-transform:uppercase;margin-bottom:10px">
                ${options.length} Options Evaluated — Option ${approved.option_id || '?'} Approved
            </h4>
            ${options.map(opt => {
            const isApproved = opt.option_id === approved.option_id;
            const impact = opt.impact_analysis || {};
            const sc = opt.new_schedule || {};
            return `
                <div style="padding:12px;margin-bottom:8px;background:${isApproved ? 'rgba(16,185,129,0.06)' : 'var(--bg-card)'};border:1px solid ${isApproved ? 'rgba(16,185,129,0.3)' : 'var(--border)'};border-radius:8px">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                        <span style="font-weight:700;font-size:14px">${opt.option_name || 'Option ' + opt.option_id} ${isApproved ? '✅ APPROVED' : ''}</span>
                        <span style="font-size:12px;font-weight:700;color:${opt.recommendation_score >= 7 ? 'var(--success)' : opt.recommendation_score >= 5 ? 'var(--warning)' : 'var(--danger)'}">
                            Score: ${opt.recommendation_score}/10
                        </span>
                    </div>
                    <div class="kv-grid" style="font-size:12px">
                        <div><span class="kv-label">Delay Added</span><div class="kv-value">+${sc.delay_added_minutes || 0} min</div></div>
                        <div><span class="kv-label">Trains Disturbed</span><div class="kv-value ${impact.trains_disturbed > 0 ? 'warning' : 'success'}">${impact.trains_disturbed || 0}</div></div>
                        <div><span class="kv-label">Passengers Affected</span><div class="kv-value">~${impact.total_passengers_affected || 0}</div></div>
                        <div><span class="kv-label">Safety</span><div class="kv-value">${(opt.safety_score || '—').toUpperCase()}</div></div>
                    </div>
                </div>`;
        }).join('')}
            ${dr.safety_notes ? `<p style="margin-top:10px;font-size:12px;color:var(--text-muted);font-style:italic">🛡️ ${dr.safety_notes}</p>` : ''}
        `;
    } else {
        document.getElementById('detailDisasterCard').style.display = 'none';
    }
}

// ══════════════════════════════════════════════════════════════════
//  HEALTH CHECK
// ══════════════════════════════════════════════════════════════════

async function checkHealth() {
    try {
        const res = await fetch(`${API}/api/health`);
        const data = await res.json();
        const badge = document.getElementById('systemStatus');
        if (data.status === 'healthy') {
            badge.textContent = '● System Online';
            badge.style.color = 'var(--success)';
        } else {
            badge.textContent = '● Degraded';
            badge.style.color = 'var(--warning)';
        }
    } catch {
        const badge = document.getElementById('systemStatus');
        badge.textContent = '● Offline';
        badge.style.color = 'var(--danger)';
    }
}

// ══════════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════════

// Add 2 default train rows
addTrainRow({ trainId: '12627', source: 'Bangalore', destination: 'New Delhi', trainType: 'Superfast', departureTime: '08:00', speed: 85, distance: 600, stops: 4, weather: 'clear', congestion: 'low', currentSpeed: 80, remainingDist: 10 });
addTrainRow({ trainId: '12650', source: 'Chennai', destination: 'Mumbai', trainType: 'Express', departureTime: '18:45', speed: 70, distance: 800, stops: 5, weather: 'rain', congestion: 'moderate', currentSpeed: 65, remainingDist: 300 });

checkHealth();
setInterval(checkHealth, 30000);
