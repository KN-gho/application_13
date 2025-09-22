from __future__ import annotations
import os, io, re, json, base64, zipfile, random
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from openai import OpenAI
from openai import RateLimitError, APIStatusError

# .env 読み込み（無ければ何もしない）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_api_key(env_key: str ="OPENAI_API_KEY") -> str | None:
    key = os.getenv(env_key)
    if key:
        return key
    try:
        return st.secrets[env_key]
    except Exception:
        return None
    
API_KEY = get_api_key()
if not API_KEY:
    st.error(
        "OpenAI APIキーが見つかりません。\n\n"
        "■ 推奨（ローカル学習向け）\n"
        "  1) .env を作成し OPENAI_API_KEY=sk-xxxx を記載\n"
        "  2) このアプリを再実行\n\n"
        "■ 参考（secrets を使う場合）\n"
        "  .streamlit/secrets.toml に OPENAI_API_KEY を記載（※リポジトリにコミットしない）\n"
        "  公式: st.secrets / secrets.toml の使い方はドキュメント参照"
    )
    st.stop()

client = OpenAI(api_key=API_KEY)

st.set_page_config(
    page_icon="🕰️",
    layout="wide"
)
st.header("タスクを登録")

#タスクを手で入力する
task = st.text_input("タスク名")

#内容を手で入力する
memo = st.text_input("メモ・内容")

#優先度をプライオリティとした
priority = st.slider("優先度",1,5,3,1)

#目安時間
duration = st.slider("目安時間(分)",0,300,60,30)


#締切日を入力
date = st.date_input("しめきり")


if "tasks" not in st.session_state:
    st.session_state["tasks"] = pd.DataFrame(columns=["タスク","カテゴリ","優先度","所要時間","締切日"])

if st.button("登録"):
    new_task = {
        "タスク": task,
        "カテゴリ": theme,
        "優先度": priority,
        "所要時間": duration,
        "締切日": date
    }
    st.session_state["tasks"] = pd.concat(
        [st.session_state["tasks"], pd.DataFrame([new_task])],
        ignore_index=True
    )
    st.success("登録しました！")