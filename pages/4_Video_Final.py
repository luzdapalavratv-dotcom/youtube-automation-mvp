import streamlit as st
from moviepy.editor import *
import os
import tempfile

st.set_page_config(page_title="4_Video_Final", layout="wide")
st.title("🎬 Editor e Gerador Final de Vídeo YouTube")

# Confirmar áudio e roteiro na sessão
if "roteiro_gerado" not in st.session_state:
    st.warning("⚠️ Gere roteiro e áudio antes nesta pipeline!")
    st.stop()

if not (hasattr(st.session_state, 'audio_completo') and st.session_state.audio_completo and os.path.exists(st.session_state.audio_completo)):
    st.warning("⚠️ Gere o áudio completo na página 3 para continuar!")
    st.stop()

audio_path = st.session_state.audio_completo

# Upload de vídeo base (ex: imagens, animação, ou tela verde)
video_upload = st.file_uploader("📤 Faça upload do vídeo base (mp4) para edição", type=["mp4"])

# Opções de texto na tela
with st.sidebar:
    st.header("📝 Legendas e Textos")
    gerar_legendas = st.checkbox("Gerar legendas automáticas (SRT)", value=True)
    texto_titulo = st.text_input("Texto título na abertura", "Título do Vídeo")
    texto_call = st.text_area("Call-to-action (final do vídeo)", "Inscreva-se, deixe seu like e compartilhe!")
    pos_titulo = st.selectbox("Posição do título", ["center", "top", "bottom"], index=0)
    pos_call = st.selectbox("Posição do CTA", ["bottom", "center", "top"], index=0)
    duracao_texto_sec = st.slider("Duração do texto em segundos", 3, 10, 5)

# Função para criar clips de texto dynâmicos
def criar_clip_texto(texto, duracao, tamanho=50, cor="white", pos="center", largura=1280):
    txt_clip = (TextClip(texto, fontsize=tamanho, color=cor, font='Arial-Bold',
                         method='caption', size=(largura, None), align='center')
                .set_duration(duracao).set_position(pos).fadein(0.5).fadeout(0.5))
    return txt_clip

# Montagem do vídeo final
if st.button("🎞️ Montar Vídeo Final"):
    with st.spinner("Renderizando vídeo final... Isso pode levar alguns minutos!"):
        # Load video base ou cria fundo preto
        if video_upload is not None:
            video_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            video_temp.write(video_upload.getvalue())
            video_temp.close()
            video_clip = VideoFileClip(video_temp.name)
        else:
            video_clip = ColorClip((1280, 720), color=(0,0,0)).set_duration(AudioFileClip(audio_path).duration)
        
        audio_clip = AudioFileClip(audio_path)
        video_clip = video_clip.set_audio(audio_clip)
        
        # Criar clipes de texto
        titulo_clip = criar_clip_texto(texto_titulo, duracao_texto_sec, tamanho=70, pos=pos_titulo)
        call_clip = criar_clip_texto(texto_call, duracao_texto_sec, tamanho=50, pos=pos_call)
        
        # Temporizar clipes
        titulo_clip = titulo_clip.set_start(0)
        call_clip = call_clip.set_start(max(0, video_clip.duration - duracao_texto_sec))
        
        # Combinar clipes
        final = CompositeVideoClip([video_clip, titulo_clip, call_clip])
        save_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final.write_videofile(save_path, codec='libx264', audio_codec='aac', threads=4, fps=24)
        
        # Mostrar player e download
        st.success("✅ Vídeo final renderizado com sucesso!")
        st.video(save_path)
        with open(save_path, "rb") as f:
            st.download_button("💾 Download Vídeo Final", f, file_name="youtube_video_final.mp4", mime="video/mp4")

# Opções para download dos arquivos intermediários
st.header("📁 Downloads Auxiliares")
if st.button("📥 Download Áudio MP3"):
    with open(audio_path, "rb") as f:
        st.download_button("Download Áudio MP3", f, file_name="audio_video.mp3", mime="audio/mpeg")

if "roteiro_gerado" in st.session_state:
    roteiro_str = ""
    roteiro = st.session_state.roteiro_gerado.get("roteiro", {})
    for secao, texto in roteiro.items():
        roteiro_str += f"{secao}:\n{texto}\n\n"
    st.download_button("📥 Download Roteiro (TXT)", roteiro_str, file_name="roteiro_video.txt", mime="text/plain")

st.markdown("---")
st.caption("🎉 Pipeline Completa! Vídeo pronto para upload no YouTube 🚀")

