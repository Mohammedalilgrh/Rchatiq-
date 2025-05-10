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
user_balances = {}

# التحقق من الاشتراك في القنوات
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

# واجهة البوت الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # نظام الدعوة
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id != user_id:
                if referrer_id not in referral_system:
                    referral_system[referrer_id] = {'invites': 0, 'level': 1, 'earnings': 0}
                referral_system[referrer_id]['invites'] += 1
                referral_system[referrer_id]['earnings'] += 0.10
                
                # تحديث رصيد المدعو
                if referrer_id not in user_balances:
                    user_balances[referrer_id] = 0
                user_balances[referrer_id] += 0.10
                
                bot.send_message(referrer_id, f"🎉 تم انضمام عضو جديد عبر دعوتك! ربحت 0.10$\nالعدد الإجمالي: {referral_system[referrer_id]['invites']}\nرصيدك الحالي: {user_balances[referrer_id]:.2f}$")
                
                # ترقية المستوى عند الوصول إلى 2$
                if user_balances[referrer_id] >= 2 and referral_system[referrer_id]['level'] < 5:
                    referral_system[referrer_id]['level'] = 5
                    bot.send_message(referrer_id, "🎊 تم ترقيتك إلى المستوى 5! ميزات جديدة:\n• أولوية في البحث عن شركاء\n• مدة محادثة 20 دقيقة بدلاً من 10\n• مكافآت دعوة مضاعفة")
        except:
            pass
    
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
    else:
        show_main_menu(user_id)

# عرض طلب الاشتراك
def show_subscription_request(user_id):
    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(
            text=f"انضم إلى {channel}",
            url=f"https://t.me/{channel[1:]}"
        ))
    markup.add(types.InlineKeyboardButton(
        text="✅ لقد اشتركت",
        callback_data="check_subscription"
    ))
    
    bot.send_message(
        user_id,
        "🔒 يجب الاشتراك في القنوات التالية:",
        reply_markup=markup
    )

# القائمة الرئيسية
def show_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 ابدأ الدردشة"),
        types.KeyboardButton("📊 إحصائياتي"),
        types.KeyboardButton("📣 دعوة أصدقاء"),
        types.KeyboardButton("💰 سحب أرباحي"),
        types.KeyboardButton("ℹ️ المساعدة")
    )
    
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    bot.send_message(
        user_id,
        f"""🎭 مرحبا بك في بوت الدردشة المجهولة!

• محادثات 100% مجهولة
• مكافآت دعوة الأصدقاء
• نظام هرمي بمزايا متعددة

اختر أحد الخيارات من القائمة:""",
        reply_markup=markup
    )

# التحقق من الاشتراك
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ تم التحقق من اشتراكك!")
        show_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات المطلوبة!")
        show_subscription_request(user_id)

# بدء الدردشة
@bot.message_handler(func=lambda message: message.text == "🚀 ابدأ الدردشة")
def start_chat(message):
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
        return
    
    for chat_pair in active_chats:
        if user_id in chat_pair:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton("⏭ إنهاء المحادثة"),
                types.KeyboardButton("🔎 البحث عن شريك جديد")
            )
            bot.send_message(user_id, "⚠️ أنت بالفعل في دردشة نشطة!", reply_markup=markup)
            return
    
    if user_id in waiting_users:
        bot.send_message(user_id, "⏳ أنت في قائمة الانتظار، جاري البحث عن شريك...")
        return
    
    waiting_users.append(user_id)
    bot.send_message(user_id, "🔎 جاري البحث عن شريك دردشة...")
    
    if len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        
        start_time = time.time()
        chat_duration = 600 if referral_system.get(user1, {}).get('level', 1) < 5 or referral_system.get(user2, {}).get('level', 1) < 5 else 1200
        active_chats[(user1, user2)] = (start_time, chat_duration)
        
        for user in [user1, user2]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton("⏭ إنهاء المحادثة"),
                types.KeyboardButton("🔎 البحث عن شريك جديد")
            )
            
            duration_msg = "10 دقائق" if referral_system.get(user, {}).get('level', 1) < 5 else "20 دقائق"
            
            bot.send_message(
                user,
                f"🎉 تم العثور على شريك دردشة!\n\n"
                f"• المحادثة مجهولة تماماً\n"
                f"• مدة المحادثة: {duration_msg}\n"
                f"• اختر أحد الخيارات أدناه",
                reply_markup=markup
            )
            
            Thread(target=countdown_timer, args=(user, start_time, chat_duration)).start()

# عد تنازلي للمحادثة
def countdown_timer(user_id, start_time, duration):
    remaining = duration
    last_alert = 0
    
    while remaining > 0:
        time.sleep(1)
        remaining = duration - (time.time() - start_time)
        
        if int(remaining / 60) > last_alert:
            last_alert = int(remaining / 60)
            if last_alert > 0:
                bot.send_message(user_id, f"⏳ متبقي {last_alert} دقيقة على انتهاء المحادثة")
    
    end_chat(user_id)

