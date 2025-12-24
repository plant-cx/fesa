import streamlit as st
import imaplib
import email
from email.header import decode_header
import webbrowser

# --- CONFIGURATION ---
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"  # Make sure this is an App Password, not your normal login!
IMAP_SERVER = "imap.gmail.com"
EMAIL_LIMIT = 5  # fetches only the last 5 emails to be fast
MAX_BODY_TOKENS = 500 # Truncates text to save "tokens" and screen space

# --- PAGE SETUP ---
st.set_page_config(page_title="Quick Mail", layout="centered")

st.markdown("""
<style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 50px;
    }
    .email-bubble {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid #4CAF50;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        color: #31333F;
        font-family: sans-serif;
    }
    .email-header {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 5px;
        color: #1f1f1f;
    }
    .email-meta {
        font-size: 0.8em;
        color: #666;
        margin-bottom: 10px;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
    }
    .email-body {
        line-height: 1.5;
        white-space: pre-wrap; /* Keeps formatting */
    }
</style>
""", unsafe_allow_html=True)

st.title("📬 Fast Inbox Loader")

# --- HELPER FUNCTIONS ---

def get_email_body(msg):
    """Extracts plain text body from email"""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()
    return "(No plain text content found)"

def clean_text(text):
    """Truncates text to save tokens/space"""
    if not text:
        return ""
    # Cut off at limit
    if len(text) > MAX_BODY_TOKENS:
        return text[:MAX_BODY_TOKENS] + "... [TRUNCATED TO SAVE TOKENS]"
    return text

# --- MAIN LOGIC ---

if st.button("🔄 Load Latest Emails"):
    with st.spinner('Connecting to IMAP...'):
        try:
            # 1. Connect to Mail
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            # 2. Search - Optimize by fetching IDs only first
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()

            # 3. Slice to get only the last N emails (Speed Optimization)
            latest_email_ids = email_ids[-EMAIL_LIMIT:] 
            
            # Reverse them so newest is at the top
            latest_email_ids = latest_email_ids[::-1]

            st.markdown('<div class="chat-container">', unsafe_allow_html=True)

            for e_id in latest_email_ids:
                # Fetch specific email by ID
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        # Get Sender
                        sender = msg.get("From")
                        
                        # Get Body & Clean it
                        raw_body = get_email_body(msg)
                        clean_body = clean_text(raw_body)

                        # Render Bubble
                        st.markdown(f"""
                        <div class="email-bubble">
                            <div class="email-header">{subject}</div>
                            <div class="email-meta">From: {sender}</div>
                            <div class="email-body">{clean_body}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
            mail.close()
            mail.logout()

        except Exception as e:
            st.error(f"Error: {e}")

else:
    st.info("Click the button to load your latest messages.")
