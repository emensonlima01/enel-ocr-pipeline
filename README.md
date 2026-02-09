# Enel OCR Pipeline (Python)

Pipeline de OCR para faturas Enel em PDF. Extrai campos estruturados via recortes por coordenadas e mapeadores especializados, entregando JSON pronto para integração via API.

## Visão geral
- OCR focado no layout Enel (página 1).
- Recortes por coordenadas para reduzir ruído.
- Detecção automática de layout (v1/v2) via cabeçalho.
- Saída estruturada com tipagem via `dataclasses`.
- API HTTP simples (Flask + Gunicorn).
- Deploy rápido com Docker Compose.

## Fluxo do pipeline
1. PDF -> imagem (PyMuPDF) da página 1 com 300 DPI.
2. Detecção de layout usando `enel_ocr/layouts/headers.json`.
3. Recorte de regiões definidas em `enel_ocr/layouts/v1.json` ou `v2.json`.
4. OCR com PaddleOCR (lang=pt, PP-OCRv3).
5. Mapeadores convertem textos em estruturas tipadas.
6. Resposta JSON pronta para consumo na API.

## Estrutura do projeto
- `enel_ocr/` pacote principal.
- `enel_ocr/api.py` API Flask + serialização.
- `enel_ocr/pipeline.py` orquestração do OCR.
- `enel_ocr/ocr/` conversão PDF->imagem, recorte e engine OCR.
- `enel_ocr/mappers/` extração e parsing dos campos.
- `enel_ocr/layouts/` coordenadas e regras de detecção.
- `scripts/run_pipeline.py` execução local do pipeline.
- `Dockerfile` e `docker-compose.yml` para deploy.

## Requisitos
- Docker + Docker Compose (recomendado) ou Python 3.11.
- Dependências de sistema (Linux) incluídas no Docker:
  - `libgl1`, `libglib2.0-0`, `libgomp1`, `libopenblas0`.

## Execução rápida (Docker)
```bash
docker compose up --build
```

Primeira execução: download dos modelos do PaddleOCR pode demorar alguns minutos. No `docker-compose.yml`, os modelos ficam no volume `paddleocr-data`.

Teste rápido:
```bash
curl -X POST http://localhost:8000/invoice \
  -H "Content-Type: application/pdf" \
  --data-binary @sua_fatura.pdf
```

## Execução local (Python)
```bash
pip install -r requirements.txt
python -m enel_ocr.api
```

Rodar o pipeline direto (sem API):
```bash
python scripts/run_pipeline.py
```
Ajuste o caminho do PDF em `scripts/run_pipeline.py` antes de executar.

## API
### POST `/invoice`
- Content-Type: `application/pdf`
- Corpo: bytes do PDF
- Respostas:
  - `200` JSON com a estrutura `Invoice`
  - `400` erro de validação (content-type, body vazio ou PDF inválido)

Exemplo de resposta (resumo):
```json
{
  "customer_name": "NOME DO CLIENTE",
  "installation_number": "1234567890",
  "billing_period": "01-2024",
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

## Modelo de dados
A API devolve JSON. Ao usar `run_pipeline` diretamente, campos numéricos são `Decimal` (exceto `CreditInfo`, que usa `float`).

### Invoice
- `invoice_items`: lista de `InvoiceItem`
- `meter_items`: lista de `MeterItem`
- `classification_consumer_unit`: string
- `supply_type`: string
- `installation_number`: string
- `customer_number`: string
- `customer_name`: string
- `tax_number`: string
- `lighting_responsible`: string
- `billing_period`: string (ex: `MM-YYYY`)
- `due_date`: string (ex: `DD-MM-YYYY`)
- `amount_due`: decimal (na API vem como string)
- `reading_dates`: `ReadingDates`
- `tax_info`: `TaxInfo`
- `important_message`: string
- `tariff_flag_periods`: lista de `TariffFlagPeriod`
- `credit_info`: `CreditInfo`

### ReadingDates
- `previous_reading`: string (data)
- `current_reading`: string (data)
- `reading_days`: inteiro
- `next_reading`: string (data)

### InvoiceItem
- `description`: string
- `unit`: string
- `quantity`: decimal
- `unit_price_with_taxes`: decimal
- `amount`: decimal
- `pis_cofins`: decimal
- `icms_tax_base`: decimal
- `icms_rate`: decimal
- `icms_amount`: decimal
- `unit_rate`: decimal

### MeterItem
- `meter_number`: string
- `segment_time`: string
- `reading_date_1`: string
- `reading_1`: decimal
- `reading_date_2`: string
- `reading_2`: decimal
- `multiplier_factor`: decimal
- `consumption_kwh`: decimal
- `number_of_days`: inteiro

### TaxInfo
- `invoice_number`: string
- `invoice_issue_date`: string
- `access_key`: string
- `cfop`: string
- `presentation_date`: string
- `tax_items`: lista de `TaxItem`

### TaxItem
- `tax_name`: string
- `base_calc`: decimal
- `rate`: decimal
- `amount`: decimal

### TariffFlagPeriod
- `flag`: string (VERDE/AMARELA/VERMELHA)
- `start_date`: string (DD-MM)
- `end_date`: string (DD-MM)

### CreditInfo
- `injected_hfp_kwh`: float
- `used_kwh`: float
- `updated_kwh`: float
- `expiring_kwh`: float

## Layouts e coordenadas
- Os recortes são definidos em `enel_ocr/layouts/v1.json` e `v2.json`.
- A detecção de layout usa `enel_ocr/layouts/headers.json` com um recorte de cabeçalho e palavras-âncora.
- As coordenadas são em pixels para imagem com 300 DPI (ver `DEFAULT_DPI`).
- Se mudar o DPI, ajuste as coordenadas.
- No layout `v2`, `NUMERO_INSTALACAO` e `NUMERO_CLIENTE` usam a mesma região, e os mappers separam os valores.

## Configuração
- `WEB_CONCURRENCY`: número de workers do Gunicorn (padrão: CPUs).
- `WEB_THREADS`: número de threads por worker (padrão: 1).
- `OCR_LOCK`: `1` (padrão) para serializar OCR por worker, `0` para desativar.
- `PADDLEOCR_HOME`: diretório de cache de modelos (padrão `~/.paddleocr`).
- `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`: limite de threads do backend numérico.

## Observações e limitações
- Layout baseado em coordenadas fixas; se o template mudar, ajuste os JSONs.
- Processa apenas a primeira página do PDF.
- Qualidade de OCR depende da resolução do PDF/scan.

## Licença
MIT. Veja `LICENSE` e `NOTICE`.

## Autor
- Emenson Lima Germano
- emenson.germano@gmail.com
- +55 85 98154-4626
