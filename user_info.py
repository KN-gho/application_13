import streamlit as st
import sqlite3
import pandas as pd

# =========================
# ページ設定
# =========================
st.set_page_config(page_title="ユーザ情報登録", page_icon="👤")

# =========================
# 定数
# =========================
DB_FILE = "user_info.db"

# 地域データ（地域名のみ表示、IDは内部で保存）
REGIONS = [
    {"title": "選択してください", "id": ""},
    {"title": "稚内", "id": "011000"}, {"title": "旭川", "id": "012010"},
    {"title": "留萌", "id": "012020"}, {"title": "網走", "id": "013010"},
    {"title": "北見", "id": "013020"}, {"title": "紋別", "id": "013030"},
    {"title": "根室", "id": "014010"}, {"title": "釧路", "id": "014020"},
    {"title": "帯広", "id": "014030"}, {"title": "室蘭", "id": "015010"},
    {"title": "浦河", "id": "015020"}, {"title": "札幌", "id": "016010"},
    {"title": "岩見沢", "id": "016020"}, {"title": "倶知安", "id": "016030"},
    {"title": "函館", "id": "017010"}, {"title": "江差", "id": "017020"},
    {"title": "青森", "id": "020010"}, {"title": "むつ", "id": "020020"},
    {"title": "八戸", "id": "020030"}, {"title": "盛岡", "id": "030010"},
    {"title": "宮古", "id": "030020"}, {"title": "大船渡", "id": "030030"},
    {"title": "仙台", "id": "040010"}, {"title": "白石", "id": "040020"},
    {"title": "秋田", "id": "050010"}, {"title": "横手", "id": "050020"},
    {"title": "山形", "id": "060010"}, {"title": "米沢", "id": "060020"},
    {"title": "酒田", "id": "060030"}, {"title": "新庄", "id": "060040"},
    {"title": "福島", "id": "070010"}, {"title": "小名浜", "id": "070020"},
    {"title": "若松", "id": "070030"}, {"title": "水戸", "id": "080010"},
    {"title": "土浦", "id": "080020"}, {"title": "宇都宮", "id": "090010"},
    {"title": "大田原", "id": "090020"}, {"title": "前橋", "id": "100010"},
    {"title": "みなかみ", "id": "100020"}, {"title": "さいたま", "id": "110010"},
    {"title": "熊谷", "id": "110020"}, {"title": "秩父", "id": "110030"},
    {"title": "千葉", "id": "120010"}, {"title": "銚子", "id": "120020"},
    {"title": "館山", "id": "120030"}, {"title": "東京", "id": "130010"},
    {"title": "大島", "id": "130020"}, {"title": "八丈島", "id": "130030"},
    {"title": "父島", "id": "130040"}, {"title": "横浜", "id": "140010"},
    {"title": "小田原", "id": "140020"}, {"title": "新潟", "id": "150010"},
    {"title": "長岡", "id": "150020"}, {"title": "高田", "id": "150030"},
    {"title": "相川", "id": "150040"}, {"title": "富山", "id": "160010"},
    {"title": "伏木", "id": "160020"}, {"title": "金沢", "id": "170010"},
    {"title": "輪島", "id": "170020"}, {"title": "福井", "id": "180010"},
    {"title": "敦賀", "id": "180020"}, {"title": "甲府", "id": "190010"},
    {"title": "河口湖", "id": "190020"}, {"title": "長野", "id": "200010"},
    {"title": "松本", "id": "200020"}, {"title": "飯田", "id": "200030"},
    {"title": "岐阜", "id": "210010"}, {"title": "高山", "id": "210020"},
    {"title": "静岡", "id": "220010"}, {"title": "網代", "id": "220020"},
    {"title": "三島", "id": "220030"}, {"title": "浜松", "id": "220040"},
    {"title": "名古屋", "id": "230010"}, {"title": "豊橋", "id": "230020"},
    {"title": "津", "id": "240010"}, {"title": "尾鷲", "id": "240020"},
    {"title": "大津", "id": "250010"}, {"title": "彦根", "id": "250020"},
    {"title": "京都", "id": "260010"}, {"title": "舞鶴", "id": "260020"},
    {"title": "大阪", "id": "270000"}, {"title": "神戸", "id": "280010"},
    {"title": "豊岡", "id": "280020"}, {"title": "奈良", "id": "290010"},
    {"title": "風屋", "id": "290020"}, {"title": "和歌山", "id": "300010"},
    {"title": "潮岬", "id": "300020"}, {"title": "鳥取", "id": "310010"},
    {"title": "米子", "id": "310020"}, {"title": "松江", "id": "320010"},
    {"title": "浜田", "id": "320020"}, {"title": "西郷", "id": "320030"},
    {"title": "岡山", "id": "330010"}, {"title": "津山", "id": "330020"},
    {"title": "広島", "id": "340010"}, {"title": "庄原", "id": "340020"},
    {"title": "下関", "id": "350010"}, {"title": "山口", "id": "350020"},
    {"title": "柳井", "id": "350030"}, {"title": "萩", "id": "350040"},
    {"title": "徳島", "id": "360010"}, {"title": "日和佐", "id": "360020"},
    {"title": "高松", "id": "370000"}, {"title": "松山", "id": "380010"},
    {"title": "新居浜", "id": "380020"}, {"title": "宇和島", "id": "380030"},
    {"title": "高知", "id": "390010"}, {"title": "室戸岬", "id": "390020"},
    {"title": "清水", "id": "390030"}, {"title": "福岡", "id": "400010"},
    {"title": "八幡", "id": "400020"}, {"title": "飯塚", "id": "400030"},
    {"title": "久留米", "id": "400040"}, {"title": "佐賀", "id": "410010"},
    {"title": "伊万里", "id": "410020"}, {"title": "長崎", "id": "420010"},
    {"title": "佐世保", "id": "420020"}, {"title": "厳原", "id": "420030"},
    {"title": "福江", "id": "420040"}, {"title": "熊本", "id": "430010"},
    {"title": "阿蘇乙姫", "id": "430020"}, {"title": "牛深", "id": "430030"},
    {"title": "人吉", "id": "430040"}, {"title": "大分", "id": "440010"},
    {"title": "中津", "id": "440020"}, {"title": "日田", "id": "440030"},
    {"title": "佐伯", "id": "440040"}, {"title": "宮崎", "id": "450010"},
    {"title": "延岡", "id": "450020"}, {"title": "都城", "id": "450030"},
    {"title": "高千穂", "id": "450040"}, {"title": "鹿児島", "id": "460010"},
    {"title": "鹿屋", "id": "460020"}, {"title": "種子島", "id": "460030"},
    {"title": "名瀬", "id": "460040"}, {"title": "那覇", "id": "471010"},
    {"title": "名護", "id": "471020"}, {"title": "久米島", "id": "471030"},
    {"title": "南大東", "id": "472000"}, {"title": "宮古島", "id": "473000"},
    {"title": "石垣島", "id": "474010"}, {"title": "与那国島", "id": "474020"}
]

