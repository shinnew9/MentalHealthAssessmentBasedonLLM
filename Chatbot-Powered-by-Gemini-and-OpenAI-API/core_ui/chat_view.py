import streamlit as st

# CULTURE_BADGES = {
#     "Chinese": "🀄",
#     "Hispanic": "🪇",
#     "African American": "🎤",
#     "Others": "🌍",
# }


def _inject_chat_css():
    st.markdown(
        """
        <style>
        .chat-wrap { display: flex; flex-direction: column; gap: 10px; }

        .msg-row { display: flex; width: 100%; }
        .msg-row.left  { justify-content: flex-start; }
        .msg-row.right { justify-content: flex-end; }

        .bubble {
            max-width: min(750px, 75%);
            padding: 10px 12px;
            border-radius: 16px;
            line-height: 1.35;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.06);
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .bubble.left  { border-top-left-radius: 8px; }
        .bubble.right { border-top-right-radius: 8px; }

        .meta {
            font-size: 12px;
            opacity: 0.70;
            margin-bottom: 4px;
            display:flex;
            gap:6px;
            align-items:center;
        }
        .meta .tag {
            font-weight: 700;
            opacity: 0.85;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_chat(turns, culture=None):
    import html
    import streamlit as st

    for t in turns:
        speaker = t.get("speaker", "client")
        raw_text = str(t.get("text", "")).strip()
        text = html.escape(raw_text).replace("\n", "<br>")

        is_client = speaker == "client"
        label = "Client" if is_client else "Counselor"
        justify = "flex-start" if is_client else "flex-end"

        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: {justify};
                width: 100%;
                margin: 12px 0;
            ">
                <div style="
                    display: inline-block;
                    width: fit-content;
                    max-width: 68%;
                    min-width: 0;
                    height: auto;
                    padding: 12px 14px;
                    border-radius: 14px;
                    background: #20242c;
                    color: #f2f2f2;
                    line-height: 1.5;
                    text-align: left;
                    white-space: normal;
                    word-break: keep-all;
                    overflow-wrap: anywhere;
                ">
                    <div style="
                        font-size: 0.72rem;
                        font-weight: 700;
                        opacity: 0.65;
                        margin-bottom: 8px;
                    ">
                        {label}
                    </div>
                    <div style="font-size: 0.95rem;">
                        {text}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )