# import streamlit as st
# import sseclient
# import requests
# import json
# import session
# from sseclient import SSEClient
# import time

# # Configuration
# bot_app_key = "OrtaxfthbkggMkOyMYIXlqcPVHaIVKrXSRHcvRiGXxvOJVDBwwJbWQxtaIBTkLzrjuVkaNJbaGBUudiFJAwngNZxNAAoAlaLSRKdETmhYyUyPMIAhphgyhEJWPpAmXIP"
# visitor_biz_id = "user"
# streaming_throttle = 5

# def get_bot_response(content, session_id):
#     """Send message to bot and get streaming response"""
#     req_data = {
#         "content": content,
#         "bot_app_key": bot_app_key,
#         "session_id": session_id,
#         "visitor_biz_id": visitor_biz_id,
#         "streaming_throttle": streaming_throttle
#     }
    
#     try:
#         response = requests.post(
#             "https://wss.lke.tencentcloud.com/v1/qbot/chat/sse",
#             data=json.dumps(req_data),
#             stream=True,
#             headers={"Accept": "text/event-stream"}
#         )
        
#         client = SSEClient(response)
        
#         for ev in client.events():
#             if ev.event == "reply":
#                 data = json.loads(ev.data)
#                 if data['payload']['is_final'] and not data['payload']['is_from_self']:
#                     return data['payload']['content']
                    
#     except Exception as e:
#         return f"Error: {str(e)}"
    
#     return "No response received"

# def main():
#     st.set_page_config(
#         page_title="Chatbot Interface",
#         page_icon="🤖",
#         layout="wide"
#     )
    
#     st.title("🤖 AI-Tutor")
#     st.markdown("---")
    
#     # Initialize session state
#     if "messages" not in st.session_state:
#         st.session_state.messages = []
    
#     if "session_id" not in st.session_state:
#         st.session_state.session_id = session.get_session()
    
#     # Display session info
#     with st.sidebar:
#         st.header("Session Info")
#         st.write(f"**Session ID:** {st.session_state.session_id}")
#         st.write(f"**Visitor ID:** {visitor_biz_id}")
        
#         if st.button("New Session"):
#             st.session_state.session_id = session.get_session()
#             st.session_state.messages = []
#             st.rerun()
            
#         if st.button("Clear Chat"):
#             st.session_state.messages = []
#             st.rerun()
    
#     # Chat interface
#     chat_container = st.container()
    
#     # Display chat messages
#     with chat_container:
#         for message in st.session_state.messages:
#             with st.chat_message(message["role"]):
#                 st.write(message["content"])
    
#     # Chat input
#     if prompt := st.chat_input("Type your message here..."):
#         # Add user message to chat history
#         st.session_state.messages.append({"role": "user", "content": prompt})
        
#         # Display user message
#         with st.chat_message("user"):
#             st.write(prompt)
        
#         # Get bot response
#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 response = get_bot_response(prompt, st.session_state.session_id)
#             st.write(response)
        
#         # Add bot response to chat history
#         st.session_state.messages.append({"role": "assistant", "content": response})
        
#         # Rerun to update the display
#         st.rerun()

# if __name__ == "__main__":
#     main()


import streamlit as st
import sseclient
import requests
import json
import session
from sseclient import SSEClient
import time
import base64
from PIL import Image
import io

# Configuration
bot_app_key = "OrtaxfthbkggMkOyMYIXlqcPVHaIVKrXSRHcvRiGXxvOJVDBwwJbWQxtaIBTkLzrjuVkaNJbaGBUudiFJAwngNZxNAAoAlaLSRKdETmhYyUyPMIAhphgyhEJWPpAmXIP"
visitor_biz_id = "user"
streaming_throttle = 5

# Mathpix Configuration - Replace with your actual credentials
MATHPIX_APP_ID = "turitoyvs_2d759a_2eca74"
MATHPIX_API_KEY = "7b8c835a195e8dab5dcd8ee677017e9c93777376128cf8f37fc3a534fb8f5d34"

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def mathpix_ocr(image):
    """Send image to Mathpix API and get LaTeX response"""
    try:
        # Convert image to base64
        img_base64 = image_to_base64(image)
        
        # Prepare the request
        url = "https://api.mathpix.com/v3/text"
        headers = {
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_API_KEY,
            "Content-type": "application/json"
        }
        
        data = {
            "src": f"data:image/png;base64,{img_base64}",
            "formats": ["text", "latex_styled"],
            "data_options": {
                "include_asciimath": True,
                "include_latex": True
            }
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            result = response.json()
            latex_text = result.get('latex_styled', result.get('text', ''))
            return latex_text, None
        else:
            return None, f"Mathpix API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"OCR Error: {str(e)}"

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
    
    # Sidebar configuration
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
        
        st.markdown("---")
    
    # Main chat interface
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("type") == "image_analysis":
                    # st.write("**OCR Result:**")
                    st.code(message["latex"], language="latex")
                    st.write("**Question**")
                    st.write(message["content"])
                else:
                    st.write(message["content"])
    
    # Input section
    # st.markdown("---")
    
    # Create two columns for text input and image upload
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.text_input("Type your message here...", key="text_input")
    
    with col2:
        uploaded_file = st.file_uploader(
            "Upload Image", 
            type=['png', 'jpg', 'jpeg'], 
            key="image_upload",
            label_visibility="collapsed"
        )
    
    # Process text input
    if prompt and st.button("Send Message", key="send_text"):
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
        
        # Clear the input and rerun
        st.rerun()
    
    # Process image upload
    if uploaded_file is not None and st.button("Analyze Image", key="send_image"):
        try:
            # Display uploaded image
            image = Image.open(uploaded_file)
            
            with st.chat_message("user"):
                st.write("**Uploaded Image:**")
                st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Perform OCR
            with st.chat_message("assistant"):
                with st.spinner("Processing image with OCR..."):
                    latex_result, error = mathpix_ocr(image)
                
                if error:
                    st.error(f"OCR failed: {error}")
                    return
                
                if latex_result:
                    # st.write("**OCR Result (LaTeX):**")
                    # st.code(latex_result, language="latex")
                    
                    # Prepare question for the bot
                    question = f"Please solve or explain this mathematical problem: {latex_result}"
                    
                    st.write("**Sending to AI for analysis...**")
                    
                    with st.spinner("Getting AI response..."):
                        bot_response = get_bot_response(question, st.session_state.session_id)
                    
                    st.write("**AI Response:**")
                    st.write(bot_response)
                    
                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": question,
                        "type": "image_analysis",
                        "latex": latex_result
                    })
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": bot_response
                    })
                else:
                    st.warning("No text detected in the image")
        
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
        
        # Rerun to update the display
        st.rerun()

if __name__ == "__main__":
    main()