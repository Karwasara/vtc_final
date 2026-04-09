from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json


def dashboard(request):
    user = request.user

    # 🔹 FIX THIS based on your user model
    user_subsidiary = user.subsidiary  

    # 🔹 Get only areas of this subsidiary
    if user.is_superuser:
        areas = AreaMaster.objects.all().order_by('area_name')
    else:
        areas = AreaMaster.objects.filter(
            subsidiary=user_subsidiary
        ).order_by('area_name')

    # 🔹 Extract area names list
    area_names = list(areas.values_list('area_name', flat=True))

    # 🔹 Filter schedules USING area_name (IMPORTANT FIX)
    if user.is_superuser:
        schedules = TrainingSchedule.objects.all()
    else:
        schedules = TrainingSchedule.objects.filter(
            area_name__in=area_names
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

    # 🔹 Sort
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
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse   # ✅ IMPORTANT

def certificate_verification(request):
    serial_number = request.GET.get('serial_number')
    aadhar_number = request.GET.get('aadhar_number')

    training = None
    trainings = None
    searched = False

    if serial_number or aadhar_number:
        searched = True

        # ❌ Prevent both inputs
        if serial_number and aadhar_number:
            messages.error(request, "Use either Serial Number OR Aadhaar")
            return render(request, 'sub/certificate_verification.html', {
                'training': None,
                'trainings': None,
                'searched': False
            })

        # 🔥 SERIAL SEARCH → REDIRECT TO DETAIL PAGE
        if serial_number:
            try:
                TrainingSchedule.objects.get(
                    certificate_serial_number_final=serial_number
                )

                # ✅ Redirect using reverse
                url = reverse('sub:certificate_detail')
                return redirect(f"{url}?serial_number={serial_number}")

            except TrainingSchedule.DoesNotExist:
                training = None

        # ✅ AADHAAR SEARCH → FILTER ONLY VALID CERTIFICATES
        elif aadhar_number:
            trainings = TrainingSchedule.objects.select_related('worker').filter(
                worker__aadhar_number=aadhar_number
            ).filter(
                Q(certificate_serial_number_final__isnull=False) &
                ~Q(certificate_serial_number_final='')
            )

    return render(request, 'sub/certificate_verification.html', {
        'training': training,
        'trainings': trainings,
        'searched': searched
    })

# ---------------- Certificate Detail ----------------
def certificate_detail(request):
    serial_number = request.GET.get('serial_number')

    training = None
    searched = False
    area_name = "Unknown"

    if serial_number:
        searched = True
        try:
            training = TrainingSchedule.objects.select_related('worker').get(
                certificate_serial_number_final=serial_number
            )

            # 🔹 Extract Area Code
            area_code = serial_number[3:6]
            area = AreaMaster.objects.filter(area_code=area_code).first()

            if area:
                area_name = area.area_name

        except TrainingSchedule.DoesNotExist:
            training = None

    if training:
        worker = training.worker

        present_days = training.attendances.filter(
            Q(present=True) | Q(present="Present") | Q(present="present")
        ).count()

        context = {
            "training": training,
            "worker": worker,
            "serial_number": training.certificate_serial_number_final,
            "issue_date": training.certificate_created_date.strftime('%d/%m/%Y') if training.certificate_created_date else None,
            "from_date": training.from_date.strftime("%d-%m-%Y"),
            "to_date": training.to_date.strftime("%d-%m-%Y"),
            "present_days": present_days,
            "area_name": area_name,
            "schedule_number": "First" if training.type_of_training == "Basic" else "Fourth",
            "chapter": "Chapter III" if training.type_of_training == "Basic" else "Chapter IV/V",
            "form_type": "FORM - A" if training.type_of_training == "Basic" else "FORM - B",
            "validity_years": "5" if training.type_of_training == "Basic" else "3",
            "masked_adhar": "XXXX-XXXX-" + worker.aadhar_number[-4:] if worker.aadhar_number else "",
            "searched": searched,
        }
    else:
        context = {
            "training": None,
            "worker": None,
            "searched": searched
        }

    return render(request, 'sub/certificate_detail.html', context)
