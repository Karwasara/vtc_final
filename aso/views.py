from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from vtc.models import TrainingSchedule
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

@login_required(login_url='accounts:login')
# Create your views here.
def dashboard(request):
    # ✅ AUTH + ROLE CHECK
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    return render(request, 'aso/dashboard.html')


@login_required(login_url='accounts:login')
def vtc_forwarded_training_list(request):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    user_areas = request.user.areas.all()
    
    trainings = TrainingSchedule.objects.filter(
        vtc_status='approved',
        aso_status__iexact='pending',
        area_name__in=[a.area_name for a in user_areas]
    ).order_by('-vtc_approved_at')
    return render(request, 'aso/received_training_list.html', {'trainings': trainings})

@login_required(login_url='accounts:login')
def aso_forwarded_training_list(request):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    user_areas = request.user.areas.all() 
    trainings = TrainingSchedule.objects.filter(
        aso_status__iexact='approved',
        area_name__in=[a.area_name for a in user_areas]
    ).order_by('-aso_approved_at')
    return render(request, 'aso/forwarded_training_list.html', {'trainings': trainings})


@login_required(login_url='accounts:login')
def forward_to_mm(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    training = get_object_or_404(TrainingSchedule, pk=pk)
    training.aso_status = 'forwarded_to_mm'
    training.save()
    messages.success(request, f"Training for {training.worker.name} forwarded to MM for final approval.")
    return redirect('aso:forwarded_training_list')

@login_required(login_url='accounts:login')
def reject_training(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    training = get_object_or_404(TrainingSchedule, pk=pk)
    training.aso_status = 'rejected'
    training.save()
    messages.success(request, f"Training for {training.worker.name} has been rejected by ASO.")
    return redirect('aso:forwarded_training_list')



from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from vtc.models import TrainingSchedule
from django.utils import timezone
@login_required(login_url='accounts:login')
def training_detail(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    training = get_object_or_404(TrainingSchedule, pk=pk)
    attendances = training.attendances.all()
    result = getattr(training, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'forward_to_mm':
            training.aso_status = 'approved'
            training.aso_approved_by = request.user
            training.aso_approved_at = timezone.now()
            training.save()
            messages.success(request, 'Training forwarded to Mine Manager.')
            return redirect('aso:forwarded_training_list')
        elif action == 'reject':
            training.aso_status = 'pending'
            training.vtc_status = 'pending'  # ✅ Reset VTC status if rejected
            training.save()
            messages.success(request, 'Training rejected by ASO and sent back to VTC.')
            return redirect('aso:forwarded_training_list')

    return render(request, 'aso/training_detail.html', {
        'training': training,
        'attendances': attendances,
        'result': result
    })


@login_required(login_url='accounts:login')
def approved_worker_detail(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'aso':
        return redirect('accounts:login')
    training = get_object_or_404(TrainingSchedule, pk=pk)
    attendances = training.attendances.all()
    result = getattr(training, 'result', None)

    return render(request, 'aso/approved_worker_detail.html', {
    'training': training,
    'attendances': attendances,
    'result': result
})

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
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'aso':
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
        'aso/certificate_detail.html',
        context
    )
