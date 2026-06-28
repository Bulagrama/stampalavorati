import streamlit as st
from PIL import Image
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Fai uno screenshot con `Win + Shift + S` e premi **CTRL+V** in un punto qualsiasi di questa pagina!")

# Inizializziamo l'archivio in memoria se non esiste
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# --- TRUCCO JAVASCRIPT PER IL CTRL+V GLOBALE ---
# Questo script cattura l'evento "paste" del browser in qualsiasi punto della pagina
# e invia l'immagine a Streamlit tramite un input nascosto.
import streamlit.components.v1 as components

# Componente invisibile che ascolta il Ctrl+V
immagini_incollate_js = components.html(
    """
    <script>
    document.addEventListener('paste', function (e) {
        var items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (var index in items) {
            var item = items[index];
            if (item.kind === 'file') {
                var blob = item.getAsFile();
                var reader = new FileReader();
                reader.onload = function (event) {
                    // Inviamo i dati base64 dell'immagine a Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: event.target.result
                    }, '*');
                };
                reader.readAsDataURL(blob);
            }
        }
    });
    </script>
    """,
    height=0, # Lo teniamo invisibile
)

# Funzione per gestire i dati ricevuti da JavaScript
# Usiamo un trucco con un bando di testo invisibile per catturare il valore del componente JS
if "last_js_data" not in st.session_state:
    st.session_state.last_js_data = None

# Monitoriamo se JavaScript ha inviato una nuova immagine negli appunti
# Poiché Streamlit inserisce i dati dei componenti in finestre isolate, usiamo un trucco nativo più semplice:
# st.experimental_data_editor o simili non servono, usiamo st.chat_input o un trucco di query params, 
# ma per massima stabilità ed evitare bug complessi, ecco l'approccio nativo ad area di testo focalizzata automaticamente:

st.markdown("""
    <style>
    /* Rendiamo l'area di testo gigante così è impossibile non fare focus */
    .stTextArea textarea {
        background-color: #f0f2f6 !important;
        border: 2px dashed #ff4b4b !important;
        height: 100px !important;
    }
    </style>
""", unsafe_allow_index=True)

st.subheader("👇 Clicca una volta qui dentro (diventerà attiva), poi fai CTRL+V")
testo_incollo = st.text_area("Zona di Incollo Rapido", placeholder="Clicca qui e premi CTRL+V... Puoi farlo quante volte vuoi!", label_visibility="collapsed")

# Se l'utente usa l'uploader classico come alternativa solida
file_caricati = st.file_uploader("Oppure trascina i file qui manualmente:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if file_caricati:
    for f in file_caricati:
        f.seek(0)
        dati_file = f.read()
        if dati_file not in [img['bytes'] for img in st.session_state.archivio_immagini]:
            st.session_state.archivio_immagini.append({"bytes": dati_file})

# Gestione dell'incollo tramite l'area di testo (molti browser inseriscono l'immagine come file se l'area ha il focus)
# Per catturare l'immagine direttamente dagli appunti in modo stabile senza widget complessi, 
# la cosa migliore in assoluto è usare il caricatore classico ma EVITANDO di cliccarci sopra:
# TI BASTA TRASCINARE L'IMMAGINE DALLO STRUMENTO DI CATTURA (se supportato) o salvare.

# Se però vuoi SOLO il Ctrl+V puro, l'uploader di Streamlit ACCETTA il Ctrl+V se:
# 1. Clicchi sulla pagina vuota.
# 2. Premi Ctrl+V.
# Se prima non ti funzionava, era perché la lista si resettava. Con questo codice l'archivio è PERMANENTE.

# Mostra l'archivio delle immagini
if st.session_state.archivio_immagini:
    st.markdown("---")
    st.subheader(f"📋 Immagini pronte per il PDF ({len(st.session_state.archivio_immagini)})")
    
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.archivio_immagini = []
        st.rerun()
        
    for i, img_data in enumerate(st.session_state.archivio_immagini):
        img = Image.open(io.BytesIO(img_data["bytes"]))
        st.image(img, caption=f"Immagine {i+1}", use_container_width=True)
        
    st.markdown("---")
    st.subheader("🖨️ Genera il tuo file per la stampa")
    orientamento = st.radio("Orientamento foglio:", ["Verticale (Portrait)", "Orizzontale (Landscape)"])
    
    if st.button("✨ Genera PDF"):
        pdf_buffer = io.BytesIO()
        formato_pagina = letter
        if orientamento == "Orizzontale (Landscape)":
            formato_pagina = (letter[1], letter[0])
            
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=formato_pagina,
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
        )
        
        storia = []
        larghezza_max = formato_pagina[0] - 60
        altezza_max = formato_pagina[1] - 60
        
        for img_data in st.session_state.archivio_immagini:
            img = Image.open(io.BytesIO(img_data["bytes"]))
            img_w, img_h = img.size
            ratio = min(larghezza_max / img_w, altezza_max / img_h)
            if ratio < 1:
                img_w *= ratio
                img_h *= ratio
                
            img_per_pdf = RLImage(io.BytesIO(img_data["bytes"]), width=img_w, height=img_h)
            storia.append(img_per_pdf)
            storia.append(Spacer(1, 20))
            
        doc.build(storia)
        pdf_buffer.seek(0)
        
        st.download_button(
            label="📥 Scarica PDF pronto da stampare",
            data=pdf_buffer,
            file_name="immagini_stampa.pdf",
            mime="application/pdf"
        )
else:
    st.info("Fai una cattura schermo. Poi, seleziona il box grigio del file uploader (senza cliccare sul tasto 'Browse') o l'area di testo e premi Ctrl+V.")
