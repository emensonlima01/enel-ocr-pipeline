# -*- coding: utf-8 -*-
from __future__ import annotations

from .coords import build_regions
from .detector import detect_layout
from .mappers import amount_due as amount_due_mapper
from .mappers import billing_period as billing_period_mapper
from .mappers import classification_consumer_unit
from .mappers import current_reading as current_reading_mapper
from .mappers import customer_number as customer_number_mapper
from .mappers import due_date as due_date_mapper
from .mappers import important_message as important_message_mapper
from .mappers import installation_number as installation_number_mapper
from .mappers import invoice_items
from .mappers import meter_items
from .mappers import next_reading as next_reading_mapper
from .mappers import personal_data as personal_data_mapper
from .mappers import reading_days as reading_days_mapper
from .mappers import lighting_responsible as lighting_responsible_mapper
from .mappers import supply_type as supply_type_mapper
from .mappers import tariff_flags
from .mappers import credit_info as credit_info_mapper
from .mappers import tax_info
from .mappers import tax_items
from .mappers import previous_reading as previous_reading_mapper
from . import models
from .models import Invoice
from .ocr.crop import ImageCropper
from .ocr.engine import run_ocr
from .ocr.pdf import pdf_page_to_image_bytes


def run_pipeline(pdf_bytes: bytes, ocr) -> Invoice:
    image_bytes = pdf_page_to_image_bytes(pdf_bytes, page_number=1)
    cropper = ImageCropper(image_bytes)
    layout_id = detect_layout(ocr, cropper)
    regions = build_regions(layout_id)

    classification_result = ""
    supply_type = ""
    installation_number = ""
    customer_number = ""
    billing_period = ""
    due_date = ""
    amount_due = ""
    current_reading = ""
    previous_reading = ""
    next_reading = ""
    reading_days = 0
    tax_info_result = None
    invoice_items_result = []
    meter_items_result = []
    tax_items_result = []
    customer_name = ""
    customer_tax_number = ""
    lighting_responsible = ""
    important_message = ""
    tariff_flag_periods = []
    credit_info = models.CreditInfo(
        injected_hfp_kwh=0.0,
        used_kwh=0.0,
        updated_kwh=0.0,
        expiring_kwh=0.0,
    )

    def _handle_descricao_faturamento(texts, boxes) -> None:
        nonlocal invoice_items_result, meter_items_result
        invoice_items_result = invoice_items.map(texts, boxes)
        meter_items_result = meter_items.map(texts, boxes)

    def _handle_tributos(texts, boxes) -> None:
        nonlocal tax_items_result
        tax_items_result = tax_items.map(texts, boxes)

    def _handle_classificacao_unidade(texts, _boxes) -> None:
        nonlocal classification_result
        classification_result = classification_consumer_unit.map(texts)

    def _handle_tipo_fornecimento(texts, _boxes) -> None:
        nonlocal supply_type
        supply_type = supply_type_mapper.map(texts)

    def _handle_numero_instalacao(texts, _boxes) -> None:
        nonlocal installation_number
        installation_number = installation_number_mapper.map(texts, layout_id=layout_id)

    def _handle_numero_cliente(texts, _boxes) -> None:
        nonlocal customer_number
        customer_number = customer_number_mapper.map(texts, layout_id=layout_id)

    def _handle_periodo_faturamento(texts, _boxes) -> None:
        nonlocal billing_period
        billing_period = billing_period_mapper.map(texts)

    def _handle_data_vencimento(texts, _boxes) -> None:
        nonlocal due_date
        due_date = due_date_mapper.map(texts)

    def _handle_valor_pagar(texts, _boxes) -> None:
        nonlocal amount_due
        amount_due = amount_due_mapper.map(texts)

    def _handle_leitura_atual(texts, _boxes) -> None:
        nonlocal current_reading
        current_reading = current_reading_mapper.map(texts)

    def _handle_leitura_anterior(texts, _boxes) -> None:
        nonlocal previous_reading
        previous_reading = previous_reading_mapper.map(texts)

    def _handle_proxima_leitura(texts, _boxes) -> None:
        nonlocal next_reading
        next_reading = next_reading_mapper.map(texts)

    def _handle_dias_leitura(texts, _boxes) -> None:
        nonlocal reading_days
        reading_days = reading_days_mapper.map(texts)

    def _handle_dados_pessoais(texts, _boxes) -> None:
        nonlocal customer_name, customer_tax_number
        customer_name, customer_tax_number = personal_data_mapper.map(texts)

    def _handle_responsavel_iluminacao(texts, _boxes) -> None:
        nonlocal lighting_responsible
        lighting_responsible = lighting_responsible_mapper.map(texts)

    def _handle_informacoes_tributarias(texts, boxes) -> None:
        nonlocal tax_info_result
        tax_info_result = tax_info.map(texts, boxes)

    def _handle_mensagem_importante(texts, _boxes) -> None:
        nonlocal important_message
        important_message = important_message_mapper.map(texts)

    handlers = {
        "DESCRICAO_FATURAMENTO": _handle_descricao_faturamento,
        "TRIBUTOS": _handle_tributos,
        "CLASSIFICACAO_UNIDADE_CONSUMIDORA": _handle_classificacao_unidade,
        "TIPO_FORNECIMENTO": _handle_tipo_fornecimento,
        "NUMERO_INSTALACAO": _handle_numero_instalacao,
        "NUMERO_CLIENTE": _handle_numero_cliente,
        "PERIODO_FATURAMENTO": _handle_periodo_faturamento,
        "DATA_VENCIMENTO": _handle_data_vencimento,
        "VALOR_PAGAR": _handle_valor_pagar,
        "LEITURA_ATUAL": _handle_leitura_atual,
        "LEITURA_ANTERIOR": _handle_leitura_anterior,
        "PROXIMA_LEITURA": _handle_proxima_leitura,
        "DIAS_LEITURA": _handle_dias_leitura,
        "DADOS_PESSOAIS": _handle_dados_pessoais,
        "RESPONSAVEL_PELA_ILUMINACAO": _handle_responsavel_iluminacao,
        "INFORMACOES_TRIBUTARIAS": _handle_informacoes_tributarias,
        "MENSAGEM_IMPORTANTE": _handle_mensagem_importante,
    }

    for region in regions:
        handler = handlers.get(region.description)
        if not handler:
            continue
        coords = (region.x, region.y, region.width, region.height)
        image_np = cropper.crop_ndarray(coords)
        texts, boxes, _scores = run_ocr(ocr, image_np)
        handler(texts, boxes)

    if important_message:
        tariff_flag_periods = tariff_flags.map(important_message)
        credit_info = credit_info_mapper.map(important_message)

    base_tax_info = tax_info_result or tax_info.TaxInfo(
        invoice_number="",
        invoice_issue_date="",
        access_key="",
        cfop="",
        presentation_date="",
        tax_items=[],
    )
    if tax_items_result:
        base_tax_info = tax_info.TaxInfo(
            invoice_number=base_tax_info.invoice_number,
            invoice_issue_date=base_tax_info.invoice_issue_date,
            access_key=base_tax_info.access_key,
            cfop=base_tax_info.cfop,
            presentation_date=base_tax_info.presentation_date,
            tax_items=tax_items_result,
        )
    return Invoice(
        invoice_items=invoice_items_result,
        meter_items=meter_items_result,
        classification_consumer_unit=classification_result,
        supply_type=supply_type,
        installation_number=installation_number,
        customer_number=customer_number,
        customer_name=customer_name,
        tax_number=customer_tax_number,
        lighting_responsible=lighting_responsible,
        billing_period=billing_period,
        due_date=due_date,
        amount_due=amount_due,
        reading_dates=models.ReadingDates(
            previous_reading=previous_reading,
            current_reading=current_reading,
            reading_days=reading_days,
            next_reading=next_reading,
        ),
        tax_info=base_tax_info,
        important_message=important_message,
        tariff_flag_periods=tariff_flag_periods,
        credit_info=credit_info,
    )
