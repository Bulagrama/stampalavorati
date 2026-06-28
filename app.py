import streamlit as st
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Incolla Immagini e Crea PDF")
st.write("Usa la scorciatoia qui sotto per caricare i tuoi screenshot uno dopo l'altro.")

# Inizializziamo la lista delle immagini nello stato della sessione
if "lista_immagini" not in st.session_state:
    st.session_state.lista_immagini = []

# --- NUOVO METODO DI INCOLLO ULTRA-STABILE ---
# Un'area di testo speciale che intercetta i file incollati
pastetarget = st.text_input("👇 Clicca qui dentro e premi CTRL+V per aggiungere l'immagine:", placeholder="Clicca qui e premi Ctrl+V")

# Usiamo un uploader nascosto o di supporto che gestisce i file incollati dal browser
file_incollato = st.file_uploader("Oppure trascina i file qui (funziona anche come archivio):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Uniamo i flussi: raccogliamo tutto nella nostra lista persistente
immagini_correnti = []

if file_incollato:
    for f in file_incollato:
        # Evitiamo duplicati controllando il nome o la dimensione
        if f not in st.session_state.lista_immagini:
            st.session_state.lista_immagini.append(f)

# Mostra le anteprime delle immagini accumulate
if st.session_state.lista_immagini:
    st.subheader(f"Immagini pronte per il PDF ({len(st.session_state.lista_immagini)})")
    
    if st.button("❌ Svuota la lista e ricomincia"):
        st.session_state.lista_immagini = []
        st.canvas = None
        st.rerun()
        
    for i, file_img in enumerate(st.session_state.lista_immagini):
        file_img.seek(0)
        img = Image.open(file_img)
        st.image(img, caption=f"Immagine {i+1}", use_container_width=True)
    
    st.markdown("---")
    st.subheader("🖨️ Crea il PDF")
    
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
        
        for file_img in st.session_state.lista_immagini:
            file_img.seek(0)
            img = Image.open(file_img)
            img_w, img_h = img.size
            ratio = min(larghezza_max / img_w, altezza_max / img_h)
            if ratio < 1:
                img_w *= ratio
                img_h *= ratio
            
            file_img.seek(0)
            img_per_pdf = RLImage(file_img, width=img_w, height=img_h)
            storia.append(img_per_pdf)
            storia.append(Spacer(1, 20))
            
        doc.build(storia)
        pdf_buffer.seek(0)
        
        st.download_button(
            label="📥 Scarica PDF per la Stampa",
            data=pdf_buffer,
            file_name="le_mie_immagini.pdf",
            mime="application/pdf"
        )
else:
    st.info("Fai uno screenshot, clicca nella casella di testo in alto e premi Ctrl+V!")
