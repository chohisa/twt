// game_engine.js
const unitPool = ["보병", "창병", "기병", "궁병"];
let selectedCategory = null;
let gameOver = false;

let gameState = {
    player_score: 0,
    ai_score: 0,
    zones: {
        A: { player_hp: 4, ai_hp: 4, captured_by: null, player_slots: [null,null,null], ai_slots: [null,null,null] },
        B: { player_hp: 8, ai_hp: 8, captured_by: null, player_slots: [null,null,null], ai_slots: [null,null,null] },
        C: { player_hp: 4, ai_hp: 4, captured_by: null, player_slots: [null,null,null], ai_slots: [null,null,null] }
    }
};

function startGame() {
    document.getElementById('mainMenu').style.display = 'none';
    document.getElementById('gameScreen').style.display = 'block';
    
    appendLog("🎮 모바일 통합 게임 엔진이 켜졌습니다.", "system");
    
    // 1선발 랜덤 배치 기믹 실행
    for (let zId in gameState.zones) {
        gameState.zones[zId].player_slots[0] = unitPool[Math.floor(Math.random() * unitPool.length)];
        gameState.zones[zId].ai_slots[0] = unitPool[Math.floor(Math.random() * unitPool.length)];
    }
    
    updateUI();
    appendLog("⚔️ 모든 접전지에 1선발 배치가 완벽히 완료되었습니다!", "system");
}

function selectHandCard(cardName) {
    if (gameOver) return;
    document.querySelectorAll('.real-card').forEach(c => c.classList.remove('selected-card'));
    document.querySelectorAll('.zone.ai').forEach(z => z.classList.remove('ai-target'));
    
    selectedCategory = cardName;
    document.getElementById(`card-${cardName}`).classList.add('selected-card');
    
    document.querySelectorAll('.zone.ai').forEach(z => {
        const zoneId = z.id.split('-')[1];
        if (!gameState.zones[zoneId].captured_by) {
            z.classList.add('ai-target');
        }
    });
}

function checkMatchup(atk, def) {
    if (atk === def) return "DRAW";
    if ((atk === "보병" && def === "창병") ||
        (atk === "창병" && def === "기병") ||
        (atk === "기병" && def === "궁병") ||
        (atk === "궁병" && def === "보병")) {
        return "WIN";
    }
    return "LOSE";
}

function targetZone(zoneId) {
    if (!selectedCategory || gameOver) return;
    
    const zone = gameState.zones[zoneId];
    if (zone.captured_by) return;

    appendLog(`[공격] 접전지 ${zoneId}에 [${selectedCategory}] 돌격!`, "player-log");
    
    const targetCard = zone.ai_slots[0];
    let damage = 0;

    if (targetCard) {
        const res = checkMatchup(selectedCategory, targetCard);
        if (res === "WIN") {
            damage = 2;
            appendLog(`└─ 상성 압승! 적 1선발 [${targetCard}] 격파 (+2 데미지)`, "player-log");
            zone.ai_slots.shift(); zone.ai_slots.push(null); 
        } else if (res === "DRAW") {
            damage = 1;
            appendLog(`└─ 동귀어진! 양측 군사 전멸 (+1 데미지)`, "system");
            zone.ai_slots.shift(); zone.ai_slots.push(null);
        } else {
            damage = 0;
            appendLog(`└─ 상성 열세! 아군 [${selectedCategory}]만 전멸 (0 데미지)`, "ai-log");
        }
    } else {
        damage = 2;
        appendLog(`└─ 빈집 털기! 본진에 직접 타격 (+2 데미지)`, "player-log");
    }

    zone.ai_hp = Math.max(0, zone.ai_hp - damage);
    
    if (zone.ai_hp <= 0 && !zone.captured_by) {
        zone.captured_by = "PLAYER";
        gameState.player_score += 1;
        appendLog(`🚩 [함락] 플레이어가 접전지 ${zoneId}를 점령했습니다!`, "player-log");
    }

    document.querySelectorAll('.real-card').forEach(c => c.classList.remove('selected-card'));
    document.querySelectorAll('.zone.ai').forEach(z => z.classList.remove('ai-target'));
    selectedCategory = null;

    if (checkGameOver()) { updateUI(); return; }

    setTimeout(() => { executeAiTurn(); }, 500);
}

