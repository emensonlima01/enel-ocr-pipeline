# -*- coding: ascii -*-
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    description: str
    x: int
    y: int
    width: int
    height: int


def build_regions() -> list[Coordinates]:
    return [
        Coordinates(
            description="CLASSIFICACAO_UNIDADE_CONSUMIDORA",
            x=178,
            y=328,
            width=639,
            height=68,
        ),
        Coordinates(
            description="TIPO_FORNECIMENTO",
            x=827,
            y=329,
            width=304,
            height=63,
        ),
        Coordinates(
            description="NUMERO_INSTALACAO",
            x=826,
            y=491,
            width=312,
            height=52,
        ),
        Coordinates(
            description="NUMERO_CLIENTE",
            x=826,
            y=596,
            width=317,
            height=70,
        ),
        Coordinates(
            description="PERIODO_FATURAMENTO",
            x=184,
            y=719,
            width=248,
            height=63,
        ),
        Coordinates(
            description="DATA_VENCIMENTO",
            x=431,
            y=713,
            width=299,
            height=71,
        ),
        Coordinates(
            description="VALOR_PAGAR",
            x=732,
            y=718,
            width=408,
            height=63,
        ),
        Coordinates(
            description="LEITURA_ATUAL",
            x=1599,
            y=325,
            width=230,
            height=74,
        ),
        Coordinates(
            description="LEITURA_ANTERIOR",
            x=1312,
            y=324,
            width=284,
            height=76,
        ),
        Coordinates(
            description="PROXIMA_LEITURA",
            x=2021,
            y=324,
            width=279,
            height=72,
        ),
        Coordinates(
            description="DIAS_LEITURA",
            x=1835,
            y=328,
            width=183,
            height=68,
        ),
        Coordinates(
            description="DADOS_PESSOAIS",
            x=165,
            y=404,
            width=659,
            height=264,
        ),
        Coordinates(
            description="RESPONSAVEL_PELA_ILUMINACAO",
            x=175,
            y=2733,
            width=967,
            height=81,
        ),
        Coordinates(
            description="INFORMACOES_TRIBUTARIAS",
            x=1408,
            y=452,
            width=926,
            height=319,
        ),
        Coordinates(
            description="MENSAGEM_IMPORTANTE",
            x=62,
            y=833,
            width=2380,
            height=421,
        ),
        Coordinates(
            description="DESCRICAO_FATURAMENTO",
            x=11,
            y=1314,
            width=1452,
            height=962,
        ),
        Coordinates(
            description="TRIBUTOS",
            x=1433,
            y=1255,
            width=445,
            height=529,
        ),
    ]
