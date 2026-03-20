from django.shortcuts import render
from django.shortcuts import render
from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render

from vtc.models import TrainingSchedule
from django.contrib import messages

# Create your views here.
from django.utils import timezone
from django.db.models import Count, Q

from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json

from django.shortcuts import render
from django.db.models import Q
import json
#from .models import TrainingSchedule, IndependentWorker

from django.db.models import Q
import json

def dashboard(request):
    areas = AreaMaster.objects.all().order_by('area_name')
    area_data = []

    for area in areas:
        area_name = area.area_name

        trained_count = TrainingSchedule.objects.filter(
            mm_status='approved',
            area_name=area_name
        ).count()

        under_training_count = TrainingSchedule.objects.filter(
            Q(mm_status__isnull=True) | Q(mm_status='Pending'),
            area_name=area_name
        ).count()

        total_trainings_count = TrainingSchedule.objects.filter(
            area_name=area_name
        ).count()

#        total_workers_count = IndependentWorker.objects.filter(
 #           area_name=area_name
  #      ).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,
        })

    area_data = sorted(area_data, key=lambda x: x['trained'], reverse=True)

    context = {
        "area_data": area_data,
        "area_labels": json.dumps([a["name"] for a in area_data]),
        "trained_counts": json.dumps([a["trained"] for a in area_data]),
        "under_training_counts": json.dumps([a["under_training"] for a in area_data]),
        "total_trainings_counts": json.dumps([a["total_trainings"] for a in area_data]),
#        "total_workers_counts": json.dumps([a["total_workers"] for a in area_data]),
        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
#        "total_workers": sum(a['total_workers'] for a in area_data),
    }

    return render(request, "mm/dashboard.html", context)

