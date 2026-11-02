import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# توكن البوت ومعرف القناة (قناتك الإجبارية)
TOKEN = "9182719246:AAEe07FYrRIgt-gdwQH-U0tM5GpDPuWYPPc"
CHANNEL_USERNAME = "@Iraq_abfa"

# حساب الانستغرام الخاص بك
INSTAGRAM_URL = "https://instagram.com/G0t.5"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# دالة التحقق من اشتراك المستخدم في القناة
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"خطأ في فحص الاشتراك: {e}")
        return False

# تصميم لوحة الأزرار (القناة + الانستغرام + التحقق)
def get_subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn_channel = InlineKeyboardButton(
        text="📢 اشترك في قناة البوت الإجبارية", 
        url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    )
    btn_insta = InlineKeyboardButton(
        text="📸 تابعني على الانستغرام", 
        url=INSTAGRAM_URL
    )
    btn_check = InlineKeyboardButton(
        text="🔄 تم الاشتراك (تحقق)", 
        callback_data="check_sub"
    )
    keyboard.add(btn_channel, btn_insta, btn_check)
    return keyboard

# أمر البدء /start
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await message.answer("✅ أهلاً بك! تم التحقق من اشتراكك. يمكنك الآن كتابة الاسم أو الرقم للبحث في قواعد البيانات.")
    else:
        msg_text = (
            "⚠️ **عذراً عزيزي!**\n\n"
            "لاستخدام البوت والبحث في البيانات، يجب عليك الاشتراك في القناة الرسمية أولاً.\n"
            "اشترك ثم اضغط على زر **(تم الاشتراك)** في الأسفل:"
        )
        await message.answer(msg_text, reply_markup=get_subscribe_keyboard(), parse_mode="Markdown")

# معالجة ضغطة زر التحقق من الاشتراك
@dp.callback_query_handler(lambda c: c.data == 'check_sub')
async def process_check_sub(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await bot.answer_callback_query(callback_query.id, text="✅ شكراً لك! تم تفعيل البحث.")
        await bot.send_message(user_id, "أرسل الآن الاسم أو الرقم الذي تريد البحث عنه.")
    else:
        await bot.answer_callback_query(
            callback_query.id, 
            text="❌ أنت غير مشترك بالقناة بعد! اشترك أولاً ثم أعد المحاولة.", 
            show_alert=True
        )

# دالة البحث داخل جميع ملفات الـ SQLite الموجودة في المجلد
def search_in_db(query: str):
    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    all_results = []

    for db in db_files:
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            
            # جلب اسم الجدول الأول في قاعدة البيانات
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                continue
                
            table_name = tables[0][0]
            
            # جلب أسماء الأعمدة في الجدول
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # إنشاء استعلام البحث عبر كافة الأعمدة النصية والرقيمة
            where_clauses = [f"`{col}` LIKE ?" for col in columns]
            sql_query = f"SELECT * FROM `{table_name}` WHERE " + " OR ".join(where_clauses) + " LIMIT 3"
            
            params = [f"%{query}%"] * len(columns)
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                formatted_data = "\n".join([f"• {col}: {val}" for col, val in zip(columns, row)])
                all_results.append(f"📁 **المحافظة ({db.replace('.db', '')}):**\n{formatted_data}")
                
            conn.close()
        except Exception as e:
            print(f"خطأ أثناء البحث في {db}: {e}")
            
    return all_results

# استقبال طلب البحث من المستخدم
@dp.message_handler()
async def handle_search(message: types.Message):
    user_id = message.from_user.id
    
    # التحقق من الاشتراك قبل السماح بالبحث
    if not await check_subscription(user_id):
        await message.answer(
            "⚠️ لا يمكنك البحث قبل الاشتراك في القناة!",
            reply_markup=get_subscribe_keyboard()
        )
        return

    query = message.text.strip()
    await message.answer(f"🔎 جاري البحث عن: `{query}` ...", parse_mode="Markdown")

    results = search_in_db(query)
    
    if results:
        for res in results[:5]: 
            await message.answer(res, parse_mode="Markdown")
    else:
        await message.answer("❌ لم يتم العثور على أي مطابقة لهذه البيانات.")

if __name__ == '__main__':
    print("البوت يعمل بنجاح...")
    executor.start_polling(dp, skip_updates=True)
