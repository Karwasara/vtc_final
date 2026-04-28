from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import IndependentWorkerForm
from .models import IndependentWorker
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import IndependentWorker
from .forms import IndependentWorkerForm  # ensure this form exists
from django.db.models import Max

def dashboard(request):
	if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login') 
    return render(request, 'vtc/dashboard.html')

#List View
def to_schedule_training(request):
    workers = IndependentWorker.objects.filter(delete_flag=False)
    return render(request, 'vtc/to_schedule_training.html', {'workers': workers})
def worker_list(request):
    workers = IndependentWorker.objects.filter(delete_flag=False).order_by('-id')
    return render(request, 'vtc/worker_list.html', {'workers': workers})

#Add worker
def add_worker(request):
    if request.method == 'POST':
        form = IndependentWorkerForm(request.POST, request.FILES)

        if form.is_valid():
            worker = form.save(commit=False)
            worker.created_by = request.user
            worker.save()

            messages.success(request, "Worker added successfully.")
            return redirect('vtc:worker_list')

        else:
            # ✅ Show all field errors properly
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = IndependentWorkerForm()

    return render(request, 'vtc/worker_form.html', {'form': form})


def view_worker(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)
    form = IndependentWorkerForm(instance=worker)

    # Make all fields readonly / disabled
    for field in form.fields.values():
        field.widget.attrs['readonly'] = True
        field.widget.attrs['disabled'] = True

    # Get all trainings where certificate is generated
    certificates = TrainingSchedule.objects.filter(
        worker=worker,
        certificate_serial_number_final__isnull=False
    ).exclude(
        certificate_serial_number_final=''
    ).order_by('-certificate_created_date')

    return render(request, 'vtc/worker_form.html', {
        'form': form,
        'worker': worker,
        'certificates': certificates,
        'is_edit': False,
        'read_only': True
    })


# Edit worker
def edit_worker(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)
    if request.method == 'POST':
        form = IndependentWorkerForm(request.POST, request.FILES, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, "Worker updated successfully.")
            return redirect('vtc:worker_list')
    else:
        form = IndependentWorkerForm(instance=worker)
    return render(request, 'vtc/worker_form.html', {'form': form, 'is_edit': True})

# Logical delete view
def delete_worker(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)
    if request.method == 'POST':
        worker.delete_flag = True
        worker.save()
        messages.success(request, "Worker deleted successfully.")
        return redirect('vtc:worker_list')
    return render(request, 'vtc/confirm_delete_w.html', {'object': worker})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import date

from vtc.models import TrainingSchedule
from .models import IndependentWorker   # adjust if needed


def schedule_training(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)

    # 🔹 Get user's mapped areas
    user_areas = request.user.areas.all()

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        type_of_training = request.POST.get('type_of_training')
        nature_of_training = request.POST.get('nature_of_training')
        contractor_name = request.POST.get('contractor_name')

        # 🔹 AREA HANDLING
        if user_areas.count() == 1:
            area_name = user_areas.first().area_name
        else:
            area_name = request.POST.get('area_name')

        # ✅ SAFE DATE CONVERSION (FIXED)
        from_date = parse_date(from_date_str)
        to_date = parse_date(to_date_str)

        # 🔴 Validation: invalid date
        if not from_date or not to_date:
            messages.error(request, 'Invalid date format.')
            return render(request, 'vtc/schedule_training.html', {
                'worker': worker,
                'user_areas': user_areas
            })

        # 🔴 Rule 1: past date
        if from_date < date.today():
            messages.error(request, 'Training can only be scheduled from today or a future date.')

        # 🔴 Rule 2: invalid range
        elif from_date > to_date:
            messages.error(request, 'From Date cannot be after To Date.')

        else:
            # 🔴 Rule 3: overlapping training
            overlapping = TrainingSchedule.objects.filter(
                worker=worker,
                from_date__lte=to_date,
                to_date__gte=from_date
            ).exists()

            if overlapping:
                messages.error(request, 'This training period overlaps with an existing training for this worker.')

            else:
                # ✅ SAVE DATA
                TrainingSchedule.objects.create(
                    worker=worker,
                    from_date=from_date,
                    to_date=to_date,
                    type_of_training=type_of_training,
                    nature_of_training=nature_of_training,
                    contractor_name=contractor_name,
                    area_name=area_name,
                    created_by=request.user,
                    modified_by=request.user
                )

                messages.success(request, 'Training scheduled successfully.')
                return redirect('vtc:to_schedule_training')

    return render(request, 'vtc/schedule_training.html', {
        'worker': worker,
        'user_areas': user_areas
    })



from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import TrainingSchedule  # Adjust import as per your project

from datetime import datetime, date

from datetime import datetime, date
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import TrainingSchedule

