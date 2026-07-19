import pandas as pd
import numpy as np
from datetime import datetime
import gradio as gr

# ==========================================
# 1. CARICAMENTO E PULIZIA DATI COMPLETI
# ==========================================
print("Avvio caricamento database completo Serie C...")
nome_file_excel = 'seriecgc.xlsx'

try:
    df = pd.read_excel(nome_file_excel)
except FileNotFoundError:
    raise FileNotFoundError(f"ERRORE: File '{nome_file_excel}' non trovato. Caricalo su Colab.")

# Pulizia dei nomi per la ricerca
df['NOME_PULITO'] = df['NOME'].str.replace(r'\(\d+\)', '', regex=True).str.strip()

# Calcolo preciso dell'età (valido per tutti i calciatori)
df['NASCITA'] = pd.to_datetime(df['NASCITA'], errors='coerce')
data_odierna = datetime.now()
df['ETA'] = (data_odierna - df['NASCITA']).dt.days / 365.25
df['ETA'] = df['ETA'].fillna(28).astype(int) # Default a 28 anni se manca il dato

# ==========================================
# 2. ALGORITMO DI RENDIMENTO/POTENZIALE GENERALE
# ==========================================
def calcola_indice_performance(row):
    punteggio = 50.0 # Base di partenza uguale per tutti

    # Bonus Esperienza / Continuità
    punteggio += (row['PRES'] / 38.0) * 20.0

    # Modificatori di Ruolo basati sull'efficacia a partita
    if row['PRES'] > 0:
        gol_per_game = row['GOL'] / row['PRES']
        gialli_per_game = row['cartellini gialli'] / row['PRES']
    else:
        gol_per_game = 0
        gialli_per_game = 0

    if row['RUOLO'] == 'ATT':
        punteggio += min(gol_per_game * 40, 20)
    elif row['RUOLO'] == 'CEN':
        punteggio += min(gol_per_game * 60, 15)
        punteggio += (1 - min(gialli_per_game, 1)) * 5
    elif row['RUOLO'] == 'DIF':
        punteggio += (1 - min(gialli_per_game, 1)) * 15
        punteggio += min(gol_per_game * 80, 10)
    elif row['RUOLO'] == 'POR':
        punteggio += (row['PRES'] / 38.0) * 15

    return min(punteggio, 99.0)

df['INDICE_IA'] = df.apply(calcola_indice_performance, axis=1).round(1)

# ==========================================
# 3. MOTORE DI RICERCA AVANZATO E FILTRAGGIO
# ==========================================
def motore_scouting(cerca_nome, ruolo_scelto, min_eta, max_eta, min_presenze, min_indice, min_gol):
    filtro = df.copy()

    # 1. Filtro testuale per nome (se l'utente scrive qualcosa)
    if cerca_nome and cerca_nome.strip() != "":
        filtro = filtro[filtro['NOME_PULITO'].str.contains(cerca_nome, case=False, na=False)]

    # 2. Filtro per Ruolo
    if ruolo_scelto != "Tutti":
        filtro = filtro[filtro['RUOLO'] == ruolo_scelto]

    # 3. Filtri numerici parametrici
    filtro = filtro[
        (filtro['ETA'] >= min_eta) &
        (filtro['ETA'] <= max_eta) &
        (filtro['PRES'] >= min_presenze) &
        (filtro['INDICE_IA'] >= min_indice) &
        (filtro['GOL'] >= min_gol)
    ]

    if len(filtro) == 0:
        return pd.DataFrame({"Messaggio": ["Nessun calciatore corrisponde ai criteri di ricerca attuali."]})

    # Selezione colonne finali da mostrare
    risultati = filtro[['NOME_PULITO', 'RUOLO', 'ETA', 'INDICE_IA', 'PRES', 'GOL', 'cartellini gialli']]
    
    risultati = risultati.rename(columns={
        'NOME_PULITO': 'Calciatore',
        'RUOLO': 'Posizione',
        'ETA': 'Età',
        'INDICE_IA': '📊 INDICE PERFORMANCE',
        'PRES': 'Presenze',
        'GOL': 'Gol',
        'cartellini gialli': 'Ammonizioni'
    })

    # Ordina per il punteggio IA migliore e mostra fino a 50 risultati (estendibile)
    return risultati.sort_values(by='📊 INDICE PERFORMANCE', ascending=False).head(50)

# ==========================================
# 4. INTERFACCIA GRAFICA GENERALE (GRADIO)
# ==========================================
ruoli_disponibili = ["Tutti"] + sorted(list(df['RUOLO'].dropna().unique()))

interfaccia = gr.Interface(
    fn=motore_scouting,
    inputs=[
        gr.Textbox(label="🔍 Cerca Calciatore per Nome (es. 'Mignani' o lascia vuoto)", placeholder="Scrivi il nome..."),
        gr.Dropdown(choices=ruoli_disponibili, value="Tutti", label="Filtra per Ruolo"),
        gr.Slider(minimum=15, maximum=42, value=15, step=1, label="Età Minima"),
        gr.Slider(minimum=15, maximum=42, value=40, step=1, label="Età Massima"),
        gr.Slider(minimum=0, maximum=38, value=0, step=1, label="Minimo Presenze"),
        gr.Slider(minimum=40, maximum=99, value=40, step=1, label="Indice Performance Minimo"),
        gr.Slider(minimum=0, maximum=30, value=0, step=1, label="Minimo Gol segnati")
    ],
    outputs=gr.Dataframe(label="Risultati della Ricerca (Top 50)"),
    title="⚽ Hub di Scouting Totale - Serie C",
    description="Cerca qualsiasi giocatore nel database per nome, oppure usa i filtri combinati per Età, Ruolo, Gol e Performance."
)

interfaccia.launch(debug=True)