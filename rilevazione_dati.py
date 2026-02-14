import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os

def estrai_prezzo(url, unita_misura):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cerca nei paragrafi
        for p in soup.find_all("p"):
            testo = p.get_text(separator=" ", strip=True)

            if unita_misura in testo:
                match = re.search(r'(\d+[.,]\d+)', testo)
                if match:
                    return match.group(1).replace(",", ".")

        return "N/D"

    except Exception as e:
        return "Errore"

# Configurazione
url_psv = "https://luce-gas.it/guida/mercato/andamento-prezzo/gas-metano"
url_pun = "https://www.papernest.it/luce-gas/mercato-energetico/pun/"

# Rilevazione
valore_psv = estrai_prezzo(url_psv, "€/Smc")
valore_pun = estrai_prezzo(url_pun, "€/kWh")
data_oggi = datetime.now().strftime("%d/%m/%Y")

# Salvataggio
cartella_script = os.path.dirname(os.path.abspath(__file__))
percorso_csv = os.path.join(cartella_script, "storico_prezzi.csv")

# Intestazione pulita (standard CSV: separati da virgola)
intestazione = "Data,PUN,PSV\n"

if not os.path.exists(percorso_csv):
    with open(percorso_csv, "w", encoding="utf-8") as f:
        f.write(intestazione)

with open(percorso_csv, "a", encoding="utf-8") as f:
    f.write(f"{data_oggi},{valore_pun},{valore_psv}\n")


print(f"Rilevato - PUN: {valore_pun}, PSV: {valore_psv}. Salvato in {percorso_csv}")


