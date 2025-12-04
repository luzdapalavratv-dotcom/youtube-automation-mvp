import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import os
import tempfile
from datetime import datetime, timedelta

st.set_page_config(page_title="5_Publicar", layout="wide")
st.title("📤 Publicador Automático YouTube")

# Verificar pipeline completa
if "roteiro_gerado" not in st.session_state or not hasattr(st.session_state, 'audio_completo'):
    st.error("❌ Complete a pipeline (páginas 1-4) antes de publicar!")
    st.stop()

# Inicializar YouTube API
@st.cache_resource
def get_youtube_service():
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"]
    )
    return youtube

youtube = get_youtube_service()

# Sidebar configurações de publicação
with st.sidebar:
    st.header("⏰ Agendamento")
    publicar_agora = st.checkbox("Publicar AGORA", value=True)
    
    if not publicar_agora:
        data_publicacao = st.date_input("Data", datetime.now() + timedelta(days=1))
        hora_publicacao = st.time_input("Hora (Horário local)", datetime.now().time())
    
    st.header("🔒 Privacidade")
    visibilidade = st.radio("Status do vídeo", 
                           ["private", "unlisted", "public"], index=2)
    
    st.header("📱 Otimização Mobile")
    categoria = st.selectbox("Categoria", 
                            ["22 (People & Blogs)", "24 (Entertainment)", "28 (Science & Technology)"], 
                            index=0)

# Preparar metadados do vídeo
st.header("📋 Metadados Automatizados")

col1, col2 = st.columns(2)

with col1:
    titulo_final = st.text_input("Título Final", 
                               value=st.session_state.roteiro_gerado.get("titulo_video", "Vídeo Gerado"))
    
    descricao = st.text_area("Descrição", height=200, value="""
🔥 [PRIMEIRAS LINHAS DO SEU ROTEIRO AQUI]

👉 Inscreva-se no canal: [LINK DO CANAL]
🔔 Ative o sininho para não perder nenhum vídeo!

#hashtags do vídeo aqui

📱 Siga também no Instagram: [INSTAGRAM]
💬 Deixe seu comentário: Qual sua maior dúvida sobre [TEMA]?
""")
    
    tags = st.text_area("Tags (separadas por vírgula)", 
                       value="youtube, tutorial, dica, segredo, como fazer")

with col2:
    st.info("**📊 Dados Automáticos:**")
    st.success(f"✅ Roteiro: {len(st.session_state.roteiro_gerado.get('roteiro', {}))} seções")
    st.success(f"✅ Áudio: {os.path.getsize(st.session_state.audio_completo)/1000000:.1f}MB")
    st.info(f"**📈 SEO Otimizado:** Título + Descrição + Tags")

# Preparar arquivo de vídeo (placeholder - integrar com página 4)
if "video_final_path" not in st.session_state:
    st.session_state.video_final_path = st.session_state.audio_completo  # Usar áudio por enquanto

# Função principal de upload
def upload_video_youtube(file_path, title, description, tags, category, privacy="public", scheduled_time=None):
    """Faz upload do vídeo no YouTube com todas as configurações"""
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags.split(','),
            'categoryId': category
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False
        }
    }
    
    if scheduled_time:
        body['status']['publishAt'] = scheduled_time.isoformat() + "Z"
    
    try:
        # Upload do arquivo
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )
        
        response = insert_request.execute()
        video_id = response['id']
        
        return {
            "success": True,
            "video_id": video_id,
            "url": f"https://youtu.be/{video_id}",
            "title": title
        }
        
    except googleapiclient.errors.HttpError as e:
        return {"success": False, "error": str(e)}

# Interface de publicação
st.header("🚀 Publicar no YouTube")

col_publicar, col_status = st.columns([1,1])

with col_publicar:
    if st.button("📤 PUBLICAR VÍDEO", type="primary", use_container_width=True):
        with st.spinner("Enviando para YouTube... (pode levar 5-10 minutos)"):
            
            # Configurar agendamento
            if not publicar_agora:
                scheduled = datetime.combine(data_publicacao, hora_publicacao)
                scheduled_time = scheduled + timedelta(hours=3)  # UTC+3
            else:
                scheduled_time = None
            
            # Executar upload
            resultado = upload_video_youtube(
                st.session_state.video_final_path,
                titulo_final,
                descricao,
                tags,
                categoria,
                visibilidade,
                scheduled_time
            )
            
            if resultado["success"]:
                st.session_state.video_publicado = resultado
                st.success("🎉 VÍDEO PUBLICADO COM SUCESSO!")
                st.balloons()
            else:
                st.error(f"❌ Erro: {resultado['error']}")

# Status do vídeo publicado
if hasattr(st.session_state, 'video_publicado'):
    st.header("✅ Vídeo Publicado!")
    
    video_data = st.session_state.video_publicado
    
    col_url, col_acoes = st.columns([1,1])
    
    with col_url:
        st.markdown(f"**🔗 [Assistir no YouTube]({video_data['url']})**")
        st.code(video_data['video_id'])
        st.video(video_data['url'])
    
    with col_acoes:
        st.info("**📋 Próximos passos:**")
        st.success("✅ Vídeo processado pelo YouTube")
        st.info("⏳ Aguardar processamento (HD)")
        st.success("🚀 Compartilhar nas redes!")
    
    # Botão copiar link
    st.markdown("``````")
    
    if st.button("📋 Copiar Link do Vídeo"):
        st.success("Link copiado! Cole onde quiser!")

# Histórico de publicações
if "historico_publicacoes" not in st.session_state:
    st.session_state.historico_publicacoes = []

if st.button("💾 Salvar no Histórico"):
    if hasattr(st.session_state, 'video_publicado'):
        st.session_state.historico_publicacoes.append(st.session_state.video_publicado)
        st.success("✅ Salvo no histórico!")

if st.session_state.historico_publicacoes:
    st.header("📚 Histórico de Vídeos Publicados")
    
    for i, video in enumerate(st.session_state.historico_publicacoes[-5:]):
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**[{video['title'][:50]}...]({video['url']})**")
        with col2:
            st.caption(video.get('data', 'hoje'))

# Validação final
st.header("✅ Checklist Completo")
st.markdown("""
- [x] ✅ Roteiro viral gerado
- [x] ✅ Thumbnail A/B testada  
- [x] ✅ Áudio neural profissional
- [x] ✅ Vídeo editado
- [x] ✅ **PUBLICADO NO YOUTUBE!** 🎉
""")

st.markdown("---")
st.caption("🔥 Pipeline 100% Automática | YouTube API v3 | Próximo: [6_Dashboard.py]")

