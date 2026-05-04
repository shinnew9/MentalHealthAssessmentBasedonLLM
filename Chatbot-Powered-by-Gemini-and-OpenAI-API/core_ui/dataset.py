import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

DATASET_FILES = {
    "Chinese": ROOT / "data" / "psydial4" / "student_only_100.jsonl",
    "Hispanic": ROOT / "data" / "psydial4" / "student_only_rewrite_hispanic_college_grad_100.jsonl",
    "African American": ROOT / "data" / "psydial4" / "student_only_rewrite_african_american_college_grad_100.jsonl",
    "Korean": {
        "Base Gemini": ROOT / "data" / "korean" / "korean_base_outputs_15.json",
        "Fine-tuned Gemini": ROOT / "data" / "korean" / "korean_finetuned_outputs_15.json",
    },
    "Others": None,
}


def load_json(path: Path):
    if not path or not path.exists():
        st.error(f"Dataset file not found: {path}")
        st.stop()

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path):
    if not path or not path.exists():
        st.error(f"Dataset file not found: {path}")
        st.stop()

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_session_psydial(raw: dict):
    sid = str(raw.get("session_id", raw.get("id", "unknown")))
    turns = raw.get("turns", [])
    norm = []

    for t in turns:
        role = (t.get("role") or "").lower().strip()
        text = t.get("text") or ""

        if not text:
            continue

        if role == "system":
            continue

        if role in ["user", "client", "patient", "seeker", "human"]:
            norm.append({"speaker": "client", "text": text})
        else:
            norm.append({"speaker": "counselor", "text": text})

    return {
        "session_id": sid,
        "turns": norm,
    }


# Korean dataset is structured as a single text input, so we need logic to split it into turns based on speaker labels.
# "내담자: ... 상담사: ..." 형태로 되어 있다고 가정하고, 이를 turn으로 나누는 로직
# Assumimng that the conversation looks like "Client: ... Counselor: ..." and splitting turns based on these speaker labels. 
# If there are lines without speaker labels, we will attach them to the previous turn. 
def parse_korean_input_to_turns(input_text: str):
    turns = []

    for line in input_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("내담자") or line.startswith("Client"):
            speaker = "client"
        elif line.startswith("상담사") or line.startswith("Counselor") or line.startswith("Therapist"):
            speaker = "counselor"
        else:
            # speaker label이 없으면 이전 turn에 붙이기
            if turns:
                turns[-1]["text"] += "\n" + line
                continue
            speaker = "client"

        turns.append({
            "speaker": speaker,
            "text": line,
        })

    return turns


def parse_session_korean_output(raw: dict):
    sid = str(raw.get("dialog_id", raw.get("session_id", raw.get("id", "unknown"))))

    input_text = str(raw.get("input", "")).strip()
    prediction = str(raw.get("prediction", "")).strip()
    reference = str(raw.get("reference", "")).strip()

    turns = parse_korean_input_to_turns(input_text)

    if prediction:
        turns.append({
            "speaker": "counselor",
            "text": prediction,
        })

    return {
        "session_id": sid,
        "turns": turns,
        "reference": reference,
    }


def resolve_dataset_path(culture: str):
    ds_conf = DATASET_FILES.get(culture)

    if culture == "Korean" and isinstance(ds_conf, dict):
        model_type = st.session_state.get("korean_model_type", "Base Gemini")
        return Path(ds_conf[model_type])

    if ds_conf:
        return Path(ds_conf)

    return None


def get_sessions_for_culture(culture: str):
    path = resolve_dataset_path(culture)

    if not path:
        st.error("This dataset is not configured yet.")
        st.stop()

    if culture == "Korean":
        raw_rows = load_json(path)
        sessions = [parse_session_korean_output(r) for r in raw_rows]
    else:
        raw_rows = load_jsonl(path)
        sessions = [parse_session_psydial(r) for r in raw_rows]

    sessions = [s for s in sessions if s.get("turns")]

    if not sessions:
        st.error("No sessions found in the dataset.")
        st.stop()

    return sessions