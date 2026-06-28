import streamlit as st
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Crea la tua lista di screenshot e stampali in un unico PDF.")

# Inizializziamo l'archivio in memoria
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# Spiegazione semplice su come usare il Ctrl+V senza far aprire le cartelle
st.info("""
💡 **Come incollare velocemente:**
1. Fai lo screenshot con **Win + Shift + S**.
2. Fai un **singolo click** nel box grigio qui sotto (se si apre la finestra di Windows, premi subito il tasto **ESC** sulla tastiera per chiuderla).
3. Premi **CTRL + V** sulla tastiera. L'immagine apparirà in elenco!
""")

# Caricatore nativo standard (accetta file multipli e Ctrl+V)
file_caricati = st.file_uploader(
    "Area di Incollo / Caricamento", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

# Salva i file nell'archivio persistente
if file_caricati:
    for f in file_caricati:
        f.seek(0)
        dati_file = f.read()
        # Evita duplicati controllando se i byte sono già salvati
        if dati_file not in [img['bytes'] for img in st.session_state.archivio_immagini]:
            st.session_state.archivio_immagini.append({
                "bytes": dati_file,
                "name": f.name
            })

# Se ci sono immagini salvate nell'archivio
if st.session_state.archivio_immagini:
    st.markdown("---")
    st.subheader(f"📋 Immagini pronte ({len(st.session_state.archivio_immagini)})")
    
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.archivio_immagini = []
        st.rerun()
        
    # Mostra le anteprime
    for i, img_data in enumerate(st.session_state.archivio_immagini):
        img = Image.open(io.BytesIO(img_data["bytes"]))
        st.image(img, caption=f"Immagine {i+1}", use_container_width=True)
        
    st.markdown("---")
    st.subheader("🖨️ Crea il PDF per la stampa")
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
