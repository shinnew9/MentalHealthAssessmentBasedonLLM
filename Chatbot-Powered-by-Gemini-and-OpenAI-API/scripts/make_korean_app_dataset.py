import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EN_TEST = ROOT / "data" / "korean" / "test_heldout_15.json"
KO_TEST = ROOT / "data" / "korean" / "korean_translated_15.json"

BASE_OUTPUT = ROOT / "data" / "korean" / "korean_base_outputs_15.json"
FT_OUTPUT = ROOT / "data" / "korean" / "korean_finetuned_outputs_15.json"

BASE_APP_OUT = ROOT / "data" / "korean" / "korean_base_app_15.json"
FT_APP_OUT = ROOT / "data" / "korean" / "korean_finetuned_app_15.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def role_to_speaker(role):
    role = str(role).lower()
    if role == "seeker":
        return "client"
    return "counselor"


def build_app_dataset(model_outputs, en_rows, ko_rows):
    en_map = {str(x.get("dialog_id")): x for x in en_rows}
    ko_map = {str(x.get("dialog_id")): x for x in ko_rows}

    app_rows = []

    for out in model_outputs:
        did = str(out.get("dialog_id"))
        en = en_map.get(did)
        ko = ko_map.get(did)

        if not en or not ko:
            print(f"[WARN] missing match for dialog_id={did}")
            continue

        en_dialog = en.get("dialog", [])
        ko_dialog = ko.get("dialog", [])

        turns = []

        for en_turn, ko_turn in zip(en_dialog, ko_dialog):
            speaker = role_to_speaker(ko_turn.get("speaker", ""))

            ko_text = str(ko_turn.get("content", "")).strip()
            en_text = str(en_turn.get("content", "")).strip()

            if not ko_text and not en_text:
                continue

            turns.append({
                "speaker": speaker,
                "text": f"{ko_text}\n\nEN: {en_text}",
                "text_ko": ko_text,
                "text_en": en_text,
            })

        prediction_ko = str(out.get("prediction", "")).strip()
        reference_ko = str(ko.get("held_out_last_turn", {}).get("content", "")).strip()
        reference_en = str(en.get("held_out_last_turn", {}).get("content", "")).strip()

        if prediction_ko:
            turns.append({
                "speaker": "counselor",
                "text": f"{prediction_ko}\n\nEN reference: {reference_en}",
                "text_ko": prediction_ko,
                "text_en": reference_en,
                "is_model_output": True,
                "reference_ko": reference_ko,
            })

        app_rows.append({
            "session_id": did,
            "dialog_id": did,
            "topic": ko.get("topic", ""),
            "psychotherapy": ko.get("psychotherapy", ""),
            "theme": ko.get("theme", ""),
            "turns": turns,
            "reference_ko": reference_ko,
            "reference_en": reference_en,
        })

    return app_rows


def main():
    en_rows = load_json(EN_TEST)
    ko_rows = load_json(KO_TEST)

    base_outputs = load_json(BASE_OUTPUT)
    ft_outputs = load_json(FT_OUTPUT)

    BASE_APP_OUT.parent.mkdir(parents=True, exist_ok=True)

    base_app = build_app_dataset(base_outputs, en_rows, ko_rows)
    ft_app = build_app_dataset(ft_outputs, en_rows, ko_rows)

    with open(BASE_APP_OUT, "w", encoding="utf-8") as f:
        json.dump(base_app, f, ensure_ascii=False, indent=2)

    with open(FT_APP_OUT, "w", encoding="utf-8") as f:
        json.dump(ft_app, f, ensure_ascii=False, indent=2)

    print(f"Saved: {BASE_APP_OUT} ({len(base_app)} sessions)")
    print(f"Saved: {FT_APP_OUT} ({len(ft_app)} sessions)")


if __name__ == "__main__":
    main()