"""Senha criptografada (PBKDF2-SHA256) e controle de tentativas."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time

ITERACOES = 600_000


def gerar_hash(senha: str, iteracoes: int = ITERACOES) -> str:
    sal = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), iteracoes)
    return f"pbkdf2_sha256${iteracoes}${sal}${dk.hex()}"


def conferir_senha(senha: str, hash_salvo: str) -> bool:
    try:
        algoritmo, iteracoes, sal, esperado = hash_salvo.strip().split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), int(iteracoes))
        return hmac.compare_digest(dk.hex(), esperado)
    except (ValueError, AttributeError):
        return False


class Limitador:
    """Conta erros de senha de TODOS os acessos (protege contra tentativa e erro)."""

    def __init__(self, maximo: int, janela_min: int, bloqueio_min: int):
        self.maximo = maximo
        self.janela = janela_min * 60
        self.bloqueio = bloqueio_min * 60
        self._falhas = []
        self._bloqueado_ate = 0.0
        self._trava = threading.Lock()

    def segundos_bloqueado(self) -> int:
        with self._trava:
            return max(0, int(self._bloqueado_ate - time.time()))

    def registrar_falha(self):
        agora = time.time()
        with self._trava:
            self._falhas = [t for t in self._falhas if agora - t < self.janela] + [agora]
            if len(self._falhas) >= self.maximo:
                self._bloqueado_ate = agora + self.bloqueio
                self._falhas = []
