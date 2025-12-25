import time
import logging
import requests
import random

# --- 1) GÜNCEL STREAM URL'LERİ ---
STREAM_URLS = {
    "Kapi_giris_sayaci": "https://:mVsETGYMTx-q0CyNNDSRZg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAKSSpAoeTktcqA_ugttWuNsAAAAA",
    "Temperature_AILE_ENG_WC": "https://:E-vsMlTLSlqSpRgaEwarBg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAI96sXZqh0ohlpI9anZzQJAAAAAA",
    "Temperature_BAY_WC": "https://:-CZYHDeORe-TQ3O63PDajw@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAKBlgzb7HEeRhcMVmYilqPMAAAAA",
    "Temperature_BAYAN_WC": "https://:wAqlPCX3RYioKK-R0J8DrA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAIYMHBDULk5mmiq7_5GMEq8AAAAA",
    "Temperature_DEPO": "https://:jjvOi6LjR_uA9KXjzdY4YQ@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAALcp2i9jskQjmY8UuSqIUpsAAAAA",
    "Temperature_SOGUK_ODA1_Z41": "https://:_3-EpqdJR96YjzU4OCQaXA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAGFxapBLb0kSjBBAD8-qaKEAAAAA",
    "Temperature_SOGUK_ODA2_Z40": "https://:nkN8jwrXRi-Juf6L7BKkeA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAABahp9wNUEUDmjJrzl160SwAAAAA",
    "Temperature_WC_HOL": "https://:G73lYfSDSk-0racFWZxadg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAM0inW0nIka3mLs_EiZuhwIAAAAA",
    "depo_yakit_miktar": "https://:JV_OHSxfRF-gcBdx9hqrzg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAABagL_xaC0KrvWjV8L7SXlsAAAAA",
    "Temperature_MARKET": "https://:1JjT8wWvSUK4XsF9FJRO6w@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAANs1w0Vhgkn1l3Q5Xp8spvQAAAAA"
}

FIELD_MAP = {s: s for s in STREAM_URLS.keys()}
SEND_INTERVAL = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
session = requests.Session()

# Merkez sıcaklık değerleri (Referans noktaları)
BASE_TEMPS = {
    "Temperature_AILE_ENG_WC": 22.0, "Temperature_BAY_WC": 21.5,
    "Temperature_BAYAN_WC": 21.8, "Temperature_WC_HOL": 22.2,
    "Temperature_MARKET": 20.0, "Temperature_DEPO": 18.5,
    "Temperature_SOGUK_ODA1_Z41": -18.0, "Temperature_SOGUK_ODA2_Z40": -18.2
}

# Başlangıç durumu
current_data = {**BASE_TEMPS, "depo_yakit_miktar": 850.0, "counter": 0}

def update_logic():
    # 1) SAYAÇ: %20 ihtimalle sadece artar
    if random.random() < 0.7:
        current_data["counter"] += 1
    
    # 2) SICAKLIKLAR: Merkez değerden +/- 3 derece dalgalanır
    for key, base in BASE_TEMPS.items():
        # Her adımda 0.4 dereceye kadar değişim (Daha belirgin grafik)
        change = random.uniform(-0.4, 0.4)
        new_val = current_data[key] + change
        
        # Sınır kontrolü (+/- 3 derece)
        if new_val > base + 3: new_val = base + 3
        if new_val < base - 3: new_val = base - 3
        
        current_data[key] = round(new_val, 2)
    
    # 3) YAKIT: Sürekli düşüş, 50'de dolum
    current_data["depo_yakit_miktar"] = round(current_data["depo_yakit_miktar"] - random.uniform(5, 10), 2)
    if current_data["depo_yakit_miktar"] < 50:
        current_data["depo_yakit_miktar"] = 850.0

def send_data():
    for s_name, url in STREAM_URLS.items():
        # Veriyi sözlükten çek, yoksa varsayılan ata
        val = current_data["counter"] if s_name == "Kapi_giris_sayaci" else current_data.get(s_name)
        try:
            session.post(url, json={FIELD_MAP[s_name]: float(val)}, timeout=5)
        except Exception as e:
            logging.error(f"Hata {s_name}: {e}")

if __name__ == "__main__":
    start_run = time.time()
    print("Sistem Başlatıldı. Her 6 Saatte Bir (veya QR okutulunca) Sıfırlanır.")
    
    # 6 saatlik döngü
    while time.time() - start_run < 21000:
        update_logic()
        send_data()
        logging.info(f"Yakit: {current_data['depo_yakit_miktar']} | Sayac: {current_data['counter']}")
        time.sleep(SEND_INTERVAL)


