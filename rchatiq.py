import os
import random
import time
from threading import Thread
from flask import Flask, request
import telebot
from telebot import types

# تهيئة البوت
TOKEN = '7716562183:AAEj_V9wzIYpd4THmG5TvOOTg9a7crvNo98'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# قنوات الاشتراك الإجباري
REQUIRED_CHANNELS = ['@Rchatiq', '@Rchatiqgroup']

# بيانات المستخدمين
waiting_users = []
active_chats = {}
user_stats = {}
referral_system = {}  # نظام الدعوة الهرمي

# التحقق من الاشتراك في القنوات
def is_subscribed(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except:
        return False

# واجهة البوت الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # نظام الدعوة الهرمي
    if len(message.text.split()) > 1:
        referrer_id = int(message.text.split()[1])
        if referrer_id != user_id and referrer_id in referral_system:
            referral_system[referrer_id]['invites'] += 1
            bot.send_message(referrer_id, f"🎉 تم انضمام عضو جديد عبر دعوتك! العدد الإجمالي: {referral_system[referrer_id]['invites']}")
    
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        for channel in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(text=f"اشترك في {channel}", url=f"https://t.me/{channel[1:]}"))
        markup.add(types.InlineKeyboardButton(text="✅ تأكد من الاشتراك", callback_data="check_subscription"))
        
        bot.send_message(user_id, "⚠️ يجب الاشتراك في القنوات التالية أولاً:", reply_markup=markup)
    else:
        show_main_menu(user_id)

def show_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 ابدأ الدردشة"))
    markup.add(types.KeyboardButton("📊 إحصائياتي"))
    markup.add(types.KeyboardButton("📣 دعوة أصدقاء"))
    
    # إضافة رابط الدعوة الخاص بالمستخدم
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    bot.send_message(user_id, f"""
🎭 مرحبا بك في بوت الدردشة المجهولة!

• كل المحادثات مجهولة 100%
• مدة كل محادثة 10 دقائق
• يمكنك التخطي في أي وقت

📣 لدعوة أصدقاء واستلام مكافآت:
{invite_link}

اضغط على 🚀 ابدأ الدردشة للبدء!
    """, reply_markup=markup)

# نظام الدعوة
@bot.message_handler(func=lambda message: message.text == "📣 دعوة أصدقاء")
def invite_friends(message):
    user_id = message.from_user.id
    
    if user_id not in referral_system:
        referral_system[user_id] = {'invites': 0, 'level': 1}
    
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    bot.send_message(user_id, f"""
📣 نظام الدعوة الهرمي:

• كلما دعوت أصدقاء أكثر، زادت مكافآتك!
• الرابط الخاص بك:
{invite_link}

عدد المدعوين: {referral_system[user_id]['invites']}
المستوى الحالي: {referral_system[user_id]['level']}
""")

# باقي الكود كما هو (مثل بدء الدردشة، العد التنازلي، إنهاء المحادثة...)
# [يتم وضع باقي الكود السابق هنا دون تغيير]

# تشغيل البوت
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://your-render-app.onrender.com/7716562183:AAEj_V9wzIYpd4THmG5TvOOTg9a7crvNo98')
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
