import streamlit as st
import sqlite3

conn = sqlite3.connect("telegram_messages.db", check_same_thread=False)
cur = conn.cursor()
if "cnt" not in st.session_state:
    st.session_state.cnt = 0

if "current_row" not in st.session_state:
    cur.execute("""
        SELECT channel, message_id, raw_text 
        FROM messages 
        WHERE label IS NULL 
        ORDER BY RANDOM() 
        LIMIT 1
    """)
    st.session_state.current_row = cur.fetchone()

if st.session_state.current_row:
    channel, message_id, text = st.session_state.current_row

    st.write(text)
    st.info(f"Размечено за сессию: {st.session_state.cnt}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Политика"):
            cur.execute(
                "UPDATE messages SET label=? WHERE channel=? AND message_id=?",
                (1, channel, message_id)
            )
            conn.commit()
            st.session_state.cnt += 1
            del st.session_state.current_row
            st.rerun()

    with col2:
        if st.button("❌ Не относится"):
            cur.execute(
                "UPDATE messages SET label=? WHERE channel=? AND message_id=?",
                (0, channel, message_id)
            )
            conn.commit()
            st.session_state.cnt += 1
            del st.session_state.current_row
            st.rerun()
else:
    st.success("Все размечено 🎉")
    if st.button("Проверить новые записи"):
        del st.session_state.current_row
        st.rerun()