# I acknowledge the use of ChatGPT (OpenAI, GPT-5) to co-create this file.

from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

Bit = int  # 0 or 1


class NGramPredictor:
    """
    Adaptive n-gram predictor over a binary stream.
    Learns P(next_bit | last n bits) with backoff to shorter histories.
    """
    def __init__(self, n: int = 2):
        if n < 1:
            raise ValueError("n must be >= 1")
        self.n = n
        # maps context tuple -> Counter({0: count, 1: count})
        self.counts: Dict[Tuple[Bit, ...], Counter] = defaultdict(Counter)
        self.global_counts = Counter()

    def update(self, history: List[Bit], next_bit: Bit) -> None:
        ctx = tuple(history[-self.n:]) if len(history) >= self.n else tuple(history)
        self.counts[ctx][next_bit] += 1
        # also update all backoff contexts for faster learning
        for k in range(len(ctx)):
            sub = ctx[k+1:]
            self.counts[sub][next_bit] += 1
        self.global_counts[next_bit] += 1

    def predict(self, history: List[Bit]) -> Bit:
        # try longest context, back off to empty
        for k in range(min(self.n, len(history)), -1, -1):
            ctx = tuple(history[-k:]) if k > 0 else tuple()
            c = self.counts.get(ctx)
            if c and (c[0] != c[1]):
                return 0 if c[0] > c[1] else 1
        # tie or no data: use global skew if available, else default 0
        if self.global_counts and (self.global_counts[0] != self.global_counts[1]):
            return 0 if self.global_counts[0] > self.global_counts[1] else 1
        return 0


@dataclass
class TurnResult:
    round_no: int
    ai_prediction: Bit
    player_bit: Bit
    correct: bool
    player_score: int
    ai_score: int

    def as_dict(self):
        return asdict(self)


class GameEngine:
    """
    Predictor Duel: player selects 0/1 each turn; AI tries to anticipate.
    Scoring: player +1 if AI is wrong; AI +1 if AI is right.
    """
    def __init__(self, rounds: int = 50, n: int = 2):
        if rounds < 1:
            raise ValueError("rounds must be >= 1")
        self.rounds = rounds
        self.predictor = NGramPredictor(n=n)
        self.reset()

    def reset(self) -> None:
        self.history: List[Bit] = []
        self.player_score = 0
        self.ai_score = 0
        self.round_no = 0
        self.log: List[TurnResult] = []

    def remaining(self) -> int:
        return self.rounds - self.round_no

    def is_finished(self) -> bool:
        return self.round_no >= self.rounds

    def turn(self, player_bit: Bit) -> TurnResult:
        if player_bit not in (0, 1):
            raise ValueError("player_bit must be 0 or 1")
        if self.is_finished():
            raise RuntimeError("game already finished")

        ai_pred = self.predictor.predict(self.history)
        correct = (ai_pred == player_bit)
        if correct:
            self.ai_score += 1
        else:
            self.player_score += 1

        self.predictor.update(self.history, player_bit)
        self.history.append(player_bit)
        self.round_no += 1

        result = TurnResult(
            round_no=self.round_no,
            ai_prediction=ai_pred,
            player_bit=player_bit,
            correct=correct,
            player_score=self.player_score,
            ai_score=self.ai_score,
        )
        self.log.append(result)
        return result

    def summary(self) -> Dict[str, int]:
        return {
            "rounds": self.rounds,
            "played": self.round_no,
            "player_score": self.player_score,
            "ai_score": self.ai_score,
        }

    def export_csv(self, path: str) -> None:
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "round_no", "ai_prediction", "player_bit",
                "correct", "player_score", "ai_score"
            ])
            w.writeheader()
            for r in self.log:
                w.writerow(r.as_dict())
