import streamlit as st
import requests
import json

st.set_page_config(page_title="Laboratório de Canais", layout="wide")

# APIs
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY")

# ===============================================
# FUNÇÕES INTERNAS
# ===============================================

def gerar_roteiro_groq(prompt: str) -> str | None:
    """Chamada simples à Groq API (modelo Llama 3.1 405B)."""
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY não encontrada nos secrets.")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-405b-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=40,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erro ao chamar Groq: {e}")
        return None


def analisar_nicho_groq(nicho: str, meta: str) -> dict:
    """
    Pede para a IA devolver um JSON com a modelagem do canal.
    Tenta fazer parse do JSON; se der erro, devolve um fallback.
    """
    prompt = f"""
Você é um estrategista profissional de canais do YouTube.

Analise o seguinte cenário e RESPONDA APENAS com um JSON **válido**:

NICHO: "{nicho}"
META DO CANAL: "{meta}"

Estrutura esperada do JSON:

{{
  "nicho": "{nicho}",
  "micronicho_recomendado": "descreva um micronicho bem específico e lucrativo",
  "frequencia_postagens": "X vídeos por semana",
  "duracao_ideal": "X a Y minutos por vídeo",
  "titulos_formula": [
    "fórmula exata de título 1",
    "fórmula exata de título 2",
    "fórmula exata de título 3",
    "fórmula exata de título 4",
    "fórmula exata de título 5"
  ],
  "thumbnails_estilo": "descrição clara de cores, elementos visuais e estilo",
  "personagens_tipos": [
    "tipo de protagonista 1",
    "tipo de protagonista 2"
  ],
  "previsao_crescimento": "estimativa de inscritos e views em 90 dias, assumindo execução consistente"
}}

Não explique nada fora do JSON. Apenas retorne o JSON.
""".strip()

    bruto = gerar_roteiro_groq(prompt)
    if not bruto:
        # fallback simples
        return {
            "nicho": nicho,
            "micronicho_recomendado": f"{nicho} com foco em histórias emocionais de alto apelo",
            "frequencia_postagens": "5 vídeos por semana",
            "duracao_ideal": "12 a 15 minutos",
            "titulos_formula": [
                "MILIONÁRIO X até que CRIANÇA Y faz Z",
                "ELE ia perder TUDO até que UMA MENINA bate à porta",
                "O SEGREDO que ninguém conta sobre X",
                "ELA ouviu ISSO no hospital e mudou o destino dele",
                "ELE riu da menina de rua, até descobrir a VERDADE"
            ],
            "thumbnails_estilo": "Fundo vermelho dramático, texto amarelo grande, rostos emocionados em close",
            "personagens_tipos": [
                "milionário solitário com trauma",
                "criança pobre com grande coração"
            ],
            "previsao_crescimento": "até 8.000 inscritos em 90 dias com consistência"
        }

    # tentar extrair JSON de dentro da resposta
    try:
        ini = bruto.find("{")
        fim = bruto.rfind("}") + 1
        json_str = bruto[ini:fim]
        dados = json.loads(json_str)
        # garantir campos básicos
        dados.setdefault("nicho", nicho)
        return dados
    except Exception:
        # fallback se o JSON vier quebrado
        return {
            "nicho": nicho,
            "micronicho_recomendado": f"{nicho} com foco em histórias emocionais de alto apelo",
            "frequencia_postagens": "5 vídeos por semana",
            "duracao_ideal": "12 a 15 minutos",
            "titulos_formula": [
                "MILIONÁRIO X até que CRIANÇA Y faz Z",
                "ELE ia perder TUDO até que UMA MENINA bate à porta",
                "O SEGREDO que ninguém conta sobre X",
                "ELA ouviu ISSO no hospital e mudou o destino dele",
                "ELE riu da menina de rua, até descobrir a VERDADE"
            ],
            "thumbnails_estilo": "Fundo vermelho dramático, texto amarelo grande, rostos emocionados em close",
            "personagens_tipos":
