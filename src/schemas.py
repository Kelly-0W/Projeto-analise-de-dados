"""Esquemas Pandera aplicados depois da padronização."""
import pandera.pandas as pa
from pandera.typing import Series

class VendasSchema(pa.DataFrameModel):
    venda_id: Series[str] = pa.Field(nullable=True)
    data: Series[pa.DateTime] = pa.Field(nullable=True)
    vendedor_id: Series[str] = pa.Field(nullable=True)
    loja_id: Series[str] = pa.Field(nullable=True)
    regiao: Series[str] = pa.Field(nullable=True)
    produto_id: Series[str] = pa.Field(nullable=True)
    produto: Series[str] = pa.Field(nullable=True)
    quantidade: Series[int] = pa.Field(nullable=True, ge=0)
    preco_unitario: Series[float] = pa.Field(nullable=True, ge=0)
    valor_total: Series[float] = pa.Field(nullable=True, ge=0)
    custo_unitario: Series[float] = pa.Field(nullable=True, ge=0)
    custo_total: Series[float] = pa.Field(nullable=True, ge=0)
    class Config: strict = True; coerce = True

class VendedoresSchema(pa.DataFrameModel):
    vendedor_id: Series[str] = pa.Field(nullable=True)
    nome_vendedor: Series[str] = pa.Field(nullable=True)
    loja_id: Series[str] = pa.Field(nullable=True)
    nome_loja: Series[str] = pa.Field(nullable=True)
    regiao: Series[str] = pa.Field(nullable=True)
    class Config: strict = True; coerce = True

class LojasSchema(pa.DataFrameModel):
    loja_id: Series[str] = pa.Field(nullable=True)
    nome_loja: Series[str] = pa.Field(nullable=True)
    cidade: Series[str] = pa.Field(nullable=True)
    estado: Series[str] = pa.Field(nullable=True, str_matches=r"^[A-Z]{2}$")
    regiao: Series[str] = pa.Field(nullable=True)
    class Config: strict = True; coerce = True

class ProdutosSchema(pa.DataFrameModel):
    produto_id: Series[str] = pa.Field(nullable=True)
    categoria: Series[str] = pa.Field(nullable=True)
    modelo: Series[str] = pa.Field(nullable=True)
    preco_unitario: Series[float] = pa.Field(nullable=True, ge=0)
    custo_unitario: Series[float] = pa.Field(nullable=True, ge=0)
    margem_unitaria: Series[float] = pa.Field(nullable=True)
    margem_percentual: Series[float] = pa.Field(alias="margem_%", nullable=True)
    class Config: strict = True; coerce = True
