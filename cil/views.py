from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster, SubsidiaryMaster
import json

def dashboard1(request):
    selected_sub_code = request.GET.get('subsidiary')  # this is code, e.g., 'NCL'

    # =========================
    # 🔵 LEVEL 1: SUBSIDIARY VIEW
    # =========================
    if not selected_sub_code:

        # Get all distinct subsidiary IDs from AreaMaster
        subsidiaries = AreaMaster.objects.values_list('subsidiary_id', flat=True).distinct()
        data = []
        labels = []  # will contain subsidiary codes

        for sub_id in subsidiaries:
            # Fetch subsidiary code and name from SubsidiaryMaster
            try:
                sub_obj = SubsidiaryMaster.objects.get(id=sub_id)
                code = sub_obj.subsidiary_code
                name = sub_obj.subsidiary_name
            except SubsidiaryMaster.DoesNotExist:
                code = str(sub_id)
                name = str(sub_id)

            labels.append(code)

            # Get all areas for this subsidiary
            areas = AreaMaster.objects.filter(subsidiary_id=sub_id)
            area_names = list(areas.values_list('area_name', flat=True))

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
                "name": name,  # full name for summary table
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "subsidiary",
            "labels": json.dumps(labels),  # chart X-axis: subsidiary codes
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
            "table_names": json.dumps([d["name"] for d in data]),  # full names for table
        }

        return render(request, "cil/dashboard.html", context)

    # =========================
    # 🟢 LEVEL 2: AREA VIEW
    # =========================
    else:
        # Lookup subsidiary ID from code
        try:
            sub_obj = SubsidiaryMaster.objects.get(subsidiary_code=selected_sub_code)
            sub_id = sub_obj.id
        except SubsidiaryMaster.DoesNotExist:
            # fallback: invalid code
            sub_id = None

        if not sub_id:
            return render(request, "cil/dashboard.html", {"level": "area", "labels": [], "trained": [], "under_training": [], "total": []})

        # Fetch areas under this subsidiary
        areas = AreaMaster.objects.filter(subsidiary_id=sub_id).order_by('area_name')
        area_names = list(areas.values_list('area_name', flat=True))
        schedules = TrainingSchedule.objects.filter(area_name__in=area_names)

        data = []
        labels = []  # area names

        for area in areas:
            labels.append(area.area_name)  # can use area code if available

            trained = schedules.filter(mm_status='approved', area_name=area.area_name).count()
            under_training = schedules.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending'), area_name=area.area_name).count()
            total = schedules.filter(area_name=area.area_name).count()

            data.append({
                "name": area.area_name,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "area",
            "selected_subsidiary": selected_sub_code,
            "labels": json.dumps(labels),
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
        }

        return render(request, "cil/dashboard.html", context)



def dashboard(request):
    # 🔒 Access control
    if not request.user.is_authenticated or request.user.user_type != 'cil':
        return redirect('accounts:login')
    selected_sub_code = request.GET.get('subsidiary')  # e.g., 'NCL'
    active_type = request.GET.get('type', 'trained')   # selected tile: trained / under_training / total
    user_area_name = getattr(request.user, 'area_name', None)  # current user area

    # =========================
    # 🔵 LEVEL 1: SUBSIDIARY VIEW
    # =========================
    if not selected_sub_code:

        subsidiaries = AreaMaster.objects.values_list('subsidiary_id', flat=True).distinct()
        data = []
        labels = []

        for sub_id in subsidiaries:
            try:
                sub_obj = SubsidiaryMaster.objects.get(id=sub_id)
                code = sub_obj.subsidiary_code
                name = sub_obj.subsidiary_name
            except SubsidiaryMaster.DoesNotExist:
                code = str(sub_id)
                name = str(sub_id)

            labels.append(code)
            areas = AreaMaster.objects.filter(subsidiary_id=sub_id)
            area_names = list(areas.values_list('area_name', flat=True))

            if area_names:
                schedules = TrainingSchedule.objects.filter(area_name__in=area_names)
                trained = schedules.filter(mm_status='approved').count()
                under_training = schedules.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending')).count()
                total = schedules.count()
            else:
                trained = under_training = total = 0

            data.append({
                "name": name,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "subsidiary",
            "labels": json.dumps(labels),
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
            "table_names": json.dumps([d["name"] for d in data]),
            "active_type": active_type,
        }
        return render(request, "cil/dashboard.html", context)

    # =========================
    # 🟢 LEVEL 2: AREA VIEW
    # =========================
    else:
        try:
            sub_obj = SubsidiaryMaster.objects.get(subsidiary_code=selected_sub_code)
            sub_id = sub_obj.id
        except SubsidiaryMaster.DoesNotExist:
            sub_id = None

        if not sub_id:
            return render(request, "cil/dashboard.html", {
                "level": "area",
                "labels": [],
                "trained": [],
                "under_training": [],
                "total": [],
                "active_type": active_type,
            })

        # Fetch areas under this subsidiary
        areas = AreaMaster.objects.filter(subsidiary_id=sub_id)

        # 🔹 Restrict to current user's area if set
        if user_area_name:
            areas = areas.filter(area_name=user_area_name)

        areas = areas.order_by('area_name')
        area_names = list(areas.values_list('area_name', flat=True))
        schedules = TrainingSchedule.objects.filter(area_name__in=area_names)

        data = []
        labels = []

        for area in areas:
            labels.append(area.area_name)
            trained = schedules.filter(mm_status='approved', area_name=area.area_name).count()
            under_training = schedules.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending'), area_name=area.area_name).count()
            total = schedules.filter(area_name=area.area_name).count()

            data.append({
                "name": area.area_name,
                "trained": trained,
                "under_training": under_training,
                "total": total,
            })

        context = {
            "level": "area",
            "selected_subsidiary": selected_sub_code,
            "labels": json.dumps(labels),
            "trained": json.dumps([d["trained"] for d in data]),
            "under_training": json.dumps([d["under_training"] for d in data]),
            "total": json.dumps([d["total"] for d in data]),
            "active_type": active_type,
        }

        return render(request, "cil/dashboard.html", context)
