import re
import spacy


nlp = spacy.load("pt_core_news_sm")


def limpar_nome(nome: str):
    return " ".join([p.capitalize() for p in nome.strip().split()])


def nome_valido(nome: str):
    doc = nlp(nome)

    if len(doc) < 2:
        return False

    propn_count = 0

    for token in doc:
        if token.text.lower() in {"de", "da", "do", "dos", "das"}:
            continue

        if token.pos_ == "PROPN":
            propn_count += 1
        else:
            return False

    return propn_count >= 2


def extrair_nomes(texto: str):
    candidatos = set()

    pattern = r"\b([a-záéíóúâêôãõç]{3,}(?:\s+[a-záéíóúâêôãõç]{2,}){1,2})\b"
    matches = re.findall(pattern, texto, flags=re.IGNORECASE)

    for m in matches:
        candidatos.add(m)

    doc = nlp(texto)
    for ent in doc.ents:
        if ent.label_ == "PER":
            candidatos.add(ent.text)

    resultado = []
    for nome in candidatos:
        nome_limpo = limpar_nome(nome)
        if nome_valido(nome_limpo):
            resultado.append(nome_limpo)

    return list(set(resultado))


def extrair_emails(texto: str):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", texto)


def extrair_telefones(texto: str):
    return re.findall(r"(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-.\s]?\d{4}", texto)


def extrair_cpfs(texto: str):
    return re.findall(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", texto)


def extrair_ceps(texto: str):
    return re.findall(r"\b\d{5}-\d{3}\b", texto)


def extrair_cartoes(texto: str):
    return re.findall(r"\b(?:\d{4}[- ]?){3}\d{4}\b", texto)


def anonimizar_texto(texto: str):
    resultado = texto

    substituicoes = [
        (extrair_emails(texto), "[EMAIL]"),
        (extrair_cartoes(texto), "[CARTAO]"),
        (extrair_telefones(texto), "[TELEFONE]"),
        (extrair_cpfs(texto), "[CPF]"),
        (extrair_ceps(texto), "[CEP]"),
        (extrair_nomes(texto), "[NOME]"),
    ]

    for valores, tag in substituicoes:
        for v in set(valores):
            resultado = re.sub(re.escape(v), tag, resultado, flags=re.IGNORECASE)

    return resultado

