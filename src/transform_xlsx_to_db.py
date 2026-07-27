"""Importa Excel, padroniza campos e publica um SQLite auditável."""
import argparse
import sqlite3
import pandas as pd
from qualidade import auditoria_pendencias, padronizar

def main():
    parser = argparse.ArgumentParser(description="Transforma planilha Excel em SQLite padronizado.")
    parser.add_argument("--origem", required=True, help="Arquivo Excel (.xlsx)")
    parser.add_argument("--destino", required=True, help="Banco SQLite de destino (.db)")
    args = parser.parse_args()
    auditorias = []
    with sqlite3.connect(args.destino) as conn:
        for aba in pd.ExcelFile(args.origem).sheet_names:
            dados = padronizar(pd.read_excel(args.origem, sheet_name=aba))
            auditorias.append(auditoria_pendencias(aba, dados))
            if "data" in dados: dados["data"] = dados["data"].dt.strftime("%Y-%m-%d")
            dados.to_sql(aba, conn, if_exists="replace", index=False)
        pd.concat(auditorias, ignore_index=True).to_sql("Qualidade_Dados_Pendentes", conn, if_exists="replace", index=False)
    print(f"Banco padronizado criado: {args.destino}")

if __name__ == "__main__": main()
