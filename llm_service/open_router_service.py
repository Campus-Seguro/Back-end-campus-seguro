import requests
import re
import time
import os

from typing import List
from dotenv import load_dotenv
from .utils import *
from .security import SecurityService

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


security_service = SecurityService()


SYSTEM_PROMPT = """
            Extraia JSON da denúncia.

            O texto fornecido pode conter placeholders de anonimização como:
            [NOME], [CPF], [EMAIL], [TELEFONE], [CARTAO], [CEP].

            Esses placeholders representam dados sensíveis que foram removidos por segurança.

            Regras:
            - Retorne UM ÚNICO objeto JSON
            - NÃO retorne múltiplos JSONs
            - Todos os campos devem estar no MESMO objeto
            - NÃO inclua comentários (// ou #)
            - NÃO inclua explicações
            - NÃO inclua texto fora do JSON
            - Todos os campos devem ser válidos em JSON
            - NÃO tente inferir ou reconstruir esses dados.
            - Considere os placeholders como entidades reais no contexto.
            - Continue a análise normalmente, ignorando a ausência dos dados reais.

            IMPORTANTE:
            - Sua resposta deve conter exatamente 1 objeto JSON
            - Não retorne múltiplos blocos
            - Não repita JSON

            - Campos desconhecidos devem ser:
            - string vazia "" para texto
            - null apenas se necessário

            - Horário:
            - formato HH:MM se existir
            - caso contrário use ""

            - tipo_agressao nunca pode ser vazio

            - Se não for denúncia:
            - "is_valid_denuncia": false
            - preencher "motivo_invalidacao"

            Tipos:
            agressao_fisica, assedio_moral, assedio_sexual, 
            injuria_racial, bullying, ameaca, discriminacao, 
            violencia_psicologica, outro

            JSON esperado:
            {
            "is_valid_denuncia": bool,
            "motivo_invalidacao": "",
            "tipo_agressao": "",
            "horario": "",
            "local": "",
            "agressor": "",
            "descricao_resumida": "",
            "confidence": 0.0
            }
"""


def chamar_openrouter(modelo: str, messages: list) -> dict:
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Campus Seguro"
        },
        json={
            "model": modelo,
            "messages": messages,
            "temperature": 0
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def executar_com_fallback(messages: list, modelos: List[str]) -> dict:
    for modelo in modelos:
        try:
            print(f"[INFO] Tentando: {modelo}")
            resp = chamar_openrouter(modelo, messages)

            if "choices" not in resp:
                print(f"[ERRO] Resposta inválida: {modelo}")
                continue

            print(f"[SUCESSO] Modelo usado: {modelo}")
            return resp

        except requests.exceptions.RequestException as e:
            print(f"[ERRO] {modelo}: {e}")
            continue

    raise Exception("Todos os modelos falharam")


def fazer_request_via_open_router(messages: list):
    modelos = [
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "poolside/laguna-m.1:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openai/gpt-oss-20b:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "openai/gpt-oss-120b:free",
        "minimax/minimax-m2.5:free"
    ]

    return executar_com_fallback(messages, modelos)


def extrair_content_openrouter(resp_json: dict) -> str:
    try:
        return resp_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ValueError("Estrutura inválida da resposta")


def extrair_relato(texto: str, debug: bool = True):
    inicio = time.time()

    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY não encontrada")

    # =========================
    # 1. Entrada do usuário
    # =========================
    texto = (texto or "").strip()[:500]

    # =========================
    # 2. Camada de segurança
    # =========================
    security_result = security_service.analisar_texto(texto)
    texto_para_llm = security_result.sanitized_text

    # Sempre garantir estrutura consistente pro front
    mensagens_seg = []

    if security_result.houve_anonimizacao:
        mensagens_seg.append(
            "Algumas informações sensíveis foram automaticamente anonimizadas."
        )

    if not security_result.is_safe:
        mensagens_seg.append(
            "Detectamos um possível comportamento suspeito na entrada."
        )

    seguranca_info = {
        "houve_anonimizacao": security_result.houve_anonimizacao,
        "risco": not security_result.is_safe,
        "mensagens": mensagens_seg  # <- SEMPRE lista válida
    }

    # =========================
    # 3. Chamada ao LLM
    # =========================
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": texto_para_llm}
    ]

    try:
        resp_json = fazer_request_via_open_router(messages)
        content = extrair_content_openrouter(resp_json)
        content = re.sub(r"//.*", "", content)

        if debug:
            print("\n=== TEXTO ENVIADO AO LLM ===")
            print(texto_para_llm)
            print("============================\n")

            print("\n=== OPENROUTER RAW ===")
            print(content)
            print("======================\n")

    except Exception as e:
        print_tempo(inicio, time.time())
        return {
            "erro": True,
            "mensagem": "Erro ao processar a solicitação.",
            "detalhe": str(e),
            "seguranca": seguranca_info
        }

    # =========================
    # 4. Parse e validação
    # =========================
    data = parse_json(content)

    if not data:
        print_tempo(inicio, time.time())
        return {
            "erro": True,
            "mensagem": "Resposta inválida do modelo.",
            "seguranca": seguranca_info
        }

    # =========================
    # 5. Normalização
    # =========================
    data["tipo_agressao"] = normalizar_tipo_agressao(data.get("tipo_agressao"))
    data["horario"] = normalizar_horario(data.get("horario"))

    # =========================
    # 6. Segurança SEMPRE presente
    # =========================
    data["seguranca"] = seguranca_info

    # (opcional mas recomendado)
    data["texto_anonimizado"] = texto_para_llm

    print_tempo(inicio, time.time())
    return data