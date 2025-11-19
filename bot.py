import logging
from typing import Optional
from telebot import TeleBot, types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
import asyncio
import aiohttp
import json

import config
from database import db
from ton_handler import ton_handler
from app.db.models import UserStateStage

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = TeleBot(config.BOT_TOKEN, state_storage=StateMemoryStorage())

# تعريف حالات المحادثة
class UserStates:
    waiting_for_stars = "waiting_for_stars"
    waiting_for_payment = "waiting_for_payment"
    waiting_for_wallet = "waiting_for_wallet"
    confirming_wallet = "confirming_wallet"

# لوحات المفاتيح
def get_start_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(types.KeyboardButton("بدء عملية البيع 💫"))
    return keyboard

def get_cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("إلغاء العملية ❌"))
    return keyboard

def get_wallet_confirmation_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("تأكيد العنوان ✅"))
    keyboard.add(types.KeyboardButton("إلغاء العملية ❌"))
    return keyboard

def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(types.KeyboardButton("بدء عملية البيع 💫"))
    keyboard.add(types.KeyboardButton("سجل المعاملات 📊"))
    return keyboard


DB_STAGE_TO_BOT_STATE = {
    UserStateStage.WAITING_FOR_STARS: UserStates.waiting_for_stars,
    UserStateStage.WAITING_FOR_PAYMENT: UserStates.waiting_for_payment,
    UserStateStage.WAITING_FOR_WALLET: UserStates.waiting_for_wallet,
    UserStateStage.CONFIRMING_WALLET: UserStates.confirming_wallet,
}


def _update_memory_state_from_persistent(user_id: int, user_state) -> None:
    with bot.retrieve_data(user_id) as data:
        if user_state.stars_count is not None:
            data['stars_count'] = user_state.stars_count
        if user_state.ton_amount is not None:
            data['ton_amount'] = user_state.ton_amount
        if user_state.payment_charge_id:
            data['payment_charge_id'] = user_state.payment_charge_id
        if user_state.wallet_address:
            data['wallet_address'] = user_state.wallet_address


def restore_user_state_if_needed(message) -> bool:
    user_id = message.from_user.id
    user_state = db.get_user_state(user_id)
    if not user_state or user_state.stage == UserStateStage.IDLE:
        return False

    telebot_state = DB_STAGE_TO_BOT_STATE.get(user_state.stage)
    if telebot_state:
        bot.set_state(user_id, telebot_state)
    _update_memory_state_from_persistent(user_id, user_state)

    stars = user_state.stars_count or 0
    ton_amount = user_state.ton_amount or (stars * config.STAR_PRICE_TON)

    if user_state.stage == UserStateStage.WAITING_FOR_STARS:
        resume_text = (
            "⚠️ **متابعة العملية**\n\n"
            "لديك عملية بيع غير مكتملة.\n"
            "أرسل عدد النجوم الذي ترغب في بيعه لاستكمال العملية."
        )
        markup = get_cancel_keyboard()
    elif user_state.stage == UserStateStage.WAITING_FOR_PAYMENT:
        resume_text = (
            "💳 **في انتظار الدفع**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n\n"
            "أكمل دفع الفاتورة التي استلمتها أو ألغ العملية لإعادة البدء."
        )
        markup = get_cancel_keyboard()
    elif user_state.stage == UserStateStage.WAITING_FOR_WALLET:
        resume_text = (
            "💎 **دفع مكتمل**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n\n"
            "الرجاء إرسال عنوان محفظة TON الخاصة بك لإتمام التحويل."
        )
        markup = get_cancel_keyboard()
    else:
        resume_text = (
            "✅ **تم استلام العنوان**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n"
            f"العنوان الحالي: {user_state.wallet_address or 'غير متوفر'}\n\n"
            "اضغط على 'تأكيد العنوان ✅' لمتابعة التحويل أو قم بإلغائها."
        )
        markup = get_wallet_confirmation_keyboard()

    bot.send_message(message.chat.id, resume_text, reply_markup=markup, parse_mode="Markdown")
    return True

