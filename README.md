# Enel OCR Pipeline (Python)
![Author](https://img.shields.io/badge/author-Emenson%20Lima%20Germano-0A66C2)
![License](https://img.shields.io/badge/license-MIT-0A66C2)

Pipeline de OCR para faturas Enel em PDF, extraindo campos estruturados
(dados cadastrais, leituras, tributos, itens de fatura) via recortes por
coordenadas. O projeto entrega JSON pronto para integracao via API.

## Destaques
- OCR focado no layout Enel (pagina 1)
- Saida JSON pronta para consumo
- Recortes por coordenadas para reduzir ruido
- API HTTP simples (Flask + Gunicorn)
- Deploy rapido com Docker Compose

## Requisitos
- Docker + Docker Compose (recomendado)
- Ou Python 3.11

## Execucao rapida (Docker)
```bash
docker compose up --build
```
A primeira execucao baixa os modelos do PaddleOCR e pode demorar alguns minutos.
No `docker-compose.yml`, os modelos ficam em volume `paddleocr-data`.

Teste rapido:
```bash
curl -X POST http://localhost:8000/invoice \
  -H "Content-Type: application/pdf" \
  --data-binary @sua_fatura.pdf
```

## Execucao local
```bash
pip install -r requirements.txt
python -m enel_ocr.api
```

Rodar pipeline direto (sem API):
```bash
python scripts/run_pipeline.py
```
Ajuste o caminho do PDF em `scripts/run_pipeline.py` antes de executar.

## API
POST `/invoice` (content-type: application/pdf) -> JSON no formato de `Invoice`.
Decimais sao serializados como string.

Exemplo de resposta (resumo):
```json
{
  "customer_name": "NOME DO CLIENTE",
  "installation_number": "1234567890",
  "billing_period": "01/2024",
  "amount_due": "124.53",
  "reading_dates": {
    "previous_reading": "10-01-2024",
    "current_reading": "09-02-2024",
    "reading_days": 30,
    "next_reading": "10-03-2024"
  },
  "invoice_items": [],
  "tax_info": {
    "invoice_number": "123456",
    "access_key": "..."
  }
}
```

## Estrutura de dados (resumo)
- Dados do cliente: nome, CPF/CNPJ, numero do cliente, numero da instalacao.
- Fatura: periodo, vencimento, valor a pagar, classificacao, tipo de fornecimento.
- Leituras: anterior, atual, proxima, dias de leitura.
- Itens: lista detalhada de faturamento (quantidade, preco, tributos, etc).
- Medicao: leituras e consumo por medidor.
- Tributos: tabela de base, aliquota e valor + info da NF (chave, CFOP).
- Mensagem importante e responsavel pela iluminacao.

## Configuracao
- `WEB_CONCURRENCY`: numero de workers do Gunicorn (padrao: numero de CPUs).
- `PADDLEOCR_HOME`: diretorio de cache de modelos (padrao `~/.paddleocr`).
- `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`:
  limite de threads do backend numerico (opcional).

## Persistencia de modelos (Docker)
- Volume `paddleocr-data` guarda os downloads do PaddleOCR.
- Para limpar o cache: `docker compose down -v`.

## Observacoes e limitacoes
- Layout baseado em coordenadas fixas; se o template mudar, ajuste
  `enel_ocr/coords.py`.
- Processa apenas a primeira pagina.
- Qualidade de OCR depende da resolucao e do scanner.

## Licenca
MIT. Veja `LICENSE`.

## Autor
- Emenson Lima Germano
- emenson.germano@gmail.com
- +55 85 98154-4626
