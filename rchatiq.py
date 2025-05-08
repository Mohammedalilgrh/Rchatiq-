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
referral_system = {}

# التحقق من الاشتراك في القنوات (معدل)
def is_subscribed(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# واجهة البوت الرئيسية (معدلة)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # نظام الدعوة
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id != user_id:
                if referrer_id not in referral_system:
                    referral_system[referrer_id] = {'invites': 0, 'level': 1}
                referral_system[referrer_id]['invites'] += 1
                bot.send_message(referrer_id, f"🎉 تم انضمام عضو جديد عبر دعوتك! العدد الإجمالي: {referral_system[referrer_id]['invites']}")
        except:
            pass
    
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
    else:
        show_main_menu(user_id)

# عرض طلب الاشتراك (جديد)
def show_subscription_request(user_id):
    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(
            text=f"انضم إلى {channel}",
            url=f"https://t.me/{channel[1:]}"
        ))
    markup.add(types.InlineKeyboardButton(
        text="✅ لقد اشتركت بالفعل",
        callback_data="check_subscription"
    ))
    
    bot.send_message(
        user_id,
        "🔒 لتتمكن من استخدام البوت، يجب الاشتراك في القنوات التالية:\n\n" +
        "\n".join([f"• {channel}" for channel in REQUIRED_CHANNELS]) +
        "\n\nبعد الاشتراك، اضغط على الزر أدناه للتحقق",
        reply_markup=markup
    )

# القائمة الرئيسية (معدلة)
def show_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 ابدأ الدردشة"),
        types.KeyboardButton("📊 إحصائياتي"),
        types.KeyboardButton("📣 دعوة أصدقاء"),
        types.KeyboardButton("ℹ️ المساعدة")
    )
    
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    bot.send_message(
        user_id,
        f"""🎭 مرحبا بك في بوت الدردشة المجهولة!

• محادثات 100% مجهولة
• مدة كل محادثة: 10 دقائق
• يمكنك التخطي في أي وقت

📣 رابط دعوة الأصدقاء:
{invite_link}

اختر أحد الخيارات من القائمة:""",
        reply_markup=markup
    )

# التحقق من الاشتراك (معدل)
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ تم التحقق من اشتراكك!")
        show_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات المطلوبة!")
        show_subscription_request(user_id)

# بدء الدردشة (معدل)
@bot.message_handler(func=lambda message: message.text == "🚀 ابدأ الدردشة")
def start_chat(message):
    user_id = message.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
        return
    
    # التحقق إذا كان المستخدم في دردشة بالفعل
    for chat_pair in active_chats:
        if user_id in chat_pair:
            bot.send_message(user_id, "⚠️ أنت بالفعل في دردشة نشطة!")
            return
    
    # التحقق إذا كان في قائمة الانتظار
    if user_id in waiting_users:
        bot.send_message(user_id, "⏳ أنت في قائمة الانتظار، جاري البحث عن شريك...")
        return
    
    # إضافة المستخدم لقائمة الانتظار
    waiting_users.append(user_id)
    bot.send_message(user_id, "🔎 جاري البحث عن شريك دردشة...")
    
    # محاولة إيجاد شريك إذا كان هناك مستخدمين آخرين في الانتظار
    if len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        
        start_time = time.time()
        active_chats[(user1, user2)] = start_time
        
        for user in [user1, user2]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("⏭ إنهاء المحادثة"))
            
            bot.send_message(
                user,
                "🎉 تم العثور على شريك دردشة!\n\n"
                "• المحادثة مجهولة تماماً\n"
                "• مدة المحادثة: 10 دقائق\n"
                "• اضغط ⏭ إنهاء المحادثة للخروج",
                reply_markup=markup
            )
            
            # بدء العد التنازلي
            Thread(target=countdown_timer, args=(user, start_time)).start()

# عد تنازلي للمحادثة (معدل)
def countdown_timer(user_id, start_time):
    remaining = 600  # 10 دقائق
    last_alert = 0
    
    while remaining > 0:
        time.sleep(1)
        remaining = 600 - (time.time() - start_time)
        
        # إرسال تنبيه كل دقيقة
        if int(remaining / 60) > last_alert:
            last_alert = int(remaining / 60)
            if last_alert > 0:  # لا تنبيه عند انتهاء الوقت
                bot.send_message(user_id, f"⏳ متبقي {last_alert} دقيقة على انتهاء المحادثة")
    
    # انتهاء الوقت
    end_chat(user_id)

