# Análise de vendas de eletrônicos — 1º semestre de 2026
Projeto de EDA com **Pandas**, validação de dados com **Pandera** e publicação dos resultados em **SQLite**.

## Indicadores entregues
- Participação percentual de vendas por região;
- Participação percentual por funcionário/vendedor;
- Participação por data: janeiro a junho, **Último trimestre** (abr–jun) e **Último semestre** (jan–jun);
- Quantidade e faturamento de cada item por região e período.

As colunas `pct_transacoes`, `pct_quantidade` e `pct_faturamento` mostram participações percentuais. Nas tabelas por região e funcionário, a base é o semestre inteiro. Em `percentual_vendas_data`, cada mês e janela é comparado ao total do semestre; portanto, os seis meses somam 100%. Em `itens_por_regiao_data`, a base é o próprio período. "Vendas" são tratadas como transações (`venda_id`); a quantidade física está em `quantidade_vendida`.

# Padronização e qualidade de dados
O módulo `src/qualidade.py` é a única fonte das regras de padronização usadas na importação Excel→SQLite e na EDA.

- IDs: remove espaços e converte para maiúsculas;
- textos: remove espaços duplicados e aplica Title Case;
- UF: remove espaços e converte para duas letras maiúsculas; o esquema Pandera bloqueia valores fora de `^[A-Z]{2}$`;
- valores financeiros: conversão tolerante a formatos brasileiro/internacional e arredondamento em 2 casas;
- quantidades: valores não inteiros viram pendência, sem truncamento silencioso;
- `margem_%`: decimal com 4 casas.

`Qualidade_Dados_Pendentes` (na importação) e `qualidade_dados_pendentes` (na análise) listam tabela, campo, número e percentual de valores ausentes após a limpeza. Assim, o Power BI pode exibir e filtrar problemas de qualidade sem interromper a atualização inteira.

Além disso, cada tabela importada recebe `status_pendencia` (`Completo` ou `Pendente`) e `campos_pendentes`. A tabela `Dados_Pendentes` (importação) / `dados_pendentes` (análise) contém exclusivamente registros com problema, uma linha por campo faltante: `tabela_origem`, `linha_origem`, `registro_id`, `campo_pendente` e `status_pendencia`.

# Gerador não interativo para GitHub Actions
Por padrão, execute:
```bash
python src/gerar_planilha.py --mes 6 --ano 2026 --destino data/raw
```

O comando sempre gera dois arquivos determinísticos:
1. `vendas_202606_completo_padronizado.xlsx`: sem dados ausentes ou erros de formato;
2. `vendas_202606_aleatorio_com_erro.xlsx`: contém campos ausentes e textos, moedas e datas propositalmente mal formatados.

Use `--interativo` apenas para o modo manual legado. O workflow em `.github/workflows/gerar-planilhas.yml` executa o modo não interativo e publica os dois arquivos como artefato do Actions.

## Execução
```powershell
# 1. Instale as dependências necessárias
python -m pip install -r requirements.txt

# 2. Transforme a planilha Excel original em um banco de dados SQLite (.db)
python src/transform_xlsx_to_db.py --origem "C:\caminho\sua_planilha_original.xlsx" --destino "C:\caminho\vendas_eletronicos_1S2026.db"

# 3. Execute a análise de dados e gere o banco com os resultados finais
python src/analise.py --origem "C:\caminho\vendas_eletronicos_1S2026.db" --destino "data\resultados\analise_vendas_1S2026.sqlite"
```

## Tabelas geradas no SQLite

| Tabela | Conteúdo |
|---|---|
| `eda_resumo_geral` | Período, transações, itens, faturamento e ticket médio |
| `percentual_vendas_regiao` | Participação de cada região no semestre |
| `percentual_vendas_funcionario` | Participação de cada vendedor no semestre |
| `percentual_vendas_data` | Todos os meses, último trimestre e último semestre |
| `itens_por_regiao_data` | Produtos por região em cada período solicitado |

O script preserva as tabelas do banco de origem ao copiar o arquivo antes de acrescentar a camada analítica.