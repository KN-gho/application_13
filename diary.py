import streamlit as st
import sqlite3
import datetime
import calendar

# ページ設定
st.set_page_config(page_title="1行日記", page_icon="📖")

# データベースファイルのパス
DB_FILE = "diary.db"

def init_database():
    """データベースを初期化"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_diary(date, content):
    """日記をデータベースに保存"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO diary (date, content) VALUES (?, ?)",
        (date, content)
    )
    conn.commit()
    conn.close()

def get_diary_by_date(date):
    """指定日付の日記を取得"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM diary WHERE date = ?", (date,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_diary(date, content):
    """日記を更新"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE diary SET content = ?, created_at = CURRENT_TIMESTAMP WHERE date = ?",
        (content, date)
    )
    conn.commit()
    conn.close()

def delete_diary(date):
    """日記を削除"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diary WHERE date = ?", (date,))
    conn.commit()
    conn.close()

def get_recent_diary(limit=5):
    """最近の日記を取得（日付降順）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, content FROM diary ORDER BY date DESC LIMIT ?",
        (limit,)
    )
    entries = cursor.fetchall()
    conn.close()
    return entries

def get_diary_by_month(year, month):
    """指定月の日記を全て取得"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, content FROM diary WHERE date LIKE ? ORDER BY date",
        (f"{year}年{month:02d}月%",)
    )
    entries = cursor.fetchall()
    conn.close()
    return {date: content for date, content in entries}

# データベース初期化
init_database()

# タイトル
st.title("📖 1行日記")

# サイドバーで日記入力
st.sidebar.header("📝 日記を書く")

# 日付選択
selected_date = st.sidebar.date_input("日付を選択してください", value=datetime.date.today())
date_str = selected_date.strftime("%Y年%m月%d日")

# 既存の日記をチェック
existing_diary = get_diary_by_date(date_str)

# 既存の日記がある場合の表示
if existing_diary:
    st.sidebar.warning(f"📝 {date_str}の日記は既に存在します")
    st.sidebar.info(f"既存の日記: {existing_diary}")

# 日記入力
diary_text = st.sidebar.text_area(
    f"{date_str}の1行日記：",
    value=existing_diary if existing_diary else "",
    placeholder="その日にあった出来事を1行で書いてください",
    height=100
)

# 保存ボタン
if st.sidebar.button("保存"):
    if diary_text:
        if existing_diary:
            # 同じ日付の日記が存在する場合
            if diary_text != existing_diary:
                # 内容が変更されている場合のみ確認
                if st.session_state.get('confirm_update', False):
                    update_diary(date_str, diary_text)
                    st.sidebar.success("✅ 日記が更新されました！")
                    st.session_state.confirm_update = False
                else:
                    st.session_state.confirm_update = True
                    st.rerun()
            else:
                st.sidebar.info("📝 内容に変更がありません")
        else:
            # 新規作成
            save_diary(date_str, diary_text)
            st.sidebar.success("✅ 日記が保存されました！")
    else:
        st.sidebar.error("日記を入力してください")

# 確認メッセージの表示
if st.session_state.get('confirm_update', False):
    st.sidebar.warning("⚠️ 既存の日記を上書きしますか？")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("✅ 上書きする"):
            update_diary(date_str, diary_text)
            st.sidebar.success("✅ 日記が更新されました！")
            st.session_state.confirm_update = False
            st.rerun()
    with col2:
        if st.button("❌ やめる"):
            st.session_state.confirm_update = False
            st.rerun()

# 過去の日記を表示（メインエリア）
st.subheader("📚 過去の日記 - カレンダー表示")

# 年月選択
col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("年", range(2020, 2030), index=datetime.date.today().year - 2020)
with col2:
    selected_month = st.selectbox("月", range(1, 13), index=datetime.date.today().month - 1)

# その月の日記データを取得
diary_data = get_diary_by_month(selected_year, selected_month)

# カレンダー表示
cal = calendar.monthcalendar(selected_year, selected_month)
weekdays = ["月", "火", "水", "木", "金", "土", "日"]

# ヘッダー（曜日）
cols = st.columns(7)
for i, weekday in enumerate(weekdays):
    cols[i].markdown(f"**{weekday}**")

# カレンダーの各週
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            # 空のセル
            cols[i].markdown("　")
        else:
            date_str = f"{selected_year}年{selected_month:02d}月{day:02d}日"
            
            if date_str in diary_data:
                # 日記がある日
                content = diary_data[date_str]
                # 内容を短縮表示
                short_content = content[:10] + "..." if len(content) > 10 else content
                
                # クリック可能なボタンとして表示
                if cols[i].button(f"📖 {day}\n{short_content}", key=f"day_{day}", help=f"{date_str}: {content}"):
                    # 削除確認
                    st.session_state[f'show_diary_{day}'] = True
                    st.rerun()
                
                # 詳細表示・削除ダイアログ
                if st.session_state.get(f'show_diary_{day}', False):
                    with st.expander(f"{date_str}の日記", expanded=True):
                        st.write(f"**内容**: {content}")
                        
                        col_edit, col_delete, col_close = st.columns(3)
                        with col_edit:
                            if st.button("✏️ 編集", key=f"edit_{day}"):
                                # サイドバーの日付を設定して編集モードに
                                st.session_state['edit_date'] = datetime.datetime.strptime(date_str, "%Y年%m月%d日").date()
                                st.session_state[f'show_diary_{day}'] = False
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️ 削除", key=f"delete_{day}"):
                                st.session_state[f'confirm_delete_{day}'] = True
                                st.rerun()
                        
                        with col_close:
                            if st.button("❌ 閉じる", key=f"close_{day}"):
                                st.session_state[f'show_diary_{day}'] = False
                                st.rerun()
                        
                        # 削除確認
                        if st.session_state.get(f'confirm_delete_{day}', False):
                            st.warning("⚠️ この日記を削除しますか？")
                            col_yes, col_no = st.columns(2)
                            
                            with col_yes:
                                if st.button("✅ 削除する", key=f"confirm_yes_{day}"):
                                    delete_diary(date_str)
                                    st.success("✅ 日記が削除されました！")
                                    st.session_state[f'confirm_delete_{day}'] = False
                                    st.session_state[f'show_diary_{day}'] = False
                                    st.rerun()
                            
                            with col_no:
                                if st.button("❌ やめる", key=f"confirm_no_{day}"):
                                    st.session_state[f'confirm_delete_{day}'] = False
                                    st.rerun()
            else:
                # 日記がない日
                cols[i].markdown(f"**{day}**\n　")

# サイドバーの日付入力を編集モードで更新
if 'edit_date' in st.session_state:
    # JavaScriptを使って日付入力を更新（実際にはst.rerunで画面更新）
    st.sidebar.info("👆 選択した日付の日記を編集できます")
    del st.session_state['edit_date']