# معالجة الأمر /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # إضافة/تحديث المستخدم في قاعدة البيانات
    db.add_user(user_id, username, full_name)
    
    # إنشاء لوحة المفاتيح
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton("بدء عملية البيع 💫"))
    
    # رسالة الترحيب
    welcome_text = f"""
مرحباً {full_name or 'عزيزي'} 👋

⚡️ **وظيفة البوت**:  
أنا بوت متخصص لشراء **النجوم** منك مقابل عملات **TON**.

💰 **سعر الصرف**:  
سعر النجم الواحد = {config.STAR_PRICE_USD}$  
أي أن كل نجم يعادل {config.STAR_PRICE_TON:.6f} TON

🚀 **كيفية البيع**:  
1️⃣ اضغط على زر 'بدء عملية البيع'  
2️⃣ أرسل عدد النجوم التي تريد بيعها  
3️⃣ سنقوم بإنشاء فاتورة دفع للنجوم  
4️⃣ بعد الدفع، أرسل عنوان محفظتك على Tonkeeper  
5️⃣ سنقوم بتحويل TON لك فور التأكد

اضغط على الزر أدناه لبدء عملية البيع!
    """
    
    try:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")
        logger.info(f"User {user_id} started the bot - keyboard sent successfully")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # إعادة المحاولة بدون تنسيق
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    if restore_user_state_if_needed(message):
        return

# معالجة زر بدء عملية البيع
@bot.message_handler(func=lambda message: message.text == "بدء عملية البيع 💫")
def start_selling(message):
    user_id = message.from_user.id
    
    # التحقق من رصيد محفظة البوت
    try:
        success, balance = asyncio.run(ton_handler.get_balance())
        if not success:
            bot.send_message(message.chat.id, 
                           "❌ **عذراً**\n\nحالياً لا يمكن بدء عملية بيع بسبب مشاكل تقنية. يرجى المحاولة لاحقاً.", 
                           reply_markup=get_start_keyboard())
            return
        
        if balance < 1.0:  # إذا كان الرصيد أقل من 1 TON
            bot.send_message(message.chat.id, 
                           f"⚠️ **تنبيه**\n\nرصيد البوت الحالي: {balance:.6f} TON\nقد لا يكون كافياً لعمليات البيع الكبيرة.", 
                           reply_markup=get_cancel_keyboard())
        
        bot.send_message(message.chat.id, 
                        "📤 **حسناً!**\n\nالآن قم بإرسال **عدد النجوم** التي تريد بيعها:\n\n- يجب أن يكون العدد رقماً صحيحاً\n- مثال: 100", 
                        reply_markup=get_cancel_keyboard())
        
        bot.set_state(message.from_user.id, UserStates.waiting_for_stars)
        db.set_user_state(user_id, UserStateStage.WAITING_FOR_STARS)
        logger.info(f"User {user_id} started selling process")
        
    except Exception as e:
        logger.error(f"Error in start_selling: {e}")
        bot.send_message(message.chat.id, 
                        "❌ حدث خطأ تقني. يرجى المحاولة مرة أخرى.", 
                        reply_markup=get_start_keyboard())

