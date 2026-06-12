import random
from dataclasses import dataclass, field
from typing import List, Optional

# --- 1. 기본 카드 및 상태 구조 정의 ---
class CardType:
    UNIT = "UNIT"
    ITEM = "ITEM"

@dataclass
class Card:
    name: str
    card_type: str
    sub_type: str  # 보병, 창병, 공격형, 수비형 등
    skill_name: Optional[str] = None

@dataclass
class Zone:
    name: str
    max_hp: int
    player_hp: int
    ai_hp: int
    # 1선발, 2선발, 3선발 구조 (인덱스 0이 1선발)
    player_slots: List[Optional[Card]] = field(default_factory=lambda: [None, None, None])
    ai_slots: List[Optional[Card]] = field(default_factory=lambda: [None, None, None])
    # 설치형 아이템 저장
    player_items: List[Card] = field(default_factory=list)
    ai_items: List[Card] = field(default_factory=list)
    is_captured: bool = False

# --- 2. 전투 및 상성 판정 핵심 로직 ---
class CombatManager:
    # 상성 사전 (Key가 Value를 이김)
    MATCHUPS = {
        "보병": "창병",
        "창병": "기병",
        "기병": "방패병",
        "방패병": "궁병",
        "궁병": "보병"
    }

    @staticmethod
    def resolve_combat(atk_card: Card, def_card: Card) -> str:
        """
        전투 결과를 판정합니다. Return: 'ATTACKER_WIN' 또는 'DEFENDER_WIN'
        """
        atk_sub = atk_card.sub_type
        def_sub = def_card.sub_type

        # 1. 용병 특수 규칙 처리
        if atk_sub == "용병" and def_sub == "용병":
            return "DEFENDER_WIN"  # 용병이 선발 용병을 치면 공격측 100% 패배

        # 2. 상성 전투 판정
        if CombatManager.MATCHUPS.get(atk_sub) == def_sub:
            return "ATTACKER_WIN"  # 상성 우위 100% 승리
        if CombatManager.MATCHUPS.get(def_sub) == atk_sub:
            return "DEFENDER_WIN"  # 상성 열위 100% 패배

        # 3. 기본 전투 판정 (상성 없음)
        # 용병은 기본 승률 55%, 그 외는 50%
        win_chance = 0.55 if atk_sub == "용병" else 0.50
        
        if random.random() < win_chance:
            return "ATTACKER_WIN"
        else:
            return "DEFENDER_WIN"

# --- 테스트 코드 ---
if __name__ == "__main__":
    # 시스템이 잘 굴러가는지 간단히 상성 확인해보기
    p_card = Card("창병 유닛", CardType.UNIT, "창병")
    ai_card = Card("기병 유닛", CardType.UNIT, "기병")
    
    # 창병이 기병을 치는 상황 (창병 <- 기병이므로 창병이 패배해야 함)
    result = CombatManager.resolve_combat(p_card, ai_card)
    print(f"전투 결과 (창병이 기병을 공격): {result}") # EXPECTED: DEFENDER_WIN
