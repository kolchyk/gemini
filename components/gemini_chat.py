import streamlit as st
import mimetypes
import os
from services.chat_service import chat_service
from config import settings

def render_gemini_chat():
    """Renders the Gemini 3 Pro Chat UI component."""
    
    # Initialize session state for Gemini 3 Pro chat
    if 'gemini_chat_history' not in st.session_state:
        st.session_state['gemini_chat_history'] = []
    if 'chat_thinking_level' not in st.session_state:
        st.session_state['chat_thinking_level'] = 'high'
    if 'chat_temperature' not in st.session_state:
        st.session_state['chat_temperature'] = 0.95
    if 'chat_file_uploader_key' not in st.session_state:
        st.session_state['chat_file_uploader_key'] = 0

    # Sidebar Settings
    with st.sidebar:
        st.markdown('<div class="model-badge">💬 gemini-3.1-pro-preview</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section-label">Налаштування</div>', unsafe_allow_html=True)
        thinking_level = st.selectbox(
            "Мислення:",
            options=["low", "high"],
            index=0 if st.session_state['chat_thinking_level'] == 'low' else 1,
            key="thinking_level_selector"
        )
        st.session_state['chat_thinking_level'] = thinking_level

        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state['chat_temperature'],
            step=0.1,
            key="chat_temperature_slider"
        )
        st.session_state['chat_temperature'] = temperature

        st.markdown('<div class="sidebar-section-label">Файли</div>', unsafe_allow_html=True)
        _chat_uploader_key = f"chat_file_uploader_{st.session_state['chat_file_uploader_key']}"
        st.file_uploader(
            "Прикріпити до наступного повідомлення:",
            accept_multiple_files=True,
            key=_chat_uploader_key,
            help="Підтримуються зображення, PDF, текст, код та інші файли",
        )
        _pending_uploads = st.session_state.get(_chat_uploader_key) or []

        st.divider()
        msg_count = len(st.session_state['gemini_chat_history'])
        st.caption(f"Повідомлень у чаті: {msg_count}")
        
        if st.button("🧹 Очистити чат", use_container_width=True, type="secondary"):
            st.session_state['gemini_chat_history'] = []
            st.rerun()

    # Main Content Area
    st.subheader("💬 Чат з Gemini 3 Pro")

    # Display empty state if no history
    if not st.session_state['gemini_chat_history']:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <h3>Почніть розмову з Gemini 3 Pro</h3>
                <p>Ви можете ставити запитання, прикріплювати файли або просити допомоги з кодом.</p>
            </div>
        """, unsafe_allow_html=True)

    # Create scrollable container for chat messages
    chat_messages_container = st.container()
    with chat_messages_container:
        st.markdown('<div class="chat-messages-scrollable">', unsafe_allow_html=True)
        # Display chat history
        for message in st.session_state['gemini_chat_history']:
            with st.chat_message(message["role"]):
                for att in message.get("attachments", []):
                    if att["mime_type"].startswith("image/") and att.get("bytes"):
                        st.image(att["bytes"], caption=att["name"], width=150)
                    else:
                        st.caption(f"📎 {att['name']}")
                st.markdown(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Введіть ваше повідомлення..."):
            # Upload any pending files to Gemini and collect attachment metadata
            attachments = []
            if _pending_uploads:
                try:
                    for uploaded_file in _pending_uploads:
                        with st.spinner(f"Завантажуємо {uploaded_file.name}..."):
                            att = chat_service.upload_file(uploaded_file)
                            attachments.append(att)
                except Exception as e:
                    st.error(f"❌ Помилка завантаження файлу: {str(e)}")

            # Build history entry and append
            user_msg = {"role": "user", "content": prompt}
            if attachments:
                user_msg["attachments"] = attachments
            st.session_state['gemini_chat_history'].append(user_msg)

            # Reset file uploader for the next message
            st.session_state['chat_file_uploader_key'] += 1

            # Display user message immediately
            with st.chat_message("user"):
                for att in attachments:
                    if att["mime_type"].startswith("image/") and att.get("bytes"):
                        st.image(att["bytes"], caption=att["name"], width=150)
                    else:
                        st.caption(f"📎 {att['name']}")
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    # Stream response
                    for chunk_text in chat_service.generate_response_stream(
                        history=st.session_state['gemini_chat_history'],
                        thinking_level=st.session_state['chat_thinking_level'],
                        temperature=st.session_state['chat_temperature']
                    ):
                        if chunk_text:
                            full_response += chunk_text
                            message_placeholder.markdown(full_response + "▌")

                    # Final update without cursor
                    message_placeholder.markdown(full_response)

                    # Add assistant response to history
                    st.session_state['gemini_chat_history'].append({"role": "assistant", "content": full_response})

                    # Log chat to Telegram
                    chat_service.log_chat(prompt, full_response)

                except Exception as e:
                    error_message = f"❌ Помилка: {str(e)}"
                    message_placeholder.error(error_message)
                    st.exception(e)

