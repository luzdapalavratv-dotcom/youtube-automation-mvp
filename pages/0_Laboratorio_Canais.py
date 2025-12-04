import streamlit as st
import googleapiclient.discovery
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from datetime import datetime

st.set_page_config(page_title="0 – Laboratório de Canais", layout="wide")
st.title("🔬 Laboratório de Canais (Modelagem + Análise)")

# -------------------------------------------------------------------
# Integra com o "banco" do app principal
# -------------------------------------------------------------------
def criar_db_vazio():
    return {"canais": {}}

if "db" not in st.session_state:
    st.session_state.db = criar_db_vazio()

db = st.session_state.db

if "canal_atual_id" not in st.session_state:
    st.session_state.canal_atual_id = None

# -------------------------------------------------------------------
# YouTube API (para análise opcional)
# -------------------------------------------------------------------
@st.cache_resource
def get_youtube_service():
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"]
    )
    return youtube

youtube = get_youtube_service()

def extrair_channel_id(url: str):
    """Extrai/resolve um channelId a partir de vários formatos de URL, usando forHandle quando possível."""
    url = url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # /channel/UCxxxx
    if path.startswith("channel/"):
        return path.split("/")[1]

    # Handle @nome ou /@nome – usar channels().list(forHandle=...) para ser exato
    if path.startswith("@"):
        handle = path[1:]
        try:
            ch_req = youtube.channels().list(
                part="id",
                forHandle=handle,
            )
            ch_res = ch_req.execute()
            items = ch_res.get("items", [])
            if items:
                return items[0]["id"]

            # Fallback: search
            req = youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1,
            )
            res = req.execute()
            items = res.get("items", [])
            if items:
                return items[0]["snippet"]["channelId"]
        except Exception:
            return None

    # /user/username ou /c/customname
    parts = path.split("/")
    if parts and parts[0] in ["user", "c"]:
        username = parts[1] if len(parts) > 1 else ""
        if username:
            try:
                req = youtube.search().list(
                    part="snippet",
                    q=username,
                    type="channel",
                    maxResults=1,
                )
                res = req.execute()
                items = res.get("items", [])
                if items:
                    return items[0]["snippet"]["channelId"]
            except Exception:
                return None

    # Fallback: busca geral
    try:
        req = youtube.search().list(
            part="snippet",
            q=url,
            type="channel",
            maxResults=1,
        )
        res = req.execute()
        items = res.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
    except Exception:
        return None

    return None

@st.cache_data(ttl=3600)
def analisar_canal_youtube(channel_id: str, top_n: int = 50):
    """Analisa canal via YouTube Data API: top vídeos, padrões de título etc."""
    try:
        ch_req = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id,
        )
        ch_res = ch_req.execute()
        items = ch_res.get("items", [])
        if not items:
            return None

        canal_info = items[0]

        search_req = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=min(top_n, 50),
            order="date",
            type="video",
        )
        search_res = search_req.execute()
        vids_raw = search_res.get("items", [])

        videos = []
        ids = [v["id"]["videoId"] for v in vids_raw]
        stats_map = {}
        if ids:
            stats_req = youtube.videos().list(
                part="statistics,contentDetails",
                id=",".join(ids),
            )
            stats_res = stats_req.execute()
            stats_map = {it["id"]: it for it in stats_res.get("items", [])}

        for v in vids_raw:
            vid = v["id"]["videoId"]
            sn = v["snippet"]
            stt_item = stats_map.get(vid, {})
            stt = stt_item.get("statistics", {})
            cont = stt_item.get("contentDetails", {})

            dur = cont.get("duration", "")
            # Shorts: duração <= ~60s OU #shorts no título (heurística)
            is_short = False
            if "S" in dur and "M" not in dur and "H" not in dur:
                is_short = True
            if "#shorts" in sn.get("title", "").lower():
                is_short = True

            videos.append(
                {
                    "video_id": vid,
                    "titulo": sn.get("title", "")[:120],
                    "publicado": sn.get("publishedAt", ""),
                    "views": int(stt.get("viewCount", 0)),
                    "likes": int(stt.get("likeCount", 0)),
                    "comments": int(stt.get("commentCount", 0)),
                    "is_short": is_short,
                }
            )

        df = pd.DataFrame(videos)
        if not df.empty:
            df["publicado"] = pd.to_datetime(df["publicado"], errors="coerce")
            df = df.sort_values("views", ascending=False)
            df["ctr_simulado"] = np.random.uniform(5, 18, len(df))  # fictício

        return {
            "nome": canal_info["snippet"]["title"],
            "subscribers": int(canal_info["statistics"].get("subscriberCount", 0)),
            "total_videos": int(canal_info["statistics"].get("videoCount", 0)),
            "videos": df,
        }
    except Exception:
        return None

