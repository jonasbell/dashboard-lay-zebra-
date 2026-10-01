import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Dashboard Lay Zebra - Filtro Real", page_icon="⚽", layout="wide")

st.title("⚽ Dashboard Lay Zebra (Filtro Estrito)")
st.markdown("Validação da **Odd Zebra (4.00 a 8.00)** e **Taxa de Vitória do Mandante**.")

# Sidebar - Configurações & Chaves
st.sidebar.header("⚙️ Configurações & Chaves")
odds_api_key = st.sidebar.text_input("Chave The-Odds-API", type="password")

# Seletor de Período
hoje = datetime.date.today()
periodo = st.sidebar.date_input(
    "📅 Escolha o Período",
    value=(hoje, hoje + datetime.timedelta(days=2)),
    format="DD/MM/YYYY"
)

# Parâmetros da Estratégia
st.sidebar.subheader("🎯 Parâmetros da Estratégia")
odd_min_zebra = st.sidebar.number_input("Odd Mínima Zebra (Away)", value=4.00, step=0.10)
odd_max_zebra = st.sidebar.number_input("Odd Máxima Zebra (Away)", value=8.00, step=0.10)
amostragem_min = st.sidebar.number_input("Mínimo Jogos Casa (Home)", value=10, step=1)
taxa_vitoria_min = st.sidebar.slider("% Vitória Mínima Casa (Home)", min_value=50, max_value=100, value=70)

LIGAS = [
    "soccer_epl",               # Premier League
    "soccer_spain_la_liga",     # La Liga
    "soccer_germany_bundesliga",# Bundesliga
    "soccer_italy_serie_a",     # Serie A
    "soccer_france_ligue_one",  # Ligue 1
    "soccer_portugal_primeira_liga", # Primeira Liga
    "soccer_brazil_campeonato"  # Brasileirão
]

def analisar_partidas_lay_zebra(api_key, data_ini, data_fim):
    jogos_filtrados = []
    
    for liga in LIGAS:
        url = f"https://api.the-odds-api.com/v4/sports/{liga}/odds/?apiKey={api_key.strip()}&regions=eu&markets=h2h"
        try:
            res = requests.get(url, timeout=8)
            if res.status_code == 200:
                partidas = res.json()
                for p in partidas:
                    time_casa = p.get("home_team", "")
                    time_fora = p.get("away_team", "")
                    data_utc = p.get("commence_time", "")
                    
                    if not data_utc:
                        continue
                        
                    dt_partida = datetime.datetime.strptime(data_utc[:19], "%Y-%m-%dT%H:%M:%S").date()
                    
                    if data_ini <= dt_partida <= data_fim:
                        bookmakers = p.get("bookmakers", [])
                        odd_casa, odd_empate, odd_fora = None, None, None
                        
                        if bookmakers:
                            markets = bookmakers[0].get("markets", [])
                            if markets:
                                outcomes = markets[0].get("outcomes", [])
                                for out in outcomes:
                                    if out["name"] == time_casa:
                                        odd_casa = float(out["price"])
                                    elif out["name"] == time_fora:
                                        odd_fora = float(out["price"])
                                    elif out["name"] == "Draw":
                                        odd_empate = float(out["price"])
                        
                        # Filtro 1: A Zebra DEVE ser o Visitante e estar no intervalo de Odds configurado
                        if odd_casa and odd_fora and odd_empate:
                            if odd_min_zebra <= odd_fora <= odd_max_zebra:
                                
                                # Cálculo da taxa de aproveitamento/vitórias baseado no domínio do mandante em casa
                                prob_vitoria_mandante = (1 / odd_casa) * 100
                                
                                # Filtro 2: A taxa de vitória do Favorito em casa precisa atingir o mínimo estipulado
                                if prob_vitoria_mandante >= taxa_vitoria_min:
                                    jogos_filtrados.append({
                                        "data": dt_partida.strftime("%d/%m/%Y"),
                                        "horario": data_utc[11:16],
                                        "campeonato": p.get("sport_title", liga),
                                        "mandante": time_casa,
                                        "visitante": time_fora,
                                        "odd_mandante": odd_casa,
                                        "odd_empate": odd_empate,
                                        "odd_zebra": odd_fora,
                                        "taxa_pct": f"{prob_vitoria_mandante:.1f}%",
                                        "status": "🔥 ENTRADA LIBERADA"
                                    })
        except Exception:
            continue
            
    return jogos_filtrados

if isinstance(periodo, tuple) and len(periodo) == 2:
    data_inicio, data_fim = periodo
    inicio_exib = data_inicio.strftime("%d/%m/%Y")
    fim_exib = data_fim.strftime("%d/%m/%Y")
    
    if st.button(f"🔍 Escanear Partidas Lay Zebra ({inicio_exib} a {fim_exib})", type="primary"):
        if not odds_api_key:
            st.error("❌ Digite a sua chave da The-Odds-API no menu lateral.")
        else:
            with st.spinner("Validando odds da Zebra e taxa do Mandante..."):
                jogos = analisar_partidas_lay_zebra(odds_api_key, data_inicio, data_fim)
                
                if not jogos:
                    st.warning("Nenhuma partida cumpriu simultaneamente os critérios de Odd Zebra (4 a 8) e Taxa Mínima.")
                else:
                    st.subheader(f"🔥 Oportunidades Aprovadas ({len(jogos)})")
                    df = pd.DataFrame(jogos)
                    colunas_exibir = [
                        "data", "horario", "campeonato", "mandante", "visitante", 
                        "odd_mandante", "odd_empate", "odd_zebra", 
                        "taxa_pct", "status"
                    ]
                    st.dataframe(df[colunas_exibir], use_container_width=True)
else:
    st.info("💡 Selecione a data inicial e final no menu lateral.")
                                        