def edit_training(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)
    worker = training.worker
    today = date.today()

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        try:
            new_from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            new_to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'vtc/edit_training.html', {'training': training})

        # If the original from_date is in the past, it cannot be changed
        if training.from_date < today and new_from_date != training.from_date:
            messages.error(request, 'From Date is in the past and cannot be changed.')

        # If the original to_date is in the past, it cannot be changed
        elif training.to_date < today and new_to_date != training.to_date:
            messages.error(request, 'To Date is in the past and cannot be changed.')

        # If the original dates are today or future, new dates cannot be set in the past
        elif training.from_date >= today and new_from_date < today:
            messages.error(request, 'From Date cannot be set to a past date.')

        elif training.to_date >= today and new_to_date < today:
            messages.error(request, 'To Date cannot be set to a past date.')

        elif new_from_date > new_to_date:
            messages.error(request, 'From Date cannot be after To Date.')

        else:
            overlapping = TrainingSchedule.objects.filter(
                worker=worker,
                from_date__lte=new_to_date,
                to_date__gte=new_from_date
            ).exclude(pk=training.pk).exists()

            if overlapping:
                messages.error(request, 'This training period overlaps with another existing training for this worker.')
            else:
                training.from_date = new_from_date
                training.to_date = new_to_date
                training.modified_by = request.user
                training.save()
                messages.success(request, 'Training updated successfully.')
                return redirect('vtc:schedule_training', pk=worker.id)

    return render(request, 'vtc/edit_training.html', {'training': training})



def delete_training(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)
    worker_id = training.worker.id
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Training deleted successfully.')
        return redirect('vtc:schedule_training', pk=worker_id)
    return render(request, 'vtc/confirm_delete.html', {'training': training})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import date, timedelta, time
from django.utils import timezone
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import date, timedelta, time
from django.utils import timezone
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import date, timedelta, time
from django.utils import timezone
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

def add_training_attendance_and_result(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)

    # Generate date range from training
    date_range = []
    current = training.from_date
    while current <= training.to_date:
        date_range.append(current)
        current += timedelta(days=1)

    # Existing attendance keyed by date
    existing_attendance = {att.date: att for att in training.attendances.all()}

    # Get training result if exists
    result = getattr(training, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ==================== SAVE DAILY ATTENDANCE ====================
        if action == 'save_attendance':
            attendance_date_str = request.POST.get('attendance_date')
            in_time_str = request.POST.get('in_time')
            out_time_str = request.POST.get('out_time')
            status = request.POST.get('status')

            if not all([attendance_date_str, in_time_str, out_time_str, status]):
                messages.error(request, "Please fill all fields for attendance.")
                return redirect(request.path)

            # Convert date
            try:
                attendance_date = date.fromisoformat(attendance_date_str)
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect(request.path)

            # Block future dates
            if attendance_date > date.today():
                messages.error(request, "Cannot mark attendance for future dates.")
                return redirect(request.path)

            # Convert times
            try:
                in_time = time.fromisoformat(in_time_str)
                out_time = time.fromisoformat(out_time_str)
            except ValueError:
                messages.error(request, "Invalid time format.")
                return redirect(request.path)

            if status == 'Present' and out_time <= in_time:
                messages.error(request, "Out time must be greater than In time.")
                return redirect(request.path)

            # Save or update attendance
            attendance, created = TrainingAttendance.objects.update_or_create(
                training=training,
                date=attendance_date,  # ✅ Use 'date' field
                defaults={
                    'in_time': in_time,
                    'out_time': out_time,
                    'present': status
                }
            )

            messages.success(request, f"Attendance for {attendance_date} saved successfully.")
            return redirect(request.path)

        # ==================== FINAL RESULT SUBMISSION ====================
        elif action == 'submit_final':
            # Only allow if all past dates have attendance
            past_dates = [d for d in date_range if d <= date.today()]
            recorded_dates = training.attendances.values_list('date', flat=True)
            if not set(past_dates).issubset(set(recorded_dates)):
                messages.error(request, "Please mark attendance for all past dates before final submission.")
                return redirect(request.path)

            attendance_file = request.FILES.get('attendance_field_file')
            performance_appraisal = request.POST.get('performance_appraisal')
            remarks = request.POST.get('remarks')

            if not training.attendance_field_file and not attendance_file:
                messages.error(request, "Attendance file is required.")
                return redirect(request.path)

            if attendance_file:
                training.attendance_field_file = attendance_file
            training.save()

            # Save or update training result
            TrainingResult.objects.update_or_create(
                training=training,
                defaults={
                    'performance_appraisal': performance_appraisal,
                    'remarks': remarks,
                    'attendance_field_file': training.attendance_field_file
                }
            )

            # Update training status
            training.vtc_status = 'approved'
            training.vtc_approved_by = request.user
            training.vtc_approved_at = timezone.now()
            training.aso_status = 'pending'
            training.save()

            messages.success(request, "Attendance and final result submitted successfully.")
            return redirect('vtc:scheduled_training_list')

    # ==================== RENDER TEMPLATE ====================
    context = {
        'training': training,
        'date_range': date_range,
        'existing_attendance': existing_attendance,
        'result': result,
        'today': date.today(),
    }
    return render(request, 'vtc/add_attendance_result.html', context)




from django.shortcuts import render
from .models import TrainingSchedule

from django.shortcuts import render
from .models import TrainingSchedule

def scheduled_training_list(request):
    trainings = TrainingSchedule.objects.filter(created_by_id=request.user).order_by('-from_date')
    return render(request, 'vtc/scheduled_training_list.html', {'trainings': trainings})


from django.shortcuts import render, get_object_or_404
from vtc.models import TrainingSchedule


from django.shortcuts import render
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster , SubsidiaryMaster
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
				# Step 2: Get Subsidiary using subsidiary_id from Area
                subsidiary = SubsidiaryMaster.objects.filter(
                    id=area.subsidiary_id
                ).first()

                if subsidiary:
                    subsidiary_name = subsidiary.subsidiary_name
				
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
			"subsidiary_name": subsidiary_name,
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
    return render(request, 'vtc/certificate_detail.html', context)









