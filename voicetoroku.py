from __future__ import annotations
import os, tempfile
import pandas as pd
import streamlit as st

from openai import OpenAI
from dotenv import load_dotenv
from st_audiorec import st_audiorec

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error(" OpenAI APIキーが見つかりません。.env を確認してください")
    st.stop()

client = OpenAI(api_key=API_KEY)

st.set_page_config(page_icon="🕰️", layout="wide")
st.header("タスク登録")

default_task = ""
default_memo = ""
default_priority = 3
default_duration = 60
default_date = None

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

if text:
    prompt = f"""
    次の文章を解析して、以下の形式で出力してください:
    タスク名:
    メモ・内容:
    優先度(1~5):
    目安時間(分):
    しめきり(YYYY-MM-DD):

    入力: {text}
    """
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    parsed = result.choices[0].message.content

    default_task = ""
    default_memo = ""
    default_priority = 3
    default_duration = 60
    default_date = None

    for line in parsed.split("\n"):
        if line.startswith("タスク名"):
            default_task = line.split(":",1)[1].strip()
        elif line.startswith("メモ"):
            default_memo = line.split(":",1)[1].strip()
        elif line.startswith("優先度"):
            default_priority = int(line.split(":",1)[1].strip() or 3)
        elif line.startswith("目安時間"):
            default_duration = int(line.split(":",1)[1].replace("分","").strip() or 60)
        elif line.startswith("しめきり"):
            default_date = line.split(":",1)[1].strip()

task = st.text_input("タスク名", value=default_task)
memo = st.text_input("メモ・内容", value=default_memo)
priority = st.slider("優先度", 1, 5, default_priority)
duration = st.slider("目安時間(分)", 0, 300, default_duration, 30)
date = st.date_input("しめきり", value=pd.to_datetime(default_date) if default_date else None)

if "tasks" not in st.session_state:
    st.session_state["tasks"] = pd.DataFrame(columns=["タスク","メモ","優先度","所要時間","締切日"])

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