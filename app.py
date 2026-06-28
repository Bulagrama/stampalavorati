import streamlit as st
from PIL import Image
import io
from streamlit_paste_uploader import paste_uploader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Fai uno screenshot con `Win + Shift + S`, clicca nel riquadro sotto e premi **CTRL+V**.")

# Inizializziamo l'archivio immagini se non esiste nella sessione
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# Questo componente crea una vera area compatibile con il Ctrl+V del browser
immagine_incollata = paste_uploader(
    "📋 Clicca qui dentro e premi CTRL+V per aggiungere lo screenshot",
    key="incollatore_appunti"
)

# Se viene rilevata una nuova immagine dagli appunti
if immagine_incollata is not None:
    # Apriamo l'immagine per estrarne i byte
    img = Image.open(immagine_incollata)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    dati_bytes = buf.getvalue()
    
    # Evitiamo di duplicarla se l'utente non cambia screenshot
    if not st.session_state.archivio_immagini or st.session_state.archivio_immagini[-1]["bytes"] != dati_bytes:
        st.session_state.archivio_immagini.append({"bytes": dati_bytes})
        st.toast("✅ Immagine salvata in lista!", icon="🔥")
        st.rerun()

# Se ci sono immagini nell'archivio, mostriamo la gestione e la stampa
if st.session_state.archivio_immagini:
    st.markdown("---")
    st.subheader(f"📋 Immagini pronte per il PDF ({len(st.session_state.archivio_immagini)})")
    
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.archivio_immagini = []
        st.rerun()
        
    # Anteprime a schermo
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
