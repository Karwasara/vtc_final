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

from django.shortcuts import render
from django.db.models import Q, Count, F, Value, CharField
from django.db.models.functions import Coalesce, Cast
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json


def dashboard(request):
    user = request.user

    # ✅ STEP 1: Get areas based on user's subsidiary
    if user.is_superuser:
        areas = AreaMaster.objects.all()
    else:
        areas = AreaMaster.objects.filter(
            subsidiary=user.subsidiary
        )

    # ✅ STEP 2: Extract area names
    area_names = list(
        areas.values_list('area_name', flat=True)
    )

    # ✅ STEP 3: Filter schedules
    if user.is_superuser:
        schedules = TrainingSchedule.objects.all()
    else:
        schedules = TrainingSchedule.objects.filter(
            area_name__in=area_names
        )

    # ✅ STEP 4: GROUP BY created_by
    vtc_data = schedules.values(
        'created_by',
        'created_by__first_name'
    ).annotate(

        # ✅ VTC NAME
        # first_name → if empty then user id
        vtc_name=Coalesce(
            F('created_by__first_name'),
            Cast(F('created_by'), CharField()),
            Value('Unknown'),
            output_field=CharField()
        ),

        trained=Count(
            'id',
            filter=Q(mm_status='approved')
        ),

        under_training=Count(
            'id',
            filter=Q(mm_status__isnull=True) |
                   Q(mm_status='Pending')
        ),

        total_trainings=Count('id')

    ).order_by('-trained')

    # ✅ STEP 5: Use vtc_name as label
    labels = [v['vtc_name'] for v in vtc_data]

    trained_counts = [
        v['trained'] for v in vtc_data
    ]

    under_training_counts = [
        v['under_training'] for v in vtc_data
    ]

    total_trainings_counts = [
        v['total_trainings'] for v in vtc_data
    ]

    context = {
        "area_data": vtc_data,

        "area_labels": json.dumps(labels),

        "trained_counts": json.dumps(
            trained_counts
        ),

        "under_training_counts": json.dumps(
            under_training_counts
        ),

        "total_trainings_counts": json.dumps(
            total_trainings_counts
        ),

        "total_trained": sum(trained_counts),

        "total_under_training": sum(
            under_training_counts
        ),

        "total_trainings": sum(
            total_trainings_counts
        ),
    }

    return render(
        request,
        "sub/dashboard.html",
        context
    )


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
from django.shortcuts import render, get_object_or_404
from vtc.models import TrainingSchedule


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from vtc.models import TrainingSchedule
from accounts.models import AreaMaster, SubsidiaryMaster
from accounts.models import CustomUser
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from vtc.models import TrainingSchedule
from accounts.models import AreaMaster, SubsidiaryMaster, CustomUser


@login_required(login_url='accounts:login')
def certificate_detail(request):
    # Authentication and role check
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'sub':
        return redirect('accounts:login')

    serial_number = request.GET.get('serial_number')
    training = None
    searched = False

    area_name = "Unknown"
    subsidiary_name = ""
    subsidiary_code = ""
    creator_first_name = ""

    if serial_number:
        searched = True

        try:
            training = TrainingSchedule.objects.select_related(
                'worker'
            ).get(
                certificate_serial_number_final=serial_number
            )

            # Get creator first name
            if training.created_by_id:
                creator = CustomUser.objects.filter(
                    id=training.created_by_id
                ).first()

                if creator:
                    creator_first_name = creator.first_name

            # Extract area code from serial number
            area_code = serial_number[3:6]

            # Get Area
            area = AreaMaster.objects.filter(
                area_code=area_code
            ).first()

            if area:
                area_name = area.area_name

                # Get Subsidiary
                subsidiary = SubsidiaryMaster.objects.filter(
                    id=area.subsidiary_id
                ).first()

                if subsidiary:
                    subsidiary_name = subsidiary.subsidiary_name
                    subsidiary_code = subsidiary.subsidiary_code

        except TrainingSchedule.DoesNotExist:
            training = None

    # Prepare context if training found
    if training:
        worker = training.worker

        from_date_str = training.from_date.strftime("%d-%m-%Y")
        to_date_str = training.to_date.strftime("%d-%m-%Y")

        present_days = training.attendances.filter(
            present="Present"
        ).count()

        schedule_number = (
            "First"
            if training.type_of_training == "Basic"
            else "Fourth"
            if training.type_of_training == "Refresher"
            else ""
        )

        chapter = (
            "Chapter III"
            if training.type_of_training == "Basic"
            else "Chapter IV/Chapter V"
        )

        form_type = (
            "FORM - A"
            if training.type_of_training == "Basic"
            else "FORM - B"
        )

        validity_years = {
            "Basic": "4",
            "Refresher": "4",
        }.get(training.type_of_training, "....")

        # Mask Aadhaar
        full_aadhar = worker.aadhar_number or ""
        masked_aadhar = (
            "XXXX-XXXX-" + full_aadhar[-4:]
            if len(full_aadhar) >= 4
            else "Invalid"
        )

        context = {
            "training": training,
            "worker": worker,
            "serial_number": training.certificate_serial_number_final,
            "issue_date": (
                training.certificate_created_date.strftime('%d/%m/%Y')
                if training.certificate_created_date
                else None
            ),
            "from_date": from_date_str,
            "to_date": to_date_str,
            "present_days": present_days,
            "area_name": area_name,
            "subsidiary_name": subsidiary_name,
            "subsidiary_code": subsidiary_code,
            "creator_first_name": creator_first_name,
            "schedule_number": schedule_number,
            "chapter": chapter,
            "form_type": form_type,
            "validity_years": validity_years,
            "masked_aadhar": masked_aadhar,
            "searched": searched,
        }

    else:
        context = {
            "training": None,
            "worker": None,
            "searched": searched,
            "creator_first_name": "",
            "area_name": "",
            "subsidiary_name": "",
            "subsidiary_code": "",
        }

    return render(
        request,
        'vtc/certificate_detail.html',
        context
    )
