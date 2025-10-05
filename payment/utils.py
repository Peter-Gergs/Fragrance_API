import requests
import uuid
import json
from django.conf import settings
from rest_framework import status

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
    إنشاء دفعة عبر OPay Cashier API والتحقق من الاستجابة.
    """
    reference = str(uuid.uuid4())[:18]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPAY_PUBLIC_KEY}",  # استخدم settings.OPAY_PUBLIC_KEY
        "MerchantId": settings.OPAY_MERCHANT_ID,  # استخدم settings.OPAY_MERCHANT_ID
    }

    # ... (payload كما هو) ...
    payload = {
        "country": country,
        "reference": reference,
        "amount": {
            "total": int(amount),
            "currency": currency,
        },
        "returnUrl": return_url,
        "callbackUrl": callback_url,
        "cancelUrl": cancel_url,
        "expireAt": 30,
        "userInfo": {
            "userEmail": user_info.get("email"),
            "userId": str(user_info.get("userId")),  # تم تعديل id إلى userId
            "userMobile": user_info.get(
                "phone"
            ),  # تم تعديل mobile إلى phone ليتوافق مع الـ view
            "userName": user_info.get("name"),
        },
        "productList": product_list,
        "payMethod": "",
    }

    try:
        response = requests.post(
            OPAY_URLS[OPAY_ENV], json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()  # إثارة خطأ لو حالة الـ HTTP كانت 4xx أو 5xx

        response_data = response.json()

        # === منطق التحقق من استجابة OPay ===
        if response_data.get("code") == "00000":
            # حالة النجاح - الـ Reference موجود هنا
            data = response_data.get("data", {})
            return {
                "reference": data.get("reference"),
                "redirect_url": data.get("cashierUrl"),
                "message": "Payment initiated successfully.",
            }
        else:
            # حالة فشل الـ API في OPay
            print(
                f"OPay API Error: {response_data.get('message')}. Details: {response_data.get('data')}"
            )
            return {
                "reference": None,
                "error": response_data.get(
                    "message", "OPay payment initiation failed."
                ),
            }

    except requests.exceptions.RequestException as e:
        # خطأ اتصال شبكة، Timeout، أو HTTP Status غير ناجح
        print(f"Network or HTTP error during OPay call: {e}")
        return {
            "reference": None,
            "error": "Failed to connect to OPay gateway.",
        }
    except json.JSONDecodeError:
        # الرد من OPay ليس بصيغة JSON
        print("Failed to decode OPay response as JSON.")
        return {
            "reference": None,
            "error": "Invalid response from OPay gateway.",
        }
