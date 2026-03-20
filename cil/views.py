from django.shortcuts import render
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import IndependentWorkerForm
from .models import IndependentWorker
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import IndependentWorker
from .forms import IndependentWorkerForm  # ensure this form exists
from django.db.models import Max

def dashboard(request):
    return render(request, 'cil/dashboard.html')
