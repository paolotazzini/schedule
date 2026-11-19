import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9"
}

def estrai_pun_segugio(url):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                locale="it-IT"
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000) # Attende eventuale caricamento dinamico
            testo_pagina = page.inner_text("body")
            browser.close()

        # Cerca: "Il valore del PUN oggi 19 novembre 2026 è 0,20866 €/kWh"
        match = re.search(
            r'Il valore del PUN oggi[^€]*?\bè\s*(\d+[.,]\d+)\s*€/kWh',
            testo_pagina,
            re.IGNORECASE
        )
        if match:
            return match.group(1).replace(",", ".")

        match_fallback = re.search(
            r'PUN oggi[^€]*?\bè\s*(\d+[.,]\d+)\s*€/kWh',
            testo_pagina,
            re.IGNORECASE
        )
        if match_fallback:
            return match_fallback.group(1).replace(",", ".")

        print("[DEBUG PUN] Frase non trovata nel testo pagina.")
        return "N/D"
    except Exception as e:
        print(f"[ERRORE PUN DETTAGLIO]: {e}")
        return "Errore"

def estrai_psv_lucegas(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
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
        print(f"[ERRORE PSV DETTAGLIO]: {e}")
        return "Errore"

# Configurazione URL
url_pun = "https://tariffe.segugio.it/indice-pun-luce/"
url_psv = "https://luce-gas.it/guida/mercato/andamento-prezzo/gas-metano"

valore_pun = estrai_pun_segugio(url_pun)
valore_psv = estrai_psv_lucegas(url_psv)
data_oggi = datetime.now().strftime("%d/%m/%Y")

# Salvataggio (aggiorna la riga di oggi se già presente)
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
