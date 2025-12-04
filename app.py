import streamlit as st
import uuid
from datetime import datetime
import pandas as pd
import googleapiclient.discovery

st.set_page_config(page_title="YouTube Automation MVP – Monitor", layout="wide")
st.title("📺 Monitor de Produção de Vídeos (Pipeline YouTube)")

# -------------------------------------------------------------------
# DB em sessão
# -------------------------------------------------------------------
def criar_db_vazio():
    return {"canais": {}}

if "db" not in st.session_state:
    st.session_state.db = criar_db_vazio()
db = st.session_state.db

if "canal_atual_id" not in st.session_state:
    st.session_state.canal_atual_id = None
if "video_atual_id" not in st.session_state:
    st.session_state.video_atual_id = None

# -------------------------------------------------------------------
# YouTube API (para importar canal pelo link)
# -------------------------------------------------------------------
@st.cache_resource
def get_youtube_service():
    return googleapiclient.discovery.build(
        "youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"]
    )

youtube = get_youtube_service()

def gerar_id():
    return str(uuid.uuid4())[:8]

def obter_canal(canal_id):
    return db["canais"].get(canal_id)

def obter_video(canal_id, video_id):
    canal = obter_canal(canal_id)
    if not canal:
        return None
    return canal["videos"].get(video_id)

def etapa_atual(status_dict):
    ordem = [
        "0_canal",
        "1_roteiro",
        "2_thumbnail",
        "3_audio",
        "4_video",
        "5_publicacao",
        "6_dashboard",
    ]
    ultima = -1
    for i, k in enumerate(ordem):
        if status_dict.get(k):
            ultima = i
    concluido = all(status_dict.get(k, False) for k in ordem)
    return ultima, concluido

def nome_etapa(idx):
    nomes = [
        "0 – Canal pronto",
        "1 – Roteiro",
        "2 – Thumbnails",
        "3 – Áudio",
        "4 – Vídeo",
        "5 – Publicação",
        "6 – Dashboard",
    ]
    if 0 <= idx < len(nomes):
        return nomes[idx]
    return "Não iniciado"

# -------------------------------------------------------------------
# Função auxiliar: importar dados de canal pelo link do YouTube
# -------------------------------------------------------------------
from urllib.parse import urlparse

def extrair_channel_id(url: str):
    url = url.strip()
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if path.startswith("channel/"):
        return path.split("/")[1]

    if path.startswith("@"):
        handle = path[1:]
        try:
            ch_req = youtube.channels().list(part="id", forHandle=handle)
            ch_res = ch_req.execute()
            items = ch_res.get("items", [])
            if items:
                return items[0]["id"]
        except Exception:
            return None

    return None

def importar_canal_por_link(link: str):
    """Retorna dict básico de canal (nome, idioma pt-BR default) ou None."""
    ch_id = extrair_channel_id(link)
    if not ch_id:
        return None

    try:
        ch_req = youtube.channels().list(part="snippet", id=ch_id)
        ch_res = ch_req.execute()
        items = ch_res.get("items", [])
        if not items:
            return None
        sn = items[0]["snippet"]
        nome = sn.get("title", "")
        return {
            "nome": nome,
            "link_youtube": link.strip(),
            "nicho": "",
            "persona": "",
            "idioma": "pt-BR",
            "criado_em": datetime.now().isoformat(),
            "videos": {},
        }
    except Exception:
        return None

# -------------------------------------------------------------------
# SIDEBAR – apenas seleção rápida de canal e vídeo
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📡 Seleção rápida")

    canais_ids = list(db["canais"].keys())
    if canais_ids:
        canais_nomes = [db["canais"][cid]["nome"] for cid in canais_ids]
        idx_canal = st.selectbox(
            "Canal atual",
            options=range(len(canais_ids)),
            format_func=lambda i: canais_nomes[i],
            index=0
            if st.session_state.canal_atual_id not in canais_ids
            else canais_ids.index(st.session_state.canal_atual_id),
        )
        canal_atual_id = canais_ids[idx_canal]
        st.session_state.canal_atual_id = canal_atual_id
    else:
        canal_atual_id = None
        st.info("Nenhum canal cadastrado ainda.")

    # Seleção de vídeo atual
    video_atual_id = None
    if canal_atual_id:
        canal = db["canais"][canal_atual_id]
        vids = canal["videos"]
        if vids:
            vids_ids = list(vids.keys())
            vids_tit = [vids[v]["titulo"] for v in vids_ids]
            idx_vid = st.selectbox(
                "Vídeo atual",
                options=range(len(vids_ids)),
                format_func=lambda i: vids_tit[i],
                index=0
                if st.session_state.video_atual_id not in vids_ids
                else vids_ids.index(st.session_state.video_atual_id),
            )
            video_atual_id = vids_ids[idx_vid]
            st.session_state.video_atual_id = video_atual_id
        else:
            st.caption("Nenhum vídeo para este canal ainda.")

    # Botão simples de novo vídeo
    if canal_atual_id:
        if st.button("➕ Novo vídeo (rápido)"):
            vid_id = gerar_id()
            canal = db["canais"][canal_atual_id]
            canal["videos"][vid_id] = {
                "titulo": f"Novo vídeo {len(canal['videos']) + 1}",
                "descricao": "",
                "status": {
                    "0_canal": True,
                    "1_roteiro": False,
                    "2_thumbnail": False,
                    "3_audio": False,
                    "4_video": False,
                    "5_publicacao": False,
                    "6_dashboard": False,
                },
                "artefatos": {
                    "roteiro": None,
                    "thumbs": None,
                    "audio_path": None,
                    "video_path": None,
                    "youtube_url": None,
                },
                "criado_em": datetime.now().isoformat(),
                "ultima_atualizacao": datetime.now().isoformat(),
            }
            st.session_state.video_atual_id = vid_id
            st.rerun()

