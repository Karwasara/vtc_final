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
from django.contrib.auth.decorators import login_required

@login_required(login_url='accounts:login')
def dashboard(request):
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
    return render(request, 'vtc/dashboard.html')

#List View
from django.db.models import Q
from django.shortcuts import render, redirect
@login_required(login_url='accounts:login')
def to_schedule_training(request):

    # AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')

    search_query = request.GET.get('q', '').strip()

    workers = IndependentWorker.objects.filter(delete_flag=False)

    # Search full database (Name + Aadhaar only)
    if search_query:
        workers = workers.filter(
            Q(name__icontains=search_query) |
            Q(aadhar_number__icontains=search_query)
        ).order_by('-id')

    # Default: latest 100 records
    else:
        workers = workers.order_by('-id')[:100]

    return render(request, 'vtc/to_schedule_training.html', {
        'workers': workers,
        'search_query': search_query
    })
	
from django.db.models import Q
from django.shortcuts import redirect, render
@login_required(login_url='accounts:login')
def worker_list(request):

    # Authentication + role check
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')

    search_query = request.GET.get('q', '').strip()

    workers = IndependentWorker.objects.filter(delete_flag=False)

    if search_query:
        workers = workers.filter(
            Q(name__icontains=search_query) |
            Q(aadhar_number__icontains=search_query)
        ).order_by('-id')

    else:
        workers = workers.order_by('-id')[:100]  # fixed to 100 records

    return render(request, 'vtc/worker_list.html', {
        'workers': workers,
        'search_query': search_query
    })

#Add worker
@login_required(login_url='accounts:login')
def add_worker(request):
    # ✅ AUTH + ROLE CHECK
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
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

