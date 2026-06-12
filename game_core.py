import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ==============================================================================
# [1] 카드 및 데이터 모델 구조 정의
# ==============================================================================
class CardType:
    UNIT = "UNIT"
    ITEM = "ITEM"

class ItemType:
    ATK = "ATK"       # 공격형 (총공세 명령, 공성 공병)
    DEF = "DEF"       # 수비형 (함정, 위장 장막)
    UTIL = "UTIL"     # 사용형 (첩보서, 군수 보급, 보급 수레, 철수 명령)

@dataclass
class Card:
    name: str
    card_type: str     # UNIT 또는 ITEM
    sub_type: str      # 보병, 창병, 기병, 방패병, 궁병, 용병 또는 아이템 이름
    skill_name: Optional[str] = None

@dataclass
class Zone:
    name: str
    max_hp: int
    player_hp: int
    ai_hp: int
    # [1선발, 2선발, 3선발] 순서 저장 배열
    player_slots: List[Optional[Card]] = field(default_factory=lambda: [None, None, None])
    ai_slots: List[Optional[Card]] = field(default_factory=lambda: [None, None, None])
    # 설치형 아이템 목록 (최대 4개 글로벌 제한 확인용)
    player_items: List[Card] = field(default_factory=list)
    ai_items: List[Card] = field(default_factory=list)
    # 점령 상태 정보 (None: 진행중, "PLAYER": 플레이어 점령, "AI": AI 점령)
    captured_by: Optional[str] = None

