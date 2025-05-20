import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from streamlit.components.v1 import html

# Logo codificato in base64 (Cluster Reply)
logo_base64 = "iVBORw0KGgoAAAANSUhEUgAAAZAAAABKCAIAAAAaD5VmAAAgAElEQVR4Aey9..."  # <-- stringa base64 completa qui
logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Cluster Reply Logo" style="height:60px;">'

st.set_page_config(page_title="Calcolo ROI AI", layout="centered")
st.title("📈 Calcolatore per ROI di POC con AI")

# HEADER
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center;'>
  {logo_html}
  <div style='font-size:18px; font-weight:300;'>Powered by <b>GK89</b></div>
</div>
<hr>
""", unsafe_allow_html=True)

# SEPARATORE
st.markdown("---")

# INPUT SECTION
with st.container():
    st.markdown("### 📅 Parametri di Ingresso")

    # Stile per sfondo giallo tenue nei campi input
    input_style = """
    <style>
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        background-color: #fff9c4;
    }
    </style>
    """
    st.markdown(input_style, unsafe_allow_html=True)

    nome_caso = st.text_input("Nome del Caso d'Uso", "Classificazione Email")
    volume_attivita = st.number_input("Volume Attività (unità/mese)", 0, value=10000)
    tempo_pre = st.number_input("Tempo per unità - PRE AI (minuti)", 0.0, value=0.75)
    tempo_post = st.number_input("Tempo per unità - POST AI (minuti)", 0.0, value=0.25)
    percentuale_auto = st.slider("% Attività Automatizzate", 0, 100, 80)
    costo_orario = st.number_input("Costo Orario Medio (€)", 0.0, value=30.0)
    costo_una_tantum = st.number_input("Costo Implementazione Una Tantum (€)", 0.0, value=3000.0)
    costo_ricorrente = st.number_input("Costo Ricorrente Mensile (€)", 0.0, value=50.0)
    periodo = st.radio("Periodo di Analisi", ["Mensile", "Annuale"])

# CALCOLI
auto_ratio = percentuale_auto / 100
ore_pre = (volume_attivita * tempo_pre) / 60
ore_post = ((volume_attivita * (1 - auto_ratio)) * tempo_post) / 60
costo_pre = ore_pre * costo_orario
costo_post = ore_post * costo_orario + costo_ricorrente

if periodo == "Annuale":
    costo_pre *= 12
    costo_post *= 12
    risparmio = costo_pre - costo_post
    roi = (risparmio - costo_una_tantum) / costo_una_tantum if costo_una_tantum else 0
    payback = costo_una_tantum / (risparmio / 12) if risparmio > 0 else float("inf")
    label = "annuo"
    risparmio_mese = risparmio / 12
else:
    risparmio = costo_pre - costo_post
    roi = (risparmio - costo_una_tantum) / costo_una_tantum if costo_una_tantum else 0
    payback = costo_una_tantum / risparmio if risparmio > 0 else float("inf")
    label = "mensile"
    risparmio_mese = risparmio

# SEPARATORE
st.markdown("---")

# OUTPUT SECTION
with st.container():
    st.markdown("### 📊 Risultati del Calcolo")
    st.metric(f"Costo PRE-AI ({label})", f"{costo_pre:,.2f} €", help="(Volume × Tempo pre AI / 60) × Costo orario")
    st.markdown("<small>Costi sostenuti oggi senza automazione.</small>", unsafe_allow_html=True)

    st.metric(f"Costo POST-AI ({label})", f"{costo_post:,.2f} €", help="((Volume × (1-% auto) × Tempo post AI / 60) × Costo orario + costi ricorrenti)")
    st.markdown("<small>Nuova struttura di costi considerando automazione parziale e costi AI.</small>", unsafe_allow_html=True)

    st.metric(f"Risparmio {label.capitalize()}", f"{risparmio:,.2f} €", help="Costo PRE-AI - Costo POST-AI")
    st.markdown(f"<small>Risparmio diretto di costo operativo, su base {label}.</small>", unsafe_allow_html=True)

    st.metric(f"ROI su base {label} (%)", f"{roi * 100:,.2f}", help="(Risparmio - Costo iniziale) / Costo iniziale × 100")
    st.markdown("<small>Indice di redditività dell'iniziativa AI rispetto all'investimento iniziale.</small>", unsafe_allow_html=True)

    st.metric("Payback Period (mesi)", f"{payback:,.2f}" if payback != float("inf") else "Non raggiunto", help="Costo iniziale / Risparmio mensile")
    st.markdown("<small>Numero di mesi necessari per recuperare l'investimento iniziale.</small>", unsafe_allow_html=True)

# SEPARATORE
st.markdown("---")

# GRAFICO
with st.container():
    st.markdown("### 🔼 ROI Cumulato nel Tempo")
    mesi = list(range(1, 25))
    cumulato = [risparmio_mese * m - costo_una_tantum for m in mesi]
    fig, ax = plt.subplots()
    ax.plot(mesi, cumulato, marker='o')
    ax.fill_between(mesi, cumulato, where=[v >= 0 for v in cumulato], alpha=0.1)
    ax.axhline(0, color='gray', linestyle='--')
    ax.axvline(payback, color='red', linestyle='--', label='Break-even')
    ax.set_xlabel("Mesi")
    ax.set_ylabel("Guadagno Netto (€)")
    ax.set_title("ROI Cumulato (mese su mese)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
    st.caption("Il grafico mostra il guadagno netto accumulato mese per mese e il punto di pareggio.")

# SEPARATORE
st.markdown("---")

# EXPORT
with st.container():
    st.markdown("### 📄 Esporta i Risultati")
    input_dict = {
        "Caso d'Uso": nome_caso,
        "Volume Mensile": volume_attivita,
        "Tempo PRE (min)": tempo_pre,
        "Tempo POST (min)": tempo_post,
        "% Automatizzato": percentuale_auto,
        "Costo Orario (€)": costo_orario,
        "Una Tantum (€)": costo_una_tantum,
        "Ricorrente/mese (€)": costo_ricorrente,
        "Periodo": periodo
    }
    output_dict = {
        f"Costo PRE-AI ({label})": costo_pre,
        f"Costo POST-AI ({label})": costo_post,
        f"Risparmio ({label})": risparmio,
        "ROI (%)": roi * 100,
        "Payback (mesi)": payback
    }

    df_input = pd.DataFrame(list(input_dict.items()), columns=["Parametro", "Valore"])
    df_output = pd.DataFrame(list(output_dict.items()), columns=["Indicatore", "Valore"])
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_input.to_excel(writer, index=False, sheet_name='Input')
        df_output.to_excel(writer, index=False, sheet_name='Output')

    st.download_button(
        label="📃 Scarica Excel",
        data=excel_buffer.getvalue(),
        file_name="ROI_AI_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("Cluster Reply - Calcolo ROI AI | Powered by GK89")