# معالجة إدخال عدد النجوم
@bot.message_handler(func=lambda message: bot.get_state(message.from_user.id) == UserStates.waiting_for_stars)
def process_stars_count(message):
    user_id = message.from_user.id
    
    if message.text == "إلغاء العملية ❌":
        cancel_operation(message)
        return
    
    try:
        stars_count = int(message.text)
        if stars_count <= 0:
            bot.send_message(message.chat.id, 
                           "❌ **خطأ في العدد**\n\nيرجى إدخال عدد صحيح أكبر من الصفر:\nمثال: 50", 
                           reply_markup=get_cancel_keyboard())
            return
        
        if stars_count > 10000:  # حد أقصى للسلامة
            bot.send_message(message.chat.id, 
                           "❌ **العدد كبير جداً**\n\nيرجى إدخال عدد أقل من 10000 نجمة", 
                           reply_markup=get_cancel_keyboard())
            return
        
        # حساب قيمة TON
        ton_amount = stars_count * config.STAR_PRICE_TON
        
        # التحقق من رصيد البوت
        success, balance = asyncio.run(ton_handler.get_balance())
        if success and balance < ton_amount:
            bot.send_message(message.chat.id, 
                           f"❌ **رصيد غير كافي**\n\nرصيد البوت الحالي: {balance:.6f} TON\nالمبلغ المطلوب: {ton_amount:.6f} TON\n\nيرجى المحاولة بعدد أقل من النجوم.", 
                           reply_markup=get_cancel_keyboard())
            return
        
        # حفظ البيانات في حالة المستخدم
        with bot.retrieve_data(user_id) as data:
            data['stars_count'] = stars_count
            data['ton_amount'] = ton_amount
        
        db.set_user_state(
            user_id,
            UserStateStage.WAITING_FOR_STARS,
            stars_count=stars_count,
            ton_amount=ton_amount,
        )
        
        # إنشاء فاتورة الدفع للنجوم
        try:
            prices = [types.LabeledPrice(label=f"{stars_count} نجمة", amount=stars_count)]
            
            # إرسال فاتورة الدفع
            bot.send_invoice(
                message.chat.id,
                title=f"بيع {stars_count} نجمة",
                description=f"بيع {stars_count} نجمة مقابل {ton_amount:.6f} TON",
                provider_token=config.PAYMENT_PROVIDER_TOKEN,
                currency="XTR",
                prices=prices,
                start_parameter="stars-sale",
                invoice_payload=f"stars_payment_{user_id}_{stars_count}"
            )
            
            bot.send_message(message.chat.id, 
                           "💎 **تم إنشاء فاتورة الدفع**\n\nاضغط على الزر أعلاه لدفع النجوم.", 
                           reply_markup=get_cancel_keyboard())
            bot.set_state(user_id, UserStates.waiting_for_payment)
            db.set_user_state(
                user_id,
                UserStateStage.WAITING_FOR_PAYMENT,
                stars_count=stars_count,
                ton_amount=ton_amount,
            )
            logger.info(f"Invoice created for user {user_id}: {stars_count} stars")
            
        except Exception as e:
            logger.error(f"Error creating invoice for user {user_id}: {e}")
            bot.send_message(message.chat.id, 
                           "❌ **خطأ في إنشاء الفاتورة**\n\nيرجى المحاولة مرة أخرى.", 
                           reply_markup=get_cancel_keyboard())
        
    except ValueError:
        bot.send_message(message.chat.id, 
                       "❌ **إدخال غير صحيح**\n\nيرجى إدخال عدد صحيح فقط:\nمثال: 100", 
                       reply_markup=get_cancel_keyboard())


@bot.message_handler(func=lambda message: bot.get_state(message.from_user.id) == UserStates.waiting_for_payment)
def remind_pending_payment(message):
    if message.text == "إلغاء العملية ❌":
        cancel_operation(message)
        return
    bot.send_message(
        message.chat.id,
        "⌛️ **الفاتورة قيد الانتظار**\n\n"
        "تم إنشاء فاتورة النجوم، يرجى إتمام الدفع عبر الزر الظاهر أعلى الدردشة.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown",
    )

# معالجة PreCheckoutQuery
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        logger.info(f"Pre-checkout processed for user {pre_checkout_query.from_user.id}")
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="حدث خطأ في المعالجة")

