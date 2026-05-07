import json
import re
import unicodedata


def normalizar_horario(horario: str) -> str:
    if not horario:
        return ""

    horario = horario.lower().strip()
    match = re.search(r"(\d{1,2})[:h](\d{2})", horario)
    if match:
        hora = match.group(1).zfill(2)
        minuto = match.group(2)
        return f"{hora}:{minuto}"

    match = re.search(r"(\d{1,2})", horario)
    if match:
        hora = match.group(1).zfill(2)
        return f"{hora}:00"

    return ""


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace(" ", "").replace("_", "").replace("-", "")

    return texto


def normalizar_tipo_agressao(tipo: str) -> str:
    if not tipo:
        return "outro"

    tipo_norm = normalizar_texto(tipo)

    if "assedio" in tipo_norm or "assede" in tipo_norm or "asseso" in tipo_norm:
        if "sexual" in tipo_norm:
            return "assedio_sexual"
        return "assedio_moral"

    if "fisic" in tipo_norm:
        return "agressao_fisica"

    if "racial" in tipo_norm or "injuria" in tipo_norm:
        return "injuria_racial"

    if "amea" in tipo_norm:
        return "ameaca"

    if "bully" in tipo_norm:
        return "bullying"

    if "discrimin" in tipo_norm:
        return "discriminacao"

    if "psicolog" in tipo_norm:
        return "violencia_psicologica"

    return "outro"


def parse_json(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1:
        try:
            return json.loads(content[start:end + 1])
        except:
            return None

    return None


def fallback_resposta(texto: str, motivo: str):
    return {
        "is_valid_denuncia": False,
        "motivo_invalidacao": motivo,
        "tipo_agressao": "",
        "horario": "",
        "local": "",
        "agressor": "",
        "descricao_resumida": texto[:200],
        "confidence": 0.0
    }


def print_tempo(inicio, fim):
    tempo_total = fim - inicio
    minutos = int(tempo_total // 60)
    segundos = int(tempo_total % 60)

    print(f"Tempo de resposta: {minutos} min {segundos} s")


def limpar_texto(texto: str) -> str:
    if not texto:
        return ""

    return texto.strip()