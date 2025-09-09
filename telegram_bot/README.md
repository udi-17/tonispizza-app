## בוט טלגרם (Python)

### הגדרה מהירה

1) קבל טוקן מבוטפאדר (BotFather) בטלגרם.
2) צור קובץ `.env` לפי הדוגמה:

```bash
cp .env.example .env
```

ערוך את `.env` והכנס את הערך ל-`TELEGRAM_BOT_TOKEN`.

### התקנת תלויות

- מומלץ (אם ניתן):

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

- אם יצירת venv נכשלת (לדוגמה חסר ensurepip), ניתן להתקין ישירות:

```bash
pip3 install --break-system-packages -r requirements.txt
```

### הרצה

```bash
# אם יש venv פעיל
python3 bot.py

# או בלי venv (לא מומלץ, אך עובד)
python3 bot.py
```

או פשוט:

```bash
./run.sh
```

### פקודות זמינות בבוט

- `/start` — הודעת פתיחה
- `/help` — עזרה
- `/ping` — בדיקת חיים (Pong)
- Echo — כל הודעת טקסט חוזרת חזרה

### הערות

- הקובץ `.env` לא נשמר ב-git (מוגן ב-`.gitignore`).
- כדי להגדיר Webhook במקום polling יש להוסיף תצורה לפי תשתית האירוח.
