#!/bin/bash

echo "🤖 מפעיל בוט שליחויות מתקדם..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 לא מותקן במערכת"
    echo "אנא התקן Python3 ונסה שוב"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 לא מותקן במערכת"
    echo "אנא התקן pip3 ונסה שוב"
    exit 1
fi

# Install requirements
echo "📦 מתקין תלויות..."
pip3 install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  קובץ .env לא נמצא"
    echo "יוצר קובץ .env לדוגמה..."
    
    cat > .env << EOF
# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Twilio Settings
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

# Telegram Settings
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# WhatsApp Settings
WHATSAPP_API_KEY=your_api_key
WHATSAPP_PHONE_NUMBER=your_whatsapp_number
EOF
    
    echo "✅ קובץ .env נוצר. אנא ערוך אותו עם הפרטים שלך"
    echo "לאחר העריכה, הפעל שוב את הסקריפט"
    exit 0
fi

# Run the bot
echo "🚀 מפעיל את הבוט..."
echo "הבוט ייפתח בדפדפן בכתובת: http://localhost:8501"
echo "לעצירה לחץ Ctrl+C"

streamlit run delivery_bot.py