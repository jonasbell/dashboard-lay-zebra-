import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Dashboard Lay Zebra - Odds Reais", page_icon="⚽", layout="wide")

st.title("⚽ Dashboard Lay Zebra (Odds Reais das Casas)")
st.markdown("Varredura em tempo real conectada à **The-Odds-API** para obter odds de mercado precisas.")

st.sidebar.header("⚙️ Chaves & Configurações")
odds_api_key = st.sidebar.text_input("Sua Chave The-Odds-API", type="password")

st.sidebar.subheader("🎯 Parâmetros da Estratégia")
odd_min = st.sidebar.number_input("Odd Mínima Zebra", value=4.00, step=0.10)
odd_max = st.sidebar.number_input("Odd Máxima Zebra", value=8.00, step=0.10)

def buscar_odds_reais(api_key):
    # Busca odds de futebol (soccer_epl, soccer_spain_la_liga, soccer_germany_bundesliga, etc.)
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={api_key.strip()}&regions=eu&markets=h2h"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, f"Erro na API de Odds ({response.status_code}): {response.text}"
            
        dados = response.json()
        jogos_odds = []
        
        for jogo in dados:
            mandante = jogo.get("home_team", "N/A")
            visitante = jogo.get("away_team", "N/A")
            data_utc = jogo.get("commence_time", "")
            
            data_formatada = data_utc[:10] if data_utc else "N/A"
            horario_formatado = data_utc[11:16] if data_utc else "N/A"
            
            # Pega as odds do primeiro bookmaker disponível (ex: Pinnacle, Bet365)
            bookmakers = jogo.get("bookmakers", [])
            odd_m, odd_e, odd_v = "N/D", "N/D", "N/D"
            
            if bookmakers:
                markets = bookmakers[0].get("markets", [])
                if markets:
                    outcomes = markets[0].get("outcomes", [])
                    for out in outcomes:
                        if out["name"] == mandante:
                            odd_m = out["price"]
                        elif out["name"] == visitante:
                            odd_v = out["price"]
                        elif out["name"] == "Draw":
                            odd_e = out["price"]
            
            jogos_odds.append({
                "data": data_formatada,
                "horario": horario_formatado,
                "mandante": mandante,
                "visitante": visitante,
                "odd_mandante": odd_m,
                "odd_empate": odd_e,
                "odd_zebra": odd_v
            })
            
        return jogos_odds, None
    except Exception as e:
        return None, f"Falha na conexão: {e}"

if st.button("🔍 Escanear Odds Reais de Mercado", type="primary"):
    if not odds_api_key:
        st.error("❌ Digite a sua chave da The-Odds-API no menu lateral.")
    else:
        with st.spinner("Buscando cotações em tempo real nas casas de apostas..."):
            jogos, erro = buscar_odds_reais(odds_api_key)
            if erro:
                st.error(f"⚠️ {erro}")
            elif not jogos:
                st.warning("Nenhuma partida com odds abertas encontrada no momento.")
            else:
                st.success(f"Encontradas {len(jogos)} partidas com odds de mercado reais!")
                df = pd.DataFrame(jogos)
                st.dataframe(df, use_container_width=True)
                
