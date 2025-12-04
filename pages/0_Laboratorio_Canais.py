import re
from urllib.parse import urlparse, parse_qs

def extrair_channel_id(url):
    """
    Extrai o Channel ID válido a partir de diferentes URLs do YouTube.
    Para /channel/ID devolve ID direto,
    Para /user/username ou /c/customname, usa API para resolver.
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    
    if len(path_parts) < 1:
        return None

    if path_parts[0] == "channel":
        # URL no formato /channel/ID
        return path_parts[1] if len(path_parts) > 1 else None
    
    elif path_parts[0] in ["user", "c"]:
        # URL no formato /user/username ou /c/customname
        username = path_parts[1] if len(path_parts) > 1 else None
        if username:
            # Chamar a API YouTube para resolver o username/customname em Channel ID
            # Exemplo simplificado:
            youtube = get_youtube_service()
            req = youtube.channels().list(forUsername=username, part="id")
            res = req.execute()
            if res["items"]:
                return res["items"][0]["id"]
        return None

    else:
        # Caso não encaixe em formatos acima, tentar extrair do query string (não comum para canais)
        return None
