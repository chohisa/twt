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
        "game_over": engine.game_over,
        "winner": engine.winner,
        "global_items": engine.get_global_item_count(is_player=True),
        "zones": {
            "A": format_zone_data("A"),
            "B": format_zone_data("B"),
            "C": format_zone_data("C")
        }
    }, ensure_ascii=False)

def format_zone_data(zone_id: str):
    """[기획 완벽 반영] 1선발 이름 무조건 실명 노출, 2/3선발은 예약되어 있을 때만 비공개, 없으면 빈자리"""
    zone = engine.zones[zone_id]
    
    player_slots_desc = [c.sub_type if c else "빈자리" for c in zone.player_slots]
    
    ai_slots_desc = []
    for idx, c in enumerate(zone.ai_slots):
        if c:
            if idx == 0:
                # 1선발은 무조건 실명 100% 전천후 공개!
                ai_slots_desc.append(c.sub_type)
            else:
                # 2, 3선발에 카드가 들어찼다면 '비공개' 마킹
                ai_slots_desc.append("비공개")
        else:
            # 카드가 예약 안 된 깨끗한 곳은 '빈자리' 명시
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
    
    # 첫 기동 시 초기 데이터(1선발 무작위 배치 정보 포함) 발송
    await websocket.send_text(json.dumps({"type": "INIT", "state": json.loads(get_game_state_json())}, ensure_ascii=False))
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            if event.get("action") == "ATTACK":
                if engine.game_over:
                    continue
                
                zone_id = event.get("zone")
                card_name = event.get("card")
                
                # 1. 플레이어 선공 공격 연산 시동
                atk_card = Card(card_name, CardType.UNIT, card_name)
                player_turn_logs = engine.process_battle(zone_id, atk_card, is_player_atk=True)
                
                # 2. 플레이어 공격 종료 후 즉시 AI 실시간 역습/예약 알고리즘 연쇄 작동
                ai_turn_logs = engine.execute_ai_turn()
                
                # 3. 모든 로그 통합 및 상태 패키징 발송
                total_logs = player_turn_logs + ai_turn_logs
                
                payload = {
                    "type": "UPDATE",
                    "state": json.loads(get_game_state_json()),
                    "logs": total_logs
                }
                await manager.broadcast(json.dumps(payload, ensure_ascii=False))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
