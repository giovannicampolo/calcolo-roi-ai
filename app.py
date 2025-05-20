import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Calcolo ROI AI", layout="centered")

st.title("📊 Calcolatore ROI per Iniziative AI (PoC)")

st.subheader("🔧 Parametri di Ingresso")

st.markdown(
    "<style>div[data-baseweb='input'] input { background-color: #fff8dc !important; }</style>",
    unsafe_allow_html=True
)

# Input
nome_caso = st.text_input("Nome del Caso d'Uso", "Classificazione Email")
volume_attivita = st.number_input("Volume Attività (unità/mese)", min_value=0, value=10000)
tempo_pre = st.number_input("Tempo per unità - PRE AI (minuti)", min_value=0.0, value=0.75)
tempo_post = st.number_input("Tempo per unità - POST AI (minuti)", min_value=0.0, value=0.25)
percentuale_auto = st.slider("% Attività Automatizzate", 0, 100, 80)
costo_orario = st.number_input("Costo Orario Medio (€)", min_value=0.0, value=30.0)
costo_una_tantum = st.number_input("Costo Implementazione Una Tantum (€)", min_value=0.0, value=3000.0)
costo_ricorrente = st.number_input("Costo Ricorrente Mensile (€)", min_value=0.0, value=50.0)
periodo = st.radio("Periodo di Analisi", ["Mensile", "Annuale"])

# Calcoli
auto_ratio = percentuale_auto / 100
tempo_tot_pre = (volume_attivita * tempo_pre) / 60
tempo_tot_post = ((volume_attivita * (1 - auto_ratio)) * tempo_post) / 60
costo_tot_pre = tempo_tot_pre * costo_orario
costo_tot_post = tempo_tot_post * costo_orario + costo_ricorrente

if periodo == "Annuale":
    costo_tot_pre *= 12
    costo_tot_post *= 12
    risparmio = costo_tot_pre - costo_tot_post
    roi = (risparmio - costo_una_tantum) / costo_una_tantum if costo_una_tantum else 0
    payback = costo_una_tantum / (risparmio / 12) if risparmio > 0 else float("inf")
    label_periodo = "annuo"
    risparmio_mensile = risparmio / 12
else:
    risparmio = costo_tot_pre - costo_tot_post
    roi = (risparmio - costo_una_tantum) / costo_una_tantum if costo_una_tantum else 0
    payback = costo_una_tantum / risparmio if risparmio > 0 else float("inf")
    label_periodo = "mensile"
    risparmio_mensile = risparmio

# Output metriche
st.subheader("📈 Risultati")
st.metric(f"💰 Costo PRE-AI ({label_periodo})", f"{costo_tot_pre:,.2f} €",
          help="(Volume × Tempo Pre AI / 60) × Costo orario")
st.metric(f"💡 Costo POST-AI ({label_periodo})", f"{costo_tot_post:,.2f} €",
          help="((Volume × (1 - % auto) × Tempo Post AI / 60) × Costo orario + costi ricorrenti)")
st.metric(f"✅ Risparmio {label_periodo.capitalize()}", f"{risparmio:,.2f} €",
          help="Costo PRE-AI - Costo POST-AI")
st.metric(f"📈 ROI su base {label_periodo} (%)", f"{roi * 100:,.2f}",
          help="(Risparmio - Costo iniziale) / Costo iniziale × 100")
st.metric("⏳ Payback Period (mesi)", f"{payback:,.2f}" if payback != float("inf") else "Non raggiungibile",
          help="Costo iniziale / Risparmio mensile")

# Grafico ROI cumulato
st.subheader("📊 ROI Cumulato nel Tempo")
mesi = list(range(1, 25))
cumulato = [risparmio_mensile * m - costo_una_tantum for m in mesi]
fig, ax = plt.subplots()
ax.plot(mesi, cumulato, marker='o')
ax.axhline(0, color='gray', linestyle='--')
ax.axvline(payback, color='red', linestyle='--', label='Break-even')
ax.set_xlabel("Mesi")
ax.set_ylabel("Guadagno Netto (€)")
ax.set_title("ROI Cumulato")
ax.grid(True)
st.pyplot(fig)

# Esportazione in Excel
st.subheader("📥 Esporta i Risultati in Excel")

input_dict = {
    "Caso d'Uso": nome_caso,
    "Volume Mensile": volume_attivita,
    "Tempo/unità PRE (min)": tempo_pre,
    "Tempo/unità POST (min)": tempo_post,
    "% Automatizzato": percentuale_auto,
    "Costo Orario (€)": costo_orario,
    "Costo Una Tantum (€)": costo_una_tantum,
    "Costo Ricorrente Mensile (€)": costo_ricorrente,
    "Periodo Analisi": periodo
}
output_dict = {
    f"Costo PRE-AI ({label_periodo})": costo_tot_pre,
    f"Costo POST-AI ({label_periodo})": costo_tot_post,
    f"Risparmio ({label_periodo})": risparmio,
    "ROI (%)": roi * 100,
    "Payback (mesi)": payback
}

input_df = pd.DataFrame(list(input_dict.items()), columns=["Parametro", "Valore"])
output_df = pd.DataFrame(list(output_dict.items()), columns=["Indicatore", "Valore"])

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    input_df.to_excel(writer, index=False, sheet_name='Input')
    output_df.to_excel(writer, index=False, sheet_name='Output')

st.download_button(
    label="📄 Scarica Excel",
    data=excel_buffer.getvalue(),
    file_name="ROI_AI_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("🟡 I campi gialli sono da compilare. Passa il mouse sopra ogni metrica per la formula.")
