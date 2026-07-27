"""Padronização e auditoria de qualidade dos dados de vendas."""
from collections.abc import Iterable
import pandas as pd

IDS = {"loja_id", "vendedor_id", "produto_id", "venda_id"}
TEXTOS = {"nome_loja", "cidade", "regiao", "nome_vendedor", "categoria", "modelo", "produto"}
FINANCEIROS = {"preco_unitario", "custo_unitario", "valor_total", "custo_total", "margem_unitaria", "valor_total_vendido", "ticket_medio", "custo_total_alocacao", "lucro_total"}
INTEIROS = {"quantidade", "numero_de_vendas", "quantidade_vendida"}
PERCENTUAIS = {"margem_%"}

def _texto(serie, title=False):
    resultado = serie.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    resultado = resultado.mask(resultado.eq(""), pd.NA)
    return resultado.str.title() if title else resultado

def _numero(serie):
    texto = _texto(serie).str.replace(r"[^0-9,.-]", "", regex=True)
    ambos = texto.str.contains(",", na=False) & texto.str.contains(r"\.", na=False)
    virgula_decimal = ambos & texto.str.rfind(",").gt(texto.str.rfind("."))
    texto = texto.where(~virgula_decimal, texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    texto = texto.where(~(ambos & ~virgula_decimal), texto.str.replace(",", "", regex=False))
    texto = texto.where(~(~ambos & texto.str.contains(",", na=False)), texto.str.replace(",", ".", regex=False))
    return pd.to_numeric(texto, errors="coerce")

def padronizar(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    for coluna in set(resultado.columns) & IDS: resultado[coluna] = _texto(resultado[coluna]).str.upper()
    for coluna in set(resultado.columns) & TEXTOS: resultado[coluna] = _texto(resultado[coluna], title=True)
    if "estado" in resultado: resultado["estado"] = _texto(resultado["estado"]).str.upper()
    for coluna in set(resultado.columns) & FINANCEIROS: resultado[coluna] = _numero(resultado[coluna]).round(2)
    for coluna in set(resultado.columns) & PERCENTUAIS: resultado[coluna] = _numero(resultado[coluna]).round(4)
    for coluna in set(resultado.columns) & INTEIROS:
        numero = _numero(resultado[coluna])
        resultado[coluna] = numero.where(numero.isna() | numero.mod(1).eq(0)).astype("Int64")
    if "data" in resultado: resultado["data"] = pd.to_datetime(resultado["data"], errors="coerce")
    return resultado

def auditoria_pendencias(tabela: str, df: pd.DataFrame, obrigatorias: Iterable[str] | None = None) -> pd.DataFrame:
    campos = list(obrigatorias) if obrigatorias else list(df.columns)
    linhas = []
    for campo in campos:
        if campo in df and (pendentes := int(df[campo].isna().sum())):
            linhas.append({"tabela_origem": tabela, "campo": campo, "valores_pendentes": pendentes, "pct_pendente": round(pendentes / len(df) * 100, 2) if len(df) else 0.0})
    return pd.DataFrame(linhas, columns=["tabela_origem", "campo", "valores_pendentes", "pct_pendente"])
