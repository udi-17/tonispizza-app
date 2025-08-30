import streamlit as st
import openai
import os
from docx import Document
import PyPDF2
import io
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="בוט סיכומים חכם",
    page_icon="📚",
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
    
    .summary-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
    }
    
    .upload-box {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background: rgba(102, 126, 234, 0.1);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ הגדרות")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password", help="הכנס את מפתח ה-API שלך מ-OpenAI")
    
    # Model selection
    model = st.selectbox(
        "בחר מודל",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
        help="בחר את המודל המתאים לסיכום שלך"
    )
    
    # Summary length
    summary_length = st.selectbox(
        "אורך הסיכום",
        ["קצר (2-3 משפטים)", "בינוני (5-7 משפטים)", "מפורט (10-15 משפטים)"],
        help="בחר את אורך הסיכום הרצוי"
    )
    
    # Language selection
    language = st.selectbox(
        "שפת הסיכום",
        ["עברית", "English", "עברית + English"],
        help="בחר את שפת הסיכום"
    )

# Main app
def main():
    st.title("🤖 בוט סיכומים חכם")
    st.markdown("### כלי מתקדם ליצירת סיכומים איכותיים מטקסטים, מסמכים ושיחות")
    
    # Tabs for different features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 סיכום טקסט", 
        "📄 סיכום מסמכים", 
        "💬 סיכום שיחות", 
        "🌐 סיכום מאתרים", 
        "📊 היסטוריית סיכומים"
    ])
    
    with tab1:
        text_summarization_tab()
    
    with tab2:
        document_summarization_tab()
    
    with tab3:
        conversation_summarization_tab()
    
    with tab4:
        website_summarization_tab()
    
    with tab5:
        summary_history_tab()

def text_summarization_tab():
    st.header("📝 סיכום טקסט")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Text input
        text_input = st.text_area(
            "הכנס טקסט לסיכום:",
            height=300,
            placeholder="הדבק כאן את הטקסט שברצונך לסכם..."
        )
        
        if st.button("📋 סרן טקסט", key="scan_text"):
            if text_input.strip():
                st.session_state.current_text = text_input
                st.success("הטקסט נסרק בהצלחה!")
            else:
                st.error("אנא הכנס טקסט לסיכום")
    
    with col2:
        st.markdown("### 📊 סטטיסטיקות טקסט")
        if text_input:
            words = len(text_input.split())
            chars = len(text_input)
            sentences = text_input.count('.') + text_input.count('!') + text_input.count('?')
            
            st.metric("מילים", words)
            st.metric("תווים", chars)
            st.metric("משפטים", sentences)
    
    # Summary generation
    if st.button("🚀 צור סיכום", key="generate_summary"):
        if not api_key:
            st.error("אנא הכנס מפתח API ב-OpenAI")
        elif not text_input.strip():
            st.error("אנא הכנס טקסט לסיכום")
        else:
            with st.spinner("יוצר סיכום..."):
                try:
                    summary = generate_summary(text_input, api_key, model, summary_length, language)
                    if summary:
                        st.session_state.summaries.append({
                            'type': 'טקסט',
                            'content': text_input[:100] + "...",
                            'summary': summary,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'model': model
                        })
                        st.success("הסיכום נוצר בהצלחה!")
                        st.markdown("### 📋 הסיכום שלך:")
                        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"שגיאה ביצירת הסיכום: {str(e)}")

