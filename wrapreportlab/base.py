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
        self.drawRightString(
            settings.MARGINS_REPORT['right'] * cm + 100,
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
        self.blank = blank

    def get_title(self):
        return self.title

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

    def get_header_and_footer(self, canvas, doc):
        if not self.blank:
            canvas.saveState()
            subheader = Paragraph('SGV', self.styles['Heading2'])
            w, offsetY = subheader.wrap(self.doc.width, self.doc.topMargin)
            subheader.drawOn(
                canvas,
                self.doc.leftMargin,
                (self.height - self.doc.topMargin) + 10 # padding bottom = 10
            )
            header = Paragraph(self.get_title(), self.styles['Heading1'])
            w, offsetY = header.wrap(self.doc.width, self.doc.topMargin)
            header.wrap(self.doc.width, self.doc.topMargin)
            header.drawOn(
                canvas,
                self.doc.leftMargin,
                (self.height - self.doc.topMargin) + offsetY + 10
            )
            canvas.restoreState()


    def build(self):
        self.write()
        self.doc.build(
            self.elements,
            onFirstPage = self.get_header_and_footer,
            canvasmaker = NumberedCanvas,
            onLaterPages = self.get_header_and_footer,
        )
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf
