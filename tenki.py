import streamlit as st
import sqlite3
import requests
import openai
from datetime import datetime, timedelta
import pandas as pd
import json

# ページ設定
st.set_page_config(
    page_title="天気連動スケジュール管理",
    page_icon="🌤️",
    layout="wide"
)

# データベース初期化
def init_database():
    conn = sqlite3.connect('schedule.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            event_name TEXT,
            location TEXT,
            outdoor INTEGER,
            importance INTEGER,
            changeable INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# スケジュール追加
def add_schedule(date, time, event_name, location, outdoor, importance, changeable):
    conn = sqlite3.connect('schedule.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO schedules (date, time, event_name, location, outdoor, importance, changeable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, time, event_name, location, outdoor, importance, changeable))
    conn.commit()
    conn.close()

# スケジュール取得
def get_schedules(date):
    conn = sqlite3.connect('schedule.db')
    df = pd.read_sql_query(
        'SELECT * FROM schedules WHERE date = ? ORDER BY time',
        conn, params=(date,)
    )
    conn.close()
    return df

# 全スケジュール取得
def get_all_schedules():
    conn = sqlite3.connect('schedule.db')
    df = pd.read_sql_query(
        'SELECT * FROM schedules ORDER BY date, time',
        conn
    )
    conn.close()
    return df

# スケジュール削除
def delete_schedule(schedule_id):
    conn = sqlite3.connect('schedule.db')
    c = conn.cursor()
    c.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

# 天気情報取得（天気.tsukumijima API使用）
def get_weather_forecast(city_code="130010"):  # 130010は東京のコード
    try:
        url = f"https://weather.tsukumijima.net/api/forecast/city/{city_code}"
        response = requests.get(url)
        data = response.json()
        
        forecasts = []
        today = datetime.now().date()
        
        # 今日、明日、明後日の予報を取得
        for i, forecast in enumerate(data['forecasts']):
            if i == 0:  # 今日はスキップ
                continue
            elif i <= 2:  # 明日と明後日
                forecast_date = today + timedelta(days=i)
                
                # 降水確率を取得（時間帯別の平均）
                rain_probs = []
                if forecast['chanceOfRain']:
                    for time_period, prob in forecast['chanceOfRain'].items():
                        if prob and prob != '--%':
                            prob_num = int(prob.replace('%', ''))
                            rain_probs.append(prob_num)
                
                avg_rain_prob = sum(rain_probs) / len(rain_probs) if rain_probs else 0
                
                # 気温情報
                temp_info = ""
                if forecast['temperature']['max']:
                    temp_info += f"最高{forecast['temperature']['max']['celsius']}°C"
                if forecast['temperature']['min']:
                    if temp_info:
                        temp_info += "/"
                    temp_info += f"最低{forecast['temperature']['min']['celsius']}°C"
                
                forecasts.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'date_label': forecast['dateLabel'],
                    'weather': forecast['telop'],
                    'detail': forecast['detail']['weather'] if forecast['detail'] and forecast['detail']['weather'] else forecast['telop'],
                    'temp_info': temp_info,
                    'rain_prob': avg_rain_prob,
                    'rain_by_time': forecast['chanceOfRain'],
                    'rain': avg_rain_prob >= 50 or '雨' in forecast['telop'],
                    'image_url': forecast['image']['url']
                })
        
        return forecasts
    except Exception as e:
        st.error(f"天気情報の取得に失敗しました: {e}")
        return []

