#!/usr/bin/env python3
"""Aplica a configuracao do servidor proprio no fonte do RustDesk 1.5.1.

Qualquer substituicao que nao encontre exatamente o trecho esperado interrompe o build,
para nunca gerar um cliente apontando para o servidor publico por engano.
"""
import base64
import os
import re
import sys


def fail(message):
    print(f"ERRO: {message}")
    sys.exit(1)


def replace_once(path, old, new, label):
    with open(path, encoding="utf-8", newline="") as source:
        text = source.read()
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperava 1 ocorrencia em {path}, encontrou {count}")
    with open(path, "w", encoding="utf-8", newline="") as target:
        target.write(text.replace(old, new))
    print(f"ok: {label}")


host = os.environ.get("RUSTDESK_HOST", "").strip()
key = os.environ.get("RUSTDESK_KEY", "").strip()

if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
    fail("RUSTDESK_HOST ausente ou invalido")
try:
    decoded_key = base64.b64decode(key, validate=True)
except ValueError:
    fail("RUSTDESK_KEY nao e base64 valido")
if len(decoded_key) != 32:
    fail("RUSTDESK_KEY precisa ser a chave publica ed25519 (32 bytes)")

CONFIG = "libs/hbb_common/src/config.rs"
COMMON = "src/common.rs"

replace_once(
    CONFIG,
    'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
    f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{host}"];',
    "servidor padrao",
)
replace_once(
    CONFIG,
    'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
    f'pub const RS_PUB_KEY: &str = "{key}";',
    "chave publica",
)
# Faz o cliente nao se considerar em servidor publico e deriva a API do host proprio.
replace_once(
    CONFIG,
    'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new("".to_owned());',
    f'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new("{host}".to_owned());',
    "servidor de producao",
)
replace_once(
    COMMON,
    '"https://admin.rustdesk.com".to_owned()',
    f'"http://{host}:21114".to_owned()',
    "fallback da API",
)
# Sem URL de atualizacao, o cliente nao avisa nem baixa a versao oficial.
replace_once(
    COMMON,
    "pub async fn do_check_software_update() -> hbb_common::ResultType<()> {",
    "pub async fn do_check_software_update() -> hbb_common::ResultType<()> { "
    "if true { return Ok(()); }",
    "atualizacao automatica desligada",
)
print("Patch aplicado.")
