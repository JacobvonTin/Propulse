import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Konfigurace - tvůj bot kopac_bot
TELEGRAM_BOT_TOKEN = "8963979440:AAExYFYa8h9sbociYw2EEENjmIDj5ll8hDo"
TELEGRAM_CHAT_ID = "TVŮJ_CHAT_ID"  # Sem doplň své Telegram Chat ID
APIFY_TOKEN = "TVŮJ_APIFY_API_TOKEN"  # Sem doplň svůj Apify token

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Chyba při odesílání na Telegram: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Přijat webhook z Apify:", data)

    # Získání ID datasetu z payloadu, který posílá Apify
    dataset_id = data.get("defaultDatasetId") or data.get("resource", {}).get("defaultDatasetId")
    
    if not dataset_id:
        return jsonify({"status": "error", "message": "Missing datasetId"}), 400

    # Stažení inzerátů z Apify Datasetu
    apify_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    response = requests.get(apify_url)
    
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch dataset from Apify"}), 500

    items = response.json()
    new_leads_count = 0

    for item in items:
        # FILTR: Zde zajistíme, že bereme POUZE přímé majitele ( OWNER )
        advertiser_type = item.get("advertiserType", "").upper()
        
        if advertiser_type != "OWNER":
            continue

        title = item.get("title") or item.get("propertyType", "Nemovitost")
        price = item.get("price", "Neuvedeno")
        location = item.get("location", "Moravskoslezský kraj")
        url = item.get("url") or item.get("link", "#")

        # Formát zprávy pro Telegram
        message = (
            "🚨 **NOVÝ PŘÍMÝ MAJITEL (Bez provize)**\n\n"
            f"🏠 **{title}**\n"
            f"💰 **Cena:** {price} Kč\n"
            f"📍 **Lokalita:** {location}\n"
            f"🔗 [Odkaz na inzerát]({url})"
        )

        send_telegram_message(message)
        new_leads_count += 1

    return jsonify({"status": "success", "processed_leads": new_leads_count}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
