import streamlit as st
import sseclient
import requests
import json
import session
from sseclient import SSEClient
import time

# Configuration
bot_app_key = "OrtaxfthbkggMkOyMYIXlqcPVHaIVKrXSRHcvRiGXxvOJVDBwwJbWQxtaIBTkLzrjuVkaNJbaGBUudiFJAwngNZxNAAoAlaLSRKdETmhYyUyPMIAhphgyhEJWPpAmXIP"
visitor_biz_id = "user"
streaming_throttle = 5

def get_bot_response(content, session_id):
    """Send message to bot and get streaming response"""
    req_data = {
        "content": content,
        "bot_app_key": bot_app_key,
        "session_id": session_id,
        "visitor_biz_id": visitor_biz_id,
        "streaming_throttle": streaming_throttle
    }
    
    try:
        response = requests.post(
            "https://wss.lke.tencentcloud.com/v1/qbot/chat/sse",
            data=json.dumps(req_data),
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        client = SSEClient(response)
        
        for ev in client.events():
            if ev.event == "reply":
                data = json.loads(ev.data)
                if data['payload']['is_final'] and not data['payload']['is_from_self']:
                    return data['payload']['content']
                    
    except Exception as e:
        return f"Error: {str(e)}"
    
    return "No response received"

def main():
    st.set_page_config(
        page_title="Chatbot Interface",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI-Tutor")
    st.markdown("---")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = session.get_session()
    
    # Display session info
    with st.sidebar:
        st.header("Session Info")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        st.write(f"**Visitor ID:** {visitor_biz_id}")
        
        if st.button("New Session"):
            st.session_state.session_id = session.get_session()
            st.session_state.messages = []
            st.rerun()
            
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_bot_response(prompt, st.session_state.session_id)
            st.write(response)
        
        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update the display
        st.rerun()

if __name__ == "__main__":
    main()