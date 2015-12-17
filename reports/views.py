#encoding:utf-8

from django.http import HttpResponse
from django.views.generic import View


class ReportView(View):   
    report = None

    def get(self, request):
        ofile = self.report.file()    
        response = HttpResponse(ofile ,content_type=self.report.get_content_type())
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.report.get_filename()
        return response    

        