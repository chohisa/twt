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
    """[기획 반영] 1선발은 공개, 2·3선발은 배치 시 비공개, 없으면 빈자리"""
    zone = engine.zones[zone_id]
    
    # 플레이어 슬롯 가공 (내 카드는 내가 다 볼 수 있음)
    player_slots_desc = [c.sub_type if c else "빈자리" for c in zone.player_slots]
    
    # AI 슬롯 가공 규칙 정밀 반영
    ai_slots_desc = []
    for idx, c in enumerate(zone.ai_slots):
        if c:
            if idx == 0:
                # 1선발은 장막 효과가 없는 한 무조건 실명 공개!
                ai_slots_desc.append(c.sub_type)
            else:
                # 2, 3선발은 카드가 배치되어 있다면 기본적으로 비공개(장막) 처리
                ai_slots_desc.append("비공개")
        else:
            # 배치를 안 한 곳은 무조건 빈자리 표시
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
