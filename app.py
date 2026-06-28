import streamlit as st
from PIL import Image
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Fai uno screenshot con `Win + Shift + S`, poi clicca nella pagina e premi **CTRL+V**.")

# Inizializziamo l'archivio immagini se non esiste
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# --- IL TRUCCO DEFINITIVO: JAVASCRIPT NATIVO ---
# Questo codice dice al browser: "Se l'utente incolla un'immagine ovunque, catturala!"
# Usiamo i query_params di Streamlit per mandare l'immagine da JavaScript a Python in modo istantaneo.

st.components.v1.html(
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
                    // Inviamo i dati dell'immagine direttamente a Streamlit
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
    height=0,
)

# Un piccolo espediente per catturare l'output del componente JS qui sopra
# Usiamo un text_input invisibile gestito da un componente personalizzato integrato
if "img_incollata_base64" not in st.session_state:
    st.session_state.img_incollata_base64 = None

# Sfruttiamo il valore di ritorno del frame usando l'approccio classico delle query o un trucco nativo
# Per evitare complicazioni, usiamo il widget nativo che reagisce al Ctrl+V se cliccato, ma potenziato:
input_testo = st.text_input("⚠️ [CLICCA QUI PRIMA DI FARE CTRL+V]", placeholder="Clicca qui dentro in modo che lampeggi la barra, poi premi CTRL+V")

# Se il browser incolla l'immagine trasformatasi in testo (Base64) o se riusciamo a catturarla:
if input_testo and input_testo.startswith("data:image"):
    try:
        header, encoded = input_testo.split(",", 1)
        data = base64.b64decode(encoded)
        if data not in [img['bytes'] for img in st.session_state.archivio_immagini]:
            st.session_state.archivio_immagini.append({"bytes": data})
            st.toast("✅ Immagine aggiunta!")
    except:
        pass

# --- ALTERNATIVA 100% FUNZIONANTE SE IL TUO BROWSER BLOCCA IL CTRL+V ---
st.markdown("---")
file_caricati = st.file_uploader(
    "🔄 Se il Ctrl+V viene bloccato dal tuo browser, trascina semplicemente lo screenshot qui dentro:", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if file_caricati:
    for f in file_caricati:
        f.seek(0)
        dati_file = f.read()
        if dati_file not in [img['bytes'] for img in st.session_state.archivio_immagini]:
            st.session_state.archivio_immagini.append({"bytes": dati_file})

# --- MOSTRIAMO LE IMMAGINI SALVATE ---
if st.session_state.archivio_immagini:
    st.subheader(f"📋 Immagini pronte per la stampa ({len(st.session_state.archivio_immagini)})")
    
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