# معالجة الدفع الناجح
@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    try:
        # استخراج عدد النجوم من payload
        payload_parts = payment_info.invoice_payload.split('_')
        if len(payload_parts) >= 4:
            stars_count = int(payload_parts[3])
            
            # حساب قيمة TON
            ton_amount = stars_count * config.STAR_PRICE_TON
            
            # حفظ البيانات في حالة المستخدم
            with bot.retrieve_data(user_id) as data:
                data['stars_count'] = stars_count
                data['ton_amount'] = ton_amount
                data['payment_charge_id'] = payment_info.telegram_payment_charge_id
        
        db.set_user_state(
            user_id,
            UserStateStage.WAITING_FOR_WALLET,
            stars_count=stars_count,
            ton_amount=ton_amount,
            payment_charge_id=payment_info.telegram_payment_charge_id,
        )
            
            # نص نجاح الدفع
            success_text = f"""
🎉 **تم استلام الدفع بنجاح!**

⭐ **عدد النجوم المستلمة:** {stars_count}  
💎 **المبلغ المستحق:** {ton_amount:.6f} TON  
🆔 **معرّف الدفع:** {payment_info.telegram_payment_charge_id}

**الآن قم بإرسال عنوان محفظتك على Tonkeeper:**
- يجب أن يبدأ العنوان بـ EQ أو UQ
- تأكد من صحة العنوان لأنه لا يمكن استرجاع الأموال
            """
            
            bot.send_message(message.chat.id, success_text, reply_markup=get_cancel_keyboard())
            bot.set_state(user_id, UserStates.waiting_for_wallet)
            logger.info(f"Payment received from user {user_id}: {stars_count} stars")
        else:
            raise ValueError("Invalid payload format")
            
    except Exception as e:
        logger.error(f"Error processing payment for user {user_id}: {e}")
        bot.send_message(message.chat.id, 
                       "❌ **خطأ في معالجة الدفع**\n\nيرجى التواصل مع الدعم.", 
                       reply_markup=get_start_keyboard())
        bot.delete_state(user_id)

# معالجة استلام عنوان المحفظة
@bot.message_handler(func=lambda message: bot.get_state(message.from_user.id) == UserStates.waiting_for_wallet)
def process_wallet_address(message):
    user_id = message.from_user.id
    
    if message.text == "إلغاء العملية ❌":
        cancel_operation(message)
        return
    
    wallet_address = message.text.strip()
    
    # تحقق من عنوان TON
    if not (wallet_address.startswith('EQ') or wallet_address.startswith('UQ') or wallet_address.startswith('0Q')):
        bot.send_message(message.chat.id, 
                       "❌ **عنوان محفظة غير صحيح**\n\nيرجى إرسال عنوان محفظة TON صحيح يبدأ بـ EQ أو UQ\n\nأعد إرسال العنوان الصحيح:", 
                       reply_markup=get_cancel_keyboard())
        return
    
    # التحقق من صحة العنوان عبر TON Center API
    try:
        is_valid = asyncio.run(ton_handler.validate_address(wallet_address))
        if not is_valid:
            bot.send_message(message.chat.id,
                           "❌ **عنوان محفظة غير صحيح**\n\nالعنوان غير صحيح أو غير نشط على شبكة TON.\n\nأعد إرسال العنوان الصحيح:",
                           reply_markup=get_cancel_keyboard())
            return
    except Exception as e:
        logger.warning(f"Could not validate address {wallet_address}: {e}")
        # نستمر رغم عدم القدرة على التحقق
    
    with bot.retrieve_data(user_id) as data:
        stars_count = data['stars_count']
        ton_amount = data['ton_amount']
        payment_charge_id = data.get('payment_charge_id')
    
    # حفظ العنوان في حالة المستخدم
    with bot.retrieve_data(user_id) as data:
        data['wallet_address'] = wallet_address

    db.set_user_state(
        user_id,
        UserStateStage.CONFIRMING_WALLET,
        stars_count=stars_count,
        ton_amount=ton_amount,
        wallet_address=wallet_address,
        payment_charge_id=payment_charge_id,
    )
    
    response_text = f"""
📋 **تفاصيل طلبك النهائية:**

⭐ **عدد النجوم:** {stars_count}  
💰 **المبلغ المستحق:** {ton_amount:.6f} TON  
📥 **عنوان المحفظة:** {wallet_address}

⚠️ **تأكد من صحة العنوان** لأنه لا يمكن استرجاع الأموال إذا كان خطأ.

اضغط على 'تأكيد العنوان ✅' للمواصلة، أو 'إلغاء العملية ❌' للإلغاء.
    """
    
    bot.send_message(message.chat.id, response_text, reply_markup=get_wallet_confirmation_keyboard())
    bot.set_state(user_id, UserStates.confirming_wallet)

