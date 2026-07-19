import pandas as pd
import numpy as np
from datetime import datetime
import gradio as gr

# ==========================================
# 1. CARICAMENTO E PULIZIA DATI "SERIE C - GIRONE C"
# ==========================================
print("Avvio caricamento dati Serie C...")
nome_file_excel = 'seriecgc.xlsx'

try:
    df = pd.read_excel(nome_file_excel)
except FileNotFoundError:
    raise FileNotFoundError(f"ERRORE: File '{nome_file_excel}' non trovato. Caricalo su Colab.")

# Pulizia dei nomi
df['NOME_PULITO'] = df['NOME'].str.replace(r'\(\d+\)', '', regex=True).str.strip()

# Calcolo preciso dell'età
df['NASCITA'] = pd.to_datetime(df['NASCITA'], errors='coerce')
data_odierna = datetime.now()
df['ETA'] = (data_odierna - df['NASCITA']).dt.days / 365.25
df['ETA'] = df['ETA'].fillna(25).astype(int)

# Isoliamo i giovani (Under 23)
df_giovani = df[df['ETA'] <= 23].copy()

# Se nel file Excel mancano valori nella colonna Assist (es. celle vuote), li riempiamo con 0
if 'ASSIST' in df_giovani.columns:
    df_giovani['ASSIST'] = df_giovani['ASSIST'].fillna(0).astype(int)

# ==========================================
# 2. ALGORITMO DI POTENZIALE PER RUOLO
# ==========================================
def calcola_potenziale_ruolo(row):
    punteggio = 40.0

    # Bonus Età
    if row['ETA'] <= 18:
        punteggio += 30
    elif row['ETA'] <= 20:
        punteggio += 20
    elif row['ETA'] <= 22:
        punteggio += 10

    # Bonus Esperienza
    punteggio += (row['PRES'] / 38.0) * 20.0

    # Modificatori di Ruolo
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
        punteggio += (1 - min(gialli_per_game, 1)) * 10
        punteggio += min(gol_per_game * 80, 10)
    elif row['RUOLO'] == 'POR':
        punteggio += (row['PRES'] / 38.0) * 10

    return min(punteggio, 99.0)

df_giovani['POTENZIALE_IA'] = df_giovani.apply(calcola_potenziale_ruolo, axis=1).round(1)

# ==========================================
# 3. MOTORE DELLA DASHBOARD GRADIO (AGGIORNATO)
# ==========================================
# Aggiunti i parametri "min_gol" e "min_assist"
def esplora_girone_c(ruolo_scelto, eta_max, min_presenze, min_potenziale, min_gol, min_assist):

    # Filtriamo per potenziale, gol e assist
    filtro = df_giovani[
        (df_giovani['ETA'] <= eta_max) &
        (df_giovani['PRES'] >= min_presenze) &
        (df_giovani['POTENZIALE_IA'] >= min_potenziale) &
        (df_giovani['GOL'] >= min_gol)
    ].copy()

    # Aggiungiamo il filtro per gli assist solo se la colonna esiste nel dataframe
    if 'ASSIST' in filtro.columns:
        filtro = filtro[filtro['ASSIST'] >= min_assist]

    if ruolo_scelto != "Tutti":
        filtro = filtro[filtro['RUOLO'] == ruolo_scelto]

    if len(filtro) == 0:
        return pd.DataFrame({"Messaggio": ["Nessun giocatore rispetta questi parametri."]}), None

    # Prepariamo le colonne per i risultati
    colonne_output = ['NOME_PULITO', 'RUOLO', 'ETA', 'POTENZIALE_IA', 'PRES', 'GOL']
    if 'ASSIST' in filtro.columns:
        colonne_output.append('ASSIST')
    colonne_output.append('cartellini gialli')

    risultati = filtro[colonne_output]

    # Rinominiamo le colonne per l'estetica della tabella
    dizionario_nomi = {
        'NOME_PULITO': 'Calciatore',
        'RUOLO': 'Posizione',
        'ETA': 'Età',
        'POTENZIALE_IA': '⚽ POTENZIALE (1-99)',
        'PRES': 'Presenze',
        'GOL': 'Gol',
        'cartellini gialli': 'Ammonizioni'
    }
    risultati = risultati.rename(columns=dizionario_nomi)

    risultati = risultati.sort_values(by='⚽ POTENZIALE (1-99)', ascending=False).head(15)
    return risultati

# ==========================================
# 4. INTERFACCIA GRAFICA (UI) (AGGIORNATA)
# ==========================================
ruoli_disponibili = ["Tutti"] + list(df_giovani['RUOLO'].unique())

interfaccia = gr.Interface(
    fn=esplora_girone_c,
    inputs=[
        gr.Dropdown(choices=ruoli_disponibili, value="Tutti", label="Filtra per Ruolo"),
        gr.Slider(minimum=16, maximum=40, value=21, step=1, label="Età Massima"),
        gr.Slider(minimum=0, maximum=38, value=10, step=1, label="Minimo Presenze in Campionato"),
        gr.Slider(minimum=40, maximum=99, value=75, step=1, label="Potenziale Minimo Richiesto"),
        # NUOVI CURSORI PER GOL E ASSIST
        gr.Slider(minimum=0, maximum=30, value=0, step=1, label="Minimo Gol"),

    ],
    outputs=gr.Dataframe(label=" Girone C (Top 15)"),
    title="🔍 Serie C - Girone C Scouting",
    description="Usa i cursori per affinare la tua ricerca e individuare i migliori prospetti secondo gli standard della tua società."
)

interfaccia.launch(debug=True)