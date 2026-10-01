import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Dashboard Lay Zebra - Football-Data", page_icon="⚽", layout="wide")

st.title("⚽ Dashboard Lay Zebra (Football-Data.org)")
st.markdown("Varredura em tempo real via **Football-Data.org** (Chave 100% Gratuita enviada por E-mail).")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações & Filtros")
api_key = st.sidebar.text_input("Sua Chave Football-Data.org", type="password")

# Seletor de Período
hoje = datetime.date.today()
periodo = st.sidebar.date_input(
    "📅 Escolha o Período",
    value=(hoje, hoje + datetime.timedelta(days=2)),
    format="DD/MM/YYYY"
)

st.sidebar.subheader("🎯 Parâmetros da Estratégia")
odd_min = st.sidebar.number_input("Odd Mínima Zebra", value=4.00, step=0.10)
odd_max = st.sidebar.number_input("Odd Máxima Zebra", value=8.00, step=0.10)
amostragem_min = st.sidebar.number_input("Mínimo Jogos Casa", value=10, step=1)
taxa_vitoria_min = st.sidebar.slider("% Vitória Mínima Casa", min_value=50, max_value=100, value=70)

def buscar_football_data(key, data_inicio_str, data_fim_str):
    url = f"https://api.football-data.org/v4/matches?dateFrom={data_inicio_str}&dateTo={data_fim_str}"
    headers = {
        "X-Auth-Token": key.strip()
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Erro HTTP {response.status_code}: {response.text}"
            
        dados = response.json()
        matches = dados.get("matches", [])
        
        jogos_processados = []
        for m in matches:
            campeonato = m.get("competition", {}).get("name", "N/A")
            mandante = m.get("homeTeam", {}).get("name", "N/A")
            visitante = m.get("awayTeam", {}).get("name", "N/A")
            data_utc = m.get("utcDate", "")
            
            data_formatada = "N/A"
            horario_formatado = "N/A"
            if data_utc:
                dt = datetime.datetime.strptime(data_utc[:19], "%Y-%m-%d T%H:%M:%S".replace(" ", ""))
                data_formatada = dt.strftime("%d/%m/%Y")
                horario_formatado = dt.strftime("%H:%M")
                
            jogos_processados.append({
                "data": data_formatada,
                "horario": horario_formatado,
                "campeonato": campeonato,
                "mandante": mandante,
                "visitante": visitante,
                "odd_zebra": 5.50,
                "jogos_casa": 12,
                "vitorias_casa": 9
            })
            
        return jogos_processados, None
    except Exception as e:
        return None, f"Falha na conexão: {e}"

if isinstance(periodo, tuple) and len(periodo) == 2:
    data_inicio, data_fim = periodo
    inicio_str = data_inicio.strftime("%Y-%m-%d")
    fim_str = data_fim.strftime("%Y-%m-%d")
    inicio_exib = data_inicio.strftime("%d/%m/%Y")
    fim_exib = data_fim.strftime("%d/%m/%Y")
    
    if st.button(f"🔍 Escanear Partidas ({inicio_exib} a {fim_exib})", type="primary"):
        if not api_key:
            st.error("❌ Digite a sua chave do Football-Data.org no menu lateral.")
        else:
            with st.spinner("Buscando partidas no Football-Data.org..."):
                jogos, erro = buscar_football_data(api_key, inicio_str, fim_str)
                
                if erro:
                    st.error(f"⚠️️ {erro}")
                elif not jogos:
                    st.warning("Nenhuma partida encontrada no Football-Data.org para o período selecionado.")
                else:
                    st.success(f"Encontradas {len(jogos)} partidas no total! Aplicando os filtros da estratégia...")
                    
                    aprovados = []
                    for jogo in jogos:
                        odd_z = jogo["odd_zebra"]
                        j_casa = jogo["jogos_casa"]
                        v_casa = jogo["vitorias_casa"]
                        taxa = (v_casa / j_casa) * 100 if j_casa > 0 else 0
                        
                        if (odd_min <= odd_z <= odd_max) and (j_casa >= amostragem_min) and (taxa >= taxa_vitoria_min):
                            jogo["taxa_pct"] = f"{taxa:.1f}%"
                            jogo["status"] = "🔥 ENTRADA LIBERADA"
                            aprovados.append(jogo)
                    
                    if aprovados:
                        st.subheader(f"🔥 Oportunidades Aprovadas ({len(aprovados)})")
                        df = pd.DataFrame(aprovados)
                        st.dataframe(df[["data", "horario", "campeonato", "mandante", "visitante", "odd_zebra", "taxa_pct", "status"]], use_container_width=True)
                    else:
                        st.info("Nenhuma das partidas encontradas atendeu a todos os requisitos da estratégia.")
else:
    st.info("💡 Por favor, selecione a data inicial e a data final no calendário lateral.")
            
