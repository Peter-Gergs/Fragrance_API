import requests
import uuid
from django.conf import settings

OPAY_PUBLIC_KEY = settings.OPAY_PUBLIC_KEY
OPAY_MERCHANT_ID = settings.OPAY_MERCHANT_ID
OPAY_ENV = getattr(settings, "OPAY_ENV", "sandbox")  # sandbox | production

OPAY_URLS = {
    "sandbox": "https://sandboxapi.opaycheckout.com/api/v1/international/cashier/create",
    "production": "https://api.opaycheckout.com/api/v1/international/cashier/create",
}


def create_cashier_payment(
    amount,
    currency,
    return_url,
    callback_url,
    cancel_url,
    user_info,
    product_list,
    country="EG",
):
    """
    إنشاء دفعة عبر OPay Cashier API
    """
    reference = str(uuid.uuid4())[:18]  # مرجع فريد للطلب
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPAY_PUBLIC_KEY}",
        "MerchantId": OPAY_MERCHANT_ID,
    }

    payload = {
        "country": country,
        "reference": reference,
        "amount": {
            "total": int(amount),  # لو بالجنيه مش السنتات
            "currency": currency,
        },
        "returnUrl": return_url,
        "callbackUrl": callback_url,
        "cancelUrl": cancel_url,
        "expireAt": 30,
        "userInfo": {
            "userEmail": user_info.get("email"),
            "userId": str(user_info.get("id")),
            "userMobile": user_info.get("mobile"),
            "userName": user_info.get("name"),
        },
        "productList": product_list,
        "payMethod": "",  # أو سيبها فاضية علشان العميل يختار
    }

    response = requests.post(
        OPAY_URLS[OPAY_ENV], json=payload, headers=headers, timeout=30
    )
    return response.json()