def document_summarization_tab():
    st.header("📄 סיכום מסמכים")
    
    st.markdown("### העלה מסמך לסיכום")
    
    uploaded_file = st.file_uploader(
        "בחר קובץ",
        type=['txt', 'docx', 'pdf'],
        help="תמיכה בקבצי TXT, DOCX ו-PDF"
    )
    
    if uploaded_file is not None:
        file_details = {
            "שם הקובץ": uploaded_file.name,
            "סוג הקובץ": uploaded_file.type,
            "גודל": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        st.json(file_details)
        
        # Process document
        if st.button("📖 עבד מסמך", key="process_doc"):
            with st.spinner("מעבד מסמך..."):
                try:
                    text_content = extract_text_from_document(uploaded_file)
                    if text_content:
                        st.session_state.current_text = text_content
                        st.success("המסמך עובד בהצלחה!")
                        
                        # Show text preview
                        with st.expander("תצוגה מקדימה של הטקסט"):
                            st.text_area("תוכן המסמך:", text_content, height=200, disabled=True)
                        
                        # Generate summary
                        if st.button("🚀 צור סיכום מהמסמך", key="doc_summary"):
                            if not api_key:
                                st.error("אנא הכנס מפתח API ב-OpenAI")
                            else:
                                with st.spinner("יוצר סיכום..."):
                                    summary = generate_summary(text_content, api_key, model, summary_length, language)
                                    if summary:
                                        st.session_state.summaries.append({
                                            'type': 'מסמך',
                                            'content': uploaded_file.name,
                                            'summary': summary,
                                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            'model': model
                                        })
                                        st.success("הסיכום נוצר בהצלחה!")
                                        st.markdown("### 📋 הסיכום שלך:")
                                        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"שגיאה בעיבוד המסמך: {str(e)}")

def conversation_summarization_tab():
    st.header("💬 סיכום שיחות")
    
    st.markdown("### הכנס שיחה או צ'אט לסיכום")
    
    # Conversation input
    conversation = st.text_area(
        "הדבק כאן את השיחה:",
        height=200,
        placeholder="שם: הודעה\nשם אחר: תגובה\n..."
    )
    
    # Conversation format options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 דוגמה לפורמט:")
        st.code("""יוסי: שלום, איך אתה?
שרה: טוב תודה, מה איתך?
יוסי: גם טוב, מה התכניות שלך היום?
שרה: אני הולכת לעבודה ואז לסרט""")
    
    with col2:
        st.markdown("#### 🎯 אפשרויות סיכום:")
        st.markdown("- **נושאים עיקריים** בשיחה")
        st.markdown("- **החלטות** שהתקבלו")
        st.markdown("- **פעולות** שצריך לבצע")
        st.markdown("- **סיכום כללי** של השיחה")
    
    if st.button("🚀 צור סיכום שיחה", key="conversation_summary"):
        if not api_key:
            st.error("אנא הכנס מפתח API ב-OpenAI")
        elif not conversation.strip():
            st.error("אנא הכנס שיחה לסיכום")
        else:
            with st.spinner("יוצר סיכום שיחה..."):
                try:
                    summary = generate_conversation_summary(conversation, api_key, model, language)
                    if summary:
                        st.session_state.summaries.append({
                            'type': 'שיחה',
                            'content': conversation[:100] + "...",
                            'summary': summary,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'model': model
                        })
                        st.success("סיכום השיחה נוצר בהצלחה!")
                        st.markdown("### 📋 סיכום השיחה:")
                        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"שגיאה ביצירת סיכום השיחה: {str(e)}")

def website_summarization_tab():
    st.header("🌐 סיכום מאתרים")
    
    st.markdown("### הכנס כתובת URL לסיכום")
    
    url = st.text_input(
        "URL:",
        placeholder="https://example.com",
        help="הכנס כתובת URL של האתר שברצונך לסכם"
    )
    
    if st.button("🌐 סרן אתר", key="scan_website"):
        if not url:
            st.error("אנא הכנס כתובת URL")
        else:
            with st.spinner("סורק אתר..."):
                try:
                    website_content = extract_website_content(url)
                    if website_content:
                        st.session_state.current_text = website_content
                        st.success("האתר נסרק בהצלחה!")
                        
                        # Show content preview
                        with st.expander("תצוגה מקדימה של התוכן"):
                            st.text_area("תוכן האתר:", website_content, height=200, disabled=True)
                        
                        # Generate summary
                        if st.button("🚀 צור סיכום מהאתר", key="website_summary"):
                            if not api_key:
                                st.error("אנא הכנס מפתח API ב-OpenAI")
                            else:
                                with st.spinner("יוצר סיכום..."):
                                    summary = generate_summary(website_content, api_key, model, summary_length, language)
                                    if summary:
                                        st.session_state.summaries.append({
                                            'type': 'אתר',
                                            'content': url,
                                            'summary': summary,
                                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            'model': model
                                        })
                                        st.success("הסיכום נוצר בהצלחה!")
                                        st.markdown("### 📋 הסיכום שלך:")
                                        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"שגיאה בסריקת האתר: {str(e)}")

