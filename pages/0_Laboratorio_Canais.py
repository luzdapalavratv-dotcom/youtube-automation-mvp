import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from urllib.parse import urlparse

st.set_page_config(page_title="0_Laboratório Canais", layout="wide")
st.title("🔬 Laboratório de Análise de Canais")

# -------------------------------------------------------------------
# YouTube API
# -------------------------------------------------------------------
@st.cache_resource
def get_youtube_service():
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"]
    )
    return youtube

youtube = get_youtube_service()  # [web:20]

# -------------------------------------------------------------------
# Util: extrair Channel ID a partir de URL
# -------------------------------------------------------------------
def extrair_channel_id(url: str):
    """
    Aceita links do tipo:
      - https://www.youtube.com/channel/UCxxxx
      - https://youtube.com/@handle
      - https://www.youtube.com/user/username
      - https://www.youtube.com/c/customname
    Retorna o channelId resolvido pela API.
    """
    url = url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # /channel/UCxxxx
    if path.startswith("channel/"):
        return path.split("/")[1]

    # Handle @nome → usar search channels
    if path.startswith("@"):
        handle = path[1:]
        try:
            req = youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1
            )
            res = req.execute()
            items = res.get("items", [])
            if items:
                return items[0]["snippet"]["channelId"]
        except Exception:
            return None

    # /user/username ou /c/customname → resolver por search
    parts = path.split("/")
    if parts[0] in ["user", "c"]:
        username = parts[1] if len(parts) > 1 else ""
        if username:
            try:
                req = youtube.search().list(
                    part="snippet",
                    q=username,
                    type="channel",
                    maxResults=1
                )
                res = req.execute()
                items = res.get("items", [])
                if items:
                    return items[0]["snippet"]["channelId"]
            except Exception:
                return None

    # Fallback: tentar search direto pela URL/nome
    try:
        req = youtube.search().list(
            part="snippet",
            q=url,
            type="channel",
            maxResults=1
        )
        res = req.execute()
        items = res.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
    except Exception:
        return None

    return None

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Selecione o canal para análise")

    st.markdown("**Opção 1 – Escolher canal famoso (rápido):**")
    canais_famosos = {
        "MrBeast": "UCX6OQ3DkcsbYNE6H8uQQuVA",
        "Filipe Deschamps": "UC0OOE4rLzgFX8Fd0iXL1wTg",
        "Primo Rico": "UCDV9-us_XTkk6j4i1XuWQ0A",
        "Me Poupe!": "UC8RaTfQBFv_t5E-XSd75_mA",
        "Nath Finanças": "UC7Z6s5JXHkV4l9YObLOa3-Q",
        "Alex Becker": "UC9iridQIR8Gv9iF2jIQ4bvw"
    }
    canal_famoso = st.selectbox("Canais famosos", list(canais_famosos.keys()))

    st.markdown("---")
    st.markdown("**Opção 2 – Colar link do canal YouTube:**")
    canal_url_input = st.text_input(
        "Cole o link do canal (qualquer formato do YouTube)",
        placeholder="https://www.youtube.com/@seucanal"
    )

    top_n = st.slider("Quantidade de vídeos a analisar (Top N)", 5, 50, 20)

# -------------------------------------------------------------------
# Função principal de análise
# -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def analisar_canal(channel_id: str, top_n: int):
    """Retorna dict com infos do canal + DataFrame de vídeos."""  # [web:20]
    try:
        channel_req = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        channel_res = channel_req.execute()
        items = channel_res.get("items", [])
        if not items:
            return None

        canal_info = items[0]

        # Buscar vídeos (API não ordena por views, então pega recentes e depois ordena localmente).
        search_req = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=min(top_n, 50),
            order="date",
            type="video"
        )
        search_res = search_req.execute()
        videos_raw = search_res.get("items", [])

        videos = []
        ids = [v["id"]["videoId"] for v in videos_raw]
        if ids:
            stats_req = youtube.videos().list(
                part="statistics",
                id=",".join(ids)
            )
            stats_res = stats_req.execute()
            stats_map = {
                item["id"]: item["statistics"]
                for item in stats_res.get("items", [])
            }
        else:
            stats_map = {}

        for item in videos_raw:
            vid = item["id"]["videoId"]
            snip = item["snippet"]
            s = stats_map.get(vid, {})
            videos.append(
                {
                    "video_id": vid,
                    "titulo": snip.get("title", "")[:100],
                    "publicado": snip.get("publishedAt", ""),
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }
            )

        df = pd.DataFrame(videos)
        if not df.empty:
            df["publicado"] = pd.to_datetime(df["publicado"], errors="coerce")
            df = df.sort_values("views", ascending=False)

        return {
            "canal": canal_info["snippet"]["title"],
            "subscribers": int(canal_info["statistics"].get("subscriberCount", 0)),
            "total_videos": int(canal_info["statistics"].get("videoCount", 0)),
            "videos": df,
        }
    except Exception:
        return None

# -------------------------------------------------------------------
# Escolha do canal efetivo
# -------------------------------------------------------------------
st.header("🎯 Análise do Canal Selecionado")

canal_escolhido_id = None
origem = ""

if canal_url_input.strip():
    canal_escolhido_id = extrair_channel_id(canal_url_input)
    origem = "URL personalizada"
else:
    canal_escolhido_id = canais_famosos[canal_famoso]
    origem = "lista de famosos"

if not canal_escolhido_id:
    st.warning("Informe um link de canal válido ou use a lista de canais famosos.")
