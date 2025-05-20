import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy_financial as npf
from io import BytesIO
import base64
from streamlit.components.v1 import html

# Logo codificato (accorciato qui per spazio)
logo_base64 = "iVBORw0KGgoAAAANSUhEUgAAAZAAAABKCAIAAAAaD5VmAAAgAElEQVR4Aey9..."
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

st.markdown("---")

# INPUT
with st.container():
    st.markdown("### 📅 Parametri di Ingresso")

    # Stile giallo per input
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

    unita_tempo = st.selectbox("Unità di Misura Tempo", ["Minuti", "Ore", "Giorni (lavorativi)"])
    tempo_pre_input = st.number_input("Tempo per unità - PRE AI", 0.0, value=0.75)
    tempo_post_input = st.number_input("Tempo per unità - POST AI", 0.0, value=0.25)
    fattore_conversione = {"Minuti": 1/60, "Ore": 1, "Giorni (lavorativi)": 8}
    tempo_pre = tempo_pre_input * fattore_conversione[unita_tempo]
    tempo_post = tempo_post_input * fattore_conversione[unita_tempo]

    percentuale_auto = st.slider("% Attività Automatizzate", 0, 100, 80)
    costo_orario = st.number_input("Costo Orario Medio (€)", 0.0, value=30.0)
    costo_una_tantum = st.number_input("Costo Implementazione Una Tantum (€)", 0.0, value=3000.0)
    costo_ricorrente = st.number_input("Costo Ricorrente Mensile (€)", 0.0, value=50.0)
    periodo = st.radio("Periodo di Analisi", ["Mensile", "Annuale"])

# CALCOLI
auto_ratio = percentuale_auto / 100
ore_pre = (volume_attivita * tempo_pre)
ore_post = (volume_attivita * (1 - auto_ratio)) * tempo_post
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

# NPV & IRR
tasso_sconto = 0.08  # 8% annuo -> mensile
flussi = [-costo_una_tantum] + [risparmio_mese] * 24
npv = npf.npv(tasso_sconto / 12, flussi)
irr = npf.irr(flussi)

st.markdown("---")

# OUTPUT
with st.container():
    st.markdown("### 📊 Risultati del Calcolo")
    st.metric(
        f"Costo PRE-AI ({label})", f"{costo_pre:,.2f} €",
        help="Costi sostenuti oggi senza automazione.\nFormula: (Volume × Tempo pre AI) × Costo orario"
    )
    st.metric(
        f"Costo POST-AI ({label})", f"{costo_post:,.2f} €",
        help="Nuova struttura di costi considerando automazione parziale e costi AI.\nFormula: ((Volume × (1 - % auto) × Tempo post AI) × Costo orario) + ricorrenti"
    )
    st.metric(
        f"Risparmio {label.capitalize()}", f"{risparmio:,.2f} €",
        help=f"Risparmio diretto operativo, su base {label}.\nFormula: Costo PRE-AI - Costo POST-AI"
    )
    st.metric(
        f"ROI su base {label} (%)", f"{roi * 100:,.2f}",
        help="Indice di redditività dell'iniziativa AI rispetto all'investimento iniziale.\nFormula: (Risparmio - Costo iniziale) / Costo iniziale × 100"
    )
    st.metric(
        "Payback Period (mesi)", f"{payback:,.2f}" if payback != float("inf") else "Non raggiunto",
        help="Numero di mesi per recuperare l'investimento iniziale.\nFormula: Costo iniziale / Risparmio mensile"
    )
    st.metric(
        "NPV (24 mesi)", f"{npv:,.2f} €",
        help="Valore Attuale Netto dei risparmi su 24 mesi, scontati all'8%.\nFormula: Σ CF_t / (1+r)^t - investimento"
    )
    st.metric(
        "IRR (%)", f"{irr * 100:,.2f}" if irr else "Non calcolabile",
        help="Tasso interno di rendimento: il tasso che annulla l'NPV"
    )

st.markdown("---")

# GRAFICO
with st.container():
    st.markdown("### 🔼 ROI Cumulato nel Tempo")
    mesi = list(range(1, 25))
    cumulato = [risparmio_mese * m - costo_una_tantum for m in mesi]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mesi,
        y=cumulato,
        mode='lines+markers',
        name='ROI Cumulato',
        hovertemplate='Mese %{x}: %{y:.2f} €<extra></extra>'
    ))
    fig.add_shape(type="line", x0=1, x1=24, y0=0, y1=0, line=dict(dash="dash", color="gray"))
    if payback != float("inf"):
        fig.add_shape(type="line", x0=payback, x1=payback, y0=min(cumulato), y1=max(cumulato),
                      line=dict(dash="dash", color="red"))

    fig.update_layout(
        title="ROI Cumulato (mese su mese)",
        xaxis_title="Mesi",
        yaxis_title="Guadagno Netto (€)",
        hovermode="x unified",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Il grafico mostra il guadagno netto accumulato mese per mese e il punto di pareggio.")

st.markdown("---")

# EXPORT
with st.container():
    st.markdown("### 📄 Esporta i Risultati")
    input_dict = {
        "Caso d'Uso": nome_caso,
        "Volume Mensile": volume_attivita,
        "Tempo PRE (ore)": tempo_pre,
        "Tempo POST (ore)": tempo_post,
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
        "Payback (mesi)": payback,
        "NPV (24 mesi)": npv,
        "IRR (%)": irr * 100 if irr else None
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

    # CSV
    csv_data = df_output.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📄 Scarica CSV",
        data=csv_data,
        file_name="ROI_AI_Report.csv",
        mime="text/csv"
    )

    # JSON
    json_data = df_output.to_json(orient="records", indent=2).encode("utf-8")
    st.download_button(
        label="📑 Scarica JSON",
        data=json_data,
        file_name="ROI_AI_Report.json",
        mime="application/json"
    )

st.caption("Cluster Reply - Calcolo ROI AI | Powered by GK89")
