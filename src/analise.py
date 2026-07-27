"""Gera uma camada analítica SQLite para vendas de eletrônicos."""
from __future__ import annotations
import argparse
import shutil
import sqlite3
import sys
from pathlib import Path
import pandas as pd
from schemas import VendasSchema, VendedoresSchema
from qualidade import auditoria_pendencias, marcar_pendencias, padronizar

JANELAS = {
    "2026-01": ("2026-01-01", "2026-01-31"),
    "2026-02": ("2026-02-01", "2026-02-28"),
    "2026-03": ("2026-03-01", "2026-03-31"),
    "2026-04": ("2026-04-01", "2026-04-30"),
    "2026-05": ("2026-05-01", "2026-05-31"),
    "2026-06": ("2026-06-01", "2026-06-30"),
    "Último trimestre": ("2026-04-01", "2026-06-30"),
    "Último semestre": ("2026-01-01", "2026-06-30"),
}

def percentual(df: pd.DataFrame, grupo: list[str], referencia: pd.DataFrame | None = None) -> pd.DataFrame:
    """Agrupa vendas e calcula participações por quantidade e faturamento."""
    agregacoes = dict(transacoes=("venda_id", "nunique"),
                      quantidade_vendida=("quantidade", "sum"),
                      valor_total_vendido=("valor_total", "sum"))
    if grupo:
        resultado = df.groupby(grupo, as_index=False).agg(**agregacoes)
    else:
        resultado = pd.DataFrame([{nome: df[coluna].nunique() if func == "nunique" else df[coluna].sum()
                                   for nome, (coluna, func) in agregacoes.items()}])
    base = df if referencia is None else referencia
    totais = {"transacoes": base["venda_id"].nunique(),
              "quantidade_vendida": base["quantidade"].sum(),
              "valor_total_vendido": base["valor_total"].sum()}
    resultado["pct_transacoes"] = resultado["transacoes"].div(totais["transacoes"]).mul(100)
    resultado["pct_quantidade"] = resultado["quantidade_vendida"].div(totais["quantidade_vendida"]).mul(100)
    resultado["pct_faturamento"] = resultado["valor_total_vendido"].div(totais["valor_total_vendido"]).mul(100)
    return resultado.round({"valor_total_vendido": 2, "pct_transacoes": 2,
                             "pct_quantidade": 2, "pct_faturamento": 2})

def por_periodo(vendas: pd.DataFrame, dimensoes: list[str], referencia: pd.DataFrame | None = None) -> pd.DataFrame:
    partes = []
    for periodo, (inicio, fim) in JANELAS.items():
        fatia = vendas.loc[vendas["data"].between(inicio, fim)].copy()
        tabela = percentual(fatia, dimensoes, referencia)
        tabela.insert(0, "periodo", periodo)
        tabela.insert(1, "inicio_periodo", pd.Timestamp(inicio))
        tabela.insert(2, "fim_periodo", pd.Timestamp(fim))
        partes.append(tabela)
    return pd.concat(partes, ignore_index=True)

def main(origem: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)

    with sqlite3.connect(origem) as conexao:
        vendas = padronizar(pd.read_sql_query("SELECT * FROM Vendas", conexao))
        vendedores = padronizar(pd.read_sql_query("SELECT * FROM Vendedores", conexao))

    vendas = VendasSchema.validate(vendas)
    vendedores = VendedoresSchema.validate(vendedores)
    pendencias = pd.concat([auditoria_pendencias("Vendas", vendas), auditoria_pendencias("Vendedores", vendedores)], ignore_index=True)
    vendas = vendas.merge(vendedores[["vendedor_id", "nome_vendedor"]], on="vendedor_id", how="left", validate="many_to_one")
    pendencias = pd.concat([pendencias, auditoria_pendencias("Vendas", vendas, ["nome_vendedor"])], ignore_index=True)
    vendas_padronizadas, detalhes_vendas = marcar_pendencias("Vendas", vendas)
    vendedores_padronizados, detalhes_vendedores = marcar_pendencias("Vendedores", vendedores)
    detalhes_pendentes = pd.concat([detalhes_vendas, detalhes_vendedores], ignore_index=True)

    tabelas = {
        "eda_resumo_geral": pd.DataFrame([{
            "data_inicial": vendas["data"].min(), "data_final": vendas["data"].max(),
            "transacoes": vendas["venda_id"].nunique(), "quantidade_vendida": vendas["quantidade"].sum(),
            "valor_total_vendido": vendas["valor_total"].sum(),
            "ticket_medio": vendas["valor_total"].sum() / vendas["venda_id"].nunique(),
        }]),
        "percentual_vendas_regiao": percentual(vendas, ["regiao"]),
        "percentual_vendas_funcionario": percentual(vendas, ["vendedor_id", "nome_vendedor", "regiao"]),
        "percentual_vendas_data": por_periodo(vendas, [], referencia=vendas),
        "itens_por_regiao_data": por_periodo(vendas, ["regiao", "produto_id", "produto"]),
        "qualidade_dados_pendentes": pendencias,
        "dados_pendentes": detalhes_pendentes,
        "vendas_padronizadas": vendas_padronizadas,
        "vendedores_padronizados": vendedores_padronizados,
    }
    with sqlite3.connect(destino) as conexao:
        for nome, tabela in tabelas.items():
            tabela.to_sql(nome, conexao, if_exists="replace", index=False)
        conexao.execute("CREATE INDEX IF NOT EXISTS idx_itens_periodo ON itens_por_regiao_data(periodo, regiao)")
        conexao.execute("CREATE INDEX IF NOT EXISTS idx_funcionario_regiao ON percentual_vendas_funcionario(regiao)")

    print(f"Análise concluída: {destino}")
    print(f"{vendas['venda_id'].nunique()} transações | R$ {vendas['valor_total'].sum():,.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--origem", type=Path, required=True, help="Banco SQLite de origem")
    parser.add_argument("--destino", type=Path, required=True, help="Banco SQLite analítico")
    args = parser.parse_args()
    try:
        main(args.origem, args.destino)
    except Exception as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        raise