# ChatGPT APIでアドバイス生成
def generate_schedule_advice(schedules, weather_info, api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # プロンプト作成
        schedule_text = ""
        for _, schedule in schedules.iterrows():
            outdoor_text = "屋外" if schedule['outdoor'] else "屋内"
            importance_text = f"重要度{schedule['importance']}/5"
            changeable_text = "変更可能" if schedule['changeable'] else "変更不可"
            schedule_text += f"- {schedule['time']} {schedule['event_name']} ({schedule['location']}, {outdoor_text}, {importance_text}, {changeable_text})\n"
        
        weather_text = ""
        for weather in weather_info:
            rain_status = "雨予報" if weather['rain'] else "晴れ予報"
            weather_text += f"{weather['date']} ({weather['date_label']}): {weather['weather']} - {rain_status}\n"
            if weather['rain_by_time']:
                weather_text += "  時間帯別降水確率: "
                time_probs = []
                for time_period, prob in weather['rain_by_time'].items():
                    if prob and prob != '--%':
                        period_name = {
                            'T00_06': '00-06時',
                            'T06_12': '06-12時', 
                            'T12_18': '12-18時',
                            'T18_24': '18-24時'
                        }.get(time_period, time_period)
                        time_probs.append(f"{period_name}:{prob}")
                weather_text += ", ".join(time_probs) + "\n"
        
        prompt = f"""
以下のスケジュールと天気予報を確認して、雨予報の日の屋外活動について具体的なアドバイスをお願いします。

【天気予報】
{weather_text}

【スケジュール】
{schedule_text}

【アドバイス条件】
- 雨予報（降水確率50%以上）の日の屋外活動に注目
- 変更可能なスケジュールのみ変更を提案
- 重要度も考慮して優先順位をつける
- 具体的な代替案も提示

アドバイスを簡潔にまとめてください。
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"アドバイス生成でエラーが発生しました: {e}"

# メイン アプリケーション
def main():
    st.title("🌤️ 天気連動スケジュール管理アプリ")
    
    # データベース初期化
    init_database()
    
    # サイドバーで都市設定
    st.sidebar.header("⚙️ 設定")
    
    # 都市選択
    city_options = {
        "東京": "130010",
        "大阪": "270000", 
        "名古屋": "230010",
        "福岡": "400010",
        "札幌": "016010",
        "仙台": "040010",
        "広島": "340010",
        "高松": "370000",
        "那覇": "471010"
    }
    
    selected_city = st.sidebar.selectbox("都市を選択", list(city_options.keys()), index=0)
    city_code = city_options[selected_city]
    
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📅 スケジュール追加", "📋 スケジュール一覧", "🌦️ 天気予報", "🤖 AIアドバイス"])
    
    with tab1:
        st.header("スケジュール追加")
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("日付", value=datetime.now().date())
            time = st.time_input("時間")
            event_name = st.text_input("イベント名")
            location = st.text_input("場所")
        
        with col2:
            outdoor = st.checkbox("屋外活動")
            importance = st.slider("重要度", 1, 5, 3)
            changeable = st.checkbox("変更可能", value=True)
        
        if st.button("スケジュール追加"):
            if event_name and location:
                add_schedule(
                    date.strftime('%Y-%m-%d'),
                    time.strftime('%H:%M'),
                    event_name,
                    location,
                    int(outdoor),
                    importance,
                    int(changeable)
                )
                st.success("スケジュールを追加しました！")
                st.rerun()
            else:
                st.error("イベント名と場所を入力してください。")
    
    with tab2:
        st.header("スケジュール一覧")
        
        schedules_df = get_all_schedules()
        
        if not schedules_df.empty:
            # 表示用にデータを整形
            display_df = schedules_df.copy()
            display_df['outdoor'] = display_df['outdoor'].map({1: '屋外', 0: '屋内'})
            display_df['changeable'] = display_df['changeable'].map({1: '可', 0: '不可'})
            
            st.dataframe(
                display_df[['date', 'time', 'event_name', 'location', 'outdoor', 'importance', 'changeable']],
                column_config={
                    'date': '日付',
                    'time': '時間',
                    'event_name': 'イベント名',
                    'location': '場所',
                    'outdoor': '屋内/屋外',
                    'importance': '重要度',
                    'changeable': '変更'
                },
                use_container_width=True
            )
            
            # スケジュール削除
            st.subheader("スケジュール削除")
            delete_options = [f"{row['date']} {row['time']} - {row['event_name']}" for _, row in schedules_df.iterrows()]
            selected_delete = st.selectbox("削除するスケジュールを選択", ["選択してください"] + delete_options)
            
            if selected_delete != "選択してください":
                selected_id = schedules_df.iloc[delete_options.index(selected_delete)]['id']
                if st.button("削除実行"):
                    delete_schedule(selected_id)
                    st.success("スケジュールを削除しました！")
                    st.rerun()
        else:
            st.info("スケジュールが登録されていません。")
    
    with tab3:
        st.header("天気予報")
        
        weather_forecasts = get_weather_forecast(city_code)
        
        if weather_forecasts:
            st.subheader(f"【{selected_city}】明日・明後日の天気予報")
            
            for forecast in weather_forecasts:
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        # 天気アイコン表示
                        try:
                            st.image(forecast['image_url'], width=80)
                        except:
                            st.write("🌤️")
                    
                    with col2:
                        st.write(f"**{forecast['date_label']} ({forecast['date']})**")
                        st.write(f"**{forecast['weather']}**")
                        if forecast['temp_info']:
                            st.write(f"🌡️ {forecast['temp_info']}")
                    
                    with col3:
                        if forecast['rain_by_time']:
                            st.write("**降水確率**")
                            for time_period, prob in forecast['rain_by_time'].items():
                                if prob and prob != '--%':
                                    period_name = {
                                        'T00_06': '00-06時',
                                        'T06_12': '06-12時', 
                                        'T12_18': '12-18時',
                                        'T18_24': '18-24時'
                                    }.get(time_period, time_period)
                                    st.write(f"{period_name}: {prob}")
                        
                        # 雨予報の警告
                        if forecast['rain']:
                            st.warning(f"⚠️ 雨の予報です（平均降水確率: {forecast['rain_prob']:.0f}%）")
                        else:
                            st.success("☀️ 良い天気の予報です")
                    
                    st.write("---")
        else:
            st.error("天気情報を取得できませんでした。しばらく時間をおいてからお試しください。")
    
    with tab4:
        st.header("AIスケジュールアドバイス")
        
        if openai_api_key:
            if st.button("AIアドバイスを取得"):
                with st.spinner("分析中..."):
                    # 明日・明後日のスケジュール取得
                    tomorrow = (datetime.now() + timedelta(days=1)).date()
                    day_after_tomorrow = (datetime.now() + timedelta(days=2)).date()
                    
                    tomorrow_schedules = get_schedules(tomorrow.strftime('%Y-%m-%d'))
                    day_after_schedules = get_schedules(day_after_tomorrow.strftime('%Y-%m-%d'))
                    
                    all_schedules = pd.concat([tomorrow_schedules, day_after_schedules], ignore_index=True)
                    
                    if not all_schedules.empty:
                        # 天気情報取得
                        weather_info = get_weather_forecast(city_code)
                        
                        if weather_info:
                            # AIアドバイス生成
                            advice = generate_schedule_advice(all_schedules, weather_info, openai_api_key)
                            
                            st.subheader("🤖 AIからのアドバイス")
                            st.write(advice)
                        else:
                            st.error("天気情報の取得に失敗しました。")
                    else:
                        st.info("明日・明後日のスケジュールが登録されていません。")
        else:
            st.info("AIアドバイスを利用するには、OpenAI API Keyを入力してください。")
            
            # API Key取得方法の説明
            with st.expander("API Keyの取得方法"):
                st.write("""
                **OpenAI API Key:**
                1. [OpenAI Platform](https://platform.openai.com/)にアクセス
                2. アカウント作成・ログイン
                3. API Keysセクションでキーを作成
                
                **天気API について:**
                このアプリは天気.tsukumijimaの無料APIを使用しているため、
                天気情報の取得にAPI Keyは不要です。
                """)
        
        # 天気情報のプレビュー
        st.subheader("現在の天気情報")
        preview_weather = get_weather_forecast(city_code)
        if preview_weather:
            for weather in preview_weather:
                rain_icon = "🌧️" if weather['rain'] else "☀️"
                st.write(f"{rain_icon} {weather['date_label']}: {weather['weather']} (平均降水確率: {weather['rain_prob']:.0f}%)")

if __name__ == "__main__":
    main()