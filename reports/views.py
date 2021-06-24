from django.shortcuts import render,get_object_or_404
from profiles.models import Profile
from django.http import JsonResponse
from .utils import get_report_image
from .models import Report
from django.views.generic import ListView,DetailView,TemplateView
from .forms import ReportForm
from sales.models import Sale, Position, CSV
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv
from django.utils.dateparse import parse_date
from products.models import Product
from customers.models import Customer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
class ReportListView(LoginRequiredMixin,ListView):
    model = Report
    template_name = 'reports/main.html'

class ReportDetailtView(LoginRequiredMixin,DetailView):
    model = Report
    template_name = 'reports/detail.html'
class UploadTemplateView(LoginRequiredMixin,TemplateView):
    template_name = 'reports/from_file.html'
@login_required
def csv_upload_view(request):
    if request.method=="POST":
        csv_file =request.FILES.get('file')
        obj=CSV.objects.create(file_name=csv_file)
        print(obj)
        with open(obj.file_name.path,'r') as f:
            reader = csv.reader(f)
            reader.__next__()
            for row in reader:
                data=row
                transaction_id=data[1]
                product = data[2]
                quantity = int(data[3])
                customer=data[4]
                date=parse_date(data[5])
                #product_obj = Product.objects.get(name__iexact=product)
                try:
                    product_obj = Product.objects.get(name__iexact=product)
                except Product.DoesNotExist:
                    product_obj=None
                if product_obj is not None:
                    customer_obj, created = Customer.objects.get_or_create(name=customer)
                    salesman_obj = Profile.objects.get(user=request.user)
                    position_obj=Position.objects.create(product=product_obj,quantity=quantity,created=date)
                    sale_obj, _ = Sale.objects.get_or_create(transaction_id=transaction_id,customer=customer_obj, salesman=salesman_obj,created=date)
                    #print(sale_obj)
                    sale_obj.pos.add(position_obj)
                    sale_obj.save()
                    #return JsonResponse({'ex':False})
    else:
        return JsonResponse({'ex':True})


    return HttpResponse()
@login_required
def create_report_view(request):
    form = ReportForm(request.POST or None)
    if request.is_ajax():
        #name=request.POST.get('name')
        #remarks = request.POST.get('remarks')
        image = request.POST.get('image')
        author= Profile.objects.get(user=request.user)
        img=get_report_image(image)
        if form.is_valid():
            instance=form.save(commit=False)
            instance.image=img
            instance.author=author
            instance.save()

        #Report.objects.create(name=name,remarks=remarks,image=img,author=author)
        return JsonResponse({'msg':'send'})
    return JsonResponse({})


def render_pdf_view(request,pk):
    template_path = 'reports/pdf.html'
    obj=get_object_or_404(Report,pk=pk)
    context = {'obj':obj}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    #d download
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    #if display
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response,)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
