import streamlit as st

# ログイン状態の確認
if not st.user.is_logged_in:
    st.title("ログイン画面")
    if st.button("Googleアカウントでログイン", icon=":material/login:"):
        st.login()
    st.stop()

# ログアウトボタン
if st.button("ログアウトする", icon=":material/logout:"):
    st.logout()  # ログアウト処理

# ユーザー情報の表示
st.markdown(f"ようこそ! {st.user.name}さん！")