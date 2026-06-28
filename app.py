import streamlit as st
from PIL import Image
import io
from streamlit_paste_button import paste_image_button
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Fai uno screenshot con Windows (`Win + Shift + S`) e poi clicca il bottone qui sotto per caricarlo.")

# Inizializziamo la lista nello stato della sessione (salviamo i file in formato Byte)
if "lista_immagini_bytes" not in st.session_state:
    st.session_state.lista_immagini_bytes = []

# Questo è il magico bottone che legge gli appunti del tuo computer!
paste_btn = paste_image_button(
    label="📋 Incolla Immagine dagli Appunti",
    background_color="#FF4B4B",
    hover_color="#D33636",
    errors="ignore"
)

# Se l'utente ha cliccato sul bottone e c'è un'immagine negli appunti
if paste_btn.image_data is not None:
    img_incollata = paste_btn.image_data
    
    # Convertiamo l'immagine in bytes per poterla salvare stabilmente
    buf = io.BytesIO()
    img_incollata.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    
    # Evitiamo di inserire la stessa identica immagine consecutivamente se si clicca più volte
    if not st.session_state.lista_immagini_bytes or st.session_state.lista_immagini_bytes[-1] != img_bytes:
        st.session_state.lista_immagini_bytes.append(img_bytes)
        st.toast("✅ Immagine aggiunta alla lista!", icon="🔥")
        st.rerun()

# Mostra le anteprime e il PDF se ci sono immagini caricate
if st.session_state.lista_immagini_bytes:
    st.markdown("---")
    st.subheader(f"Immagini accumulate ({len(st.session_state.lista_immagini_bytes)})")
    
    if st.button("❌ Svuota tutto e ricomincia"):
        st.session_state.lista_immagini_bytes = []
        st.rerun()
        
    # Mostriamo le anteprime a schermo
    for i, img_bytes in enumerate(st.session_state.lista_immagini_bytes):
        img = Image.open(io.BytesIO(img_bytes))
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
        
        for img_bytes in st.session_state.lista_immagini_bytes:
            img = Image.open(io.BytesIO(img_bytes))
            img_w, img_h = img.size
            ratio = min(larghezza_max / img_w, altezza_max / img_h)
            if ratio < 1:
                img_w *= ratio
                img_h *= ratio
            
            # Prepariamo l'immagine per ReportLab rileggendo i bytes
            img_per_pdf = RLImage(io.BytesIO(img_bytes), width=img_w, height=img_h)
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
    st.info("Fai una cattura schermo, poi clicca sul bottone rosso qui sopra per provarla.")