# -------------------------------------------------------------------
# Corpo – se não há canal, mostrar chamada
# -------------------------------------------------------------------
if not st.session_state.canal_atual_id:
    st.warning("Nenhum canal selecionado. Use o painel lateral para criar ou selecionar um canal.")
else:
    canal_atual_id = st.session_state.canal_atual_id

canal = obter_canal(canal_atual_id) if canal_atual_id else None

# -------------------------------------------------------------------
# BLOCO 1 – KPIs do canal atual
# -------------------------------------------------------------------
if canal:
    st.subheader(f"📺 Canal: **{canal['nome']}**")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        st.metric("Nicho", canal.get("nicho", "-"))
    with col_c2:
        st.metric("Idioma", canal.get("idioma", "-"))
    with col_c3:
        st.metric("Vídeos cadastrados", len(canal["videos"]))
    with col_c4:
        st.metric("Criado em", canal.get("criado_em", "")[:10])

    st.markdown("---")

# -------------------------------------------------------------------
# BLOCO 2 – Gestão de canais (expander na área principal)
# -------------------------------------------------------------------
st.markdown("### ⚙️ Gestão de canais")

# Dados base para o formulário
if canal:
    canal_form_data = canal.copy()
else:
    canal_form_data = {
        "nome": "",
        "link_youtube": "",
        "nicho": "",
        "persona": "",
        "idioma": "pt-BR",
        "criado_em": datetime.now().isoformat(),
        "videos": {},
    }

with st.expander(
    "Criar novo canal ou editar canal atual",
    expanded=not bool(db["canais"]),
):
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        nome_canal = st.text_input(
            "Nome do canal",
            value=canal_form_data.get("nome", ""),
        )
        link_canal = st.text_input(
            "Link do canal no YouTube",
            value=canal_form_data.get("link_youtube", ""),
            placeholder="https://www.youtube.com/@seucanal",
        )
        nicho_canal = st.text_input(
            "Nicho principal",
            value=canal_form_data.get("nicho", ""),
        )

    with col_f2:
        persona = st.text_area(
            "Persona resumida",
            value=canal_form_data.get("persona", ""),
            height=80,
        )
        idioma = st.selectbox(
            "Idioma principal",
            ["pt-BR", "en-US", "es-ES"],
            index=["pt-BR", "en-US", "es-ES"].index(
                canal_form_data.get("idioma", "pt-BR")
            ),
        )

    col_b1, col_b2, col_b3 = st.columns(3)

    # Salvar alterações no canal atual
    with col_b1:
        if st.button("💾 Salvar alterações no canal atual"):
            if not canal_atual_id:
                st.warning("Nenhum canal selecionado para editar.")
            elif not nome_canal.strip():
                st.warning("Informe um nome para o canal.")
            else:
                db["canais"][canal_atual_id].update(
                    {
                        "nome": nome_canal.strip(),
                        "link_youtube": link_canal.strip(),
                        "nicho": nicho_canal.strip(),
                        "persona": persona.strip(),
                        "idioma": idioma,
                    }
                )
                st.success("Canal atualizado.")
                st.rerun()

    # Criar novo canal em branco
    with col_b2:
        if st.button("➕ Criar novo canal em branco"):
            if not nome_canal.strip():
                st.warning("Informe um nome para o novo canal.")
            else:
                new_id = gerar_id()
                db["canais"][new_id] = {
                    "nome": nome_canal.strip(),
                    "link_youtube": link_canal.strip(),
                    "nicho": nicho_canal.strip(),
                    "persona": persona.strip(),
                    "idioma": idioma,
                    "criado_em": datetime.now().isoformat(),
                    "videos": {},
                }
                st.session_state.canal_atual_id = new_id
                st.success("Novo canal criado.")
                st.rerun()

    # Criar canal a partir de link do YouTube
    with col_b3:
        if st.button("🔍 Importar canal pelo link do YouTube"):
            if not link_canal.strip():
                st.warning("Cole o link do canal do YouTube.")
            else:
                canal_importado = importar_canal_por_link(link_canal)
                if not canal_importado:
                    st.error("Não foi possível importar esse canal. Verifique o link.")
                else:
                    new_id = gerar_id()
                    db["canais"][new_id] = canal_importado
                    st.session_state.canal_atual_id = new_id
                    st.success(f"Canal importado: {canal_importado['nome']}")
                    st.rerun()