# معالجة تأكيد العنوان وإرسال TON
@bot.message_handler(func=lambda message: message.text == "تأكيد العنوان ✅" and bot.get_state(message.from_user.id) == UserStates.confirming_wallet)
def confirm_wallet_and_send_ton(message):
    user_id = message.from_user.id
    
    with bot.retrieve_data(user_id) as data:
        stars_count = data['stars_count']
        ton_amount = data['ton_amount']
        wallet_address = data['wallet_address']
        payment_charge_id = data.get('payment_charge_id')
    
    # حفظ الطلب في قاعدة البيانات
    db.create_order(user_id, stars_count, ton_amount, wallet_address, payment_charge_id)
    
    # إرسال رسالة الانتظار
    processing_msg = bot.send_message(message.chat.id, 
                                    "🔄 **جاري معالجة التحويل...**\n\nقد تستغرق العملية بضع دقائق.")
    
    try:
        # محاولة إرسال TON
        success, tx_hash = asyncio.run(ton_handler.send_ton(wallet_address, ton_amount))
        
        if success:
            # حفظ المعاملة في قاعدة البيانات
            db.complete_order(user_id, tx_hash)
            
            success_text = f"""
✅ **تمت العملية بنجاح!**

⭐ **عدد النجوم المستلمة:** {stars_count}  
💰 **المبلغ المحول:** {ton_amount:.6f} TON  
📥 **عنوان المحفظة:** {wallet_address}  
🔗 **هاش المعاملة:** {tx_hash}

يمكنك تتبع المعاملة على: https://testnet.tonscan.org/tx/{tx_hash}

شكراً لاستخدامك البوت! 🎉
            """
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.send_message(message.chat.id, success_text, reply_markup=get_start_keyboard())
            logger.info(f"TON sent successfully to user {user_id}: {ton_amount} TON, tx_hash: {tx_hash}")
        else:
            error_text = f"""
❌ **حدث خطأ في التحويل**

⚠️ لم نتمكن من إرسال TON إلى محفظتك.  
**السبب:** {tx_hash}

✅ تم استلام النجوم بنجاح وسنقوم بحل المشكلة قريباً.
يرجى التواصل مع الدعم مع تقديم رقم المستخدم: {user_id}
            """
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.send_message(message.chat.id, error_text, reply_markup=get_start_keyboard())
            logger.error(f"Failed to send TON to user {user_id}: {tx_hash}")
        
    except Exception as e:
        logger.error(f"Error in TON transfer for user {user_id}: {e}")
        error_text = f"""
❌ **حدث خطأ غير متوقع**

⚠️ حدث خطأ أثناء محاولة التحويل.
**الخطأ:** {str(e)}

✅ تم استلام النجوم بنجاح وسنقوم بحل المشكلة قريباً.
يرجى التواصل مع الدعم.
        """
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.send_message(message.chat.id, error_text, reply_markup=get_start_keyboard())
    
    finally:
        bot.delete_state(user_id)

