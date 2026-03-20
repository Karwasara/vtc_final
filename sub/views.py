from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json


def dashboard(request):
    user = request.user

    # 🔹 Adjust this line based on your actual model
    # Example: user.profile.subsidiary OR user.subsidiary
    user_subsidiary = user.subsidiary  

    # 🔹 Superuser can see all data
    if user.is_superuser:
        areas = AreaMaster.objects.all().order_by('area_name')
        schedules = TrainingSchedule.objects.all()
    else:
        areas = AreaMaster.objects.filter(
            subsidiary=user_subsidiary
        ).order_by('area_name')

        schedules = TrainingSchedule.objects.filter(
            subsidiary=user_subsidiary
        )

    area_data = []

    for area in areas:
        area_name = area.area_name

        trained_count = schedules.filter(
            mm_status='approved',
            area_name=area_name
        ).count()

        under_training_count = schedules.filter(
            Q(mm_status__isnull=True) | Q(mm_status='Pending'),
            area_name=area_name
        ).count()

        total_trainings_count = schedules.filter(
            area_name=area_name
        ).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,
        })

    # 🔹 Sort by trained count
    area_data = sorted(area_data, key=lambda x: x['trained'], reverse=True)

    context = {
        "area_data": area_data,
        "area_labels": json.dumps([a["name"] for a in area_data]),
        "trained_counts": json.dumps([a["trained"] for a in area_data]),
        "under_training_counts": json.dumps([a["under_training"] for a in area_data]),
        "total_trainings_counts": json.dumps([a["total_trainings"] for a in area_data]),

        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
    }

    return render(request, "sub/dashboard.html", context)
