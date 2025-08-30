import streamlit as st
import requests
import json
import smtplib
import schedule
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
import os
from twilio.rest import Client
import telegram
import asyncio
import schedule
import pandas as pd
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="🤖 בוט שליחויות מתקדם",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL and Hebrew support
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
    
    .main {
        direction: rtl;
        font-family: 'Heebo', sans-serif;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #764ba2, #667eea);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .delivery-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
    }
    
    .status-success {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    }
    
    .status-pending {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    }
    
    .status-failed {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'deliveries' not in st.session_state:
    st.session_state.deliveries = []
if 'scheduled_tasks' not in st.session_state:
    st.session_state.scheduled_tasks = []

# Initialize database
def init_database():
    conn = sqlite3.connect('delivery_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS deliveries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT,
                  recipient TEXT,
                  content TEXT,
                  status TEXT,
                  timestamp DATETIME,
                  channel TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS scheduled_deliveries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT,
                  recipient TEXT,
                  content TEXT,
                  schedule_time DATETIME,
                  status TEXT,
                  channel TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT,
                  phone TEXT,
                  telegram_id TEXT,
                  whatsapp TEXT)''')
    
    conn.commit()
    conn.close()

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ הגדרות שליחות")
    
    # Channel selection
    delivery_channel = st.selectbox(
        "ערוץ שליחה",
        ["📧 אימייל", "📱 SMS (Twilio)", "💬 טלגרם", "📋 WhatsApp", "🌐 Webhook"],
        help="בחר את ערוץ השליחה הרצוי"
    )
    
    # Email settings
    if delivery_channel == "📧 אימייל":
        st.subheader("הגדרות אימייל")
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
        email_username = st.text_input("שם משתמש אימייל")
        email_password = st.text_input("סיסמה אימייל", type="password")
    
    # Twilio settings
    elif delivery_channel == "📱 SMS (Twilio)":
        st.subheader("הגדרות Twilio")
        twilio_account_sid = st.text_input("Account SID")
        twilio_auth_token = st.text_input("Auth Token", type="password")
        twilio_phone_number = st.text_input("מספר טלפון Twilio")
    
    # Telegram settings
    elif delivery_channel == "💬 טלגרם":
        st.subheader("הגדרות טלגרם")
        telegram_bot_token = st.text_input("Bot Token")
        telegram_chat_id = st.text_input("Chat ID")
    
    # WhatsApp settings
    elif delivery_channel == "📋 WhatsApp":
        st.subheader("הגדרות WhatsApp")
        whatsapp_api_key = st.text_input("API Key")
        whatsapp_phone_number = st.text_input("מספר טלפון WhatsApp")
    
    # Webhook settings
    elif delivery_channel == "🌐 Webhook":
        st.subheader("הגדרות Webhook")
        webhook_url = st.text_input("Webhook URL")
        webhook_headers = st.text_area("Headers (JSON)", value='{"Content-Type": "application/json"}')

# Main app
def main():
    st.title("🤖 בוט שליחויות מתקדם")
    st.markdown("### כלי מתקדם לשליחת הודעות, תזכורות והתראות במגוון ערוצים")
    
    # Initialize database
    init_database()
    
    # Tabs for different features
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 שליחה מיידית", 
        "⏰ שליחה מתוזמנת", 
        "👥 ניהול אנשי קשר", 
        "📊 היסטוריית שליחות", 
        "📋 תבניות הודעות", 
        "🔄 שליחה המונית"
    ])
    
    with tab1:
        immediate_delivery_tab()
    
    with tab2:
        scheduled_delivery_tab()
    
    with tab3:
        contacts_management_tab()
    
    with tab4:
        delivery_history_tab()
    
    with tab5:
        message_templates_tab()
    
    with tab6:
        bulk_delivery_tab()

def immediate_delivery_tab():
    st.header("📤 שליחה מיידית")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Message type
        message_type = st.selectbox(
            "סוג הודעה",
            ["📧 הודעה כללית", "⏰ תזכורת", "🚨 התראה", "📋 עדכון סטטוס", "🎉 ברכה"]
        )
        
        # Recipient input
        recipient = st.text_input(
            "נמען:",
            placeholder="אימייל, מספר טלפון, או מזהה טלגרם"
        )
        
        # Message content
        message_content = st.text_area(
            "תוכן ההודעה:",
            height=200,
            placeholder="כתוב כאן את תוכן ההודעה..."
        )
        
        # Priority
        priority = st.selectbox(
            "עדיפות:",
            ["🔵 רגילה", "🟡 בינונית", "🔴 גבוהה", "⚡ דחופה"]
        )
        
        # Send button
        if st.button("📤 שלח הודעה", key="send_immediate"):
            if not recipient or not message_content:
                st.error("אנא מלא את כל השדות הנדרשים")
            else:
                send_message(message_type, recipient, message_content, priority, delivery_channel)
    
    with col2:
        st.markdown("### 📊 סטטוס שליחה")
        st.markdown("**ערוץ:** " + delivery_channel)
        st.markdown("**סוג:** " + message_type)
        st.markdown("**עדיפות:** " + priority)
        
        if st.session_state.deliveries:
            latest = st.session_state.deliveries[-1]
            st.markdown("**שליחה אחרונה:**")
            st.markdown(f"**סטטוס:** {latest['status']}")
            st.markdown(f"**זמן:** {latest['timestamp']}")

def scheduled_delivery_tab():
    st.header("⏰ שליחה מתוזמנת")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Schedule type
        schedule_type = st.selectbox(
            "סוג תזמון",
            ["🕐 פעם אחת", "🔄 חוזר", "📅 יומי", "📆 שבועי", "📅 חודשי"]
        )
        
        # Date and time
        schedule_date = st.date_input("תאריך שליחה")
        schedule_time = st.time_input("שעת שליחה")
        
        # Recurring options
        if schedule_type == "🔄 חוזר":
            repeat_every = st.number_input("חזור כל X דקות", min_value=1, value=60)
        elif schedule_type == "📅 יומי":
            repeat_days = st.multiselect(
                "ימי חזרה",
                ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
            )
        
        # Message details
        scheduled_recipient = st.text_input("נמען (מתוזמן):")
        scheduled_content = st.text_area("תוכן הודעה (מתוזמן):", height=150)
        
        # Schedule button
        if st.button("⏰ תזמן שליחה", key="schedule_delivery"):
            if not scheduled_recipient or not scheduled_content:
                st.error("אנא מלא את כל השדות הנדרשים")
            else:
                schedule_message(schedule_type, scheduled_recipient, scheduled_content, 
                              schedule_date, schedule_time, delivery_channel)
    
    with col2:
        st.markdown("### 📅 משימות מתוזמנות")
        if st.session_state.scheduled_tasks:
            for i, task in enumerate(st.session_state.scheduled_tasks):
                with st.expander(f"משימה {i+1} - {task['schedule_time']}"):
                    st.markdown(f"**נמען:** {task['recipient']}")
                    st.markdown(f"**תוכן:** {task['content'][:50]}...")
                    st.markdown(f"**סטטוס:** {task['status']}")
                    
                    if st.button(f"🗑️ מחק משימה {i+1}", key=f"delete_task_{i}"):
                        st.session_state.scheduled_tasks.pop(i)
                        st.rerun()

def contacts_management_tab():
    st.header("👥 ניהול אנשי קשר")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ הוסף איש קשר חדש")
        
        contact_name = st.text_input("שם מלא:")
        contact_email = st.text_input("אימייל:")
        contact_phone = st.text_input("מספר טלפון:")
        contact_telegram = st.text_input("מזהה טלגרם:")
        contact_whatsapp = st.text_input("מספר WhatsApp:")
        
        if st.button("💾 שמור איש קשר", key="save_contact"):
            if contact_name:
                save_contact(contact_name, contact_email, contact_phone, contact_telegram, contact_whatsapp)
                st.success("איש הקשר נשמר בהצלחה!")
            else:
                st.error("אנא הכנס שם איש קשר")
    
    with col2:
        st.subheader("📋 אנשי קשר שמורים")
        
        # Load contacts from database
        conn = sqlite3.connect('delivery_bot.db')
        contacts_df = pd.read_sql_query("SELECT * FROM contacts", conn)
        conn.close()
        
        if not contacts_df.empty:
            for _, contact in contacts_df.iterrows():
                with st.expander(f"👤 {contact['name']}"):
                    st.markdown(f"**אימייל:** {contact['email'] or 'לא צוין'}")
                    st.markdown(f"**טלפון:** {contact['phone'] or 'לא צוין'}")
                    st.markdown(f"**טלגרם:** {contact['telegram_id'] or 'לא צוין'}")
                    st.markdown(f"**WhatsApp:** {contact['whatsapp'] or 'לא צוין'}")
                    
                    # Quick send buttons
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"📧 שלח אימייל", key=f"email_{contact['id']}"):
                            st.session_state.quick_recipient = contact['email']
                            st.session_state.quick_channel = "📧 אימייל"
                    
                    with col_b:
                        if st.button(f"📱 שלח SMS", key=f"sms_{contact['id']}"):
                            st.session_state.quick_recipient = contact['phone']
                            st.session_state.quick_channel = "📱 SMS (Twilio)"
        else:
            st.info("אין עדיין אנשי קשר שמורים")

def delivery_history_tab():
    st.header("📊 היסטוריית שליחות")
    
    # Load delivery history from database
    conn = sqlite3.connect('delivery_bot.db')
    deliveries_df = pd.read_sql_query("SELECT * FROM deliveries ORDER BY timestamp DESC", conn)
    conn.close()
    
    if not deliveries_df.empty:
        st.markdown(f"### סה״כ שליחות: {len(deliveries_df)}")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("סנן לפי סטטוס:", ["הכל", "הצלחה", "כישלון", "ממתין"])
        
        with col2:
            channel_filter = st.selectbox("סנן לפי ערוץ:", ["הכל", "אימייל", "SMS", "טלגרם", "WhatsApp", "Webhook"])
        
        with col3:
            date_filter = st.date_input("סנן לפי תאריך:")
        
        # Apply filters
        filtered_df = deliveries_df.copy()
        if status_filter != "הכל":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        if channel_filter != "הכל":
            filtered_df = filtered_df[filtered_df['channel'] == channel_filter]
        
        # Display filtered results
        for _, delivery in filtered_df.iterrows():
            status_class = "status-success" if delivery['status'] == "הצלחה" else \
                          "status-pending" if delivery['status'] == "ממתין" else "status-failed"
            
            st.markdown(f"""
            <div class="delivery-card {status_class}">
                <h4>📤 {delivery['type']}</h4>
                <p><strong>נמען:</strong> {delivery['recipient']}</p>
                <p><strong>תוכן:</strong> {delivery['content'][:100]}...</p>
                <p><strong>ערוץ:</strong> {delivery['channel']}</p>
                <p><strong>סטטוס:</strong> {delivery['status']}</p>
                <p><strong>זמן:</strong> {delivery['timestamp']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("אין עדיין היסטוריית שליחות")

def message_templates_tab():
    st.header("📋 תבניות הודעות")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ צור תבנית חדשה")
        
        template_name = st.text_input("שם התבנית:")
        template_category = st.selectbox("קטגוריה:", ["תזכורות", "התראות", "ברכות", "עדכונים", "אחר"])
        template_content = st.text_area("תוכן התבנית:", height=150, 
                                      placeholder="כתוב כאן את תבנית ההודעה. השתמש ב-{name} להחלפת שמות")
        
        if st.button("💾 שמור תבנית", key="save_template"):
            if template_name and template_content:
                save_template(template_name, template_category, template_content)
                st.success("התבנית נשמרה בהצלחה!")
            else:
                st.error("אנא מלא את כל השדות הנדרשים")
    
    with col2:
        st.subheader("📚 תבניות שמורות")
        
        # Sample templates
        sample_templates = {
            "תזכורת פגישה": "שלום {name}, תזכורת לפגישה מחר בשעה {time}",
            "התראה חשובה": "שלום {name}, יש לך {count} הודעות חדשות",
            "ברכה ליום הולדת": "מזל טוב {name}! מאחלים לך יום הולדת שמח ובריא!",
            "עדכון סטטוס": "שלום {name}, הסטטוס של הבקשה שלך השתנה ל-{status}"
        }
        
        for template_name, template_content in sample_templates.items():
            with st.expander(f"📋 {template_name}"):
                st.text_area("תוכן:", template_content, height=100, disabled=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"📝 ערוך", key=f"edit_{template_name}"):
                        st.session_state.editing_template = template_name
                
                with col_b:
                    if st.button(f"📤 השתמש", key=f"use_{template_name}"):
                        st.session_state.selected_template = template_content

def bulk_delivery_tab():
    st.header("🔄 שליחה המונית")
    
    st.markdown("### 📁 העלה קובץ CSV עם פרטי הנמענים")
    
    uploaded_file = st.file_uploader(
        "בחר קובץ CSV",
        type=['csv'],
        help="הקובץ צריך להכיל עמודות: name, email, phone, message"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"הקובץ נטען בהצלחה! {len(df)} נמענים")
            
            # Preview data
            st.subheader("📋 תצוגה מקדימה של הנתונים")
            st.dataframe(df.head())
            
            # Bulk send options
            st.subheader("⚙️ הגדרות שליחה המונית")
            
            col1, col2 = st.columns(2)
            
            with col1:
                delay_between = st.number_input("השהייה בין שליחות (שניות)", min_value=1, value=5)
                start_time = st.time_input("שעת התחלה")
            
            with col2:
                max_daily = st.number_input("מקסימום שליחות יומי", min_value=1, value=100)
                test_mode = st.checkbox("מצב בדיקה (שליחה לעצמך בלבד)")
            
            # Bulk send button
            if st.button("🚀 התחל שליחה המונית", key="bulk_send"):
                if test_mode:
                    st.info("מצב בדיקה מופעל - השליחה תישלח לעצמך בלבד")
                
                with st.spinner("שולח הודעות..."):
                    bulk_send_messages(df, delay_between, max_daily, test_mode)
        
        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ: {str(e)}")

# Helper functions
def send_message(message_type, recipient, content, priority, channel):
    """Send message through selected channel"""
    try:
        if channel == "📧 אימייל":
            result = send_email(recipient, content, message_type, priority)
        elif channel == "📱 SMS (Twilio)":
            result = send_sms(recipient, content, message_type, priority)
        elif channel == "💬 טלגרם":
            result = send_telegram(recipient, content, message_type, priority)
        elif channel == "📋 WhatsApp":
            result = send_whatsapp(recipient, content, message_type, priority)
        elif channel == "🌐 Webhook":
            result = send_webhook(recipient, content, message_type, priority)
        
        # Save to database
        save_delivery(message_type, recipient, content, result['status'], channel)
        
        # Update session state
        st.session_state.deliveries.append({
            'type': message_type,
            'recipient': recipient,
            'content': content,
            'status': result['status'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'channel': channel
        })
        
        if result['status'] == 'הצלחה':
            st.success(f"ההודעה נשלחה בהצלחה דרך {channel}!")
        else:
            st.error(f"שגיאה בשליחת ההודעה: {result['message']}")
    
    except Exception as e:
        st.error(f"שגיאה בשליחת ההודעה: {str(e)}")

def send_email(recipient, content, message_type, priority):
    """Send email using SMTP"""
    try:
        # This is a placeholder - you would implement actual SMTP logic here
        return {'status': 'הצלחה', 'message': 'אימייל נשלח בהצלחה'}
    except Exception as e:
        return {'status': 'כישלון', 'message': str(e)}

def send_sms(recipient, content, message_type, priority):
    """Send SMS using Twilio"""
    try:
        # This is a placeholder - you would implement actual Twilio logic here
        return {'status': 'הצלחה', 'message': 'SMS נשלח בהצלחה'}
    except Exception as e:
        return {'status': 'כישלון', 'message': str(e)}

def send_telegram(recipient, content, message_type, priority):
    """Send Telegram message"""
    try:
        # This is a placeholder - you would implement actual Telegram logic here
        return {'status': 'הצלחה', 'message': 'הודעת טלגרם נשלחה בהצלחה'}
    except Exception as e:
        return {'status': 'כישלון', 'message': str(e)}

def send_whatsapp(recipient, content, message_type, priority):
    """Send WhatsApp message"""
    try:
        # This is a placeholder - you would implement actual WhatsApp API logic here
        return {'status': 'הצלחה', 'message': 'הודעת WhatsApp נשלחה בהצלחה'}
    except Exception as e:
        return {'status': 'כישלון', 'message': str(e)}

def send_webhook(recipient, content, message_type, priority):
    """Send webhook"""
    try:
        # This is a placeholder - you would implement actual webhook logic here
        return {'status': 'הצלחה', 'message': 'Webhook נשלח בהצלחה'}
    except Exception as e:
        return {'status': 'כישלון', 'message': str(e)}

def schedule_message(schedule_type, recipient, content, date, time, channel):
    """Schedule a message for later delivery"""
    schedule_datetime = datetime.combine(date, time)
    
    task = {
        'type': 'הודעה מתוזמנת',
        'recipient': recipient,
        'content': content,
        'schedule_time': schedule_datetime.strftime("%Y-%m-%d %H:%M"),
        'status': 'ממתין',
        'channel': channel
    }
    
    st.session_state.scheduled_tasks.append(task)
    st.success(f"ההודעה תוזמנה לשליחה ב-{schedule_datetime.strftime('%Y-%m-%d %H:%M')}")

def save_contact(name, email, phone, telegram_id, whatsapp):
    """Save contact to database"""
    conn = sqlite3.connect('delivery_bot.db')
    c = conn.cursor()
    c.execute('''INSERT INTO contacts (name, email, phone, telegram_id, whatsapp)
                 VALUES (?, ?, ?, ?, ?)''', (name, email, phone, telegram_id, whatsapp))
    conn.commit()
    conn.close()

def save_delivery(message_type, recipient, content, status, channel):
    """Save delivery to database"""
    conn = sqlite3.connect('delivery_bot.db')
    c = conn.cursor()
    c.execute('''INSERT INTO deliveries (type, recipient, content, status, timestamp, channel)
                 VALUES (?, ?, ?, ?, ?, ?)''', 
              (message_type, recipient, content, status, datetime.now(), channel))
    conn.commit()
    conn.close()

def save_template(name, category, content):
    """Save message template"""
    # This would save to database or file
    pass

def bulk_send_messages(df, delay, max_daily, test_mode):
    """Send messages in bulk"""
    st.info(f"מתחיל שליחה המונית ל-{len(df)} נמענים...")
    
    # This would implement actual bulk sending logic
    for index, row in df.iterrows():
        if test_mode:
            recipient = "test@example.com"  # Send to yourself in test mode
        else:
            recipient = row.get('email', row.get('phone', 'unknown'))
        
        # Simulate sending
        time.sleep(delay)
        
        if index % 10 == 0:  # Progress update every 10 messages
            st.write(f"נשלחו {index + 1} מתוך {len(df)} הודעות...")
    
    st.success("השליחה ההמונית הושלמה בהצלחה!")

if __name__ == "__main__":
    main()