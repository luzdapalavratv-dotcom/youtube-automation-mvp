import streamlit as st
import asyncio
import edge_tts
import io
import os
from datetime import datetime

st.set_page_config(page_title="3 – Áudio TTS", layout="wide")
st.title("🎙 3 – Gerador de Áudio TTS para o Vídeo")

# -------------------------------------------------------------------
# Integra com o "banco" e seleção do monitor
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

canal_id = st.session_state.canal_atual_id
video_id = st.session_state.video_atual_id

if not canal_id or canal_id not in db["canais"]:
    st.error("Nenhum canal selecionado. Vá ao app principal (monitor) e escolha um canal/vídeo.")
    st.stop()

canal = db["canais"][canal_id]
videos = canal["videos"]
if not video_id or video_id not in videos:
    st.error("Nenhum vídeo selecionado. Vá ao monitor e escolha um vídeo para este canal.")
    st.stop()

video = videos[video_id]

# Garante estrutura de artefatos
if "audio_path" not in video["artefatos"]:
    video["artefatos"]["audio_path"] = None
if "audio_info" not in video["artefatos"]:
    video["artefatos"]["audio_info"] = {}

# Se existir roteiro salvo, vamos usar
roteiro = video["artefatos"].get("roteiro")

# -------------------------------------------------------------------
# Sidebar – voz e configurações
# -------------------------------------------------------------------
with st.sidebar:
    st.header("📺 Contexto")
    st.markdown(f"**Canal:** {canal.get('nome','')}")
    st.markdown(f"**Vídeo:** {video.get('titulo','')}")

    st.markdown("---")
    st.header("🗣 Voz TTS (Edge-TTS)")

    vozes = {
        "🇺🇸 English (US) – Female": "en-US-JennyNeural",
        "🇺🇸 English (US) – Male": "en-US-GuyNeural",
        "🇧🇷 Português (BR) – Female": "pt-BR-FranciscaNeural",
        "🇧🇷 Português (BR) – Male": "pt-BR-AntonioNeural",
        "🇪🇸 Español (ES) – Female": "es-ES-ElviraNeural",
        "🇪🇸 Español (MX) – Female": "es-MX-DaliaNeural",
    }
    voz_label = st.selectbox("Voz", list(vozes.keys()), index=2)
    voz_code = vozes[voz_label]

    velocidade = st.slider("Velocidade (rate)", 0.5, 1.5, 1.0, 0.1)
    pitch = st.slider("Pitch (tom)", -10, 10, 0)
    volume = st.slider("Volume (dB)", -10, 10, 0)

    st.caption("Edge-TTS usa as vozes neurais da Microsoft (alta qualidade, gratuito).")  # [web:184][web:185]

# -------------------------------------------------------------------
# Funções TTS (Edge-TTS) – assíncrono
# -------------------------------------------------------------------
async def gerar_audio_edge_tts(texto: str, voz: str, output_path: str, rate: float, pitch: int, volume: int):
    """
    Gera áudio com Edge-TTS.
    Rate: multiplicador de velocidade (1.0 = normal).
    Pitch/volume: ajustados via SSML simples.
    """  # [web:184]

    rate_percent = int((rate - 1.0) * 100)  # ex.: 1.1 -> +10%
    rate_str = f"{rate_percent:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    volume_str = f"{volume:+d}dB"

    ssml = f"""
<speak version="1.0" xml:lang="pt-BR">
  <prosody rate="{rate_str}" pitch="{pitch_str}" volume="{volume_str}">
    {texto}
  </prosody>
</speak>
""".strip()

    # A biblioteca aceita o texto SSML direto, sem parâmetro 'ssml' [web:184]
    communicate = edge_tts.Communicate(ssml, voz)
    await communicate.save(output_path)


def run_tts_sync(texto: str, voz: str, rate: float, pitch: int, volume: int) -> str | None:
    """Executa Edge-TTS em loop isolado e retorna caminho do arquivo MP3."""
    import tempfile
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        output_path = tmp.name

    try:
        loop.run_until_complete(gerar_audio_edge_tts(texto, voz, output_path, rate, pitch, volume))
        return output_path
    except Exception as e:
        st.error(f"Erro ao gerar áudio TTS: {e}")
        return None
    finally:
        loop.close()

