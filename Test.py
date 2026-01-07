import requests
import time
import random
import logging
from datetime import datetime

# Sabitler
ELEMENT_FLAGS_STREAM = 0x01000003
QC_ELEMENT_FLAGS = 'n:a'
QC_KEY = 'k'
QC_NAME = 'n:n'

# ================== AYARLAR ==================
CLIENT_ID = "bAA3iF1cKgtiVw136hynke2CcumxBoRjYjvrUAUZYd1Na32E"
CLIENT_SECRET = "z4Cijm4Ac2oxfQOy1vNqKd54CpL4Pmy3CJokKAdELJ0VKVPpTKewjvZsOPgf5KdA"
FACILITY_ID = "urn:adsk.dtt:c3alioHzTgyVZob6LD_HwQ"

# ==============================================================================
# HASSAS AYAR LİSTESİ (BURASI SENİN KONTROLÜNDE)
# Sol Taraf: Tandem'deki Bağlantı Adı (Stream Name)
# Sağ Taraf: Oraya göndereceğimiz paketin etiketi (JSON Key)
# ==============================================================================
SENSOR_CONFIG = {
    # --- KAPI VE YAKIT (Senin özel isim istediklerin) ---
    "Kapi_sayaci": "Kapi_giris_sayaci", 
    "Depo_yakit_miktar": "Depo_yakit_miktarı", 

    # --- SICAKLIKLAR (Bunlar genelde standarttır) ---
    # Eğer bunlardan biri de özel isim istiyorsa buradan değiştirebilirsin.
    # Genelde sıcaklık için "z:Hg" kullanılır.
    "Temperature_bay_wc": "z:Hg",
    "Temperature_aile_wc": "z:Hg",
    "Temperature_bayan_wc": "z:Hg",
    "Temperature_depo": "z:Hg",
    "Temperature_market": "z:Hg",
    "Temperature_soguk_oda2": "z:Hg",
    "Temperature_wc_hol": "z:Hg",
    "Temperature_soguk_oda1": "z:Hg"
}

WAIT_TIME = 60 # Saniye

# ================== FONKSİYONLAR ==================

def get_token():
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    try:
        r = requests.post(url, data={
            'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials', 'scope': 'data:read data:write'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        if r.status_code != 200:
            print(f"❌ Token Alınamadı! Hata Kodu: {r.status_code}")
            return None
            
        return r.json().get('access_token')
    except Exception as e:
        print(f"❌ Bağlantı Hatası (Token): {e}")
        return None

def get_stream_ids(token, model_id):
    """Sadece ID'leri bulur, gerisini senin listene bırakır"""
    print("🔍 Tandem'e bağlanılıyor ve ID'ler çekiliyor...")
    url = f"https://developer.api.autodesk.com/tandem/v1/modeldata/{model_id}/scan"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    ready_sensors = []
    
    try:
        # Hata korumalı istek
        r = requests.post(url, headers=headers, json={"families": ["n"], "includeHistory": False, "skipArrays": True})
        
        if r.status_code != 200:
            print(f"❌ Tarama Hatası (Kod {r.status_code}): {r.text}")
            return []
            
        data = r.json()
        
        # Gelen verinin liste olduğundan emin ol (Senin aldığın hatayı çözer)
        if not isinstance(data, list):
            print("❌ Beklenmedik sunucu yanıtı (Liste gelmedi).")
            return []
            
        print(f"{'SENSÖR':<25} | {'DURUM'} | {'PAKET ETİKETİ'}")
        print("-" * 65)

        for item in data:
            if not isinstance(item, dict): continue
            if item.get(QC_ELEMENT_FLAGS) != ELEMENT_FLAGS_STREAM: continue
            
            name = item.get(QC_NAME)
            key_id = item.get(QC_KEY)
            
            # Eğer bu isim senin yukarıdaki LİSTEDE varsa işle
            if name in SENSOR_CONFIG:
                target_key = SENSOR_CONFIG[name]
                
                # Türü belirle (Simülasyon için)
                s_type = "TEMP"
                start_val = 22.0
                if "yakit" in name.lower(): 
                    s_type = "FUEL"
                    start_val = 850.0
                elif "kapi" in name.lower() or "sayac" in name.lower(): 
                    s_type = "DOOR"
                    start_val = 0
                elif "soguk" in name.lower(): 
                    start_val = -18.0

                ready_sensors.append({
                    "name": name,
                    "stream_id": key_id,
                    "json_key": target_key, # Senin belirlediğin anahtar
                    "value": start_val,
                    "type": s_type
                })
                print(f"{name:<25} | ✅ Hazır | {target_key}")
            
        print("-" * 65)
        return ready_sensors

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")
        return []

def simulate_and_send(token, model_id, sensors):
    url = f"https://developer.api.autodesk.com/tandem/v1/timeseries/models/{model_id}/webhooks/generic"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print(f"\n--- ⏰ {datetime.now().strftime('%H:%M:%S')} Güncellemesi ---")
    
    for s in sensors:
        # 1. MATEMATİK (Simülasyon)
        if s["type"] == "TEMP":
            s["value"] += random.uniform(-0.5, 0.5)
            if "soguk" in s["name"].lower(): s["value"] = max(min(s["value"], -15), -22)
            else: s["value"] = max(min(s["value"], 25), 18)
        elif s["type"] == "DOOR":
            if random.random() < 0.6: s["value"] += 1
        elif s["type"] == "FUEL":
            s["value"] -= random.uniform(2, 5)
            if s["value"] < 50: s["value"] = 850.0
        
        s["value"] = round(s["value"], 2)
        
        # 2. GÖNDERİM (Senin seçtiğin anahtarla)
        payload = {
            "id": s["stream_id"],
            s["json_key"]: s["value"] 
        }
        
        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code in [200, 204]:
                print(f"📤 {s['name']:<25}: {s['value']}")
            else:
                print(f"⚠️ Gitmedi {s['name']}: {r.status_code}")
        except: pass

# ================== MAIN ==================

def main():
    print("🚀 MANUEL AYARLI TANDEM BOTU BAŞLATILIYOR...\n")
    
    token = get_token()
    if not token: return
    
    model_id = FACILITY_ID.replace("dtt:", "dtm:")
    
    # Listeyi hazırla
    sensors = get_stream_ids(token, model_id)
    
    if not sensors:
        print("\n❌ Listendeki sensörler Tandem'de bulunamadı!")
        print("👉 Lütfen kodun başındaki 'SENSOR_CONFIG' listesindeki isimlerin Tandem ile birebir aynı olduğundan emin ol.")
        return
        
    print(f"\n✅ {len(sensors)} sensör başarıyla ayarlandı. Simülasyon başlıyor...\n")
    
    try:
        while True:
            token = get_token()
            if token: simulate_and_send(token, model_id, sensors)
            time.sleep(WAIT_TIME)
    except KeyboardInterrupt:
        print("\nDurduruldu.")

if __name__ == "__main__":
    main()
