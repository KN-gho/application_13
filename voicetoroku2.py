from __future__ import annotations
import os, tempfile
import pandas as pd
import streamlit as st

from openai import OpenAI
from dotenv import load_dotenv
from st_audiorec import st_audiorec
import datetime
import calendar, re

# ===== APIキー設定 =====
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

st.sidebar.header("APIキー設定")

if "api_key" not in st.session_state:
    st.session_state.api_key = API_KEY or ""

user_api_key = st.sidebar.text_input(
    "OpenAI APIキーを入力してください",
    type="password",
)

if user_api_key:
    st.session_state.api_key = user_api_key

API_KEY = st.session_state.api_key

if not API_KEY:
    st.error(" OpenAI APIキーが見つかりません。.env を確認してください")
    st.stop()

client = OpenAI(api_key=API_KEY)

# ===== ページ設定 =====
st.set_page_config(page_icon="🕰️", layout="wide")
st.header("タスク登録")

# ===== デフォルト値 =====
default_task = ""
default_memo = ""
default_priority = 3
default_duration = 60
default_date = None
today = datetime.date.today()

# ===== 音声入力 =====
wav_audio_data = st_audiorec()
text = None

if wav_audio_data is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(wav_audio_data)
        audio_path = tmpfile.name

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    text = transcript.text
    st.write(" 音声入力結果:", text)

# ===== 音声解析（ChatGPT） =====
if text:
    prompt = f"""
    次の文章を解析して、以下の形式で出力してください:
    タスク名:
    メモ・内容:
    優先度(1~5):
    目安時間(分):
    しめきり(YYYY-MM-DD形式。今日が{today}で「25日まで」と言われたら、必ず{today.year}-{today.month:02d}-25と出力する。過ぎていれば翌月の日付にする):

    入力: {text}
    """

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    parsed = result.choices[0].message.content

    # ===== 締切日解析関数 =====
    def parse_deadline(raw: str, today: datetime.date) -> datetime.date | None:
        s = (raw or "").strip()
        if not s:
            return None

        # 日本語の「まで」などを除去
        s = s.replace("までに", "").replace("まで", "").strip()
        if s.endswith("日"):
            s = s[:-1].strip()

        # パターン1: YYYY-MM-DD
        try:
            return datetime.date.fromisoformat(s)
        except ValueError:
            pass

        # パターン2: MM-DD
        m = re.fullmatch(r'(\d{1,2})-(\d{1,2})', s)
        if m:
            month, day = map(int, m.groups())
            last_day = calendar.monthrange(today.year, month)[1]
            return datetime.date(today.year, month, min(day, last_day))

        # パターン3: MM月DD日
        m = re.fullmatch(r'(\d{1,2})月(\d{1,2})', s)
        if m:
            month, day = map(int, m.groups())
            last_day = calendar.monthrange(today.year, month)[1]
            return datetime.date(today.year, month, min(day, last_day))

        # パターン4: DD（日にちだけ）
        if s.isdigit():
            day = int(s)
            year, month = today.year, today.month
            if day >= today.day:  # 今月
                last_day = calendar.monthrange(year, month)[1]
                return datetime.date(year, month, min(day, last_day))
            # 来月
            month += 1
            if month == 13:
                month = 1
                year += 1
            last_day = calendar.monthrange(year, month)[1]
            return datetime.date(year, month, min(day, last_day))

        return None

    # ===== 解析結果を取り込む =====
    for line in parsed.split("\n"):
        if line.startswith("タスク名"):
            default_task = line.split(":", 1)[1].strip()
        elif line.startswith("メモ"):
            default_memo = line.split(":", 1)[1].strip()
        elif line.startswith("優先度"):
            default_priority = int(line.split(":", 1)[1].strip() or 3)
        elif line.startswith("目安時間"):
            default_duration = int(line.split(":", 1)[1].replace("分", "").strip() or 60)
        elif line.startswith("しめきり"):
            raw_date = line.split(":", 1)[1].strip()
            parsed_date = parse_deadline(raw_date, today)
            if parsed_date is not None:
                default_date = parsed_date

# ===== 入力フォーム =====
task = st.text_input("タスク名", value=default_task)
memo = st.text_input("メモ・内容", value=default_memo)
priority = st.slider("優先度", 1, 5, default_priority)
duration = st.slider("目安時間(分)", 0, 300, default_duration, 30)

if default_date is None:
    default_date = today
date = st.date_input("しめきり", value=default_date)

# ===== 登録処理 =====
if "tasks" not in st.session_state:
    st.session_state["tasks"] = pd.DataFrame(columns=["タスク", "メモ", "優先度", "所要時間", "締切日"])

if st.button("登録"):
    new_task = {
        "タスク": task,
        "メモ": memo,
        "優先度": priority,
        "所要時間": duration,
        "締切日": date
    }
    st.session_state["tasks"] = pd.concat(
        [st.session_state["tasks"], pd.DataFrame([new_task])],
        ignore_index=True
    )
    st.success("✅ 登録しました")

st.dataframe(st.session_state["tasks"])
