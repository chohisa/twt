# game_core.py
from enum import Enum
import random

class CardType(Enum):
    UNIT = 1      # 군수
    ITEM_ATK = 2  # 공격 아이템
    ITEM_DEF = 3  # 수비 아이템
    ITEM_UTIL = 4 # 유틸 아이템

class Card:
    def __init__(self, name: str, card_type: CardType, sub_type: str):
        self.name = name
        self.card_type = card_type
        self.sub_type = sub_type  # "보병", "창병", "기병", "궁병", "용병"

class Zone:
    def __init__(self, name: str, max_hp: int):
        self.name = name
        self.max_hp = max_hp
        self.player_hp = max_hp
        self.ai_hp = max_hp
        self.captured_by = None  # "PLAYER", "AI", None
        
        # 3선발 고정 슬롯 (Card 객체 혹은 None)
        self.player_slots: list[Card | None] = [None, None, None]
        self.ai_slots: list[Card | None] = [None, None, None]
        
        self.player_items = []
        self.ai_items = []

class GameEngine:
    def __init__(self):
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.winner = None
        
        # 접전지 세팅 (B는 요충지 HP 8, A와 C는 일반 HP 4)
        self.zones = {
            "A": Zone("A", 4),
            "B": Zone("B", 8),
            "C": Zone("C", 4)
        }
        
        # 기본 군수 풀 (용병 제외)
        self.unit_pool = ["보병", "창병", "기병", "궁병"]
        
        # [기믹 1] 게임 생성 시 전 지역 1선발 자동 랜덤 배치
        self.setup_initial_units()

    def setup_initial_units(self):
        for zone_id in self.zones:
            p_unit = random.choice(self.unit_pool)
            self.zones[zone_id].player_slots[0] = Card(p_unit, CardType.UNIT, p_unit)
            
            ai_unit = random.choice(self.unit_pool)
            self.zones[zone_id].ai_slots[0] = Card(ai_unit, CardType.UNIT, ai_unit)

    def get_global_item_count(self, is_player: bool) -> int:
        total = 0
        for zone in self.zones.values():
            total += len(zone.player_items) if is_player else len(zone.ai_items)
        return total

    def check_matchup(self, atk_sub: str, def_sub: str) -> str:
        """[기획 핵심] 군수 카드 간 상성표 판정 엔진 (WIN, DRAW, LOSE)"""
        if atk_sub == def_sub:
            return "DRAW"
            
        # 상성 규칙 딕셔너리
        win_relations = {
            "보병": "창병",
            "창병": "기병",
            "기병": ["방패병", "궁병"], # 확장성 고려
            "궁병": "보병"
        }
        
        # 특수 보정 (기병은 궁병을 밟음)
        if atk_sub == "기병" and def_sub == "궁병":
            return "WIN"
            
        target = win_relations.get(atk_sub)
        if target and def_sub in target if isinstance(target, list) else def_sub == target:
            return "WIN"
            
        return "LOSE"

    def advance_slots(self, slots: list):
        """[기믹 2] 선발 카드 파괴 시 2->1선발, 3->2선발로 연쇄 슬라이딩 전진"""
        slots.pop(0)  # 1선발 제거
        slots.append(None)  # 빈자리 보충

    def process_battle(self, zone_id: str, atk_card: Card, is_player_atk: bool) -> list[str]:
        """모든 기믹 연산이 동시에 굴러가는 핵심 융합 메인 프레임"""
        logs = []
        if self.game_over:
            return ["⚠️ 이미 종료된 게임입니다."]

        zone = self.zones[zone_id]
        
        # 진영 레이블 분기
        atk_side = "플레이어" if is_player_atk else "AI"
        def_side = "AI" if is_player_atk else "플레이어"
        
        def_slots = zone.ai_slots if is_player_atk else zone.player_slots
        
        logs.append(f"⚔️ {atk_side}이(가) 접전지 {zone_id}에 [{atk_card.sub_type}] 군수를 투입해 돌격합니다!")

        # 방어 측 1선발 타겟 확인
        target_card = def_slots[0]

        if target_card is not None:
            # 1선발 수비 유닛이 존재하는 경우 -> 상성 매치 돌입
            logs.append(f"🛡️ {def_side}의 1선발 [{target_card.sub_type}] 무리가 방어 진형을 펼쳤습니다!")
            result = self.check_matchup(atk_card.sub_type, target_card.sub_type)

            if result == "WIN":
                damage = 2
                logs.append(f"🔥 [상성 압승] [{atk_card.sub_type}]이(가) [{target_card.sub_type}]을 완벽히 격파했습니다! (데미지 2배!)")
                self.advance_slots(def_slots) # 적 1선발 파괴 및 전진 기믹 작동
                logs.append(f"🏃 {def_side} 진영의 다음 대기 카드가 선발 전선으로 전진합니다.")
                
            elif result == "DRAW":
                damage = 1
                logs.append(f"💥 [동등 공방] 치열한 접전 끝에 두 군수 무리가 동귀어진했습니다! (데미지 1)")
                self.advance_slots(def_slots) # 적 1선발 파괴 및 전진
                
            else: # LOSE
                damage = 0
                logs.append(f"🛡️ [상성 열세] 적의 방어선이 너무 견고합니다! 공격 측 [{atk_card.sub_type}] 유닛만 무력하게 전멸했습니다. (데미지 0)")
        else:
            # 1선발 자리가 완전히 비어있을 때 패널티 데미지
            damage = 2
            logs.append(f"새해 ⚠️ {def_side}의 1선발 라인이 텅 비어있습니다! 본진에 직접 타격을 입힙니다! (기본 데미지 2)")

        # 데미지 차감 연산
        if is_player_atk:
            zone.ai_hp = max(0, zone.ai_hp - damage)
            # 점령 검사
            if zone.ai_hp <= 0 and zone.captured_by is None:
                zone.captured_by = "PLAYER"
                self.player_score += 1
                logs.append(f"🚩 [지역 점령] 플레이어가 접전지 {zone_id}를 완전히 정복했습니다! (현재 스코어 {self.player_score}/2)")
        else:
            zone.player_hp = max(0, zone.player_hp - damage)
            if zone.player_hp <= 0 and zone.captured_by is None:
                zone.captured_by = "AI"
                self.ai_score += 1
                logs.append(f"🚨 [지역 상실] AI가 접전지 {zone_id}를 점령했습니다! (현재 스코어 {self.ai_score}/2)")

        # 최종 승리 조건 체크 (2개 지역 선점)
        if self.player_score >= 2:
            self.game_over = True
            self.winner = "PLAYER"
            logs.append("🏆🏆🏆 [최종 승리] 플레이어가 전쟁에서 대승을 거두었습니다! 게임이 종료됩니다. 🏆🏆🏆")
        elif self.ai_score >= 2:
            self.game_over = True
            self.winner = "AI"
            logs.append("💀💀💀 [최종 패배] AI 군단에게 수도를 함락당했습니다. 게임 오버. 💀💀💀")

        return logs

    def execute_ai_turn(self) -> list[str]:
        """[기믹 4] AI의 실시간 예약 배치 알고리즘 및 무작위 반격 제어"""
        ai_logs = ["🤖 [AI 턴 가동] 상대방이 작전을 수립 중입니다..."]
        if self.game_over:
            return []

        # 1. 수비 카드 빈자리 예약 배치 기믹 (2, 3선발 보충)
        for zone_id, zone in self.zones.items():
            if zone.captured_by:
                continue
            for idx in [1, 2]: # 2선발과 3선발 추적
                if zone.ai_slots[idx] is None:
                    # 30% 확률로 빈자리에 몰래 예약 군수 배치 (장막 효과)
                    if random.random() < 0.4:
                        new_unit = random.choice(self.unit_pool)
                        zone.ai_slots[idx] = Card(new_unit, CardType.UNIT, new_unit)
                        ai_logs.append(f"🤫 AI가 접전지 {zone_id}의 {idx+1}선발 자리에 카드를 몰래 예약 배치했습니다. [비공개 활성화]")
                        break # 한 전선당 턴마다 1장씩만 예약

        # 2. 플레이어를 향한 무작위 기습 반격
        active_zones = [z_id for z_id, z in self.zones.items() if z.captured_by is None]
        if active_zones:
            target_zone_id = random.choice(active_zones)
            ai_atk_unit = random.choice(self.unit_pool)
            ai_atk_card = Card(ai_atk_unit, CardType.UNIT, ai_atk_unit)
            
            # AI 전투 실행 및 로그 병합
            battle_results = self.process_battle(target_zone_id, ai_atk_card, is_player_atk=False)
            ai_logs.extend(battle_results)
            
        return ai_logs
