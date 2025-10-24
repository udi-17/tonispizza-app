# בוט סיכומים לטלגרם – משרד שליחויות

בוט טלגרם לניהול משלוחים, לקוחות, שליחים, וסיכומים יומיים/בטווחי תאריכים, כולל יצוא CSV ותזמון אוטומטי.

## יכולות
- רישום משתמשים ותפקידי גישה (admin/manager/courier/viewer)
- ניהול לקוחות (הוספה, חיפוש)
- ניהול משלוחים (יצירה, שיבוץ שליח, עדכון סטטוס)
- סיכומים לפי טווח תאריכים, לפי שליח/לקוח
- יצוא CSV
- תזמון סיכום יומי אוטומטי לצ'אט

## התקנה
1. צרו סביבת וירטואלית והתקינו תלויות:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r telegram_courier_bot/requirements.txt
```

2. צרו קובץ `.env` לפי הדוגמה:
```bash
cp telegram_courier_bot/.env.example telegram_courier_bot/.env
```
ערכו את `BOT_TOKEN` וערכים נוספים לפי הצורך.

3. הריצו את הבוט:
```bash
python -m telegram_courier_bot.main
```

## משתני סביבה (`.env`)
- `BOT_TOKEN`: הטוקן מבוט-פאדר
- `ADMIN_CHAT_ID`: מזהה צ'אט לקבלת סיכומים (אופציונלי)
- `DB_URL`: נתיב מסד הנתונים (SQLite כברירת מחדל)
- `TIMEZONE`: אזור זמן ברירת מחדל (למשל `Asia/Jerusalem`)

## פקודות עיקריות
- `/start` — התחלה ורישום
- `/help` — עזרה
- `/whoami` — פרטי משתמש ותפקיד
- `/setrole @username role` — שינוי תפקיד (admin/manager בלבד)
- `/addclient name | phone | address` — הוספת לקוח
- `/listclients [query]` — חיפוש לקוחות
- `/newdelivery client_id | pickup | dropoff | price | YYYY-MM-DD` — יצירת משלוח
- `/assign delivery_id @courier` — שיבוץ שליח
- `/status delivery_id new_status [note]` — עדכון סטטוס (created/assigned/picked_up/in_transit/delivered/canceled/failed)
- `/summary [today|yesterday|YYYY-MM-DD|YYYY-MM-DD..YYYY-MM-DD] [courier:@u|client:id]` — סיכום
- `/exportcsv [אותו טווח כמו /summary]` — יצוא CSV
- `/schedule_daily HH:MM [TZ]` — תזמון סיכום יומי לצ'אט הנוכחי
- `/unschedule` — ביטול תזמון

## הערות
- ציבור השליחים מזוהים כמשתמשים עם תפקיד `courier`. מנהלים יכולים לשנות תפקידים באמצעות `/setrole` לאחר שהמשתמש עשה `/start` פעם אחת.
- קלטי פקודות נוחים בפורמט `|` כדי להימנע מדו-שיחים מורכבים.
- קבצי CSV נשמרים בתיקייה `exports/` ונשלחים כקובץ בצ'אט.
