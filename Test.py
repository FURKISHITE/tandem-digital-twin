import time
import logging
import requests
import random

# Stream URL'leri
STREAM_URLS = {
    "Kapi_giris_sayaci": "https://:mVsETGYMTx-q0CyNNDSRZg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAKSSpAoeTktcqA_ugttWuNsAAAAA",
    "Temperature_AILE_ENG_WC": "https://:E-vsMlTLSlqSpRgaEwarBg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAI96sXZqh0ohlpI9anZzQJAAAAAA",
    "Temperature_BAY_WC": "https://:-CZYHDeORe-TQ3O63PDajw@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAKBlgzb7HEeRhcMVmYilqPMAAAAA",
    "Temperature_BAYAN_WC": "https://:wAqlPCX3RYioKK-R0J8DrA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAIYMHBDULk5mmi7_5GMEq8AAAAA",
    "Temperature_DEPO": "https://:jjvOi6LjR_uA9KXjzdY4YQ@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAALcp2i9jskQjmY8UuSqIUpsAAAAA",
    "Temperature_SOGUK_ODA1_Z41": "https://:_3-EpqdJR96YjzU4OCQaXA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAGFxapBLb0kSjBBAD8-qaKEAAAAA",
    "Temperature_SOGUK_ODA2_Z40": "https://:nkN8jwrXRi-Juf6L7BKkeA@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAABahp9wNUEUDmjJrzl160SwAAAAA",
    "Temperature_WC_HOL": "https://:G73lYfSDSk-0racFWZxadg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAAM0inW0nIka3mLs_EiZuhwIAAAAA",
    "depo_yakit_miktar": "https://:JV_OHSxfRF-gcBdx9hqrzg@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAABagL_xaC0KrvWjV8L7SXlsAAAAA",
    "Temperature_MARKET": "https://:1JjT8wWvSUK4XsF9FJRO6w@tandem.autodesk.com/api/v1/timeseries/models/urn:adsk.dtm:c3alioHzTgyVZob6LD_HwQ/streams/AQAAANs1w0Vhgkn1l3Q5Xp8spvQAAAAA"
}

FIELD_MAP = {s: s for s in STREAM_URLS.keys()}
UPDATE_INTERVAL = 1
SEND_INTERVAL = 15

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
session = requests.Session()

current_data = {
    "Temperature_AILE_ENG_WC": 22.5, "Temperature_BAY_WC": 21.0, "Temperature_BAYAN_WC": 21.5,
    "Temperature_DEPO": 19.8, "Temperature_SOGUK_ODA1_Z41": -18.0, "Temperature_SOGUK_ODA2_Z40": -18.4,
    "Temperature_WC_HOL": 23.0, "Temperature_MARKET": 20.5, "depo_yakit_miktar": 850.0, "counter": 0
}

def update_values():
    if random.random() < 0.2:
        current_data["counter"] += 1
    for key in current_data:
        if "Temperature" in key:
            current_data[key] = round(current_data[key] + random.uniform(-0.02, 0.02), 2)
    # Yakıt hızlı eksilsin (3-5 arası)
    current_data["depo_yakit_miktar"] = round(current_data["depo_yakit_miktar"] - random.uniform(3, 5), 2)
    if current_data["depo_yakit_miktar"] < 50:
        current_data["depo_yakit_miktar"] = 850.0

def post_stream(stream_name: str, value):
    url = STREAM_URLS[stream_name]
    payload = {FIELD_MAP[stream_name]: float(value)}
    try:
        session.post(url, json=payload, timeout=5)
    except:
        pass

if __name__ == "__main__":
    start_run = time.time()
    last_send_time = 0
    print("GitHub Actions Bulut Simülasyonu Başladı...")
    
    # GitHub Actions süresi (yaklaşık 290 saniye) boyunca çalışır
    while time.time() - start_run < 290:
        update_values()
        now = time.time()
        if now - last_send_time >= SEND_INTERVAL:
            for s_name in STREAM_URLS.keys():
                val = current_data["counter"] if s_name == "Kapi_giris_sayaci" else current_data[s_name]
                post_stream(s_name, val)
            last_send_time = now
            logging.info(f"Gönderildi - Yakıt: {current_data['depo_yakit_miktar']}")
        time.sleep(UPDATE_INTERVAL)