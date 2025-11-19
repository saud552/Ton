"""Legacy configuration bridge to the new settings system."""

from app import get_settings

settings = get_settings()

BOT_TOKEN = settings.bot_token
PAYMENT_PROVIDER_TOKEN = settings.payment_provider_token
WALLET_MNEMONIC = settings.wallet_mnemonic
WALLET_PRIVATE_KEY = settings.wallet_private_key
DEPOSIT_ADDRESS = settings.deposit_address

API_KEY = settings.ton_api_key
RUN_IN_MAINNET = settings.run_in_mainnet
API_BASE_URL = settings.api_base_url

STAR_PRICE_USD = settings.star_price_usd
TON_PRICE_USD = settings.ton_price_usd
STAR_PRICE_TON = settings.star_price_ton

DATABASE_FILE = settings.database_file