# -------------------------------------------------------------------
# Sidebar – escolher canal já criado no sistema
# -------------------------------------------------------------------
with st.sidebar:
    st.header("🎛 Seleção de Canal no Sistema")

    canais_ids = list(db["canais"].keys())
    if canais_ids:
        canais_nomes = [db["canais"][cid]["nome"] for cid in canais_ids]
        idx_sel = st.selectbox(
            "Canal atual",
            options=range(len(canais_ids)),
            format_func=lambda i: canais_nomes[i],
            index=0
            if st.session_state.canal_atual_id not in canais_ids
            else canais_ids.index(st.session_state.canal_atual_id),
        )
        st.session_state.canal_atual_id = canais_ids[idx_sel]
    else:
        st.info("Nenhum canal cadastrado ainda (crie no app principal ou aqui).")

# -------------------------------------------------------------------
# Layout principal: duas abas
# -------------------------------------------------------------------
tab1, tab2 = st.tabs(["🧬 Modelagem do Canal", "📊 Análise via YouTube"])

# -------------------------------------------------------------------
# ABA 1 – Modelagem / Configuração do Canal
# -------------------------------------------------------------------
with tab1:
    st.subheader("🧬 Configuração detalhada do canal")

    canal_id = st.session_state.canal_atual_id
    if canal_id and canal_id in db["canais"]:
        canal_data = db["canais"][canal_id]
    else:
        canal_data = {
            "nome": "",
            "link_youtube": "",
            "nicho": "",
            "persona": "",
            "idioma": "pt-BR",
            "frequencia": "",
            "tipos_video": [],
            "tom_marca": "",
            "palavras_proibidas": "",
            "preferencias_titulo": "",
            "diretrizes_gerais": "",
            "criado_em": datetime.now().isoformat(),
            "videos": {},
        }

    with st.form("form_canal"):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            nome = st.text_input("Nome do canal", value=canal_data.get("nome", ""))
            link = st.text_input(
                "Link do canal no YouTube (opcional)",
                value=canal_data.get("link_youtube", ""),
            )
            nicho = st.text_input("Nicho principal", value=canal_data.get("nicho", ""))
            idioma = st.selectbox(
                "Idioma principal",
                ["pt-BR", "en-US", "es-ES"],
                index=["pt-BR", "en-US", "es-ES"].index(
                    canal_data.get("idioma", "pt-BR")
                ),
            )

        with col_a2:
            persona = st.text_area(
                "Persona do público-alvo",
                value=canal_data.get(
                    "persona",
                    "Ex.: Adultos de 25-40 anos, buscando renda extra e liberdade financeira.",
                ),
                height=80,
            )
            frequencia = st.text_input(
                "Frequência ideal (ex.: 2 vídeos/semana)",
                value=canal_data.get("frequencia", ""),
            )
            tipos_video = st.multiselect(
                "Tipos de vídeo",
                ["Longform", "Shorts", "Highlights", "Lives"],
                default=canal_data.get("tipos_video", ["Longform"]),
            )

        st.markdown("### 🎙️ Voz e Diretrizes da Marca")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            tom_marca = st.text_area(
                "Tom da marca",
                value=canal_data.get(
                    "tom_marca",
                    "Ex.: Direto, motivacional, com humor leve, sem palavrões.",
                ),
                height=80,
            )
            palavras_proibidas = st.text_area(
                "Palavras/temas proibidos",
                value=canal_data.get("palavras_proibidas", ""),
                height=80,
            )
        with col_b2:
            preferencias_titulo = st.text_area(
                "Preferências para títulos",
                value=canal_data.get(
                    "preferencias_titulo",
                    "Ex.: Sempre usar números; evitar títulos muito longos; começar com benefício.",
                ),
                height=80,
            )
            diretrizes_gerais = st.text_area(
                "Diretrizes gerais (estrutura de vídeos, CTA, etc.)",
                value=canal_data.get("diretrizes_gerais", ""),
                height=80,
            )

        salvar = st.form_submit_button("💾 Salvar configurações do canal")

    if salvar:
        if not canal_id or canal_id not in db["canais"]:
            from uuid import uuid4
            canal_id = str(uuid4())[:8]
            st.session_state.canal_atual_id = canal_id

        db["canais"][canal_id] = {
            **db["canais"].get(canal_id, {}),
            "nome": nome.strip(),
            "link_youtube": link.strip(),
            "nicho": nicho.strip(),
            "idioma": idioma,
            "persona": persona.strip(),
            "frequencia": frequencia.strip(),
            "tipos_video": tipos_video,
            "tom_marca": tom_marca.strip(),
            "palavras_proibidas": palavras_proibidas.strip(),
            "preferencias_titulo": preferencias_titulo.strip(),
            "diretrizes_gerais": diretrizes_gerais.strip(),
            "criado_em": canal_data.get("criado_em", datetime.now().isoformat()),
            "videos": canal_data.get("videos", {}),
        }
        st.success("Canal atualizado no sistema!")
        st.experimental_rerun()

    st.markdown("---")
    st.caption(
        "As informações salvas aqui são usadas em todas as outras páginas "
        "(roteiro, thumbnails, áudio, etc.) para personalizar o conteúdo."
    )

