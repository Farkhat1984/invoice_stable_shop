# utils/pdf_generator.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import os
from datetime import datetime


class InvoicePDFGenerator:
    def __init__(self):
        # Получаем абсолютный путь к директории utils
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Путь к файлу шрифта в текущей директории
        font_path = os.path.join(current_dir, 'DejaVuSans.ttf')

        # Путь к директории для сохранения PDF
        project_dir = os.path.dirname(os.path.dirname(current_dir))
        self.output_dir = os.path.join(project_dir, 'generated_pdfs')

        # Создаём директорию для PDF если её нет
        os.makedirs(self.output_dir, exist_ok=True)

        # Проверяем существование файла шрифта
        if not os.path.exists(font_path):
            raise FileNotFoundError(
                f"Шрифт не найден по пути: {font_path}\n"
                f"Пожалуйста, убедитесь что файл DejaVuSans.ttf находится в директории: {current_dir}"
            )

        # Регистрация шрифта для поддержки кириллицы
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))

        self.styles = getSampleStyleSheet()
        self.style_header = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontName='DejaVu',
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

        self.style_normal = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName='DejaVu',
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6
        )

    def generate_pdf(self, invoice_data, filename=None):
        if filename is None:
            filename = self.get_invoice_filename(invoice_data.get('id', 'new'))

        output_path = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Создаем список элементов для документа
        elements = []

        # Добавляем заголовок
        elements.append(Paragraph("НАКЛАДНАЯ", self.style_header))

        # Добавляем основную информацию
        elements.append(Paragraph(f"Номер: {invoice_data.get('id', '')}", self.style_normal))
        elements.append(Paragraph(f"Дата: {invoice_data.get('created_at', '').split('T')[0]}", self.style_normal))
        elements.append(Paragraph(f"Контакт: {invoice_data.get('contact', '')}", self.style_normal))
        elements.append(Spacer(1, 0.5 * cm))

        if invoice_data.get('additional_info'):
            elements.append(Paragraph(f"Дополнительная информация:", self.style_normal))
            elements.append(Paragraph(invoice_data.get('additional_info', ''), self.style_normal))
            elements.append(Spacer(1, 0.5 * cm))

        # Создаем таблицу с товарами
        table_data = [
            ['№', 'Наименование', 'Количество', 'Цена', 'Сумма']
        ]

        for idx, item in enumerate(invoice_data.get('items', []), 1):
            if item.get('name') and item.get('quantity') and item.get('price'):
                table_data.append([
                    str(idx),
                    item.get('name', ''),
                    str(item.get('quantity', '')),
                    f"{float(item.get('price', 0)):.2f}",
                    f"{float(item.get('quantity', 0)) * float(item.get('price', 0)):.2f}"
                ])

        # Создаем таблицу
        table = Table(table_data, colWidths=[1 * cm, 8 * cm, 3 * cm, 3 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 2, colors.black),
            ('LINEBEFORE', (1, 1), (1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

        # Добавляем итоговую сумму
        elements.append(Paragraph(
            f"Итого: {invoice_data.get('total', 0):.2f}",
            ParagraphStyle(
                'Total',
                parent=self.style_normal,
                fontSize=14,
                alignment=2  # Right alignment
            )
        ))

        # Добавляем статус оплаты
        payment_status = "Оплачено" if invoice_data.get('is_paid', False) else "Не оплачено"
        elements.append(Paragraph(
            f"Статус оплаты: {payment_status}",
            ParagraphStyle(
                'PaymentStatus',
                parent=self.style_normal,
                fontSize=14,
                alignment=2
            )
        ))

        # Создаем PDF
        doc.build(elements)
        return output_path

    @staticmethod
    def get_invoice_filename(invoice_id):
        """Генерирует имя файла для накладной"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"invoice_{invoice_id}_{timestamp}.pdf"