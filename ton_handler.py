import aiohttp
import logging
import json
import config

logger = logging.getLogger(__name__)

class TONHandler:
    def __init__(self):
        self.api_base_url = config.API_BASE_URL
        self.api_key = config.API_KEY

    async def send_ton(self, recipient_address: str, amount_ton: float):
        """إرسال عملات TON حقيقي باستخدام TON Center API"""
        try:
            # التحقق من صحة العنوان
            if not await self.validate_address(recipient_address):
                return False, "عنوان المحفظة غير صحيح"
            
            # التحقق من الرصيد
            success, balance = await self.get_balance()
            if not success:
                return False, "فشل في التحقق من رصيد المحفظة"
            
            if balance < amount_ton:
                return False, f"رصيد غير كافي. الرصيد الحالي: {balance:.6f} TON"
            
            # إعداد بيانات المعاملة
            transaction_data = {
                "secretKey": config.WALLET_PRIVATE_KEY,  # سنحتاج إلى Private Key
                "to": recipient_address,
                "amount": int(amount_ton * 1e9),  # تحويل إلى nanotons
                "message": "Payment for Telegram Stars"
            }
            
            # إرسال المعاملة عبر TON Center API
            url = f"{self.api_base_url}/sendTransaction"
            params = {'api_key': self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=transaction_data, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            tx_hash = result['result']['hash']
                            logger.info(f"تم إرسال {amount_ton} TON بنجاح إلى {recipient_address}")
                            return True, tx_hash
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"خطأ في API: {error_msg}")
                            return False, f"خطأ في الشبكة: {error_msg}"
                    else:
                        error_msg = f"خطأ HTTP: {response.status}"
                        logger.error(error_msg)
                        return False, error_msg
                        
        except Exception as e:
            error_msg = f"خطأ في إرسال TON: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def get_balance(self, address: str = None):
        """الحصول على الرصيد الحقيقي للمحفظة"""
        try:
            if address is None:
                address = config.DEPOSIT_ADDRESS
            
            url = f"{self.api_base_url}/getAddressBalance"
            params = {
                'address': address,
                'api_key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            balance_nano = int(result['result'])
                            balance_ton = balance_nano / 1e9
                            logger.info(f"الرصيد الحقيقي: {balance_ton:.6f} TON")
                            return True, balance_ton
                    logger.error(f"فشل في جلب الرصيد: {response.status}")
                    return False, 0
        except Exception as e:
            logger.error(f"خطأ في جلب الرصيد: {e}")
            return False, 0

    async def validate_address(self, address: str):
        """التحقق من صحة عنوان TON"""
        try:
            url = f"{self.api_base_url}/validateAddress"
            params = {
                'address': address,
                'api_key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False) and result.get('result', {}).get('valid', False)
            return False
        except Exception as e:
            logger.error(f"خطأ في التحقق من العنوان: {e}")
            return False

    async def get_transaction_info(self, tx_hash: str):
        """الحصول على معلومات المعاملة"""
        try:
            url = f"{self.api_base_url}/getTransactions"
            params = {
                'hash': tx_hash,
                'api_key': self.api_key,
                'limit': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok') and result['result']:
                            return True, result['result'][0]
                    return False, None
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات المعاملة: {e}")
            return False, None

# إنشاء كائن المعالج
ton_handler = TONHandler()