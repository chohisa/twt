# server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from game_core import GameEngine, Card, CardType

app = FastAPI()
engine = GameEngine()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def get_game_state_json():
    """웹 화면(HTML)이 이해할 수 있도록 현재 엔진의 상태를 포맷팅합니다."""
    return json.dumps({
        "player_score": engine.player_score,
        "ai_score": engine.ai_score,
        "current_turn": engine.current_turn,
        "is_player_turn": engine.is_player_turn,
        "global_items": engine.get_global_item_count(is_player=True),
        "zones": {
            "A": format_zone_data("A"),
            "B": format_zone_data("B"),
            "C": format_zone_data("C")
        }
    }, ensure_ascii=False)

def format_zone_data(zone_id: str):
    """각 접전지의 슬롯 상태를 안전하게 가공합니다."""
    zone = engine.zones[zone_id]
    
    # 플레이어 슬롯 가공
    player_slots_desc = [c.sub_type if c else "빈자리" for c in zone.player_slots]
    
    # AI 슬롯 가공 (카드가 배치되어 있어도 기본적으로 유저 화면엔 '비공개'로 필터링)
    # 단, 전투가 벌어져 장막이 걷히거나 패배한 카드가 아니라면 기본값은 '비공개'로 유지합니다.
    ai_slots_desc = []
    for c in zone.ai_slots:
        if c:
            # 전투 규칙 연동 전까지는 '비공개' 텍스트를 유지하되 데이터가 있음을 알림
            ai_slots_desc.append("비공개") 
        else:
            ai_slots_desc.append("빈자리")
            
    return {
        "player_hp": zone.player_hp,
        "ai_hp": zone.ai_hp,
        "captured_by": zone.captured_by,
        "player_slots": player_slots_desc,
        "ai_slots": ai_slots_desc,
        "player_item_desc": "아이템 없음" if not zone.player_items else f"설치됨({len(zone.player_items)})",
        "ai_item_count": len(zone.ai_items)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # 접속하자마자 첫 상태(랜덤 배치된 1선발 포함) 전송
    await websocket.send_text(json.dumps({"type": "INIT", "state": json.loads(get_game_state_json())}, ensure_ascii=False))
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            if event.get("action") == "ATTACK":
                zone_id = event.get("zone")
                card_name = event.get("card")
                
                atk_card = Card(card_name, CardType.UNIT, card_name)
                battle_logs = engine.execute_attack(zone_id, atk_card, is_player_atk=True)
                
                payload = {
                    "type": "UPDATE",
                    "state": json.loads(get_game_state_json()),
                    "logs": battle_logs
                }
                await manager.broadcast(json.dumps(payload, ensure_ascii=False))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
