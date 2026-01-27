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
    coords = [(region.x, region.y, region.width, region.height) for region in regions]
    region_images = cropper.crop_many_ndarray(coords)
    for region, image_np in zip(regions, region_images):
        if region.description == "DESCRICAO_FATURAMENTO":
            texts, boxes, _scores = run_ocr(ocr, image_np)
            invoice_items_result = invoice_items.map(texts, boxes)
            meter_items_result = meter_items.map(texts, boxes)
        elif region.description == "TRIBUTOS":
            texts, boxes, _scores = run_ocr(ocr, image_np)
            tax_items_result = tax_items.map(texts, boxes)
        elif region.description == "CLASSIFICACAO_UNIDADE_CONSUMIDORA":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            classification_result = classification_consumer_unit.map(texts)
        elif region.description == "TIPO_FORNECIMENTO":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            supply_type = supply_type_mapper.map(texts)
        elif region.description == "NUMERO_INSTALACAO":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            installation_number = installation_number_mapper.map(texts, layout_id=layout_id)
        elif region.description == "NUMERO_CLIENTE":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            customer_number = customer_number_mapper.map(texts, layout_id=layout_id)
        elif region.description == "PERIODO_FATURAMENTO":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            billing_period = billing_period_mapper.map(texts)
        elif region.description == "DATA_VENCIMENTO":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            due_date = due_date_mapper.map(texts)
        elif region.description == "VALOR_PAGAR":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            amount_due = amount_due_mapper.map(texts)
        elif region.description == "LEITURA_ATUAL":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            current_reading = current_reading_mapper.map(texts)
        elif region.description == "LEITURA_ANTERIOR":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            previous_reading = previous_reading_mapper.map(texts)
        elif region.description == "PROXIMA_LEITURA":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            next_reading = next_reading_mapper.map(texts)
        elif region.description == "DIAS_LEITURA":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            reading_days = reading_days_mapper.map(texts)
        elif region.description == "DADOS_PESSOAIS":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            customer_name, customer_tax_number = personal_data_mapper.map(texts)
        elif region.description == "RESPONSAVEL_PELA_ILUMINACAO":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            lighting_responsible = lighting_responsible_mapper.map(texts)
        elif region.description == "INFORMACOES_TRIBUTARIAS":
            texts, boxes, _scores = run_ocr(ocr, image_np)
            tax_info_result = tax_info.map(texts, boxes)
        elif region.description == "MENSAGEM_IMPORTANTE":
            texts, _boxes, _scores = run_ocr(ocr, image_np)
            important_message = important_message_mapper.map(texts)

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
    )