# إنهاء المحادثة
@bot.message_handler(func=lambda message: message.text == "⏭ إنهاء المحادثة")
def end_chat_handler(message):
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
            
            if user not in user_stats:
                user_stats[user] = {'chats': 0, 'last_chat': None}
            user_stats[user]['chats'] += 1
            user_stats[user]['last_chat'] = time.time()
            
            show_main_menu(user)

# البحث عن شريك جديد
@bot.message_handler(func=lambda message: message.text == "🔎 البحث عن شريك جديد")
def find_new_partner(message):
    user_id = message.from_user.id
    
    # إنهاء المحادثة الحالية إذا كان في واحدة
    end_chat(user_id)
    
    # البدء في البحث عن شريك جديد
    start_chat(message)

# عرض الإحصائيات
@bot.message_handler(func=lambda message: message.text == "📊 إحصائياتي")
def show_stats(message):
    user_id = message.from_user.id
    
    if user_id not in user_stats:
        user_stats[user_id] = {
            'chats': 0,
            'last_chat': None
        }
    
    stats = user_stats[user_id]
    last_chat = "لم تقم بأي دردشة بعد"
    if stats['last_chat']:
        last_chat = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats['last_chat']))
    
    balance = user_balances.get(user_id, 0)
    level = referral_system.get(user_id, {}).get('level', 1)
    
    bot.send_message(
        user_id,
        f"""📊 إحصائياتك الشخصية:

• عدد المحادثات: {stats['chats']}
• آخر محادثة: {last_chat}
• رصيدك الحالي: {balance:.2f}$
• مستواك الحالي: {level}
• المستخدمين النشطين الآن: {len(waiting_users) + len(active_chats)*2}"""
    )

# نظام الدعوة
@bot.message_handler(func=lambda message: message.text == "📣 دعوة أصدقاء")
def invite_friends(message):
    user_id = message.from_user.id
    
    if user_id not in referral_system:
        referral_system[user_id] = {'invites': 0, 'level': 1, 'earnings': 0}
    
    invite_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    balance = user_balances.get(user_id, 0)
    
    bot.send_message(
        user_id,
        f"""📣 نظام الدعوة الهرمي:

رابط دعوتك الخاص:
{invite_link}

🎁 لكل صديق تدعوه:
• تربح 0.10$ مباشرة
• عند وصول رصيدك لـ 2$، يتم ترقيتك للمستوى 5 تلقائياً

إحصائياتك:
├ عدد المدعوين: {referral_system[user_id]['invites']}
├ رصيدك الحالي: {balance:.2f}$
└ المستوى الحالي: {referral_system[user_id]['level']}

شارك الرابط مع أصدقائك واحصل على مكافآت!"""
    )

# سحب الأرباح
@bot.message_handler(func=lambda message: message.text == "💰 سحب أرباحي")
def withdraw_earnings(message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)
    
    if balance < 2:
        bot.send_message(
            user_id,
            f"❌ رصيدك الحالي {balance:.2f}$ غير كافي للسحب (الحد الأدنى 2$)\n\n"
            "📣 ادعُ المزيد من الأصدقاء لزيادة رصيدك:\n"
            f"https://t.me/{(bot.get_me()).username}?start={user_id}"
        )
    else:
        # هنا يمكنك إضافة طريقة السحب الفعلية (PayPal، تحويل بنكي، إلخ)
        user_balances[user_id] = 0
        referral_system[user_id]['earnings'] += balance
        
        bot.send_message(
            user_id,
            f"✅ تم تقديم طلب سحب بقيمة {balance:.2f}$\n"
            "سيتم التحويل خلال 24-48 ساعة\n\n"
            "شكراً لاستخدامك بوتنا!"
        )

# المساعدة
@bot.message_handler(func=lambda message: message.text == "ℹ️ المساعدة")
def show_help(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        """ℹ️ كيفية استخدام البوت:

1. اضغط "🚀 ابدأ الدردشة" للبحث عن شريك
2. استمتع بمحادثة مجهولة
3. يمكنك إنهاء المحادثة أو البحث عن شريك جديد
4. ادعُ أصدقائك لربح 0.10$ لكل دعوة
5. اسحب أرباحك عند الوصول لـ 2$

📣 لدعوة أصدقاء:
• شارك رابط الدعوة الخاص بك
• كلما زاد عدد المدعوين، زادت مكافآتك

للإبلاغ عن مشاكل، راسل الدعم الفني"""
    )

# معالجة الرسائل بين المستخدمين
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        show_subscription_request(user_id)
        return
    
    for pair in active_chats:
        if user_id in pair:
            partner = pair[0] if pair[1] == user_id else pair[1]
            try:
                bot.send_message(partner, message.text)
            except:
                end_chat(user_id)
            return
    
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
