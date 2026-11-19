import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def estrai_pun_segugio(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Cerca l'intera pagina testuale per la frase esatta:
        # "Il valore del PUN oggi ... è 0,20866 €/kWh"
        testo_pagina = soup.get_text(" ", strip=True)
        
        match = re.search(
            r'Il valore del PUN oggi[^€]*?\bè\s*(\d+[.,]\d+)\s*€/kWh',
            testo_pagina,
            re.IGNORECASE
        )
        if match:
            return match.group(1).replace(",", ".")

        # Fallback nel caso tolgano la data o cambino leggermente l'inizio
        match_fallback = re.search(
            r'PUN oggi[^€]*?\bè\s*(\d+[.,]\d+)\s*€/kWh',
            testo_pagina,
            re.IGNORECASE
        )
        if match_fallback:
            return match_fallback.group(1).replace(",", ".")

        return "N/D"
    except Exception as e:
        print(f"Errore PUN: {e}")
        return "Errore"

def estrai_psv_lucegas(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all(string=True):
            text = tag.strip()
            if "ultimo giorno rilevato, è di" in text or "PSV oggi" in text:
                match = re.search(r'(\d+[.,]\d+)', text)
                if match:
                    return match.group(1).replace(",", ".")

        elemento = soup.find(string=re.compile(r"€/Smc"))
        if elemento:
            match = re.search(r'(\d+[.,]\d+)', elemento)
            if match:
                return match.group(1).replace(",", ".")

        return "N/D"
    except Exception as e:
        print(f"Errore PSV: {e}")
        return "Errore"

# Configurazione URL
url_pun = "https://tariffe.segugio.it/indice-pun-luce/"
url_psv = "https://luce-gas.it/guida/mercato/andamento-prezzo/gas-metano"

valore_pun = estrai_pun_segugio(url_pun)
valore_psv = estrai_psv_lucegas(url_psv)
data_oggi = datetime.now().strftime("%d/%m/%Y")

# Salvataggio (aggiorna la riga di oggi se già presente, senza duplicarla)
cartella_script = os.path.dirname(os.path.abspath(__file__))
percorso_csv = os.path.join(cartella_script, "storico_prezzi.csv")
intestazione = "Data,PUN,PSV\n"

righe_esistenti = []
if os.path.exists(percorso_csv):
    with open(percorso_csv, "r", encoding="utf-8") as f:
        righe_esistenti = [r for r in f.readlines() if r.strip() and not r.startswith(data_oggi)]
else:
    righe_esistenti.append(intestazione)

righe_esistenti.append(f"{data_oggi},{valore_pun},{valore_psv}\n")

with open(percorso_csv, "w", encoding="utf-8") as f:
    f.writelines(righe_esistenti)

print(f"Rilevato - PUN: {valore_pun}, PSV: {valore_psv}. Salvato in {percorso_csv}")

