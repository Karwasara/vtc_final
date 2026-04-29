from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json


from django.shortcuts import render
from django.db.models import Q, Count
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json

def dashboard(request):
    # 🔒 Access control
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'sub':
        return redirect('accounts:login')

    user = request.user

    if user.is_superuser:
        areas = AreaMaster.objects.all()
    else:
        areas = AreaMaster.objects.filter(subsidiary=user.subsidiary)

    area_names = list(areas.values_list('area_name', flat=True))

    if user.is_superuser:
        schedules = TrainingSchedule.objects.all()
    else:
        schedules = TrainingSchedule.objects.filter(area_name__in=area_names)

    vtc_data = schedules.values(
        'created_by__id',
        'area_name'
    ).annotate(
        trained=Count('id', filter=Q(mm_status='approved')),
        under_training=Count(
            'id',
            filter=Q(mm_status__isnull=True) | Q(mm_status='Pending')
        ),
        total_trainings=Count('id')
    ).order_by('-trained')

    labels = [v['area_name'] for v in vtc_data]
    trained_counts = [v['trained'] for v in vtc_data]
    under_training_counts = [v['under_training'] for v in vtc_data]
    total_trainings_counts = [v['total_trainings'] for v in vtc_data]

    context = {
        "area_data": vtc_data,
        "area_labels": json.dumps(labels),
        "trained_counts": json.dumps(trained_counts),
        "under_training_counts": json.dumps(under_training_counts),
        "total_trainings_counts": json.dumps(total_trainings_counts),
        "total_trained": sum(trained_counts),
        "total_under_training": sum(under_training_counts),
        "total_trainings": sum(total_trainings_counts),
    }

    return render(request, "sub/dashboard.html", context)

from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse   # ✅ IMPORTANT

def certificate_verification(request):
    # 🔒 Access control
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'sub':
        return redirect('accounts:login')

    serial_number = request.GET.get('serial_number')
    aadhar_number = request.GET.get('aadhar_number')

    training = None
    trainings = None
    searched = False

    if serial_number or aadhar_number:
        searched = True

        if serial_number and aadhar_number:
            messages.error(request, "Use either Serial Number OR Aadhaar")
            return render(request, 'sub/certificate_verification.html', {
                'training': None,
                'trainings': None,
                'searched': False
            })

        if serial_number:
            try:
                TrainingSchedule.objects.get(
                    certificate_serial_number_final=serial_number
                )
                url = reverse('sub:certificate_detail')
                return redirect(f"{url}?serial_number={serial_number}")
            except TrainingSchedule.DoesNotExist:
                training = None

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
    # 🔒 Access control
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'sub':
        return redirect('accounts:login')

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
