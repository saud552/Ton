from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_keyboard():
    """لوحة المفاتيح لرسالة الترحيب"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("بدء عملية البيع 💫"))
    return keyboard

def get_cancel_keyboard():
    """زر إلغاء العملية"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("إلغاء العملية ❌"))
    return keyboard

def get_wallet_confirmation_keyboard():
    """لوحة تأكيد إرسال العنوان"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("تأكيد العنوان ✅"))
    keyboard.add(KeyboardButton("إلغاء العملية ❌"))
    return keyboard

def get_main_menu_keyboard():
    """لوحة القائمة الرئيسية"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("بدء عملية البيع 💫"))
    keyboard.add(KeyboardButton("سجل المعاملات 📊"))
    return keyboard