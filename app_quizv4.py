import streamlit as st
import streamlit.components.v1 as components
import random
import time
import re
import os  # Necessario per leggere il file locale

# ===============================
# Configurazione Pagina
# ===============================
st.set_page_config(page_title="🧠 Quiz Web Pro", layout="centered")

# CSS per styling avanzato
st.markdown("""
    <style>
    .stRadio > label {font-size: 18px !important; padding: 10px; border-radius: 5px; width: 100%;}
    .question-text {font-size: 22px; font-weight: bold; margin-bottom: 20px; color: #1f2937;}
    .correct-answer {color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin: 5px 0;}
    .wrong-answer {color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin: 5px 0;}
    .original-id {color: #007bff; font-family: monospace; font-size: 0.9em; margin-right: 8px;}
    </style>
""", unsafe_allow_html=True)

# ===============================
# 1. Parsing con Cattura ID Domanda
# ===============================
def carica_domande(contenuto_str):
    domande = []
    lines = contenuto_str.split('\n')
    curr_domanda = None
    
    # Regex per catturare il NUMERO (Gruppo 1) e il TESTO (Gruppo 2)
    regex_domanda_start = re.compile(r'^DOMANDA:\s*(\d+)\s*[:\.-]?\s*(.*)', re.IGNORECASE)
    regex_opzione = re.compile(r'^([A-Z])\)\s*(.*)')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match_domanda = regex_domanda_start.match(line)
        
        if match_domanda:
            if curr_domanda and curr_domanda['opzioni'] and curr_domanda['corretta']:
                domande.append(curr_domanda)
            
            numero_orig = match_domanda.group(1) 
            testo_pulito = match_domanda.group(2).strip()
            
            curr_domanda = {
                "id_orig": numero_orig,
                "testo": testo_pulito,
                "opzioni": [],
                "corretta": None
            }
        
        elif curr_domanda is not None:
            match_opzione = regex_opzione.match(line)
            
            if match_opzione:
                lettera = match_opzione.group(1)
                testo_opzione = line
                is_correct = False
                
                if line.endswith("*"):
                    is_correct = True
                    testo_opzione = line[:-1].strip()
                
                curr_domanda["opzioni"].append(testo_opzione)
                if is_correct:
                    curr_domanda["corretta"] = lettera
            else:
                if not curr_domanda["opzioni"]:
                    curr_domanda["testo"] += " " + line

    if curr_domanda and curr_domanda['opzioni'] and curr_domanda['corretta']:
        domande.append(curr_domanda)
        
    return domande

# ===============================
# 2. Gestione Stato
# ===============================
def inizializza_stato():
    if 'stato_quiz' not in st.session_state: st.session_state.stato_quiz = 'setup'
    if 'domande_selezionate' not in st.session_state: st.session_state.domande_selezionate = []
    if 'indice' not in st.session_state: st.session_state.indice = 0
    if 'risposte_date' not in st.session_state: st.session_state.risposte_date = {}
    if 'start_time' not in st.session_state: st.session_state.start_time = 0
    if 'durata_secondi' not in st.session_state: st.session_state.durata_secondi = 3600

inizializza_stato()

# ===============================
# 3. Interfaccia
# ===============================

# --- FASE 1: SETUP ---
if st.session_state.stato_quiz == 'setup':
    st.title("📂 Carica Test amore mio")
    st.markdown("Carica un file `.txt` personale oppure usa il database incluso.")
    
    # 1. File Uploader
    uploaded_file = st.file_uploader("Trascina qui il file domande", type=["txt"])
    
    # 2. Checkbox per file predefinito
    usare_default = st.checkbox("Usa file incluso (DATABASE 1.txt)")

    c1, c2 = st.columns(2)
    minuti = c1.number_input("⏱️ Minuti", value=60, min_value=1)
    num_domande = c2.number_input("❓ N. Domande", value=80, min_value=1)
    
    # Pulsante Avvio
    if st.button("🚀 INIZIA TEST", type="primary", use_container_width=True):
        testo_da_elaborare = None
        
        # Logica di selezione file
        if uploaded_file is not None:
            # Priorità al file caricato
            testo_da_elaborare = uploaded_file.getvalue().decode("utf-8", errors='ignore')
        elif usare_default:
            # Se checkbox attiva, cerca file locale
            if os.path.exists("DATABASE 1.txt"):
                try:
                    with open("DATABASE 1.txt", "r", encoding="utf-8", errors="ignore") as f:
                        testo_da_elaborare = f.read()
                except Exception as e:
                    st.error(f"Errore lettura file locale: {e}")
            else:
                st.error("❌ Il file 'DATABASE 1.txt' non è presente nella cartella del programma.")
        else:
            st.warning("⚠️ Per favore, carica un file o seleziona 'Usa file incluso'.")

        # Se abbiamo del testo, processiamo
        if testo_da_elaborare:
            domande_parse = carica_domande(testo_da_elaborare)
            
            if domande_parse:
                st.success(f"✅ Caricate {len(domande_parse)} domande.")
                time.sleep(1) # Breve pausa per mostrare il messaggio
                
                # Setup Sessione
                st.session_state.domande_selezionate = random.sample(
                    domande_parse, min(num_domande, len(domande_parse))
                )
                st.session_state.durata_secondi = minuti * 60
                st.session_state.start_time = time.time()
                st.session_state.indice = 0
                st.session_state.risposte_date = {}
                st.session_state.stato_quiz = 'in_corso'
                st.rerun()
            else:
                st.error("❌ Nessuna domanda valida trovata nel file.")

