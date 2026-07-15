import streamlit as st
import requests

st.set_page_config(page_title="Enterprise AI Agent", layout="wide")
st.title("🤖 AI Agent Pháp lý & Nghiệp vụ")

API_URL = "http://localhost:8000/api/v1/chat"

# Khởi tạo bộ nhớ tạm cho lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lại các tin nhắn cũ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

# Ô nhập dữ liệu
if prompt := st.chat_input("Hỏi AI Agent..."):
    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)

    # Hiển thị câu trả lời của AI
    with st.chat_message("assistant"):
        with st.spinner("Agent đang nghiên cứu..."):
            try:
                # Gọi API Backend
                res = requests.post(API_URL, json={"query": prompt}).json()
                answer = res.get("answer")
                contexts = res.get("contexts", [])
                
                # In ra câu trả lời
                st.markdown(answer)
                st.caption(f"Trích xuất từ: {res.get('source')}")
                
                # Nút mở rộng để xem tài liệu Qdrant đã truy xuất (Bạch hóa dữ liệu)
                if contexts:
                    with st.expander("📄 Xem tài liệu được truy xuất từ Qdrant"):
                        for i, ctx in enumerate(contexts):
                            st.info(f"**Tài liệu {i+1}:**\n{ctx}")
                            
                # Lưu vào lịch sử chat
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Lỗi không thể kết nối đến Backend: {e}")