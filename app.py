import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.graph_objects as go
from io import BytesIO
import base64

# Logo codificato (accorciato per esempio)
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
ore_pre = volume_attivita * tempo_pre
ore_post = volume_attivita * (1 - auto_ratio) * tempo_post
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

# NPV e IRR
tasso_sconto = 0.08
flussi = [-costo_una_tantum] + [risparmio_mese] * 24
npv = npf.npv(tasso_sconto / 12, flussi)
irr = npf.irr(flussi)

st.markdown("---")

# OUTPUT
with st.container():
    st.markdown("### 📊 Risultati del Calcolo")
    st.metric(
        f"Costo PRE-AI ({label})", f"{costo_pre:,.2f} €",
        help="Costi sostenuti senza AI.\nFormula: (Volume × Tempo pre AI) × Costo orario"
    )
    st.metric(
        f"Costo POST-AI ({label})", f"{costo_post:,.2f} €",
        help="Costi con AI.\nFormula: ((Volume × (1 - % auto) × Tempo post AI) × Costo orario) + ricorrenti"
    )
    st.metric(
        f"Risparmio {label.capitalize()}", f"{risparmio:,.2f} €",
        help=f"Formula: Costo PRE-AI - Costo POST-AI"
    )
    st.metric(
        f"ROI su base {label} (%)", f"{roi * 100:,.2f}",
        help="Formula: (Risparmio - Costo Iniziale) / Costo Iniziale × 100"
    )
    st.metric(
        "Payback Period (mesi)", f"{payback:,.2f}" if payback != float("inf") else "Non raggiunto",
        help="Formula: Costo iniziale / Risparmio mensile"
    )
    st.metric(
        "NPV (24 mesi)", f"{npv:,.2f} €",
        help="Valore attuale dei risparmi futuri su 24 mesi\nFormula: Σ CF_t / (1 + r)^t - Investimento"
    )
    st.metric(
        "IRR (%)", f"{irr * 100:,.2f}" if irr else "Non calcolabile",
        help="Tasso che annulla l'NPV. NPV = 0"
    )

st.markdown("---")

# GRAFICO
with st.container():
    st.markdown("### 🔼 ROI Cumulato nel Tempo")
    mesi = list(range(1, 25))
    cumulato = [risparmio_mese * m - costo_una_tantum for m in mesi]

    fig = go.Figure()

    # Area
    fig.add_trace(go.Scatter(
        x=mesi,
        y=cumulato,
        fill='tozeroy',
        mode='none',
        name='Area ROI',
        fillcolor='rgba(0,123,255,0.2)',
        hoverinfo='skip'
    ))

    # Linea ROI
    fig.add_trace(go.Scatter(
        x=mesi,
        y=cumulato,
        mode='lines+markers',
        name='ROI Cumulato',
        marker=dict(size=6),
        line=dict(color='blue'),
        hovertemplate='Mese %{x}: %{y:.2f} €<extra></extra>'
    ))

    # Linea a zero
    fig.add_shape(type="line", x0=1, x1=24, y0=0, y1=0, line=dict(dash="dash", color="gray"))

    # Break-even
    if payback != float("inf"):
        fig.add_shape(type="line", x0=payback, x1=payback, y0=min(cumulato), y1=max(cumulato), line=dict(dash="dash", color="red"))
        fig.add_trace(go.Scatter(
            x=[payback],
            y=[risparmio_mese * payback - costo_una_tantum],
            mode="markers+text",
            text=["Break-even"],
            textposition="top right",
            marker=dict(color="red", size=8),
            showlegend=False,
            hoverinfo="skip"
        ))

    # Punto NPV (a fine periodo)
    fig.add_trace(go.Scatter(
        x=[24],
        y=[npv],
        mode="markers+text",
        marker=dict(color="green", size=10, symbol='star'),
        text=["NPV"],
        textposition="top center",
        showlegend=False,
        hovertemplate="NPV: %{y:.2f} €<extra></extra>"
    ))

    fig.update_layout(
        title="ROI Cumulato (mese su mese)",
        xaxis_title="Mesi",
        yaxis_title="Guadagno Netto (€)",
        hovermode="x unified",
        showlegend=False,
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Il grafico mostra il guadagno netto mese per mese, con evidenza del punto di pareggio e del NPV.")

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

    st.download_button("📃 Scarica Excel", excel_buffer.getvalue(), "ROI_AI_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("📄 Scarica CSV", df_output.to_csv(index=False).encode("utf-8"), "ROI_AI_Report.csv", mime="text/csv")
    st.download_button("📑 Scarica JSON", df_output.to_json(orient="records", indent=2).encode("utf-8"), "ROI_AI_Report.json", mime="application/json")

st.caption("Cluster Reply - Calcolo ROI AI | Powered by GK89")
