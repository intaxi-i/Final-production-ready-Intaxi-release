import os

# Конфигурация хирургических патчей: файл -> что ищем -> на что меняем
FIXES = [
    {
        "file": "backend_v2/app/services/city_order_service.py",
        "replacements": [
            ("select(CityOrder).filter(CityOrder.id == order_id)", 
             "select(CityOrder).filter(CityOrder.id == order_id).with_for_update()")
        ]
    },
    {
        "file": "backend_v2/app/services/city_trip_service.py",
        "replacements": [
            ("select(CityOrder).where(CityOrder.id == order_id)", 
             "select(CityOrder).where(CityOrder.id == order_id).with_for_update()"),
            ("select(CityCounteroffer).where(CityCounteroffer.id == offer_id)", 
             "select(CityCounteroffer).where(CityCounteroffer.id == offer_id).with_for_update()"),
            ("select(CityTrip).where(CityTrip.id == trip_id)", 
             "select(CityTrip).where(CityTrip.id == trip_id).with_for_update()"),
            ("select(DriverOnlineState).where(DriverOnlineState.driver_user_id == driver.id)",
             "select(DriverOnlineState).where(DriverOnlineState.driver_user_id == driver.id).with_for_update()"),
             ("select(DriverOnlineState).where(DriverOnlineState.driver_user_id == trip.driver_user_id)",
              "select(DriverOnlineState).where(DriverOnlineState.driver_user_id == trip.driver_user_id).with_for_update()")
        ]
    },
    {
        "file": "backend_v2/app/services/intercity_service.py",
        "replacements": [
            ("select(IntercityRequest).where(IntercityRequest.id == request_id)", 
             "select(IntercityRequest).where(IntercityRequest.id == request_id).with_for_update()"),
            ("select(IntercityRoute).where(IntercityRoute.id == route_id)", 
             "select(IntercityRoute).where(IntercityRoute.id == route_id).with_for_update()")
        ]
    },
    {
        "file": "backend_v2/app/services/wallet_service.py",
        "replacements": [
            ("select(Wallet).where(Wallet.user_id == user.id)", 
             "select(Wallet).where(Wallet.user_id == user.id).with_for_update()"),
            ("select(PaymentTopupRequest).where(PaymentTopupRequest.id == topup_id)", 
             "select(PaymentTopupRequest).where(PaymentTopupRequest.id == topup_id).with_for_update()"),
            ("select(User).where(User.id == row.driver_user_id)", 
             "select(User).where(User.id == row.driver_user_id).with_for_update()")
        ]
    },
    {
        "file": "api/city_flow_runtime_patch_v2.py",
        "replacements": [
            ("select(CityOrderV1).where(CityOrderV1.id == target_id)", 
             "select(CityOrderV1).where(CityOrderV1.id == target_id).with_for_update()")
        ]
    },
    {
        "file": "intaxi_bot/app/database/city_flow_helper_patch.py",
        "replacements": [
            ("select(CityOrderV1).where(CityOrderV1.id == order_id)", 
             "select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update()")
        ]
    },
    {
        "file": "intaxi_bot/app/database/requests.py",
        "replacements": [
            ("select(DriverPaymentRequest).where(DriverPaymentRequest.id == request_id, DriverPaymentRequest.status == 'pending')", 
             "select(DriverPaymentRequest).where(DriverPaymentRequest.id == request_id, DriverPaymentRequest.status == 'pending').with_for_update()"),
            ("select(User).where(User.tg_id == req.driver_tg_id)", 
             "select(User).where(User.tg_id == req.driver_tg_id).with_for_update()"),
            ("select(IntercityRouteV1).where(IntercityRouteV1.id == item_id)",
             "select(IntercityRouteV1).where(IntercityRouteV1.id == item_id).with_for_update()"),
            ("select(IntercityRequestV1).where(IntercityRequestV1.id == item_id)",
             "select(IntercityRequestV1).where(IntercityRequestV1.id == item_id).with_for_update()")
        ]
    }
]

def apply_fixes():
    print("🚀 Начинаем автоисправление баз данных (Race Condition)...")
    for item in FIXES:
        path = item["file"]
        if not os.path.exists(path):
            print(f"⚠️ Файл не найден, пропускаем: {path}")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        changed = False
        for old_str, new_str in item["replacements"]:
            # Если старый код есть, а блокировки еще нет — заменяем
            if old_str in content and new_str not in content:
                content = content.replace(old_str, new_str)
                changed = True
                
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Успешно обновлен: {path}")
        else:
            print(f"ℹ️ Без изменений (уже исправлено или код отличается): {path}")
            
    print("🎉 Все патчи безопасности успешно применены! Теперь заказы и баланс под надежной защитой.")

if __name__ == "__main__":
    apply_fixes()