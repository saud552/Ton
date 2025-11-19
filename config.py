# توكن البوت
BOT_TOKEN = "2087749078:AAEECUBh7rvAvstGdaI--h7TsCb2CqAJLZY"

# إعدادات الدفع بالنجوم
PAYMENT_PROVIDER_TOKEN = ""  # فارغ للنجوم

# محفظة TON
WALLET_MNEMONIC = "toe advice expire never shoot fatal virtual album health decline deliver scorpion clarify tattoo obey tonight mixed time village final trophy derive famous alone"
DEPOSIT_ADDRESS = "8134b4e2288644733cc4d64728dbff8a3f3b77b067ae93c05b6103fc0bf814b1"

# TON API
API_KEY = "ff3bb5fff207abf0671a5531cd366232644bb6825ebef814f469da13540dbf86"
RUN_IN_MAINNET = True  # غير إلى True عندما تكون جاهزاً للشبكة الرئيسية

if RUN_IN_MAINNET:
    API_BASE_URL = 'https://toncenter.com/api/v2'
else:
    API_BASE_URL = 'https://testnet.toncenter.com/api/v2'

# الأسعار
STAR_PRICE_USD = 0.0119
TON_PRICE_USD = 2.28  # قم بتحديثه دورياً
STAR_PRICE_TON = STAR_PRICE_USD / TON_PRICE_USD

# قاعدة البيانات
DATABASE_FILE = "bot_database.db"