# --- FASE 2: IN CORSO ---
elif st.session_state.stato_quiz == 'in_corso':
    
    elapsed = time.time() - st.session_state.start_time
    rimanente = int(st.session_state.durata_secondi - elapsed)
    
    if rimanente <= 0:
        st.session_state.stato_quiz = 'fine'
        st.rerun()

    # --- TIMER JAVASCRIPT REAL-TIME ---
    timer_html = f"""
    <div style="
        display: flex; justify-content: center; align-items: center;
        background-color: #f0f2f6; border: 2px solid {'#ef4444' if rimanente < 300 else '#3b82f6'};
        border-radius: 10px; padding: 10px; margin-bottom: 20px;
        font-family: sans-serif; font-size: 24px; font-weight: bold; color: #1f2937;
    ">
        ⏳ <span id="timer_display" style="margin-left: 10px;">--:--</span>
    </div>
    <script>
        var seconds = {rimanente};
        function updateTimer() {{
            var m = Math.floor(seconds / 60);
            var s = seconds % 60;
            var timeString = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            document.getElementById("timer_display").innerText = timeString;
            if (seconds > 0) {{
                seconds--;
            }}
        }}
        updateTimer();
        setInterval(updateTimer, 1000);
    </script>
    """
    components.html(timer_html, height=80)

    # Sidebar
    with st.sidebar:
        st.write(f"Domanda: **{st.session_state.indice + 1}** / {len(st.session_state.domande_selezionate)}")
        st.progress((st.session_state.indice + 1) / len(st.session_state.domande_selezionate))
        if st.button("Termina Test"):
            st.session_state.stato_quiz = 'fine'
            st.rerun()

    # --- MOSTRA DOMANDA ---
    domanda = st.session_state.domande_selezionate[st.session_state.indice]
    
    testo_formattato = f"<span class='original-id'>({domanda['id_orig']})</span> {domanda['testo']}"
    st.markdown(f"<div class='question-text'>{testo_formattato}</div>", unsafe_allow_html=True)
    
    precedente = st.session_state.risposte_date.get(st.session_state.indice)
    index_selezionato = None
    if precedente:
        for i, opt in enumerate(domanda['opzioni']):
            if opt.startswith(precedente):
                index_selezionato = i
                break
    
    scelta = st.radio("Risposte:", domanda['opzioni'], index=index_selezionato, key=f"q_{st.session_state.indice}", label_visibility="collapsed")
    
    c_prev, c_next = st.columns([1, 4])
    with c_prev:
        if st.session_state.indice > 0:
            if st.button("⬅️ Indietro"):
                if scelta: st.session_state.risposte_date[st.session_state.indice] = scelta[0]
                st.session_state.indice -= 1
                st.rerun()
                
    with c_next:
        btn_txt = "✅ CONSEGNA" if st.session_state.indice == len(st.session_state.domande_selezionate)-1 else "➡️ Conferma"
        if st.button(btn_txt, type="primary"):
            if not scelta:
                st.warning("Seleziona una risposta!")
            else:
                st.session_state.risposte_date[st.session_state.indice] = scelta[0]
                if st.session_state.indice < len(st.session_state.domande_selezionate) - 1:
                    st.session_state.indice += 1
                    st.rerun()
                else:
                    st.session_state.stato_quiz = 'fine'
                    st.rerun()

# --- FASE 3: RISULTATI ---
elif st.session_state.stato_quiz == 'fine':
    st.title("📊 Risultati")
    corrette = sum(1 for i, d in enumerate(st.session_state.domande_selezionate) if st.session_state.risposte_date.get(i,"") == d['corretta'])
    totale = len(st.session_state.domande_selezionate)
    perc = (corrette/totale)*100
    
    col_score = '#d4edda' if perc >= 60 else '#f8d7da'
    st.markdown(f"""
    <div style="background-color: {col_score}; padding: 20px; border-radius: 10px; text-align: center;">
        <h2 style="margin:0;">Punteggio: {corrette} su {totale}</h2>
        <p style="font-size: 18px;">({perc:.1f}%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Revisione")
    for i, dom in enumerate(st.session_state.domande_selezionate):
        user_ans = st.session_state.risposte_date.get(i, "Nessuna")
        is_ok = (user_ans == dom['corretta'])
        
        expander_title = f"{'✅' if is_ok else '❌'} Domanda ({dom['id_orig']})"
        
        with st.expander(expander_title, expanded=not is_ok):
            st.markdown(f"**{dom['testo']}**")
            if is_ok:
                st.markdown(f"<div class='correct-answer'>Tua risposta: {user_ans} (Corretta)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='wrong-answer'>Tua risposta: {user_ans} (Errata)</div>", unsafe_allow_html=True)
                st.markdown(f"👉 **Corretta:** {dom['corretta']}")
            
            st.write("---")
            for opt in dom['opzioni']:
                if opt.startswith(dom['corretta']):
                    st.markdown(f"**{opt}** 👈", unsafe_allow_html=True)
                else:
                    st.write(opt)

    if st.button("Ricomincia"):
        st.session_state.clear()

        st.rerun()