# إنهاء المحادثة (معدل)
@bot.message_handler(func=lambda message: message.text == "⏭ إنهاء المحادثة")
def skip_chat(message):
    end_chat(message.from_user.id)

def end_chat(user_id):
    chat_pair = None
    for pair in list(active_chats.keys()):
        if user_id in pair:
            chat_pair = pair
            break
    
    if chat_pair:
        user1, user2 = chat_pair
        del active_chats[chat_pair]
        
        for user in [user1, user2]:
            if user != user_id:
                bot.send_message(user, "تم إنهاء المحادثة.", reply_markup=types.ReplyKeyboardRemove())
            
            # تحديث الإحصائيات
            if user not in user_stats:
                user_stats[user] = {'chats': 0, 'last_chat': None}
            user_stats[user]['chats'] += 1
            user_stats[user]['last_chat'] = time.time()
            
            show_main_menu(user)

# عرض الإحصائيات (معدل)
@bot.message_handler(func=lambda message: message.text == "📊 إحصائياتي")
def show_stats(message):
    user_id = message.from_user.id
    
    # تهيئة الإحصائيات إذا لم تكن موجودة
    if user_id not in user_stats:
        user_stats[user_id] = {
            'chats': 0,
            'last_chat': None,
            'invites': referral_system.get(user_id, {}).get('invites', 0)
        }
    
    stats = user_stats[user_id]
    last_chat = "لم تقم بأي دردشة بعد"
    if stats['last_chat']:
        last_chat = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats['last_chat']))
    
    bot.send_message(
        user_id,
        f"""📊 إحصائياتك الشخصية:

• عدد المحادثات: {stats['chats']}
• آخر محادثة: {last_chat}
• عدد المدعوين: {stats.get('invites', 0)}
• المستخدمين النشطين الآن: {len(waiting_users) + len(active_chats)*2}"""
    )

# نظام الدعوة (معدل)
@bot.message_handler(func=lambda message: message.text == "📣 دعوة أصدقاء")
def invite_friends(message):
    user_id = message.from_user.id
    
    if user_id not in referral_system:
        referral_system[user_id] = {'invites': 0, 'level': 1}
    
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    bot.send_message(
        user_id,
        f"""📣 نظام الدعوة الهرمي:

رابط دعوتك الخاص:
{invite_link}

• كل صديق يدعوه صديقك سيزيد من مستواك
• المكافآت تزداد مع كل مستوى

إحصائياتك:
├ عدد المدعوين: {referral_system[user_id]['invites']}
└ المستوى الحالي: {referral_system[user_id]['level']}

شارك الرابط مع أصدقائك واحصل على مكافآت!"""
    )

# المساعدة (جديد)
@bot.message_handler(func=lambda message: message.text == "ℹ️ المساعدة")
def show_help(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        """ℹ️ كيفية استخدام البوت:

1. اشترك في القنوات المطلوبة
2. اضغط "🚀 ابدأ الدردشة" للبحث عن شريك
3. استمتع بمحادثة مجهولة لمدة 10 دقائق
4. يمكنك إنهاء المحادثة في أي وقت

📣 لدعوة أصدقاء:
• شارك رابط الدعوة الخاص بك
• كلما زاد عدد المدعوين، زادت مكافآتك

للإبلاغ عن مشاكل، راسل الدعم الفني"""
    )

# معالجة الرسائل بين المستخدمين (معدل)
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
        return
    
    # البحث عن شريك الدردشة
    for pair in active_chats:
        if user_id in pair:
            partner = pair[0] if pair[1] == user_id else pair[1]
            try:
                bot.send_message(partner, message.text)
            except:
                end_chat(user_id)
            return
    
    # إذا لم يكن في دردشة
    bot.send_message(
        user_id,
        "لإرسال رسالة، يجب أن تكون في دردشة نشطة.\nاضغط 🚀 ابدأ الدردشة للبدء."
    )

# تشغيل البوت
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://rchatiq.onrender.com/7716562183:AAEj_V9wzIYpd4THmG5TvOOTg9a7crvNo98')
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