# معالجة سجل المعاملات
@bot.message_handler(func=lambda message: message.text == "سجل المعاملات 📊")
def show_transaction_history(message):
    user_id = message.from_user.id
    
    transactions = db.get_user_transactions(user_id, limit=5)
    
    if not transactions:
        bot.send_message(message.chat.id, 
                       "📊 **سجل المعاملات**\n\nلا توجد معاملات سابقة.", 
                       reply_markup=get_main_menu_keyboard())
        return
    
    history_text = "📊 **سجل المعاملات الأخيرة**\n\n"
    
    for i, tx in enumerate(transactions, 1):
        short_hash = tx.tx_hash[:8] + "..." + tx.tx_hash[-8:] if len(tx.tx_hash) > 16 else tx.tx_hash
        short_wallet = (
            tx.wallet_address[:8] + "..." + tx.wallet_address[-8:]
            if len(tx.wallet_address) > 16
            else tx.wallet_address
        )
        created_str = tx.created.strftime("%Y-%m-%d") if tx.created else "-"
        
        history_text += f"{i}. ⭐ {tx.stars_count} → 💰 {tx.ton_amount:.6f} TON\n"
        history_text += f"   📍 {short_wallet}\n"
        history_text += f"   🔗 {short_hash}\n"
        history_text += f"   📅 {created_str}\n\n"
    
    bot.send_message(message.chat.id, history_text, reply_markup=get_main_menu_keyboard())

# معالجة إلغاء العملية
@bot.message_handler(func=lambda message: message.text == "إلغاء العملية ❌")
def cancel_operation(message):
    user_id = message.from_user.id
    bot.delete_state(user_id)
    db.clear_user_state(user_id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton("بدء عملية البيع 💫"))
    
    bot.send_message(message.chat.id, 
                    "❌ **تم إلغاء العملية**\n\nيمكنك البدء من جديد في أي وقت!", 
                    reply_markup=markup)
    logger.info(f"Operation cancelled by user {user_id}")

# معالجة أي رسائل أخرى
@bot.message_handler(func=lambda message: True)
def other_messages(message):
    bot.send_message(message.chat.id, 
                    "🔍 **تعذر فهم الرسالة**\n\nاستخدم الأزرار أو الأوامر للتفاعل مع البوت.", 
                    reply_markup=get_start_keyboard())

# فحص الوظائف الحقيقية عند البدء
async def check_real_functionality():
    """التحقق من الوظائف الحقيقية للبوت"""
    print("🔍 جاري التحقق من الوظائف الحقيقية...")
    
    try:
        # التحقق من رصيد حقيقي
        success, balance = await ton_handler.get_balance()
        if success:
            print(f"✅ الرصيد الحقيقي: {balance:.6f} TON")
        else:
            print("❌ فشل في جلب الرصيد الحقيقي - استخدام وضع المحاكاة")
        
        # التحقق من اتصال TON Center API
        test_address = "EQCD39VS5jcptHL8vMjEXrzGaRcCVYto7HUn4bpAOg8xqB2N"  # عنوان اختبار
        is_valid = await ton_handler.validate_address(test_address)
        print(f"✅ اتصال TON Center API: {'ناجح' if is_valid else 'فاشل'}")
        
    except Exception as e:
        print(f"⚠️ تحذير في فحص الوظائف: {e}")

# تشغيل البوت
if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت...")
    
    # التحقق من اتصال قاعدة البيانات
    try:
        db.connection.execute("SELECT 1")
        print("✅ قاعدة البيانات متصلة بنجاح")
    except Exception as e:
        print(f"❌ خطأ في اتصال قاعدة البيانات: {e}")
    
    # التحقق من الوظائف الحقيقية
    asyncio.run(check_real_functionality())
    
    print("✅ البوت جاهز للتشغيل...")
    print("=" * 50)
    print("🎯 البوت يعمل الآن!")
    print("📱 يمكن للمستخدمين التفاعل مع البوت عبر /start")
    print("=" * 50)
    
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Error in bot polling: {e}")
        print(f"❌ خطأ في تشغيل البوت: {e}")