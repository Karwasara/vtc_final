from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from vtc.models import TrainingSchedule

# Create your views here.
def dashboard(request):
    return render(request, 'aso/dashboard.html')



def vtc_forwarded_training_list(request):
    user_area = request.user.area 
    
    trainings = TrainingSchedule.objects.filter(
        vtc_status='approved',
        aso_status__iexact='pending',
        vtc_approved_by__area=user_area  # <--- this line filters by related user’s area
    ).order_by('-vtc_approved_at')
    return render(request, 'aso/received_training_list.html', {'trainings': trainings})
def aso_forwarded_training_list(request):
    user_area = request.user.area 
    trainings = TrainingSchedule.objects.filter(
        aso_status__iexact='approved',
        vtc_approved_by__area=user_area
    ).order_by('-aso_approved_at')
    return render(request, 'aso/forwarded_training_list.html', {'trainings': trainings})



def forward_to_mm(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)
    training.aso_status = 'forwarded_to_mm'
    training.save()
    messages.success(request, f"Training for {training.worker.name} forwarded to MM for final approval.")
    return redirect('aso:forwarded_training_list')


def reject_training(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)
    training.aso_status = 'rejected'
    training.save()
    messages.success(request, f"Training for {training.worker.name} has been rejected by ASO.")
    return redirect('aso:forwarded_training_list')



from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from vtc.models import TrainingSchedule
from django.utils import timezone
def training_detail(request, pk):
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


def approved_worker_detail(request, pk):
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


from django.shortcuts import render
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
def certificate_detail(request):
    serial_number = request.GET.get('serial_number')
    training = None
    searched = False
    area_name = "Unknown"

    if serial_number:
        searched = True
        try:
            training = TrainingSchedule.objects.select_related('worker').get(certificate_serial_number_final=serial_number)
            # Extract area code from 4th to 6th char (0-based index: 3 to 6 exclusive)
            area_code = serial_number[3:6]

            # Lookup area name by area code
            from accounts.models import AreaMaster  # replace with your actual app/model
            area = AreaMaster.objects.filter(area_code=area_code).first()
            if area:
                area_name = area.area_name
        except TrainingSchedule.DoesNotExist:
            training = None

    # Prepare context if training is found
    if training:
        worker = training.worker
        from_date_str = training.from_date.strftime("%d-%m-%Y")
        to_date_str = training.to_date.strftime("%d-%m-%Y")
        present_days = training.attendances.filter(present="Present").count()
        area_name = area_name
        schedule_number = (
            "First" if training.type_of_training == "Basic"
            else "Fourth" if training.type_of_training == "Refresher"
            else ""
        )
        chapter = "Chapter III" if training.type_of_training == "Basic" else "Chapter IV/Chapter V"
        form_type = "FORM - A" if training.type_of_training == "Basic" else "FORM - B"
        validity_years = {
            "Basic": "5",
            "Refresher": "3"
        }.get(training.type_of_training, "....")

        # Mask Aadhaar
        full_adhar = worker.aadhar_number or ""
        masked_adhar = "XXXX-XXXX-" + full_adhar[-4:] if len(full_adhar) >= 4 else "Invalid"
        
        context = {
            "training": training,
            "worker": worker,
            "serial_number": training.certificate_serial_number_final,
            "issue_date": training.certificate_created_date.strftime('%d/%m/%Y') if training.certificate_created_date else None,
            "from_date": from_date_str,
            "to_date": to_date_str,
            "present_days": present_days,
            "area_name": area_name,
            "schedule_number": schedule_number,
            "chapter": chapter,
            "form_type": form_type,
            "validity_years": validity_years,
            "masked_adhar": masked_adhar,
            "searched": searched,
        }
    else:
        context = {
            "training": None,
            "worker": None,
            "searched": searched,
        }

    return render(request, 'aso/certificate_detail.html', context)