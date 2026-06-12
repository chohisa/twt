# server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
from game_core import GameEngine, Card, CardType

app = FastAPI()
engine = GameEngine()

# 연결된 웹 브라우저 클라이언트들을 관리하는 매니저
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
            "A": {
                "player_hp": engine.zones["A"].player_hp,
                "ai_hp": engine.zones["A"].ai_hp,
                "captured_by": engine.zones["A"].captured_by,
                "player_slots": [c.sub_type if c else "빈자리" for c in engine.zones["A"].player_slots],
                "ai_slots": [c.sub_type if c else "비공개" for c in engine.zones["A"].ai_slots], # 일단 껍데기 규칙
                "player_item_desc": f"함정{len([i for i in engine.zones['A'].player_items if i.name=='함정'])}",
                "ai_item_count": len(engine.zones["A"].ai_items)
            },
            "B": {
                "player_hp": engine.zones["B"].player_hp,
                "ai_hp": engine.zones["B"].ai_hp,
                "captured_by": engine.zones["B"].captured_by,
                "player_slots": [c.sub_type if c else "빈자리" for c in engine.zones["B"].player_slots],
                "ai_slots": [c.sub_type if c else "비공개" for c in engine.zones["B"].ai_slots],
                "player_item_desc": "아이템 없음",
                "ai_item_count": len(engine.zones["B"].ai_items)
            },
            "C": {
                "player_hp": engine.zones["C"].player_hp,
                "ai_hp": engine.zones["C"].ai_hp,
                "captured_by": engine.zones["C"].captured_by,
                "player_slots": [c.sub_type if c else "빈자리" for c in engine.zones["C"].player_slots],
                "ai_slots": [c.sub_type if c else "비공개" for c in engine.zones["C"].ai_slots],
                "player_item_desc": f"함정{len([i for i in engine.zones['C'].player_items if i.name=='함정'])}",
                "ai_item_count": len(engine.zones["C"].ai_items)
            }
        }
    }, ensure_ascii=False)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # 접속하자마자 첫 상태 전송
    await websocket.send_text(json.dumps({"type": "INIT", "state": json.loads(get_game_state_json())}, ensure_ascii=False))
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            # 유저가 공격 카드를 내서 상대를 조준했을 때의 이벤트 처리
            if event.get("action") == "ATTACK":
                zone_id = event.get("zone")
                card_name = event.get("card")
                
                # 가상의 카드 객체 임시 생성 (추후 손패 관리 시스템 완성 시 연동)
                atk_card = Card(card_name, CardType.UNIT, card_name)
                
                # 엔진 가동 및 전투 연산 실행
                battle_logs = engine.execute_attack(zone_id, atk_card, is_player_atk=True)
                
                # 연산이 끝난 후 변경된 전체 데이터와 로그를 클라이언트에 전송
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
