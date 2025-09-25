from __future__ import annotations
import streamlit as st
import sqlite3
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ===== 色分け関数 =====
def pressure_color(score_ratio: float) -> str:
    if score_ratio >= 0.85:
        return "red"
    elif score_ratio >= 0.60:
        return "orange"
    elif score_ratio >= 0.40:
        return "yellow"
    else:
        return "white"

# ===== ドーナツ描画関数 =====
def donut_chart(score_ratio: float, title: str):
    score_pct = min(round(score_ratio * 100, 1), 100)
    color = pressure_color(score_ratio)

    fig = go.Figure(go.Pie(
        values=[score_pct, 100 - score_pct],
        hole=0.7,
        textinfo='none',
        marker_colors=[color, "#eee"]
    ))

    fig.add_annotation(
        text=f"{round(score_ratio * 100, 1)}%",
        x=0.5, y=0.5,
        font=dict(size=24, color="black"),
        showarrow=False
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        title=dict(text=title, x=0.5, xanchor="center")
    )
    return fig

# ===== 日次スコア計算 =====
def get_daily_score(conn, user_id):
    cur = conn.cursor()
    # 起床・就寝時間
    cur.execute("SELECT weekday_wake_time, weekday_sleep_time FROM user_settings WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return 0.0

    wake, sleep = row
    wake_dt = datetime.strptime(wake, "%H:%M:%S")
    sleep_dt = datetime.strptime(sleep, "%H:%M:%S")
    disposable_hours = (sleep_dt - wake_dt).seconds / 3600

    # タスク（progress_time を差し引いた残り時間で計算）
    today = datetime.now().date()
    cur.execute("""
        SELECT deadline, estimated_time, progress_time 
        FROM tasks
        WHERE user_id=? AND completed=0
    """, (user_id,))
    tasks = cur.fetchall()

    weighted_time = 0
    for d, est, prog in tasks:
        remaining = max(0, (est or 0) - (prog or 0))
        if datetime.strptime(d, "%Y-%m-%d").date() == today:
            weighted_time += remaining
        elif datetime.strptime(d, "%Y-%m-%d").date() > today:
            weighted_time += remaining * 0.5

    score = weighted_time / (disposable_hours * 60) if disposable_hours > 0 else 0.0
    return score

# ===== 週次スコア計算 =====
def get_weekly_score(conn, user_id):
    cur = conn.cursor()
    today = datetime.now().date()
    days_left = 6 - today.weekday()
    end_date = today + timedelta(days=days_left)

    # 起床・就寝時間
    cur.execute("SELECT weekday_wake_time, weekday_sleep_time FROM user_settings WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return 0.0

    wake, sleep = row
    wake_dt = datetime.strptime(wake, "%H:%M:%S")
    sleep_dt = datetime.strptime(sleep, "%H:%M:%S")
    daily_hours = (sleep_dt - wake_dt).seconds / 3600
    weekly_disposable = daily_hours * (days_left + 1)

    # タスク（progress_time を差し引いた残り時間で計算）
    cur.execute("""
        SELECT deadline, estimated_time, progress_time 
        FROM tasks
        WHERE user_id=? AND completed=0
    """, (user_id,))
    tasks = cur.fetchall()

    weighted_time = 0
    for d, est, prog in tasks:
        remaining = max(0, (est or 0) - (prog or 0))
        dl = datetime.strptime(d, "%Y-%m-%d").date()
        if dl <= end_date:
            weighted_time += remaining
        else:
            weighted_time += remaining * 0.5

    score = weighted_time / (weekly_disposable * 60) if weekly_disposable > 0 else 0.0
    return score





# ===== テスト実行用UI =====
def main():
    conn = sqlite3.connect("time_household.db")
    user_id = 1  # 仮固定

    st.header("圧力スコアテスト")

    if st.button("サンプルデータ追加"):
        conn.execute("DELETE FROM user_settings WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM tasks WHERE user_id=?", (user_id,))

        conn.execute("""
        INSERT INTO user_settings (
            user_id,
            weekday_wake_time, weekday_sleep_time,
            weekend_wake_time, weekend_sleep_time,
            weekday_work_start, weekday_work_end
        ) VALUES (
            1,
            '07:00:00','23:00:00',
            '08:00:00','23:30:00',
            '09:00:00','18:00:00'
        )
        """)

        conn.execute("""
        INSERT INTO tasks (
            user_id, title, category, content, deadline,
            priority, estimated_time, progress_time,
            progress_sessions, completed, created_at
        ) VALUES
        (1, 'レポート作成', 'task', 'MBAのレポート', DATE('now'),
         'high', 120, 30, 0, 0, DATE('now')),
        (1, '資料チェック', 'task', '来週の会議資料', DATE('now','+1 day'),
         'medium', 60, 0, 0, 0, DATE('now'))
        """)
        conn.commit()
        st.success("サンプルデータを追加しました！")

    today_score = get_daily_score(conn, user_id)
    weekly_score = get_weekly_score(conn, user_id)

    st.plotly_chart(donut_chart(today_score, "今日の圧力スコア"), use_container_width=True)
    st.plotly_chart(donut_chart(weekly_score, "今週の圧力スコア（予測）"), use_container_width=True)

    conn.close()

if __name__ == "__main__":
    main()
