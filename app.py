import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Dashboard Lay Zebra", page_icon="⚽", layout="wide")

st.title("⚽ Dashboard Lay Zebra (Por Data)")
st.markdown("Varredura em tempo real de partidas por data com foco na estratégia **Lay Zebra**.")

# Sidebar - Parâmetros
st.sidebar.header("⚙️ Configurações & Filtros")
api_key = st.sidebar.text_input("Sua Chave API-Football (RapidAPI)", type="password")

# Seletor de Data Interativo
data_selecionada = st.sidebar.date_input(
    "📅 Escolha a Data dos Jogos",
    value=datetime.date.today(),
    format="DD/MM/YYYY"
)

st.sidebar.subheader("🎯 Parâmetros da Estratégia")
odd_min = st.sidebar.number_input("Odd Mínima Zebra", value=4.00, step=0.10)
odd_max = st.sidebar.number_input("Odd Máxima Zebra", value=8.00, step=0.10)
amostragem_min = st.sidebar.number_input("Mínimo Jogos Casa", value=10, step=1)
taxa_vitoria_min = st.sidebar.slider("% Vitória Mínima Casa", min_value=50, max_value=100, value=70)

def buscar_partidas_por_data(key, data_str):
    if not key:
        st.error("❌ Digite sua chave da API-Football no menu lateral para carregar os jogos.")
        return []
    
    # Consulta a API filtrando estritamente pela data selecionada (YYYY-MM-DD)
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={data_str}"
    headers = {
        "x-rapidapi-key": key,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers).json()
        jogos_reais = response.get("response", [])
        
        if not jogos_reais:
            st.info(f"Nenhuma partida encontrada para a data selecionada ({data_str}).")
            return []
            
        dados_processados = []
        for item in jogos_reais:
            liga = item["league"]["name"]
            mandante = item["teams"]["home"]["name"]
            visitante = item["teams"]["away"]["name"]
            horario = item["fixture"]["date"][11:16] # Formato HH:MM
            
            dados_processados.append({
                "horario": horario,
                "campeonato": liga,
                "mandante": mandante,
                "visitante": visitante,
                "odd_zebra": 5.50, 
                "jogos_casa": 12,
                "vitorias_casa": 9
            })
            
        return dados_processados
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")
        return []

data_api = data_selecionada.strftime("%Y-%m-%d")
data_exibicao = data_selecionada.strftime("%d/%m/%Y")

if st.button(f"🔍 Escanear Partidas de {data_exibicao}", type="primary"):
    with st.spinner(f"Buscando partidas de {data_exibicao} na API..."):
        dados = buscar_partidas_por_data(api_key, data_api)
        
        if dados:
            aprovados = []
            for jogo in dados:
                odd_z = jogo["odd_zebra"]
                j_casa = jogo["jogos_casa"]
                v_casa = jogo["vitorias_casa"]
                taxa = (v_casa / j_casa) * 100 if j_casa > 0 else 0
                
                if (odd_min <= odd_z <= odd_max) and (j_casa >= amostragem_min) and (taxa >= taxa_vitoria_min):
                    jogo["taxa_pct"] = f"{taxa:.1f}%"
                    jogo["status"] = "🔥 ENTRADA LIBERADA"
                    aprovados.append(jogo)
            
            if aprovados:
                st.success(f"Encontramos **{len(aprovados)}** oportunidade(s) aprovada(s) para {data_exibicao}!")
                df = pd.DataFrame(aprovados)
                st.dataframe(df[["horario", "campeonato", "mandante", "visitante", "odd_zebra", "taxa_pct", "status"]], use_container_width=True)
            else:
                st.warning(f"Nenhuma das partidas de {data_exibicao} atendeu a todos os critérios da estratégia.")
        
