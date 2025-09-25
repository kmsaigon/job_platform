from django.shortcuts import get_object_or_404, render
from .models import Company


def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    return render(request, 'companies/detail.html', {'company': company})