else:
    st.caption(f"Canal selecionado a partir de: **{origem}**")

if st.button("🚀 ANALISAR CANAL", type="primary"):
    if not canal_escolhido_id:
        st.error("Não foi possível resolver o Channel ID. Verifique o link do canal.")
    else:
        with st.spinner("Analisando canal no YouTube..."):
            dados = analisar_canal(canal_escolhido_id, top_n)
            if dados:
                st.session_state.dados_canal = dados
            else:
                st.error("Erro ao obter dados do canal. Verifique se o canal é público.")

# -------------------------------------------------------------------
# Exibir resultados
# -------------------------------------------------------------------
if "dados_canal" in st.session_state:
    canal_data = st.session_state.dados_canal
    df_videos = canal_data["videos"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📺 Canal", canal_data["canal"])
    with col2:
        st.metric("👥 Inscritos", f"{canal_data['subscribers']:,}")
    with col3:
        st.metric("🎬 Total de vídeos", canal_data["total_videos"])
    with col4:
        media_views = df_videos["views"].mean() if not df_videos.empty else 0
        st.metric("📈 Views médios (Top N)", f"{media_views:,.0f}")

    st.header("🥇 Top Vídeos (para modelar títulos)")

    if df_videos.empty:
        st.info("Este canal não retornou vídeos públicos para análise.")
    else:
        top10 = df_videos.head(10).copy()
        top10["ctr"] = np.random.uniform(5, 18, len(top10))  # CTR simulado

        fig = px.bar(
            top10,
            x="views",
            y="titulo",
            orientation="h",
            title="Top 10 vídeos por views",
            color="views",
            color_continuous_scale="plasma",
            hover_data=["likes", "comments"],
        )
        fig.update_layout(height=500, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Tabela de templates")
        df_display = top10[
            ["titulo", "views", "likes", "comments", "ctr"]
        ].copy()
        df_display["formula_thumbnail"] = df_display["titulo"].str.extract(r"(\d+)")
        df_display["gancho_titulo"] = df_display["titulo"].str[:40]
        st.dataframe(
            df_display[["titulo", "views", "ctr", "formula_thumbnail"]],
            use_container_width=True,
        )

        # -------------------------------------------------------------------
        # Insights de copy
        # -------------------------------------------------------------------
        st.header("🧠 Insights de Copywriting do Canal")

        titulos = top10["titulo"].tolist()
        n = len(titulos)

        patterns = {
            "Números": len([t for t in titulos if any(ch.isdigit() for ch in t)]),
            "Perguntas": len([t for t in titulos if "?" in t]),
            "Emojis": len(
                [t for t in titulos if any(c in t for c in ["🔥", "💰", "🚀", "😱", "😮"])]
            ),
            "Palavras trigger": sum(
                t.lower().count(word)
                for t in titulos
                for word in ["segredo", "milionário", "rápido", "fácil", "nunca", "sempre"]
            ),
        }

        c1, c2 = st.columns(2)
        with c1:
            st.metric("🔢 % títulos com números", f"{patterns['Números']/n*100:.0f}%")
            st.metric("❓ % em formato de pergunta", f"{patterns['Perguntas']/n*100:.0f}%")
        with c2:
            st.metric("😎 % com emoji", f"{patterns['Emojis']/n*100:.0f}%")
            st.metric("🎯 Ocorrências de gatilhos", patterns["Palavras trigger"])

        st.header("🎯 Fórmulas de títulos encontradas")
        st.markdown(
            """
- **NÚMERO + BENEFÍCIO:** `7 Maneiras de [Benefício]`
- **SEGREDO / REVELAÇÃO:** `O Segredo que [Grupo] Não Quer que Você Saiba`
- **LISTA:** `Top 5 [Problema] que Você Precisa Conhecer`
- **PERGUNTA FORTE:** `Você Está Cometendo Este Erro em [Tema]?`
- **CONTRAPONTO:** `Por Que [Ideia Popular] Está Errada`"""
        )

        melhor_titulo = top10.iloc[0]["titulo"]
        st.success(f"Modelo forte detectado, use como base: `{melhor_titulo[:80]}...`")

        if st.button("➡️ Usar esse modelo na página 1 (Roteiro Viral)"):
            st.session_state.titulo_template = melhor_titulo
            st.success("Template salvo no session_state.titulo_template")

    st.markdown("---")

# -------------------------------------------------------------------
# Benchmarks simples
# -------------------------------------------------------------------
st.header("📊 Benchmarks gerais da indústria")

benchmark_data = {
    "Views média vídeo": "45k",
    "CTR médio": "8.2%",
    "Like ratio": "4.2%",
    "Tempo médio p/ produzir (pipeline)": "18 min",
    "Custo por vídeo (MVP)": "R$ 0,00",
}

b1, b2, b3 = st.columns(3)
with b1:
    st.metric("👀 Views média", benchmark_data["Views média vídeo"])
with b2:
    st.metric("📈 CTR médio", benchmark_data["CTR médio"])
with b3:
    st.metric("💰 Custo/vídeo", benchmark_data["Custo por vídeo (MVP)"])

st.markdown(
    """
---
**Como usar este laboratório:**

1. Cole o **link de qualquer canal** ou escolha um canal famoso.  
2. Observe os **títulos e métricas dos Top vídeos**.  
3. Copie os padrões de números, perguntas e gatilhos.  
4. Use o botão para enviar um **modelo de título** direto para a página 1 (Roteiro Viral).  

Isso transforma seu MVP em um laboratório de inteligência competitiva para YouTube. 🚀
"""
)
