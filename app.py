import streamlit as st
from PIL import Image
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer

st.set_page_config(page_title="Incolla e Stampa Immagini", layout="centered")

st.title("📸 Cattura, Incolla e Stampa")
st.write("Fai uno screenshot con `Win + Shift + S`. Poi usa l'area di testo grigia in basso per incollare con **CTRL+V**.")

# Inizializziamo l'archivio immagini se non esiste nella sessione
if "archivio_immagini" not in st.session_state:
    st.session_state.archivio_immagini = []

# --- MECCANISMO NATIVO JAVASCRIPT CON INPUT DI TESTO ---
# Usiamo un'area di testo HTML standard. JavaScript intercetta il Ctrl+V dell'immagine, 
# la converte in formato testo (Base64) e la inserisce in un input nascosto di Streamlit.

st.subheader("📋 Zona di Incollo Rapido")
st.write("Clicca una volta nel riquadro grigio qui sotto (deve comparire il cursore per scrivere) e premi **CTRL+V**:")

# Questo script inserisce un'area HTML personalizzata che cattura l'evento di incollo
componente_incollo = st.components.v1.html(
    """
    <div id="paste-zone" style="border: 2px dashed #ff4b4b; background-color: #f0f2f6; padding: 20px; text-align: center; border-radius: 10px; cursor: pointer;">
        <p style="margin: 0; font-family: sans-serif; color: #31333F;">🎯 Clicca QUI dentro e premi <strong>CTRL + V</strong></p>
    </div>
    <script>
    const zone = document.getElementById('paste-zone');
    
    // Rende l'area cliccabile per metterla a fuoco
    zone.addEventListener('click', () => {
        zone.style.backgroundColor = '#e0e4ec';
    });

    document.addEventListener('paste', function (e) {
        var items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (var index in items) {
            var item = items[index];
            if (item.kind === 'file') {
                var blob = item.getAsFile();
                var reader = new FileReader();
                reader.onload = function (event) {
                    // Invia la stringa dell'immagine a Streamlit
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
    height=90,
)

# Per ricevere i dati dal componente HTML sopra in modo pulito e stabile, usiamo un trucco nativo di testo
testo_nascosto = st.text_input("Se vedi del testo strano comparire qui dopo l'incollo, l'immagine è stata catturata!", key="stringa_immagine")

if testo_nascosto and testo_nascosto.startswith("data:image"):
    try:
        # Estraiamo i byte dall'immagine codificata in Base64
        header, encoded = testo_nascosto.split(",", 1)
        dati_bytes = base64.b64decode(encoded)
        
        # Evitiamo duplicati identici consecutivi
        if not st.session_state.archivio_immagini or st.session_state.archivio_immagini[-1]["bytes"] != dati_bytes:
            st.session_state.archivio_immagini.append({"bytes": dati_bytes})
            st.toast("✅ Immagine salvata con successo!")
            # Puliamo l'input per i prossimi inserimenti resettando lo stato
            st.rerun()
    except Exception as e:
        pass

# --- GESTIONE ARCHIVIO E STAMPA ---
if st.session_state.archivio_immagini:
    st.markdown("---")
    st.subheader(f"📋 Immagini accumulate ({len(st.session_state.archivio_immagini)})")
    
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
