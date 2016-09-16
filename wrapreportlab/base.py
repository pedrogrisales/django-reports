# -*- coding: utf-8 -*-
# Python library
import os
import csv
import locale
from io import BytesIO

locale.setlocale( locale.LC_ALL, 'es_CO.UTF-8' )

# Django library
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.utils.encoding import smart_str

# Third library
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Spacer
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus import Table, TableStyle, Image


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.drawString(
            settings.MARGINS_REPORT['right'] * cm ,
            settings.MARGINS_REPORT['bottom'] * cm,
            "Página %d de %d" % (self._pageNumber, page_count)
        )


class BaseReport(object):
    """
    docstring for BaseReport
    """
    def __init__(self):
        self.filename = ""
        self.content_type = ""
        self.buffer = BytesIO()

    def get_content_type(self):
        return self.content_type

    def get_filename(self):
        return self.filename

    def write(self):
        pass

    def build(self):
        pass

    def file(self):
        return ContentFile(self.build())


class TextReport(BaseReport):

    def __init__(self):
        super(TextReport, self).__init__()
        self.content_type = 'text/csv'
        self.writer = csv.writer(self.buffer, delimiter=";")

    def build(self):
        self.write()
        self.buffer.write(u'\ufeff'.encode('utf8'))
        ofile = self.buffer.getvalue()
        self.buffer.close()
        return ofile


class PdfReport(BaseReport):

    def __init__(self, pagesize=letter):
        super(PdfReport, self).__init__()
        self.pagesize = pagesize
        self.width, self.height = pagesize
        self.content_type = 'application/pdf'


class CanvasReport(PdfReport):

    def __init__(self, pagesize):
        super(CanvasReport, self).__init__(pagesize)
        self.page = canvas.Canvas(self.buffer)

    def build(self, page=None):
        self.write()
        self.page.save()
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


class DocumentReport(PdfReport):
    """
    docstring for DocumentReport
    """
    def __init__(self, pagesize=letter, blank=False):
        super(DocumentReport, self).__init__(pagesize)
        self.doc = self.get_template()
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.title = ''
        self.subtitle = ''
        self.firm = ''
        self.blank = blank

    def get_title(self):
        return self.title

    def get_subtitle(self):
        return self.subtitle

    def get_firm(arg):
        return self.firm

    def get_template(self):
        margins = settings.MARGINS_REPORT
        return SimpleDocTemplate(
            self.buffer,
            rightMargin = margins['right'] * cm,
            leftMargin = margins['left'] * cm,
            topMargin = margins['top'] * cm,
            bottomMargin = margins['bottom'] * cm,
            pagesize = self.pagesize
        )

    def get_footer_pages(self, canvas, doc):
        canvas.saveState()
        style = self.styles['Normal']
        style.alignment = TA_RIGHT
        title = Paragraph(self.get_firm(), style)
        w, offsetY = title.wrap(self.doc.width, self.doc.topMargin)        
        title.drawOn(canvas, self.doc.leftMargin , self.doc.bottomMargin)
        canvas.restoreState()

    def get_header_first_page(self, canvas, doc):
        canvas.saveState()
        title = Paragraph(self.get_title(), self.styles['Heading1'])
        w, offsetY = title.wrap(self.doc.width, self.doc.topMargin)
        title.drawOn(canvas, self.doc.leftMargin, (self.height - self.doc.topMargin))
        subtitle = Paragraph(self.get_subtitle(), self.styles['Heading2'])
        w, offsetY = subtitle.wrap(self.doc.width, self.doc.topMargin)
        subtitle.drawOn(canvas, self.doc.leftMargin,
                                (self.height - self.doc.topMargin) - offsetY)
        canvas.restoreState()
        self.get_footer_pages(canvas, doc)

    def get_header_lates_pages(self, canvas, doc):
        canvas.saveState()
        title = Paragraph("<b>%s - %s</b>" % (self.get_title(), self.get_subtitle()), self.styles['BodyText'])
        w, offsetY = title.wrap(self.doc.width, self.doc.topMargin)
        title.drawOn(canvas, self.doc.leftMargin, (self.height - self.doc.topMargin))
        canvas.restoreState()
        self.get_footer_pages(canvas, doc)

    def build(self):
        self.write()
        if self.blank:
            self.doc.build(
                self.elements,
            )
        else:
            self.doc.build(
                self.elements,
                onFirstPage = self.get_header_first_page,
                canvasmaker = NumberedCanvas,
                onLaterPages = self.get_header_lates_pages,
            )
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf
