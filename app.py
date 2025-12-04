import streamlit as st

st.set_page_config(
    page_title="YouTube Automation MVP",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 **YouTube Automation MVP**")
st.markdown("**Sistema completo: Estratégia → Vídeo → YouTube**")

# Verificação APIs
groq_key = st.secrets.get("GROQ_API_KEY", None)
yt_key = st.secrets.get("YOUTUBE_API_KEY", None)

if not groq_key:
    st.error("❌ 1.1 GROQ_API_KEY faltando em Secrets!")
elif not yt_key:
    st.warning("⚠️ 1.2 YOUTUBE_API_KEY faltando (nicho finder limitado)")
else:
    st.success("✅ Todas APIs OK!")

st.markdown("---")
st.info("""
**📋 CHECKLIST no seu papel:**
1️⃣ Faça APIs 1.1 e 1.2
2️⃣ Clique em cada página para testar
3️⃣ Marque conforme funciona
4️⃣ Me informe códigos com problema: 2.1, 3.4, etc.
""")

st.markdown("### **Páginas do MVP**")
st.success("Clique nas abas laterais → teste sequencialmente!")