# =========================
# DBユーティリティ
# =========================
def init_database():
    """DB初期化＆既存テーブルの不足カラムを自動追加（マイグレーション）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            region_id TEXT,
            region_name TEXT,
            work_hours REAL,
            commute_hours REAL,
            sleep_hours REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("PRAGMA table_info(user_info)")
    cols = {row[1] for row in cursor.fetchall()}
    if "region_id" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN region_id TEXT")
    if "region_name" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN region_name TEXT")
    if "work_hours" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN work_hours REAL")
    if "commute_hours" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN commute_hours REAL")
    if "sleep_hours" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN sleep_hours REAL")
    if "created_at" not in cols:
        cursor.execute("ALTER TABLE user_info ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    conn.commit()
    conn.close()

def get_user_by_name(name: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, region_id, region_name, work_hours, commute_hours, sleep_hours, created_at FROM user_info WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return row

def insert_user(name: str, email: str, region_id: str, region_name: str, work_hours: float, commute_hours: float, sleep_hours: float):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_info (name, email, region_id, region_name, work_hours, commute_hours, sleep_hours) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, email, region_id, region_name, work_hours, commute_hours, sleep_hours)
    )
    conn.commit()
    conn.close()

def update_user_by_name(name: str, email: str, region_id: str, region_name: str, work_hours: float, commute_hours: float, sleep_hours: float):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_info SET email = ?, region_id = ?, region_name = ?, work_hours = ?, commute_hours = ?, sleep_hours = ? WHERE name = ?",
        (email, region_id, region_name, work_hours, commute_hours, sleep_hours, name)
    )
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, region_name, work_hours, commute_hours, sleep_hours, created_at FROM user_info ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_user_by_id(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_info WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# =========================
# コールバック（チェックで選択）
# =========================
def on_select_row(row_id: int, name: str, email: str, region_name: str, work_hours: float, commute_hours: float, sleep_hours: float):
    # チェックボックスが解除された場合（現在選択中のIDと同じIDのチェックが外された）
    checkbox_key = f"cb_{row_id}"
    if checkbox_key in st.session_state and not st.session_state[checkbox_key]:
        st.session_state["selected_id"] = None
        return
    
    st.session_state["selected_id"] = int(row_id)
    # サイドバーのフォーム値を更新
    st.session_state["form_name"] = name
    st.session_state["form_email"] = email
    st.session_state["form_region"] = region_name
    st.session_state["form_work_hours"] = work_hours if work_hours else 0.0
    st.session_state["form_commute_hours"] = commute_hours if commute_hours else 0.0
    st.session_state["form_sleep_hours"] = sleep_hours if sleep_hours else 0.0

# =========================
# アプリ本体
# =========================
# DB初期化
init_database()

st.title("👤 ユーザ情報")

# ----- セッション状態の初期化 -----
for key, default in [
    ("confirm_delete_id", None),
    ("confirm_delete_name", ""),
    ("selected_id", None),
    ("form_name", ""),
    ("form_email", ""),
    ("form_region", "選択してください"),
    ("form_work_hours", 0.0),
    ("form_commute_hours", 0.0),
    ("form_sleep_hours", 0.0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ----- サイドバー：入力フォーム（選択に応じて自動反映） -----
st.sidebar.header("ユーザ情報入力")

# 選択されたユーザの情報でフォームを初期化
selected_user = None
if st.session_state["selected_id"]:
    users_list = get_all_users()
    for user in users_list:
        if user[0] == st.session_state["selected_id"]:
            selected_user = user
            break

# フォーム入力値を決定
if selected_user:
    default_name = selected_user[1]
    default_email = selected_user[2] 
    default_region = selected_user[3] if selected_user[3] else "選択してください"
    # 数値型に変換（None、空文字列、文字列の場合を考慮）
    default_work_hours = float(selected_user[4]) if selected_user[4] is not None and str(selected_user[4]).strip() != "" else 0.0
    default_commute_hours = float(selected_user[5]) if selected_user[5] is not None and str(selected_user[5]).strip() != "" else 0.0
    default_sleep_hours = float(selected_user[6]) if selected_user[6] is not None and str(selected_user[6]).strip() != "" else 0.0
else:
    default_name = ""
    default_email = ""
    default_region = "選択してください"
    default_work_hours = 0.0
    default_commute_hours = 0.0
    default_sleep_hours = 0.0

name = st.sidebar.text_input("名前", value=default_name)
email = st.sidebar.text_input("メールアドレス", value=default_email)

region_titles = [r["title"] for r in REGIONS]
idx = region_titles.index(default_region) if default_region in region_titles else 0
region_name = st.sidebar.selectbox("住まいの地域", region_titles, index=idx)
region_id = next(r["id"] for r in REGIONS if r["title"] == region_name)

# 時間入力項目を追加
work_hours = st.sidebar.number_input("勤務時間（時間）", min_value=0.0, max_value=24.0, value=default_work_hours, step=0.5)
commute_hours = st.sidebar.number_input("通勤時間（時間）", min_value=0.0, max_value=12.0, value=default_commute_hours, step=0.5)
sleep_hours = st.sidebar.number_input("睡眠時間（時間）", min_value=0.0, max_value=24.0, value=default_sleep_hours, step=0.5)

if st.sidebar.button("保存 / 更新"):
    if not name or not email:
        st.error("❌ 名前とメールアドレスは必須です")
    elif region_name == "選択してください":
        st.error("❌ 住まいの地域を選択してください")
    else:
        existing = get_user_by_name(name)
        if existing:
            update_user_by_name(name, email, region_id, region_name, work_hours, commute_hours, sleep_hours)
            st.success("✅ ユーザ情報を更新しました")
        else:
            insert_user(name, email, region_id, region_name, work_hours, commute_hours, sleep_hours)
            st.success("✅ ユーザ情報を保存しました")
        st.rerun()

# ----- 登録済みユーザ一覧（チェックボックス＋横並び＋削除確認） -----
st.subheader("📋 登録済みユーザ一覧")
users = get_all_users()

if users:
    df = pd.DataFrame(users, columns=["ID", "名前", "メールアドレス", "地域", "勤務時間", "通勤時間", "睡眠時間", "登録日時"])
    df.reset_index(drop=True, inplace=True)

    # 列幅（先頭にチェックボックス列を追加）
    widths = [1, 1.5, 2.5, 1.5, 1, 1, 1, 2, 1.5]

    # ヘッダー行
    header_cols = st.columns(widths)
    header_cols[0].markdown("**選択**")
    header_cols[1].markdown("**名前**")
    header_cols[2].markdown("**メール**")
    header_cols[3].markdown("**地域**")
    header_cols[4].markdown("**勤務時間**")
    header_cols[5].markdown("**通勤時間**")
    header_cols[6].markdown("**睡眠時間**")
    header_cols[7].markdown("**登録日時**")
    header_cols[8].markdown("**操作**")

    # データ行
    for _, row in df.iterrows():
        cols = st.columns(widths)

        # チェックボックス（選択状態は selected_id と同期）
        is_checked = st.session_state["selected_id"] == int(row["ID"])
        cols[0].checkbox(
            "",
            value=is_checked,
            key=f"cb_{row['ID']}",
            on_change=on_select_row,
            args=(int(row["ID"]), row["名前"], row["メールアドレス"], row["地域"], row["勤務時間"], row["通勤時間"], row["睡眠時間"])
        )

        cols[1].write(row["名前"])
        cols[2].write(row["メールアドレス"])
        cols[3].write(row["地域"])
        cols[4].write(f"{row['勤務時間']}h" if row["勤務時間"] else "－")
        cols[5].write(f"{row['通勤時間']}h" if row["通勤時間"] else "－")
        cols[6].write(f"{row['睡眠時間']}h" if row["睡眠時間"] else "－")
        cols[7].write(row["登録日時"])

        # 削除UI：確認ダイアログ（同一行のみ）
        if st.session_state["confirm_delete_id"] is None:
            if cols[8].button("🗑️ 削除", key=f"del_{row['ID']}"):
                st.session_state["confirm_delete_id"] = int(row["ID"])
                st.session_state["confirm_delete_name"] = row["名前"]
                st.rerun()
        else:
            if int(row["ID"]) == st.session_state["confirm_delete_id"]:
                st.warning(f"「{row['名前']}」さんの情報を削除しますか？この操作は元に戻せません。")
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("✅ はい、削除する", key=f"yes_{row['ID']}"):
                        delete_user_by_id(int(row["ID"]))
                        # 削除対象が選択中なら選択解除＆フォーム初期化
                        if st.session_state["selected_id"] == int(row["ID"]):
                            st.session_state["selected_id"] = None
                            st.session_state["form_name"] = ""
                            st.session_state["form_email"] = ""
                            st.session_state["form_region"] = "選択してください"
                            st.session_state["form_work_hours"] = 0.0
                            st.session_state["form_commute_hours"] = 0.0
                            st.session_state["form_sleep_hours"] = 0.0
                        st.session_state["confirm_delete_id"] = None
                        st.session_state["confirm_delete_name"] = ""
                        st.success("✅ 削除しました。")
                        st.rerun()
                with c2:
                    if st.button("❎ キャンセル", key=f"no_{row['ID']}"):
                        st.session_state["confirm_delete_id"] = None
                        st.session_state["confirm_delete_name"] = ""
                        st.info("削除をキャンセルしました。")
                        st.rerun()
            else:
                cols[8].write("—")
else:
    st.info("まだユーザ情報は登録されていません。")