function executeAiTurn() {
    if (gameOver) return;

    // AI 2, 3선발 비밀 예약 배치 기믹
    for (let zId in gameState.zones) {
        let zone = gameState.zones[zId];
        if (zone.captured_by) continue;
        for (let i = 1; i <= 2; i++) {
            if (zone.ai_slots[i] === null && Math.random() < 0.4) {
                zone.ai_slots[i] = unitPool[Math.floor(Math.random() * unitPool.length)];
                appendLog(`🤫 AI가 접전지 ${zId}에 카드를 몰래 예약했습니다.`, "system");
                break;
            }
        }
    }

    // AI 무작위 반격 기믹
    const activeZones = Object.keys(gameState.zones).filter(zId => !gameState.zones[zId].captured_by);
    if (activeZones.length > 0) {
        const targetZoneId = activeZones[Math.floor(Math.random() * activeZones.length)];
        const aiAtkUnit = unitPool[Math.floor(Math.random() * unitPool.length)];
        const zone = gameState.zones[targetZoneId];

        appendLog(`[적 공격] AI가 접전지 ${targetZoneId}에 [${aiAtkUnit}] 투입!`, "ai-log");
        
        const playerTarget = zone.player_slots[0];
        let damage = 0;

        if (playerTarget) {
            const res = checkMatchup(aiAtkUnit, playerTarget);
            if (res === "WIN") {
                damage = 2;
                appendLog(`└─ 아군 패배! 1선발 [${playerTarget}] 무너짐 (-2 HP)`, "ai-log");
                zone.player_slots.shift(); zone.player_slots.push(null); 
            } else if (res === "DRAW") {
                damage = 1;
                appendLog(`└─ 동귀어진! 아군 전선 무너짐 (-1 HP)`, "system");
                zone.player_slots.shift(); zone.player_slots.push(null);
            } else {
                damage = 0;
                appendLog(`└─ 방어 성공! 아군 [${playerTarget}]이 막아냄 (0 데미지)`, "player-log");
            }
        } else {
            damage = 2;
            appendLog(`└─ 아군 방어선 없음! 본진 직접 타격 (-2 HP)`, "ai-log");
        }

        zone.player_hp = Math.max(0, zone.player_hp - damage);

        if (zone.player_hp <= 0 && !zone.captured_by) {
            zone.captured_by = "AI";
            gameState.ai_score += 1;
            appendLog(`🚨 [상실] AI가 접전지 ${targetZoneId}를 완전히 지배합니다!`, "ai-log");
        }
    }

    checkGameOver();
    updateUI();
}

function checkGameOver() {
    if (gameState.player_score >= 2) {
        gameOver = true;
        appendLog("🏆🏆🏆 [최종 승리] 전쟁에서 승리했습니다! 🏆🏆🏆", "system");
        return true;
    } else if (gameState.ai_score >= 2) {
        gameOver = true;
        appendLog("💀💀💀 [최종 패배] 게임 오버 되었습니다. 💀💀💀", "system");
        return true;
    }
    return false;
}

function renderSlots(slotsArray, containerId, isAI) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";

    for (let i = 0; i < 3; i++) {
        const cardName = slotsArray[i];
        if (!cardName) {
            container.innerHTML += `<div class="card-slot empty-slot">${i+1}선발: [ 빈자리 ]</div>`;
        } else {
            if (isAI && i > 0) {
                container.innerHTML += `<div class="card-slot hidden-card">${i+1}선발: [ 비공개 ]</div>`;
            } else {
                container.innerHTML += `<div class="card-slot">${i+1}선발: [ ${cardName} ]</div>`;
            }
        }
    }
}

function updateUI() {
    document.getElementById('p-score').innerText = gameState.player_score;
    document.getElementById('ai-score').innerText = gameState.ai_score;

    ["A", "B", "C"].forEach(zId => {
        const zoneData = gameState.zones[zId];
        const aiZone = document.getElementById(`zone-${zId}-ai`);
        const pZone = document.getElementById(`zone-${zId}-player`);

        if (zoneData.captured_by === "PLAYER") {
            aiZone.className = "zone ai captured-player";
            pZone.className = "zone player captured-player";
            aiZone.innerHTML = `<div class="captured-msg">★ 내 영토 ★</div>`;
            pZone.innerHTML = "";
            return;
        } else if (zoneData.captured_by === "AI") {
            aiZone.className = "zone ai captured-ai";
            pZone.className = "zone player captured-ai";
            aiZone.innerHTML = `<div class="captured-msg">💀 적 점령 💀</div>`;
            pZone.innerHTML = "";
            return;
        }

        document.getElementById(`hp-${zId}-ai`).innerText = `HP: ${zoneData.ai_hp} / ${zId === 'B' ? 8 : 4}`;
        document.getElementById(`hp-${zId}-player`).innerText = `HP: ${zoneData.player_hp} / ${zId === 'B' ? 8 : 4}`;

        renderSlots(zoneData.ai_slots, `slots-${zId}-ai`, true);
        renderSlots(zoneData.player_slots, `slots-${zId}-player`, false);
    });
}

function appendLog(text, className) {
    const logBox = document.getElementById('log-box');
    if (!logBox) return;
    const newLine = document.createElement('div');
    newLine.className = `log-line ${className || ''}`;
    newLine.innerText = text;
    logBox.appendChild(newLine);
    logBox.scrollTop = logBox.scrollHeight;
}