# -------------------------------------------------------------------
# ABA 2 – Análise via YouTube (copy de títulos, padrões, etc.)
# -------------------------------------------------------------------
with tab2:
    st.subheader("📊 Análise de um canal real no YouTube")

    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        link_analise = st.text_input(
            "Cole o link do canal no YouTube para analisar",
            value=db["canais"]
            .get(st.session_state.canal_atual_id, {})
            .get("link_youtube", ""),
        )
    with col_l2:
        top_n = st.slider("Quantidade de vídeos para analisar", 5, 50, 20)

    if st.button("🔍 Analisar canal no YouTube"):
        ch_id = extrair_channel_id(link_analise)
        if not ch_id:
            st.error("Não foi possível extrair o ID do canal. Verifique o link.")
        else:
            with st.spinner("Consultando YouTube Data API..."):
                analise = analisar_canal_youtube(ch_id, top_n=top_n)
                if not analise:
                    st.error("Erro ao consultar dados do canal.")
                else:
                    st.session_state.analise_canal_youtube = analise
                    st.session_state.analise_channel_id = ch_id
                    st.success("Análise concluída!")

    analise = st.session_state.get("analise_canal_youtube")
    if analise:
        df_v = analise["videos"]

        st.markdown(
            f"### 📺 {analise['nome']}  |  "
            f"👥 {analise['subscribers']:,} inscritos  |  "
            f"🎬 {analise['total_videos']} vídeos"
        )

        if not df_v.empty:
            # Separar longos e shorts
            df_long = df_v[df_v["is_short"] == False]
            df_short = df_v[df_v["is_short"] == True]

            # ---------- VÍDEOS LONGOS ----------
            st.subheader("🥇 Top 10 vídeos longos por views")

            if df_long.empty:
                st.info("Nenhum vídeo longo encontrado para este canal.")
            else:
                top10_long = df_long.head(10).copy()
                top10_long["link_video"] = (
                    "https://www.youtube.com/watch?v=" + top10_long["video_id"]
                )

                # Tabela numérica
                st.dataframe(
                    top10_long[["titulo", "views", "likes", "comments", "ctr_simulado"]],
                    use_container_width=True,
                )

                # Lista de links clicáveis
                st.markdown("**Links dos vídeos longos:**")
                for _, row in top10_long.iterrows():
                    url = row["link_video"]
                    st.markdown(f"- [▶️ {row['titulo']}]({url})")

            # ---------- SHORTS ----------
            st.subheader("📱 Top 10 Shorts por views")

            if df_short.empty:
                st.info("Nenhum Short encontrado para este canal.")
            else:
                top10_short = df_short.head(10).copy()
                top10_short["link_video"] = (
                    "https://www.youtube.com/watch?v=" + top10_short["video_id"]
                )

                st.dataframe(
                    top10_short[
                        ["titulo", "views", "likes", "comments", "ctr_simulado"]
                    ],
                    use_container_width=True,
                )

                st.markdown("**Links dos Shorts:**")
                for _, row in top10_short.iterrows():
                    url = row["link_video"]
                    st.markdown(f"- [▶️ {row['titulo']}]({url})")

            # Padrões de títulos (usando todos os vídeos analisados)
            st.subheader("🧠 Padrões de títulos (todos os vídeos analisados)")

            titulos = df_v["titulo"].tolist()
            n = len(titulos)
            numeros = len([t for t in titulos if any(ch.isdigit() for ch in t)])
            perguntas = len([t for t in titulos if "?" in t])
            emojis = len(
                [t for t in titulos if any(c in t for c in ["🔥", "💰", "🚀", "😱", "😮"])]
            )
            palavras_trigger = sum(
                t.lower().count(word)
                for t in titulos
                for word in ["segredo", "milionário", "rápido", "fácil", "nunca", "sempre"]
            )

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Títulos com números", f"{numeros/n*100:.0f}%")
                st.metric("Títulos em forma de pergunta", f"{perguntas/n*100:.0f}%")
            with c2:
                st.metric("Títulos com emoji", f"{emojis/n*100:.0f}%")
                st.metric("Ocorrências de gatilhos", palavras_trigger)

            melhor_titulo = (
                df_long.head(1)["titulo"].iloc[0]
                if not df_long.empty
                else df_v.head(1)["titulo"].iloc[0]
            )
            st.success(
                f"Modelo forte de título detectado, exemplo: `{melhor_titulo[:80]}...`"
            )

            col_bt1, col_bt2 = st.columns(2)
            with col_bt1:
                if st.button("💡 Usar melhor título como template (página 1)"):
                    st.session_state.titulo_template = melhor_titulo
                    st.success("Template salvo em session_state.titulo_template")

            with col_bt2:
                if st.session_state.canal_atual_id in db["canais"]:
                    sugestao = (
                        f"- {numeros/n*100:.0f}% dos top vídeos usam NÚMEROS no título.\n"
                        f"- {perguntas/n*100:.0f}% usam PERGUNTAS fortes.\n"
                        f"- {emojis/n*100:.0f}% usam EMOJIS.\n"
                        "- Priorizar títulos curtos com benefício claro na frente.\n"
                    )
                    if st.button("✍️ Gravar essas diretrizes no canal atual"):
                        canal_cfg = db["canais"][st.session_state.canal_atual_id]
                        atual = canal_cfg.get("preferencias_titulo", "")
                        novo = (atual + "\n\n" + sugestao).strip()
                        canal_cfg["preferencias_titulo"] = novo
                        st.success("Diretrizes gravadas nas preferências de título do canal.")

        else:
            st.info("Canal sem vídeos públicos para análise.")

    st.markdown("---")
    st.caption(
        "Use esta aba para copiar estratégias de canais reais e alimentar as "
        "configurações do seu canal no sistema. O app principal usa essas "
        "informações para guiar roteiros, thumbnails e outros elementos."
    )
