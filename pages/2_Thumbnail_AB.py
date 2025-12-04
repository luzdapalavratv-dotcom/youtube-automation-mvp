import streamlit as st

def gerar_ab_thumbnails_nativo(titulo):
    """Gera 3 thumbnails OTIMIZADOS para YouTube A/B oficial"""
    prompts = [
        f"{titulo}, thumbnail dramático VERMELHO + texto AMARELO grande, 1280x720",
        f"{titulo}, thumbnail minimalista AZUL + texto BRANCO clean, 1280x720", 
        f"{titulo}, thumbnail épico DOURADO + luzes cinematicas, 1280x720"
    ]
    
    thumbs = {}
    for i, prompt in enumerate(prompts):
        thumbs[f"Test {i+1}"] = turbo_perfeito(prompt)
    
    return thumbs

# Interface YouTube A/B Native
st.title("🧪 **Gerador A/B YouTube NATIVE**")
titulo = st.text_input("Título do vídeo", "Milionário + Menina Órfã")

if st.button("🎨 Gerar 3 Thumbnails para Test & Compare"):
    ab_set = gerar_ab_thumbnails_nativo(titulo)
    
    col1, col2, col3 = st.columns(3)
    for nome, url in ab_set.items():
        with locals()[f"col{nome[-1]}"]:
            st.image(url, caption=nome, use_column_width=True)
            st.download_button(
                label=f"📥 Download {nome}",
                data=requests.get(url).content,
                file_name=f"{titulo}_{nome}.jpg",
                mime="image/jpeg"
            )

st.info("""
**📋 COMO USAR no YouTube:**
1. Publique seu vídeo
2. YouTube Studio → Thumbnail → "Test & Compare" 
3. Upload estes 3 arquivos
4. YouTube testa 7 dias → VENCEDOR automático!
""")

