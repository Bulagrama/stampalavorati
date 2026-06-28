import streamlit as st
from PIL import Image
import io
import re
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Inserisci i tuoi screenshot premendo semplicemente **CTRL+V**.")

# Inizializziamo l'archivio in memoria
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# Campo di testo speciale: i browser accettano SEMPRE il Ctrl+V qui dentro
st.subheader("👇 Clicca qui dentro e premi CTRL+V")
input_incollo = st.text_input(
    "Casella di incollo",
    value="",
    placeholder="Clicca qui, poi premi Ctrl+V...",
    label_visibility="collapsed",
    key="input_chiave"
)

# Quando incolli un'immagine in un campo di testo, alcuni browser inseriscono del testo speciale o dei tag.
# Per intercettare l'immagine in modo universale, lasciamo anche la possibilità di usare un trucco:
# Se l'utente trascina l'immagine o se viene incollata come stringa base64, la catturiamo.
# Inoltre, aggiungiamo un uploader nascosto che cattura i dati se il browser decide di passargli il file.

file_caricati = st.file_uploader(
    "In alternativa, se il Ctrl+V non va, puoi trascinare lo screenshot direttamente qui dentro:", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

# 1. Gestione caricamento da uploader/trascinamento
if file_caricati:
    for f in file_caricati:
        f.seek(0)
        dati_file = f.read()
        if dati_file not in [img['bytes'] for img in st.session_state.archivio_immagini]:
            st.session_state.archivio_immagini.append({"bytes": dati_file})

# 2. Gestione del Ctrl+V nel campo di testo (se il browser passa l'immagine come dati)
if input_incollo:
    # Se il browser incolla l'immagine sotto forma di URI Base64 (accade in molti sistemi)
    if "data:image" in input_incollo:
        try:
            base64_data = re.sub('^data:image/.+;base64,', '', input_incollo)
            dati_file = base64.b64decode(base64_data)
            if dati_file not in [img['bytes'] for img in st.session_state.archivio_immagini]:
                st.session_state.archivio_immagini.append({"bytes": dati_file})
                st.toast("✅ Immagine incollata con successo!")
        except Exception:
            pass

# Mostra l'archivio delle immagini accumulate
if st.session_state.archivio_immagini:
    st.markdown("---")
    st.subheader(f"📋 Immagini pronte per il PDF ({len(st.session_state.archivio_immagini)})")
    
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.archivio_immagini = []
        st.rerun()
        
    # Mostra le anteprime
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
