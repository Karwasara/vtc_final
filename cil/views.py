from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json

def dashboard(request):
    selected_subsidiary = request.GET.get('subsidiary')

    # =========================
    # 🔵 LEVEL 1: SUBSIDIARY VIEW
    # =========================
    if not selected_subsidiary:

        # Get all distinct subsidiaries
        subsidiaries = AreaMaster.objects.values_list('subsidiary', flat=True).distinct()
        data = []

        labels = []  # this will contain subsidiary codes

        for sub in subsidiaries:
            # Get all areas for this subsidiary
            areas = AreaMaster.objects.filter(subsidiary=sub)
            area_names = list(areas.values_list('area_name', flat=True))

            # Get subsidiary code: pick first area's code (or define a proper field)
            if areas.exists() and hasattr(areas.first(), 'subsidiary_code'):
                code = areas.first().subsidiary_code
            else:
                code = sub  # fallback to name if code not present

            labels.append(code)

            # Count schedules
            if area_names:
                schedules = TrainingSchedule.objects.filter(area_name__in=area_names)
                trained = schedules.filter(mm_status='approved').count()
                under_training = schedules.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending')).count()
                total = schedules.count()
            else:
                trained = 0
                under_training = 0
                total = 0

            data.append({
                "name": sub,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "subsidiary",
            "labels": json.dumps(labels),  # use codes on X-axis
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
        }

        return render(request, "cil/dashboard.html", context)

    # =========================
    # 🟢 LEVEL 2: AREA VIEW
    # =========================
    else:
        areas = AreaMaster.objects.filter(subsidiary=selected_subsidiary).order_by('area_name')
        area_names = list(areas.values_list('area_name', flat=True))
        schedules = TrainingSchedule.objects.filter(area_name__in=area_names)

        data = []
        labels = []  # area codes or names

        for area in areas:
            area_name = area.area_name
            labels.append(area_name)  # for area view, can use name or code if available

            trained = schedules.filter(mm_status='approved', area_name=area_name).count()
            under_training = schedules.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending'), area_name=area_name).count()
            total = schedules.filter(area_name=area_name).count()

            data.append({
                "name": area_name,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "area",
            "selected_subsidiary": selected_subsidiary,
            "labels": json.dumps(labels),  # area names or codes
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
        }

        return render(request, "cil/dashboard.html", context)
