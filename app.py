import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer
import io

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Incolla Immagini e Crea PDF per Stampa")
st.write("Clicca sul box qui sotto e usa **Ctrl+V** per caricare le immagini una alla volta (oppure trascinale).")

# Inizializziamo lo stato della sessione per salvare le immagini
if "lista_immagini" not in st.session_state:
    st.session_state.lista_immagini = []

# Componente di caricamento (accetta più file)
file_caricati = st.file_uploader(
    "Area di upload / Incolla qui con Ctrl+V", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True,
    key="uploader"
)

# Se ci sono nuovi file caricati, li salviamo nello stato della sessione
if file_caricati:
    st.session_state.lista_immagini = file_caricati

# Mostra le anteprime delle immagini caricate
if st.session_state.lista_immagini:
    st.subheader(f"Immagini Caricate ({len(st.session_state.lista_immagini)})")
    
    # Bottone per svuotare la lista se si vuole ricominciare
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.lista_immagini = []
        st.rerun()
        
    for i, file_img in enumerate(st.session_state.lista_immagini):
        img = Image.open(file_img)
        st.image(img, caption=f"Immagine {i+1}", use_container_width=True)
    
    st.markdown("---")
    st.subheader("🖨️ Genera il tuo file per la stampa")
    
    # Configurazione layout PDF semplice
    orientamento = st.radio("Orientamento foglio:", ["Verticale (Portrait)", "Orizzontale (Landscape)"])
    
    if st.button("✨ Genera PDF"):
        # Creiamo un buffer in memoria per il PDF senza salvare file sul server
        pdf_buffer = io.BytesIO()
        
        formato_pagina = letter
        if orientamento == "Orizzontale (Landscape)":
            formato_pagina = (letter[1], letter[0]) # Inverte larghezza e altezza
            
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=formato_pagina,
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
        )
        
        storia = []
        larghezza_max = formato_pagina[0] - 60 # Sottraiamo i margini
        altezza_max = formato_pagina[1] - 60
        
        for file_img in st.session_state.lista_immagini:
            # Resettiamo il puntatore del file per sicurezza
            file_img.seek(0)
            img = Image.open(file_img)
            
            # Calcolo proporzioni per non far strabordare l'immagine dal foglio
            img_w, img_h = img.size
            ratio = min(larghezza_max / img_w, altezza_max / img_h)
            # Se l'immagine è più piccola della pagina, la teniamo originale, altrimenti la scaliamo
            if ratio < 1:
                img_w = img_w * ratio
                img_h = img_h * ratio
            
            # Usiamo i byte dell'immagine direttamente nel PDF
            file_img.seek(0)
            img_per_pdf = RLImage(file_img, width=img_w, height=img_h)
            storia.append(img_per_pdf)
            storia.append(Spacer(1, 20)) # Spazio tra un'immagine e l'altra
            
        # Costruisci il PDF
        doc.build(storia)
        pdf_buffer.seek(0)
        
        # Bottone di download per l'utente
        st.download_button(
            label="📥 Scarica PDF pronto da stampare",
            data=pdf_buffer,
            file_name="immagini_stampa.pdf",
            mime="application/pdf"
        )
else:
    st.info("Incolla o trascina la prima immagine per iniziare!")
