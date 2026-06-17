from __future__ import annotations

from dataclasses import dataclass

STATE_COUNT = 5
DEFAULT_STATE_PROB = [0.70, 0.20, 0.08, 0.02, 0.00]
STATE_WEIGHTS = [0, 1, 2, 3, 4]
DEFAULT_EXPERIMENT_MASTERY_PROB = 0.5
DEFAULT_EXPERIMENT_MASTERY_SCORE = 50.0

READ_EVENT_STRENGTH = {
    "open_knowledge_point": 0.015,
    "read_text_card": 0.05,
    "video_completed": 0.08,
    "ai_explanation_read": 0.04,
    "finish_experiment": 0.10,
    "open_experiment": 0.02,
}

CORRECT_LIKELIHOOD = {
    "basic": [0.18, 0.42, 0.68, 0.84, 0.93],
    "medium": [0.10, 0.30, 0.56, 0.78, 0.91],
    "hard": [0.04, 0.18, 0.42, 0.70, 0.88],
}

CORRECT_PROMOTION = {"basic": 0.05, "medium": 0.08, "hard": 0.12}
WRONG_DEMOTION = {"basic": 0.04, "medium": 0.06, "hard": 0.08}

QUESTION_GUESS_RATE = {
    "single_choice": 0.25,
    "true_false": 0.5,
    "fill_blank": 0.1,
}
DEFAULT_SLIP_RATE = 0.1


def normalize_prob(prob: list[float]) -> list[float]:
    if len(prob) != STATE_COUNT:
        raise ValueError("state_prob must have length 5")
    clipped = [max(0.0, float(item)) for item in prob]
    total = sum(clipped)
    if total <= 0:
        return DEFAULT_STATE_PROB.copy()
    return [item / total for item in clipped]


def mastery_score(prob: list[float]) -> float:
    prob = normalize_prob(prob)
    weighted = sum(weight * p for weight, p in zip(STATE_WEIGHTS, prob))
    return round(100.0 * weighted / 4.0, 2)


def promote(prob: list[float], strength: float) -> list[float]:
    prob = normalize_prob(prob)
    result = prob.copy()
    for index in range(STATE_COUNT - 1):
        movable = result[index] * strength * (1.0 - index / 5.0)
        result[index] -= movable
        result[index + 1] += movable
    return normalize_prob(result)


def demote(prob: list[float], strength: float) -> list[float]:
    prob = normalize_prob(prob)
    result = prob.copy()
    for index in range(STATE_COUNT - 1, 0, -1):
        movable = result[index] * strength * (index / 5.0)
        result[index] -= movable
        result[index - 1] += movable
    return normalize_prob(result)


def apply_learning_event(prob: list[float], event_type: str) -> list[float]:
    strength = READ_EVENT_STRENGTH.get(event_type)
    if strength is None:
        return normalize_prob(prob)
    return promote(prob, strength)


def apply_answer_event(prob: list[float], correct: bool, difficulty: str = "basic") -> list[float]:
    difficulty = difficulty if difficulty in CORRECT_LIKELIHOOD else "basic"
    prob = normalize_prob(prob)
    likelihood = CORRECT_LIKELIHOOD[difficulty]
    if correct:
        posterior = normalize_prob([p * l for p, l in zip(prob, likelihood)])
        return promote(posterior, CORRECT_PROMOTION[difficulty])
    wrong_likelihood = [max(0.08, 1.0 - l) for l in likelihood]
    posterior = normalize_prob([p * l for p, l in zip(prob, wrong_likelihood)])
    return demote(posterior, WRONG_DEMOTION[difficulty])


def update_mastery(
    state_prob: list[float] | None,
    event_type: str,
    difficulty: str = "basic",
    correct: bool | None = None,
) -> dict[str, float | list[float]]:
    prob = normalize_prob(state_prob or DEFAULT_STATE_PROB)
    if event_type in READ_EVENT_STRENGTH:
        prob = apply_learning_event(prob, event_type)
    elif event_type in {"answer_correct", "answer_wrong"}:
        is_correct = correct if correct is not None else event_type == "answer_correct"
        prob = apply_answer_event(prob, bool(is_correct), difficulty)
    return {"state_prob": [round(item, 6) for item in prob], "mastery_score": mastery_score(prob)}


def experiment_mastery_score(probability: float | None) -> float:
    probability = DEFAULT_EXPERIMENT_MASTERY_PROB if probability is None else float(probability)
    return round(max(0.0, min(1.0, probability)) * 100.0, 2)


def update_experiment_mastery(
    mastery_prob: float | None,
    *,
    question_type: str,
    correct: bool,
) -> dict[str, float]:
    prior = DEFAULT_EXPERIMENT_MASTERY_PROB if mastery_prob is None else max(0.0, min(1.0, float(mastery_prob)))
    guess = QUESTION_GUESS_RATE.get(question_type, QUESTION_GUESS_RATE["single_choice"])
    slip = DEFAULT_SLIP_RATE
    if correct:
        numerator = prior * (1.0 - slip)
        denominator = numerator + (1.0 - prior) * guess
    else:
        numerator = prior * slip
        denominator = numerator + (1.0 - prior) * (1.0 - guess)
    posterior = prior if denominator <= 0 else numerator / denominator
    posterior = round(max(0.0, min(1.0, posterior)), 6)
    return {"mastery_prob": posterior, "mastery_score": experiment_mastery_score(posterior)}


@dataclass(frozen=True)
class MasterySnapshot:
    state_prob: list[float]
    mastery_score: float

    @classmethod
    def initial(cls) -> "MasterySnapshot":
        prob = DEFAULT_STATE_PROB.copy()
        return cls(prob, mastery_score(prob))
