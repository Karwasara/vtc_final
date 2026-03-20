from django.shortcuts import render
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json
from django.db.models import Q, Count

def dashboard(request):
    # User-specific area filter
    user_area_name = getattr(request.user, 'area_name', None)

    if user_area_name:
        areas = AreaMaster.objects.filter(area_name=user_area_name).order_by('area_name')
    else:
        areas = AreaMaster.objects.all().order_by('area_name')

    area_data = []

    for area in areas:
        area_name = area.area_name

        # Count trainings per status
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

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
        })

    # Sort descending by trained count
    area_data = sorted(area_data, key=lambda x: x['trained'], reverse=True)

    context = {
        "area_data": area_data,
        "labels": json.dumps([a["name"] for a in area_data]),
        "trained": json.dumps([a["trained"] for a in area_data]),
        "under_training": json.dumps([a["under_training"] for a in area_data]),
        "total": json.dumps([a["total_trainings"] for a in area_data]),
        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
        "level": "area",
    }

    return render(request, "mm/dashboard.html", context)