st.markdown("---")

# -------------------------------------------------------------------
# Se ainda não há canal selecionado após possíveis criações, parar aqui
# -------------------------------------------------------------------
canal_id = st.session_state.canal_atual_id
if not canal_id:
    st.stop()

canal = obter_canal(canal_id)

# -------------------------------------------------------------------
# BLOCO 3 – Tabela de vídeos + criação detalhada de novo vídeo
# -------------------------------------------------------------------
st.header("🎞️ Vídeos deste canal")

videos_dict = canal["videos"]
if not videos_dict:
    st.info("Nenhum vídeo cadastrado ainda para este canal.")
else:
    rows = []
    for vid, data in videos_dict.items():
        idx, done = etapa_atual(data["status"])
        rows.append(
            {
                "video_id": vid,
                "Título": data["titulo"],
                "Etapa atual": nome_etapa(idx) if idx >= 0 else "Não iniciado",
                "Concluído": "✅" if done else "⏳",
                "Criado em": data.get("criado_em", "")[:16],
            }
        )
    df_list = pd.DataFrame(rows)

    col_ls1, col_ls2 = st.columns([2, 1])
    with col_ls1:
        st.dataframe(
            df_list[["Título", "Etapa atual", "Concluído", "Criado em"]],
            use_container_width=True,
            height=260,
        )

    with col_ls2:
        vids_ids = [r["video_id"] for r in rows]
        vids_titulos = [r["Título"] for r in rows]
        idx_video_sel = st.selectbox(
            "Vídeo em foco",
            options=range(len(vids_ids)),
            format_func=lambda i: vids_titulos[i],
            index=0
            if st.session_state.video_atual_id not in vids_ids
            else vids_ids.index(st.session_state.video_atual_id),
        )
        video_atual_id = vids_ids[idx_video_sel]
        st.session_state.video_atual_id = video_atual_id

# Expander para criação detalhada de novo vídeo
with st.expander("➕ Criar novo vídeo para este canal"):
    col_nv1, col_nv2 = st.columns(2)
    with col_nv1:
        novo_titulo_video = st.text_input("Título do vídeo")
        tipo_video = st.selectbox("Tipo", ["Longform", "Short"], index=0)
    with col_nv2:
        descricao_rapida = st.text_area(
            "Descrição / ideia rápida",
            height=80,
        )

    if st.button("Criar vídeo (detalhado)"):
        if not novo_titulo_video.strip():
            st.warning("Informe um título para o vídeo.")
        else:
            vid_id = gerar_id()
            canal["videos"][vid_id] = {
                "titulo": novo_titulo_video.strip(),
                "descricao": descricao_rapida.strip(),
                "tipo": tipo_video,
                "status": {
                    "0_canal": True,
                    "1_roteiro": False,
                    "2_thumbnail": False,
                    "3_audio": False,
                    "4_video": False,
                    "5_publicacao": False,
                    "6_dashboard": False,
                },
                "artefatos": {
                    "roteiro": None,
                    "thumbs": None,
                    "audio_path": None,
                    "video_path": None,
                    "youtube_url": None,
                },
                "criado_em": datetime.now().isoformat(),
                "ultima_atualizacao": datetime.now().isoformat(),
            }
            st.session_state.video_atual_id = vid_id
            st.success("Vídeo criado.")
            st.rerun()

st.markdown("---")

# -------------------------------------------------------------------
# BLOCO 4 – Painel detalhado do vídeo selecionado
# -------------------------------------------------------------------
video = obter_video(canal_id, st.session_state.video_atual_id)
if not video:
    st.stop()

st.header("🎯 Pipeline do vídeo selecionado")

col_v1, col_v2 = st.columns([2, 1])
with col_v1:
    st.markdown(f"### 🎬 {video.get('titulo', '(sem título)')}")
    if video.get("descricao"):
        st.caption(video["descricao"])
