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
            # form.save()
            worker = form.save(commit=False)   # don't save yet
            worker.created_by = request.user   # ✅ assign logged-in user
            worker.save()
            messages.success(request, "Worker added successfully.")
            return redirect('vtc:worker_list')
    else:
        form = IndependentWorkerForm()

    return render(request, 'vtc/worker_form.html', {'form': form})


def view_worker(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)
    form = IndependentWorkerForm(instance=worker)

    # Make all fields readonly or disabled
    for field in form.fields.values():
        field.widget.attrs['readonly'] = True  # For text fields
        field.widget.attrs['disabled'] = True  # For dropdowns, files, etc.

    return render(request, 'vtc/worker_form.html', {
        'form': form,
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


# for training schedule and result
from django.shortcuts import render
from django.shortcuts import render, redirect
from vtc.models import TrainingSchedule

# Create your views here.

# def unscheduled_worker_list(request):
#     # workers = WorkerID.objects.filter(approval_status='pending')
#     workers = IndependentWorker.objects.filter(mm_approval_status='approved')
#     return render(request, 'vtc/hod_approved_workers.html', {'workers': workers})

from datetime import datetime, date  # ensure 'date' is imported
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

def schedule_training(request, pk):
    worker = get_object_or_404(IndependentWorker, pk=pk)

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        type_of_training = request.POST.get('type_of_training')
        nature_of_training = request.POST.get('nature_of_training')
        contractor_name = request.POST.get('contractor_name')

        # Convert to date objects
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date format.')
            return render(request, 'vtc/schedule_training.html', {'worker': worker})

        # ✅ Rule 1: From Date must be today or later
        if from_date < date.today():
            messages.error(request, 'Training can only be scheduled from today or a future date.')
        # ✅ Rule 2: From Date must not be after To Date
        elif from_date > to_date:
            messages.error(request, 'From Date cannot be after To Date.')
        else:
            # ✅ Rule 3: Check for overlapping dates
            overlapping = TrainingSchedule.objects.filter(
                worker=worker,
                from_date__lte=to_date,
                to_date__gte=from_date
            ).exists()

            if overlapping:
                messages.error(request, 'This training period overlaps with an existing training for this worker.')
            else:
                # ✅ Save only if all validations pass
                TrainingSchedule.objects.create(
                    worker=worker,
                    from_date=from_date,
                    to_date=to_date,
                    type_of_training=type_of_training,
                    nature_of_training=nature_of_training,
                    contractor_name=contractor_name,
                    created_by=request.user,
                    modified_by=request.user
                )
                messages.success(request, 'Training scheduled successfully.')
                return redirect('vtc:to_schedule_training')

    return render(request, 'vtc/schedule_training.html', {'worker': worker})



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
from datetime import timedelta
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import timedelta
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from .models import TrainingSchedule, TrainingAttendance, TrainingResult

def add_training_attendance_and_result(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)

    # Generate date range
    date_range = []
    current = training.from_date
    while current <= training.to_date:
        date_range.append(current)
        current += timedelta(days=1)

    # Retrieve attendance with status (Present/Absent/Holiday)
    existing_attendance = {att.date: att.present for att in training.attendances.all()}
    result = getattr(training, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == "save_attendance":
            attendance_date_str = request.POST.get("attendance_date")
            status = request.POST.get("status")

            if not attendance_date_str or not status:
                messages.error(request, "Invalid attendance data.")
            else:
                try:
                    attendance_date = date.fromisoformat(attendance_date_str)  # ✅ Works now
                except ValueError:
                    messages.error(request, f"Invalid date format: {attendance_date_str}")
                    return redirect(request.path)

                # ⛔ Block future dates
                if attendance_date > date.today():
                    messages.error(request, "You cannot mark attendance for a future date.")
                else:
                    attendance, created = TrainingAttendance.objects.get_or_create(
                        training=training,
                        date=attendance_date
                    )
                    if created:  # Only save once
                        attendance.present = status
                        attendance.save()
                        messages.success(request, f"Attendance for {attendance_date} saved as {status}.")
                    else:
                        messages.warning(request, f"Attendance for {attendance_date} is already saved and locked.")

        elif action == "submit_final":
            # Allow forward only if all dates till today are marked
            all_days = [d for d in date_range if d <= date.today()]
            recorded_days = TrainingAttendance.objects.filter(training=training).values_list('date', flat=True)

            if set(all_days).issubset(set(recorded_days)):
                attendance_file = request.FILES.get('attendance_field_file')
                performance_appraisal = request.POST.get('performance_appraisal')
                remarks = request.POST.get('remarks')

                if not training.attendance_field_file and not attendance_file:
                    messages.error(request, "Attendance file is required.")
                    return redirect('your_form_page')
                
                if attendance_file:
                    training.attendance_field_file = attendance_file
                training.save()
                TrainingResult.objects.update_or_create(
                    training=training,
                    defaults={
                        'performance_appraisal': performance_appraisal,
                        'remarks': remarks,
                        'attendance_field_file': attendance_file if attendance_file else training.attendance_field_file
                    }
                )

        # Save the uploaded file if provided
                training.vtc_status = 'approved'
                training.vtc_approved_by = request.user
                training.vtc_approved_at = timezone.now()
                training.aso_status = 'pending'

                training.save()

                messages.success(request, "✅ Attendance & Result submitted for approval.")
                return redirect('vtc:scheduled_training_list')
            else:
                messages.error(request, "⚠ Please mark attendance for all past dates before submitting.")

    return render(request, 'vtc/add_attendance_result.html', {
        'training': training,
        'date_range': date_range,
        'existing_attendance': existing_attendance,
        'result': result,
        'today': date.today(),
    })




from django.shortcuts import render
from .models import TrainingSchedule

def scheduled_training_list(request):
    trainings = TrainingSchedule.objects.filter(created_by_id=request.user).order_by('-from_date')
    return render(request, 'vtc/scheduled_training_list.html', {'trainings': trainings})


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

    return render(request, 'vtc/certificate_detail.html', context)