def summary_history_tab():
    st.header("📊 היסטוריית סיכומים")
    
    if not st.session_state.summaries:
        st.info("אין עדיין סיכומים בהיסטוריה. צור סיכום ראשון כדי לראות אותו כאן!")
    else:
        st.markdown(f"### סה״כ סיכומים: {len(st.session_state.summaries)}")
        
        for i, summary in enumerate(reversed(st.session_state.summaries)):
            with st.expander(f"{summary['type']} - {summary['timestamp']}"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**סוג:** {summary['type']}")
                    st.markdown(f"**מודל:** {summary['model']}")
                    st.markdown(f"**תאריך:** {summary['timestamp']}")
                
                with col2:
                    st.markdown("**תוכן מקורי:**")
                    st.text(summary['content'])
                    st.markdown("**סיכום:**")
                    st.markdown(f'<div class="summary-box">{summary["summary"]}</div>', unsafe_allow_html=True)
                
                # Delete button
                if st.button(f"🗑️ מחק", key=f"delete_{i}"):
                    st.session_state.summaries.pop(len(st.session_state.summaries) - 1 - i)
                    st.rerun()

# Helper functions
def generate_summary(text, api_key, model, length, language):
    """Generate summary using OpenAI API"""
    try:
        openai.api_key = api_key
        
        # Determine summary length
        length_map = {
            "קצר (2-3 משפטים)": "very short",
            "בינוני (5-7 משפטים)": "medium",
            "מפורט (10-15 משפטים)": "detailed"
        }
        
        # Language instructions
        lang_instructions = {
            "עברית": "כתוב את הסיכום בעברית בלבד",
            "English": "Write the summary in English only",
            "עברית + English": "כתוב את הסיכום בעברית ואז באנגלית"
        }
        
        prompt = f"""
        סום את הטקסט הבא ב-{length_map[length]} סיכום:
        
        {text}
        
        הוראות:
        - {lang_instructions[language]}
        - שמור על עובדות מדויקות
        - השתמש בשפה ברורה ומובנת
        - התמקד בנקודות העיקריות
        """
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "אתה מומחה בסיכום טקסטים. צור סיכומים מדויקים, ברורים ומקצועיים."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"שגיאה ביצירת הסיכום: {str(e)}")
        return None

def generate_conversation_summary(conversation, api_key, model, language):
    """Generate conversation summary using OpenAI API"""
    try:
        openai.api_key = api_key
        
        lang_instructions = {
            "עברית": "כתוב את הסיכום בעברית בלבד",
            "English": "Write the summary in English only",
            "עברית + English": "כתוב את הסיכום בעברית ואז באנגלית"
        }
        
        prompt = f"""
        סום את השיחה הבאה:
        
        {conversation}
        
        הוראות:
        - {lang_instructions[language]}
        - זהה את הנושאים העיקריים
        - ציין החלטות שהתקבלו
        - ציין פעולות שצריך לבצע
        - צור סיכום ברור ומאורגן
        """
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "אתה מומחה בסיכום שיחות וצ'אטים. צור סיכומים מאורגנים ומקצועיים."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"שגיאה ביצירת סיכום השיחה: {str(e)}")
        return None

def extract_text_from_document(file):
    """Extract text from uploaded document"""
    try:
        if file.type == "text/plain":
            return str(file.read(), "utf-8")
        
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            return " ".join([paragraph.text for paragraph in doc.paragraphs])
        
        elif file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        
        else:
            st.error("סוג קובץ לא נתמך")
            return None
    
    except Exception as e:
        st.error(f"שגיאה בקריאת הקובץ: {str(e)}")
        return None

def extract_website_content(url):
    """Extract content from website URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit to first 5000 characters
    
    except Exception as e:
        st.error(f"שגיאה בסריקת האתר: {str(e)}")
        return None

if __name__ == "__main__":
    main()