@login_required(login_url='accounts:login')
def view_worker(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
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

@login_required(login_url='accounts:login')
def schedule_training(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
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
@login_required(login_url='accounts:login')
def edit_training(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
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
@login_required(login_url='accounts:login')
def add_training_attendance_and_result(request, pk):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
    training = get_object_or_404(TrainingSchedule, pk=pk)

    # Generate date range from training
    date_range = []
    current = training.from_date
    while current <= training.to_date:
        date_range.append(current)
        current += timedelta(days=1)

    # Existing attendance keyed by date
    existing_attendance = {att.date: att for att in training.attendances.all()}
    print(existing_attendance)
     # ✅ STEP 1: Get worker (linked to training)
    worker = training.worker

    # 🔗 IMPORTANT: Aadhaar ↔ EmployeeCode mapping
    employee_code = worker.aadhar_number

    bio_qs = BiometricAttendanceRaw.objects.filter(
    employee_code=employee_code,
    attendance_date__range=(training.from_date, training.to_date)
    )

    bio_dict = {b.attendance_date: b for b in bio_qs}

    # print(bibio_dicto.attendance_date, in_time, out_time)
    # Get training result if exists
    result = getattr(training, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ==================== SAVE DAILY ATTENDANCE ====================
        if action == 'save_attendance':
            attendance_date_str = request.POST.get('attendance_date')
            in_time_str = request.POST.get('in_time') or None
            out_time_str = request.POST.get('out_time') or None
            status = request.POST.get('status')
            print(status,in_time_str,out_time_str,attendance_date_str)

            if not all([attendance_date_str, status]):
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
                in_time = time.fromisoformat(in_time_str) if in_time_str else None
                out_time = time.fromisoformat(out_time_str) if out_time_str else None
            except ValueError:
                messages.error(request, "Invalid time format.")
                return redirect(request.path)

            if status == 'Present':
                if in_time and out_time:
                    if out_time <= in_time:
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
        'bio_dict': bio_dict,
        'today': date.today(),
    }
    return render(request, 'vtc/add_attendance_result.html', context)




from django.shortcuts import render
from .models import TrainingSchedule

from django.shortcuts import render
from .models import TrainingSchedule
@login_required(login_url='accounts:login')
def scheduled_training_list(request):
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')

    trainings = TrainingSchedule.objects.filter(
        created_by_id=request.user
    ).order_by('-from_date')

    return render(request, 'vtc/scheduled_training_list.html', {
        'trainings': trainings
    })


from django.shortcuts import render, get_object_or_404
from vtc.models import TrainingSchedule


from django.shortcuts import render
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster , SubsidiaryMaster
@login_required(login_url='accounts:login')
def certificate_detail(request):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'vtc':
        return redirect('accounts:login')
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



#biometric NCL
import requests
import requests
from datetime import date
from .models import TrainingSchedule, BiometricAPILog
from accounts.models import AreaMaster , SubsidiaryMaster,CustomUser

def fetch_biometric_data(from_date, to_date, employee_code=""):
    # If no specific employee code is provided, perform the reversed step-by-step lookup
    if not employee_code:
        # Step 1: Get all training schedules active today
        active_schedules = TrainingSchedule.objects.filter(
            from_date__lte=from_date,
            to_date__gte=to_date
        ).select_related('worker')

        # Step 2: Extract unique creator user IDs from today's schedules
        creator_ids = list(set([
            schedule.created_by_id 
            for schedule in active_schedules 
            if schedule.created_by_id
        ]))

        if not creator_ids:
            return []  # No scheduled trainings created by anyone today

        # Step 3: Fetch the user records to map their user ID to their subsidiary ID
        users = CustomUser.objects.filter(
            id__in=creator_ids
        ).values('id', 'subsidiary_id')
        
        user_to_subsidiary_map = {
            user['id']: user['subsidiary_id'] 
            for user in users 
            if user['subsidiary_id'] is not None
        }

        # Step 4: Query the Subsidiary master to filter only those subsidiary IDs whose code is "ncl"
        unique_subsidiary_ids = list(set(user_to_subsidiary_map.values()))
        ncl_subsidiary_ids = list(SubsidiaryMaster.objects.filter(
            id__in=unique_subsidiary_ids,
            subsidiary_code__iexact="ncl"
        ).values_list('id', flat=True))

        # Step 5: Filter the schedules down to only those created by users belonging to "ncl"
        ncl_schedules = []
        for schedule in active_schedules:
            creator_id = schedule.created_by_id
            user_sub_id = user_to_subsidiary_map.get(creator_id)
            
            if user_sub_id in ncl_subsidiary_ids:
                ncl_schedules.append(schedule)

        # Step 6: Extract the unique employee ID card numbers
        employee_codes = list(set([
            schedule.worker.aadhar_number 
            for schedule in ncl_schedules 
            if schedule.worker and schedule.worker.aadhar_number
        ]))
        
        # Join into a comma-separated string (e.g. "EMP01,EMP02")
        employee_code = ",".join(employee_codes)

    # --- API request payload and log creation ---
    url = "http://112.133.254.146:41000/TimeWatchAPI/NCLAttendance"

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": "T!meW@tch#123@"
    }

    payload = {
        "FromDate": str(from_date),
        "ToDate": str(to_date),
        "EmployeeCode": employee_code
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        status_str = 'success' if response.status_code == 200 else 'failed'
    except Exception as e:
        response_data = {"error": str(e)}
        status_str = 'failed'

    # Save transaction log in database
    BiometricAPILog.objects.create(
        employee_code=employee_code,
        from_date=from_date,
        to_date=to_date,
        request_payload=payload,
        response_payload=response_data,
        status=status_str
    )

    return response_data




from django.http import HttpResponseForbidden, JsonResponse
from datetime import date

from .models import BiometricAttendanceRaw
def biometric_api_test(request):
    try:
        today = date.today()

        data = fetch_biometric_data(
            from_date=today,
            to_date=today,
            employee_code=""   # empty = all employees
        )
       # print(data)
        return JsonResponse({
            "status": "success",
            "count": len(data),
            "data": data[:5]  # show only first 5 records
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })

from datetime import datetime

def parse_datetime(dt_str):
    if not dt_str:
        return None
    return datetime.strptime(dt_str, "%m/%d/%Y %I:%M:%S %p")


def store_biometric_data(api_response):
    records = api_response.get("Data", []) # handle both formats

    print("Records received:", len(records))

    for record in records:
        print(record)
        try:
            attendance_date = datetime.strptime(
                record["AttendanceDate"].split("T")[0],
                "%Y-%m-%d"
            ).date()

            in_time = parse_datetime(record.get("IN"))
            out_time = parse_datetime(record.get("OUT"))

            obj, created = BiometricAttendanceRaw.objects.update_or_create(
                employee_code=record["EmployeeCode"],
                attendance_date=attendance_date,
                defaults={
                    "employee_name": record.get("EmployeeName"),
                    "in_time": in_time,
                    "out_time": out_time,
                    "status": record.get("Status", "").strip(),
                }
            )

            print("Saved:", obj.employee_code, "Created:", created)

        except Exception as e:
            print("❌ Error:", e)


from django.http import JsonResponse
from datetime import date

from .models import TrainingSchedule

def sync_biometric_attendance(request):
    try:
        # ✅ Step 1: Get today's date
        today = date.today()

        # ✅ Step 2: Call API (bulk fetch)
        api_response = fetch_biometric_data(today, today, "")

        # ✅ Step 3: Store raw data
        store_biometric_data(api_response)

        # ✅ Step 4: Process trainings of today
        # trainings = TrainingSchedule.objects.filter(
        #     start_date__lte=today,
        #     end_date__gte=today
        # )

        # for training in trainings:
        #     process_attendance(training, today)

        return JsonResponse({
            "status": "success",
            "message": "Biometric attendance synced successfully"
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })








