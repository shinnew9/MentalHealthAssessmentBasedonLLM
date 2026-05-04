import streamlit as st
from pathlib import Path

from core_ui.layout import set_base_page_config, inject_base_css, render_app_header, render_top_right_signout
from core.logs_assess import (
    read_assess_rows, # assess_sessions.csv 읽는 함수
    rated_session_ids,
    compute_progress, # done/total 계산
    last_culture_for_rater,
)
from core_ui.dataset import get_sessions_for_culture, DATASET_FILES # 데이터 로더 + 파일맵


# - last_culture_for_rater(rows, rater_id) : rater_id 기준 가장 마지막 culture 추론
# - _go_assess(culture, start_mode)        : culture 세팅 후 02_Assess로 이동
# - _reset_culture_state()                : lock 해제 및 관련 state reset

# Fallback implementations
def last_culture_for_rater(rows, rater_id: str):
    """rows (list[dict])에서 해당 rater_id의 가장 최근 row의 culture를 반환"""
    rater_id = (rater_id or "").strip()
    if not rater_id:
        return None
    # timestamp_utc 기준 정렬이 제일 좋지만, rows가 append 순서라면 뒤에서부터 찾는 게 안전
    for r in reversed(rows):
        if (r.get("rater_id", "").strip() == rater_id):
            c = (r.get("culture", "") or "").strip()
            return c or None
    return None


def _reset_culture_state():
    for k in ["culture", "selected_culture_lock", "session_idx", "korean_model_type", "sampled_sessions"]:
        st.session_state.pop(k, None)


def _go_assess(culture: str, start_mode: str = "resume", model_type: str | None = None):
    st.session_state["culture"] = culture
    st.session_state["selected_culture_lock"] = culture

    if culture == "Korean" and model_type:
        st.session_state["korean_model_type"] = model_type

    # cache reset
    for k in list(st.session_state.keys()):
        if k.startswith("_sessions_cache") or k.startswith("_korean_sampled_sessions"):
            st.session_state.pop(k, None)

    if start_mode == "start":
        st.session_state["session_idx"] = 0
        st.session_state["start_mode"] = "start"
    else:
        st.session_state["start_mode"] = "resume"

    st.switch_page("pages/02_Assess.py")



# Page
set_base_page_config()
inject_base_css()

def require_signed_in():
    if not st.session_state.get("email"):
        st.warning("Please sign in first.")
        st.switch_page("Home.py")


def main():
    require_signed_in()
    render_app_header()
    render_top_right_signout(key="signout_dataset")

    st.markdown("## Dataset")
    st.caption("Select a dataset. You can resume from the next unrated session based on assess_sessions.csv.")

    rater_id = (st.session_state.get("rater_id") or "").strip()
    if not rater_id:
        st.warning("Rater ID is missing. Please sign in again.")
        st.switch_page("Home.py")

    # Load rows
    rows = read_assess_rows()  # list[dict]

    # 내 row만 필터
    rows_me = [r for r in rows if (r.get("rater_id", "").strip() == rater_id)]

    # lock 결정
    # 1) session_state에 lock 있으면 그걸 사용
    # 2) 없으면 rows_me에서 마지막 culture 추론해서 lock으로 설정
    # if not st.session_state.get("selected_culture_lock"):
    #     inferred = last_culture_for_rater(rows, rater_id=rater_id)
    #     if inferred:
    #         st.session_state["selected_culture_lock"] = inferred

    lock = st.session_state.get("selected_culture_lock")

    # First-time vs Resume-mode
    is_first_time = (len(rows_me) == 0 and not lock)

    # Mode banner / unlock 
    if not is_first_time and lock:
        st.info(f"Current dataset locked to: **{lock}** (based on your last activity).")

        # 여기 key 꼭 필요 (중복 방지)
        if st.button("Change dataset (unlock)", key="unlock_dataset_btn", use_container_width=False):
            _reset_culture_state()
            st.toast("Unlocked. Choose a dataset again.", icon="🔓")
            st.rerun()

    st.markdown("---")

    # 보여줄 cultures 결정
    if is_first_time:
        # 첫 방문: 선택만 하게 (진행률/Resume 숨김)
        cultures = ["Chinese", "Hispanic", "African American", "Korean"]
    else:
        # Resume: lock된 것만 보여주기 (없으면 3개 보여줌)
        cultures = [lock] if lock else ["Chinese", "Hispanic", "African American", "Korean"]

    cols = st.columns(len(cultures))

    for i, culture in enumerate(cultures):
        with cols[i]:
            st.markdown(f"### {culture}")

            # 데이터 구성되어있는지 확인
            ds_path = DATASET_FILES.get(culture)
            if not ds_path:
                st.caption("Not configured")
                st.button("Not available", disabled=True, key=f"na_{culture}", use_container_width=True)
                continue

            sessions = get_sessions_for_culture(culture)
            total = len(sessions)

            done, _ = compute_progress(total, rows, rater_id=rater_id, culture=culture)
            frac = 0 if total == 0 else (done / total)

            if not is_first_time:
                st.progress(frac)
                st.caption(f"Progress: {done}/{total}")
            else:
                st.caption("Ready to start")

            # Buttons
            model_type = None
            if culture == "Korean":
                model_type = st.radio(
                    "Select Korean model output",
                    ["Base Gemini", "Fine-tuned Gemini"],
                    key="korean_model_type_radio",
                )

            if is_first_time:
                # First time: Select only
                if st.button("Select", key=f"select_{culture}", use_container_width=True):
                    _go_assess(culture, start_mode="start", model_type=model_type)
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Resume", key=f"resume_{culture}", use_container_width=True):
                        _go_assess(culture, start_mode="resume", model_type=model_type)
                with b2:
                    if st.button("Start from 1", key=f"start_{culture}", use_container_width=True):
                        _go_assess(culture, start_mode="start", model_type=model_type)


    st.markdown("---")
    if is_first_time:
        st.info("Tip: Choose your dataset first. After you save your first rating, you'll get a Resume button next time.")
    else:
        st.info("Tip: Use **Resume** to continue from the next unrated session automatically.")


if __name__ == "__main__":
    main()