with col_v2:
    idx_e, finished = etapa_atual(video["status"])
    st.metric("Etapa atual", nome_etapa(idx_e) if idx_e >= 0 else "Não iniciado")
    st.metric("Status geral", "Concluído ✅" if finished else "Em produção ⏳")

st.markdown("#### 🧩 Etapas da pipeline")

etapas = [
    ("0_canal", "0 – Canal pronto", "Somente cadastro e análise do canal"),
    ("1_roteiro", "1 – Roteiro", "Roteiro gerado e aprovado"),
    ("2_thumbnail", "2 – Thumbnails", "Thumbs A/B/C geradas e escolhidas"),
    ("3_audio", "3 – Áudio", "Narração TTS pronta"),
    ("4_video", "4 – Vídeo", "Vídeo final renderizado"),
    ("5_publicacao", "5 – Publicação", "Upload/agendamento no YouTube"),
    ("6_dashboard", "6 – Dashboard", "Métricas e resultados monitorados"),
]

for key, nome, desc in etapas:
    done = video["status"].get(key, False)
    idx = etapas.index((key, nome, desc))

    col_e1, col_e2, col_e3 = st.columns([2, 4, 2])
    with col_e1:
        icone = "✅" if done else ("🟡" if idx <= etapa_atual(video["status"])[0] + 1 else "⚪")
        st.markdown(f"**{icone} {nome}**")
        st.caption(desc)
    with col_e2:
        resumo = ""
        artefatos = video.get("artefatos", {})
        if key == "1_roteiro" and artefatos.get("roteiro"):
            resumo = "Roteiro salvo."
        elif key == "2_thumbnail" and artefatos.get("thumbs"):
            resumo = "Thumbnails geradas."
        elif key == "3_audio" and artefatos.get("audio_path"):
            resumo = f"Áudio em: {artefatos['audio_path']}"
        elif key == "4_video" and artefatos.get("video_path"):
            resumo = f"Vídeo em: {artefatos['video_path']}"
        elif key == "5_publicacao" and artefatos.get("youtube_url"):
            resumo = f"Publicado: {artefatos['youtube_url']}"
        elif key == "6_dashboard":
            resumo = "Dados disponíveis no dashboard (página 6), se configurado."
        else:
            resumo = "Ainda sem artefatos salvos."

        st.caption(resumo)

    with col_e3:
        pagina_map = {
            "0_canal": "pages/0_Laboratorio_Canais.py",
            "1_roteiro": "pages/1_Roteiro_Viral.py",
            "2_thumbnail": "pages/2_Thumbnail_AB.py",
            "3_audio": "pages/3_Audio_TTS.py",
            "4_video": "pages/4_Video_Final.py",
            "5_publicacao": "pages/5_Publicar.py",
            "6_dashboard": "pages/6_Dashboard.py",
        }
        destino = pagina_map.get(key)
        if destino:
            st.page_link(
                destino,
                label="Ir para etapa",
                icon="➡️",
            )

    st.markdown("---")

# -------------------------------------------------------------------
# BLOCO 5 – Resumo agregado do canal
# -------------------------------------------------------------------
st.header("📊 Resumo de progresso do canal")

contagem = {
    "Ideia / só criado": 0,
    "Roteiro pronto": 0,
    "Thumb pronta": 0,
    "Áudio pronto": 0,
    "Vídeo pronto": 0,
    "Publicado": 0,
}

for vid_id, v in canal["videos"].items():
    stt = v["status"]
    if stt.get("5_publicacao"):
        contagem["Publicado"] += 1
    elif stt.get("4_video"):
        contagem["Vídeo pronto"] += 1
    elif stt.get("3_audio"):
        contagem["Áudio pronto"] += 1
    elif stt.get("2_thumbnail"):
        contagem["Thumb pronta"] += 1
    elif stt.get("1_roteiro"):
        contagem["Roteiro pronto"] += 1
    else:
        contagem["Ideia / só criado"] += 1

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("Somente criados", contagem["Ideia / só criado"])
with col_r2:
    st.metric("Roteiro pronto", contagem["Roteiro pronto"])
with col_r3:
    st.metric("Thumb pronta", contagem["Thumb pronta"])

col_r4, col_r5, col_r6 = st.columns(3)
with col_r4:
    st.metric("Áudio pronto", contagem["Áudio pronto"])
with col_r5:
    st.metric("Vídeo pronto", contagem["Vídeo pronto"])
with col_r6:
    st.metric("Publicados", contagem["Publicado"])

st.markdown("---")
st.caption(
    "Use este monitor como painel central. Cada página (0–6) lê "
    "`st.session_state.canal_atual_id` e `st.session_state.video_atual_id` "
    "para saber em qual vídeo trabalhar e atualiza o `db` conforme as etapas avançam."
)
