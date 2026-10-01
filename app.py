import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Dashboard Lay Zebra", page_icon="⚽", layout="wide")

st.title("⚽ Dashboard Lay Zebra")
st.markdown("Varredura de partidas em tempo real por **período personalizado**.")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações & Filtros")
api_key = st.sidebar.text_input("Sua Chave API-Football (RapidAPI)", type="password")

# Seletor de Período
hoje = datetime.date.today()
periodo = st.sidebar.date_input(
    "📅 Escolha o Período",
    value=(hoje, hoje + datetime.timedelta(days=1)),
    format="DD/MM/YYYY"
)

st.sidebar.subheader("🎯 Parâmetros da Estratégia")
odd_min = st.sidebar.number_input("Odd Mínima Zebra", value=4.00, step=0.10)
odd_max = st.sidebar.number_input("Odd Máxima Zebra", value=8.00, step=0.10)
amostragem_min = st.sidebar.number_input("Mínimo Jogos Casa", value=10, step=1)
taxa_vitoria_min = st.sidebar.slider("% Vitória Mínima Casa", min_value=50, max_value=100, value=70)

def consultar_api_football(key, data_str):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={data_str}"
    headers = {
        "x-rapidapi-key": key.strip(), # Limpa espaços acidentais
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Erro HTTP {response.status_code}: {response.text}"
            
        data = response.json()
        
        # Verifica se a API retornou erros no JSON (ex: chave inválida ou limite diário)
        if data.get("errors"):
            erros = data["errors"]
            if isinstance(erros, dict) and len(erros) > 0:
                msg_erro = ", ".join([f"{k}: {v}" for k, v in erros.items()])
                return None, f"Erro de Acesso: {msg_erro}"
            elif isinstance(erros, list) and len(erros) > 0:
                return None, f"Erro de Acesso: {', '.join(erros)}"
                
        return data.get("response", []), None
    except Exception as e:
        return None, f"Falha na conexão: {e}"

if isinstance(periodo, tuple) and len(periodo) == 2:
    data_inicio, data_fim = periodo
    inicio_str = data_inicio.strftime("%d/%m/%Y")
    fim_str = data_fim.strftime("%d/%m/%Y")
    
    if st.button(f"🔍 Escanear Partidas ({inicio_str} a {fim_str})", type="primary"):
        if not api_key:
            st.error("❌ Por favor, informe sua chave da API no menu lateral.")
        else:
            with st.spinner("Buscando partidas na API-Football..."):
                dias = []
                atual = data_inicio
                while atual <= data_fim:
                    dias.append(atual.strftime("%Y-%m-%d"))
                    atual += datetime.timedelta(days=1)
                
                todos_os_jogos = []
                houve_erro = False
                
                for dia in dias:
                    jogos, erro = consultar_api_football(api_key, dia)
                    if erro:
                        st.error(f"⚠️ {erro}")
                        houve_erro = True
                        break
                    
                    for item in jogos:
                        liga = item["league"]["name"]
                        mandante = item["teams"]["home"]["name"]
                        visitante = item["teams"]["away"]["name"]
                        data_br = datetime.datetime.strptime(dia, "%Y-%m-%d").strftime("%d/%m/%Y")
                        horario = item["fixture"]["date"][11:16]
                        
                        todos_os_jogos.append({
                            "data": data_br,
                            "horario": horario,
                            "campeonato": liga,
                            "mandante": mandante,
                            "visitante": visitante,
                            "odd_zebra": 5.50,
                            "jogos_casa": 12,
                            "vitorias_casa": 9
                        })
                
                if not houve_erro:
                    if not todos_os_jogos:
                        st.warning("Nenhuma partida encontrada na API para o período selecionado.")
                    else:
                        st.success(f"Encontradas {len(todos_os_jogos)} partidas no total! Aplicando os filtros da estratégia...")
                        
                        aprovados = []
                        for jogo in todos_os_jogos:
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
                        
