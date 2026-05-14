import random

KOREAN_SAMPLE_SIZE = 6
KOREAN_MIN_MESSAGES = 6
KOREAN_FIXED_SEED = "irb_fixed_korean_6_sessions_v2_min6messages"


def session_num_messages(session: dict) -> int:
    for key in ["messages", "conversation", "dialogue", "turns"]:
        value = session.get(key)

        if isinstance(value, list):
            return len(value)

        if isinstance(value, str):
            return (
                value.count("Client")
                + value.count("Counselor")
                + value.count("Therapist")
            )

    return 0


def select_fixed_korean_sessions(sessions: list[dict]) -> list[dict]:
    eligible_sessions = [
        s for s in sessions
        if session_num_messages(s) >= KOREAN_MIN_MESSAGES
    ]

    if len(eligible_sessions) >= KOREAN_SAMPLE_SIZE:
        sessions = eligible_sessions

    rng = random.Random(KOREAN_FIXED_SEED)

    if len(sessions) > KOREAN_SAMPLE_SIZE:
        sessions = rng.sample(sessions, KOREAN_SAMPLE_SIZE)

    return sorted(sessions, key=lambda x: str(x.get("session_id", "")))