# -------------------------------------------------------------------
# Conteúdo base para leitura
# -------------------------------------------------------------------
st.subheader("📝 Texto que será narrado")

if roteiro and isinstance(roteiro, dict) and "roteiro" in roteiro:
    secoes = roteiro["roteiro"]
    secoes_nomes = list(secoes.keys())
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        secao_sel = st.selectbox("Escolha uma seção do roteiro para ouvir/editar", secoes_nomes)
    with col_s2:
        concatenar_todas = st.checkbox("Usar ROTEIRO COMPLETO (todas as seções)", value=False)

    if concatenar_todas:
        texto_base = ""
        for s, t in secoes.items():
            texto_base += f"[{s}]\n{t}\n\n"
    else:
        texto_base = secoes.get(secao_sel, "")
else:
    st.info("Nenhum roteiro salvo para este vídeo. Você pode colar um texto manualmente abaixo.")
    texto_base = ""

texto_manual = st.text_area(
    "Texto para narração (você pode editar o texto da seção ou colar algo completamente diferente)",
    value=texto_base,
    height=250,
)

if not texto_manual.strip():
    st.warning("Informe algum texto para gerar o áudio.")

# -------------------------------------------------------------------
# Geração do áudio
# -------------------------------------------------------------------
st.subheader("🎙 Gerar áudio")

col_g1, col_g2 = st.columns(2)
with col_g1:
    if st.button("🚀 Gerar áudio TTS", type="primary"):
        if not texto_manual.strip():
            st.warning("Texto vazio. Preencha antes de gerar.")
        else:
            with st.spinner("Gerando áudio com Edge-TTS..."):
                audio_path = run_tts_sync(texto_manual, voz_code, velocidade, pitch, volume)
                if audio_path and os.path.exists(audio_path):
                    video["artefatos"]["audio_path"] = audio_path
                    video["artefatos"]["audio_info"] = {
                        "voz": voz_label,
                        "voz_code": voz_code,
                        "velocidade": velocidade,
                        "pitch": pitch,
                        "volume": volume,
                        "gerado_em": datetime.now().isoformat(),
                        "texto_usado": texto_manual[:5000],  # guarda um resumo
                    }
                    video["status"]["3_audio"] = True
                    video["ultima_atualizacao"] = datetime.now().isoformat()
                    st.success("Áudio gerado e salvo no vídeo (etapa 3 concluída).")
with col_g2:
    if st.button("🗑 Remover áudio deste vídeo"):
        video["artefatos"]["audio_path"] = None
        video["artefatos"]["audio_info"] = {}
        video["status"]["3_audio"] = False
        video["ultima_atualizacao"] = datetime.now().isoformat()
        st.success("Áudio removido deste vídeo.")

st.markdown("---")

# -------------------------------------------------------------------
# Player e download
# -------------------------------------------------------------------
st.subheader("🎧 Player do áudio gerado")

audio_path_salvo = video["artefatos"].get("audio_path")

if audio_path_salvo and os.path.exists(audio_path_salvo):
    st.audio(audio_path_salvo, format="audio/mpeg")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with open(audio_path_salvo, "rb") as f:
            st.download_button(
                "💾 Baixar MP3",
                data=f.read(),
                file_name=f"audio_{video.get('titulo','video')[:20]}.mp3",
                mime="audio/mpeg",
            )
    with col_d2:
        info = video["artefatos"].get("audio_info", {})
        st.markdown("**Configurações usadas:**")
        st.caption(
            f"Voz: {info.get('voz','-')}  \n"
            f"Velocidade: {info.get('velocidade','-')}x  \n"
            f"Pitch: {info.get('pitch','-')}  \n"
            f"Volume: {info.get('volume','-')} dB"
        )
else:
    st.info("Nenhum áudio disponível ainda para este vídeo. Gere um áudio acima.")

st.markdown("---")
st.caption(
    "Após gerar o áudio TTS e salvar, volte ao **Monitor de Produção** "
    "para seguir para a etapa 4 (montagem do vídeo)."
)
