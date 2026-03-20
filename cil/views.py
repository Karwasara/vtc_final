from django.shortcuts import render
from django.db.models import Q, Count
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json


def dashboard(request):
    selected_subsidiary = request.GET.get('subsidiary')

    # =========================
    # 🔵 LEVEL 1: SUBSIDIARY VIEW
    # =========================
    if not selected_subsidiary:

        # Get all subsidiaries from AreaMaster
        subsidiaries = AreaMaster.objects.values_list(
            'subsidiary', flat=True
        ).distinct()

        data = []

        for sub in subsidiaries:
            areas = AreaMaster.objects.filter(subsidiary=sub)
            area_names = areas.values_list('area_name', flat=True)

            schedules = TrainingSchedule.objects.filter(
                area_name__in=area_names
            )

            trained = schedules.filter(mm_status='approved').count()
            under_training = schedules.filter(
                Q(mm_status__isnull=True) | Q(mm_status='Pending')
            ).count()
            total = schedules.count()

            data.append({
                "name": sub,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "subsidiary",
            "labels": json.dumps([d["name"] for d in data]),
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
        }

        return render(request, "cil/dashboard.html", context)

    # =========================
    # 🟢 LEVEL 2: AREA VIEW
    # =========================
    else:
        areas = AreaMaster.objects.filter(
            subsidiary=selected_subsidiary
        ).order_by('area_name')

        area_names = areas.values_list('area_name', flat=True)

        schedules = TrainingSchedule.objects.filter(
            area_name__in=area_names
        )

        data = []

        for area in areas:
            area_name = area.area_name

            trained = schedules.filter(
                mm_status='approved',
                area_name=area_name
            ).count()

            under_training = schedules.filter(
                Q(mm_status__isnull=True) | Q(mm_status='Pending'),
                area_name=area_name
            ).count()

            total = schedules.filter(
                area_name=area_name
            ).count()

            data.append({
                "name": area_name,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "area",
            "selected_subsidiary": selected_subsidiary,
            "labels": json.dumps([d["name"] for d in data]),
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
        }

        return render(request, "cil/dashboard.html", context)
