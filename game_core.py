# game_core.py
from enum import Enum
import random

class CardType(Enum):
    UNIT = 1      # 군수 (보병, 창병, 기병, 궁병 등)
    ITEM_ATK = 2  # 공격 아이템
    ITEM_DEF = 3  # 수비 아이템
    ITEM_UTIL = 4 # 유틸 아이템

class Card:
    def __init__(self, name: str, card_type: CardType, sub_type: str):
        self.name = name
        self.card_type = card_type
        self.sub_type = sub_type  # "보병", "창병", "기병", "궁병" 등

class Zone:
    def __init__(self, name: str, max_hp: int):
        self.name = name
        self.max_hp = max_hp
        self.player_hp = max_hp
        self.ai_hp = max_hp
        self.captured_by = None  # "PLAYER", "AI", None
        
        # 1선발, 2선발, 3선발 자리를 명확히 고정 (None이면 빈자리)
        self.player_slots = [None, None, None]
        self.ai_slots = [None, None, None]
        
        self.player_items = []
        self.ai_items = []

class GameEngine:
    def __init__(self):
        self.player_score = 0
        self.ai_score = 0
        self.current_turn = 1
        self.is_player_turn = True
        
        # 접전지 초기화 (B는 HP 8, A와 C는 HP 4)
        self.zones = {
            "A": Zone("A", 4),
            "B": Zone("B", 8),
            "C": Zone("C", 4)
        }
        
        # 게임 시작 시 1선발 랜덤 배치 실행
        self.setup_initial_units()

    def setup_initial_units(self):
        """[기획 반영] 게임 시작 시 모든 접전지의 1선발에 용병을 제외한 군수카드를 랜덤 배치"""
        available_units = ["보병", "창병", "기병", "궁병"]
        
        for zone_id in self.zones:
            # 플레이어 1선발 랜덤 배치
            p_unit_name = random.choice(available_units)
            self.zones[zone_id].player_slots[0] = Card(p_unit_name, CardType.UNIT, p_unit_name)
            
            # AI 1선발 랜덤 배치
            ai_unit_name = random.choice(available_units)
            self.zones[zone_id].ai_slots[0] = Card(ai_unit_name, CardType.UNIT, ai_unit_name)

    def get_global_item_count(self, is_player: bool) -> int:
        """전체 전장에 설치된 아이템 총합 계산"""
        total = 0
        for zone in self.zones.values():
            total += len(zone.player_items) if is_player else len(zone.ai_items)
        return total

    def execute_attack(self, zone_id: str, atk_card: Card, is_player_atk: bool) -> list[str]:
        """전투 연산 메인 로직 (현재는 간단한 타격 및 슬롯 소모 로그만 구현)"""
        zone = self.zones[zone_id]
        logs = []
        
        attacker_label = "플레이어" if is_player_atk else "AI"
        defender_label = "AI" if is_player_atk else "플레이어"
        
        logs.append(f"⚔️ {attacker_label}이(가) 접전지 {zone_id}에 [{atk_card.name}] 공격을 감행했습니다!")
        
        # 임시 전투 연산: 공격받은 진영의 HP를 1 깎고 로그 처리
        if is_player_atk:
            zone.ai_hp = max(0, zone.ai_hp - 1)
            logs.append(f"💥 AI의 접전지 {zone_id} HP가 1 감소했습니다. (남은 HP: {zone.ai_hp})")
            
            # 공격 후 연출용으로 AI의 1선발 장막을 살짝 오픈하는 예시 규칙
            if zone.ai_slots[0]:
                logs.append(f"👁️ 접전지 {zone_id}의 AI 1선발 정체가 탄로났습니다! 👉 [{zone.ai_slots[0].sub_type}]")
            
            # 점령 판정
            if zone.ai_hp <= 0 and zone.captured_by is None:
                zone.captured_by = "PLAYER"
                self.player_score += 1
                logs.append(f"🎉 [🎉 점령 완료] 플레이어가 접전지 {zone_id}를 완전히 함락했습니다!")
        
        return logs
