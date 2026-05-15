import random

KOREAN_SAMPLE_SIZE = 6
KOREAN_MIN_MESSAGES = 6
KOREAN_FIXED_SEED = "irb_fixed_korean_6_sessions_v2_min6messages"


KOREAN_FIXED_SESSION_IDS = {
    "000727",
    "000466",
    "000908",
    "000526",
    "000693",
    "000932",
}


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
    session_id_order = {sid: i for i, sid in enumerate(KOREAN_FIXED_SESSION_IDS)}

    selected = [
        s for s in sessions
        if str(s.get("session_id", "")).strip() in session_id_order
    ]

    selected = sorted(
        selected,
        key=lambda s: session_id_order.get(str(s.get("session_id", "")).strip(), 999)
    )

    return selected