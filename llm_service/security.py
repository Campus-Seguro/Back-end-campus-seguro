import re
from dataclasses import dataclass, field
from typing import List
from .personal_information import anonimizar_texto


@dataclass
class SecurityResult:
    is_safe: bool = True
    flags: List[str] = field(default_factory=list)
    sanitized_text: str = ""
    houve_anonimizacao: bool = False


class SecurityService:

    def analisar_texto(self, texto: str) -> SecurityResult:
        result = SecurityResult()

        if self.detectar_prompt_injection(texto):
            result.flags.append("prompt_injection")
            result.is_safe = False

        texto_anonimizado = anonimizar_texto(texto)
        result.sanitized_text = texto_anonimizado

        if texto != texto_anonimizado:
            result.houve_anonimizacao = True
            result.flags.append("dados_sensiveis_anonimizados")

        return result


    def detectar_prompt_injection(self, texto: str) -> bool:
        padroes = [
            "ignore",
            "ignore todas as instruções",
            "responda apenas",
            "não siga",
            "system prompt",
            "finja que"
        ]

        texto_lower = texto.lower()
        return any(p in texto_lower for p in padroes)