# ==============================================================================
# [2] 게임 규칙 및 전투 판정 핵심 엔진
# ==============================================================================
class GameEngine:
    MATCHUPS = {
        "보병": "창병",
        "창병": "기병",
        "기병": "방패병",
        "방패병": "궁병",
        "궁병": "보병"
    }

    def __init__(self):
        self.zones = {
            "A": Zone("Zone A", 4, 4, 4),
            "B": Zone("Zone B", 8, 8, 8),
            "C": Zone("Zone C", 4, 4, 4)
        }
        self.player_score = 0
        self.ai_score = 0
        self.current_turn = 1
        self.is_player_turn = True
        self.is_first_turn = True  # 게임 최초의 첫 턴(선/후공 첫 턴 제약용)
        self.is_player_first = True # 플레이어가 선공인지 여부
        
        # 턴당 사용 횟수 제한 카운터
        self.turn_counters = {
            "player_공성공병": 0, "player_군수보급": 0, "player_철수명령": 0,
            "ai_공성공병": 0, "ai_군수보급": 0, "ai_철수명령": 0
        }

    def reset_turn_counters(self):
        for key in self.turn_counters:
            self.turn_counters[key] = 0

    def get_global_item_count(self, is_player: bool) -> int:
        """글로벌 설치형 아이템(함정, 장막)의 총 개수를 구합니다."""
        count = 0
        for zone in self.zones.values():
            count += len(zone.player_items if is_player else zone.ai_items)
        return count

    def check_zone_capture(self, zone_id: str) -> Optional[str]:
        """특정 접전지의 HP를 체크하여 점령 상태를 비가역적으로 갱신합니다."""
        zone = self.zones[zone_id]
        if zone.captured_by is not None:
            return zone.captured_by

        if zone.ai_hp <= 0:
            zone.captured_by = "PLAYER"
            self.player_score += 1
            self.clear_captured_zone(zone, "PLAYER")
            return "PLAYER"
        elif zone.player_hp <= 0:
            zone.captured_by = "AI"
            self.ai_score += 1
            self.clear_captured_zone(zone, "AI")
            return "AI"
        return None

    def clear_captured_zone(self, zone: Zone, winner: str):
        """점령 완결 시 해당 레인의 모든 카드와 아이템을 완전히 청소합니다."""
        zone.player_slots = [None, None, None]
        zone.ai_slots = [None, None, None]
        zone.player_items.clear()
        zone.ai_items.clear()

    def shift_slots(self, slots: List[Optional[Card]]):
        """선발 승격 로직: 빈자리가 생기면 뒤의 카드가 항상 앞으로 전진합니다."""
        non_empty = [card for card in slots if card is not None]
        while len(non_empty) < 3:
            non_empty.append(None)
        for i in range(3):
            slots[i] = non_empty[i]

    # --------------------------------------------------------------------------
    # 핵심 전투 프로세스 (공격 전개 및 우선순위 체인 판정)
    # --------------------------------------------------------------------------
    def execute_attack(self, zone_id: str, atk_card: Card, is_player_atk: bool) -> List[str]:
        """
        손패의 군수 카드를 소모하여 특정 Zone을 공격합니다.
        턴 종료 매커니즘 및 전투 이벤트를 순차 로그 리스트로 반환합니다.
        """
        logs = []
        zone = self.zones[zone_id]
        
        if zone.captured_by is not None:
            return [f"이미 {zone.captured_by} 진영이 점령한 지역입니다. 공격할 수 없습니다."]

        attacker_str = "플레이어" if is_player_atk else "AI"
        defender_str = "AI" if is_player_atk else "플레이어"
        
        logs.append(f"[{attacker_str}]이(가) [접전지 {zone_id}]에 '{atk_card.name}'(으)로 공격을 감행합니다!")

        def_slots = zone.ai_slots if is_player_atk else zone.player_slots
        def_items = zone.ai_items if is_player_atk else zone.player_items

        # 1. 수비 카드 없는 무방비 지역 직격 판정
        if def_slots[0] is None:
            damage = 2
            if is_player_atk:
                zone.ai_hp = max(0, zone.ai_hp - damage)
                logs.append(f"💥 수비 카드가 없는 무방비 지역입니다! AI 진영에 직격 데미지 {damage}을 입혔습니다.")
            else:
                zone.player_hp = max(0, zone.player_hp - damage)
                logs.append(f"💥 수비 카드가 없는 무방비 지역입니다! 플레이어 진영이 직격 데미지 {damage}을 입었습니다.")
            self.check_zone_capture(zone_id)
            return logs

        # 2. 설치형 아이템 [함정] 최우선 판정 체인
        has_trap = any(item.name == "함정" for item in def_items)
        trap_triggered = False

        if has_trap:
            # 예외 처리: 공격 카드가 '기병'인 경우 함정을 파괴하고 무시함
            if atk_card.sub_type == "기병":
                for item in def_items:
                    if item.name == "함정":
                        def_items.remove(item)
                        break
                logs.append("🐎 기병 스킬 [돌파 기동] 발동! 상대의 '함정' 1개를 파괴하고 무시한 채 돌격합니다.")
            else:
                # 일반적인 경우 함정 발동으로 공격 전면 무효화 및 소모 종료
                trap_triggered = True
                for item in def_items:
                    if item.name == "함정":
                        def_items.remove(item)
                        break
                logs.append("💥 [함정 발동!] 공격이 가로막혀 완전히 무효화되었습니다.")
                
                # 1% 확률 반격 연산
                if random.random() < 0.01:
                    if is_player_atk:
                        zone.player_hp = max(0, zone.player_hp - 1)
                        logs.append("🎯 치명적 반격 성공! 플레이어 접전지 체력이 1 감소했습니다.")
                    else:
                        zone.ai_hp = max(0, zone.ai_hp - 1)
                        logs.append("🎯 치명적 반격 성공! AI 접전지 체력이 1 감소했습니다.")
                    self.check_zone_capture(zone_id)
                return logs

        # 3. 정규 전투 진입 (1선발 대 손패 소모 카드)
        def_card = def_slots[0]
        logs.append(f"⚔️ 전투 개시: 공격측 [{atk_card.sub_type}] VS 수비측 [{def_card.sub_type}]")
        
        combat_res = self.resolve_combat_logic(atk_card, def_card)
        
        if combat_res == "ATTACKER_WIN":
            # 창병 관통 공격 확률 주사위
            damage = 1
            if atk_card.sub_type == "창병" and random.random() < 0.40:
                damage = 2
                logs.append("🔱 창병 스킬 [관통 돌격] 발동! 피해량이 2로 증가합니다.")

            if is_player_atk:
                zone.ai_hp = max(0, zone.ai_hp - damage)
            else:
                zone.player_hp = max(0, zone.player_hp - damage)
            
            logs.append(f"🎉 공격측 승리! 수비측 1선발 [{def_card.sub_type}] 카드가 제거되고 접전지 체력이 {damage} 감소합니다.")
            def_slots[0] = None
            self.shift_slots(def_slots) # 선발 승격 진행
            
            # 궁병 연속 사격 확률 주사위
            if atk_card.sub_type == "궁병" and def_slots[0] is not None and random.random() < 0.30:
                logs.append("🏹 궁병 스킬 [연속 사격] 발동! 다음 선발 카드와 연전 연쇄에 돌입합니다.")
                next_def = def_slots[0]
                combat_res2 = self.resolve_combat_logic(atk_card, next_def)
                if combat_res2 == "ATTACKER_WIN":
                    if is_player_atk: zone.ai_hp = max(0, zone.ai_hp - 1)
                    else: zone.player_hp = max(0, zone.player_hp - 1)
                    logs.append(f"🏹 연속 사격 성공! 수비측 다음 선발 [{next_def.sub_type}] 마저 사살하고 체력을 1 깎았습니다.")
                    def_slots[0] = None
                    self.shift_slots(def_slots)
                else:
                    logs.append(f"🏹 연속 사격 실패. 수비측의 완강한 저항 [{next_def.sub_type}]에 가로막혔습니다.")

        else:
            # 수비측 승리 판정 시 보병 불굴 생존력 주사위
            if def_card.sub_type == "보병" and random.random() < 0.50:
                logs.append("🛡️ 보병 스킬 [불굴] 발동! 패배의 운명을 극복하고 체력 감소 없이 1선발 자리를 지켜냅니다.")
            else:
                logs.append("🛡️ 수비측 방어 성공! 공격 카드는 소모되었으며 필드 방어선의 변화는 없습니다.")

        self.check_zone_capture(zone_id)
        return logs

    def resolve_combat_logic(self, atk: Card, def_card: Card) -> str:
        """단일 카드 대 카드의 하드코어 승률 연산 사전"""
        a_sub = atk.sub_type
        d_sub = def_card.sub_type

        # 용병 저격 매칭
        if a_sub == "용병" and d_sub == "용병":
            return "DEFENDER_WIN"

        # 가위바위보 상성 100% 확정선
        if self.MATCHUPS.get(a_sub) == d_sub:
            return "ATTACKER_WIN"
        if self.MATCHUPS.get(d_sub) == a_sub:
            return "DEFENDER_WIN"

        # 무상성 난수 계산 (용병 공격 보너스 55%, 기본 50%)
        chance = 0.55 if a_sub == "용병" else 0.50
        return "ATTACKER_WIN" if random.random() < chance else "DEFENDER_WIN"
