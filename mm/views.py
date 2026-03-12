from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render

from vtc.models import TrainingSchedule
from django.contrib import messages

# Create your views here.
from django.utils import timezone
from django.db.models import Count, Q

from django.shortcuts import render
from django.db.models import Q
from vtc.models import TrainingSchedule
from accounts.models import AreaMaster
import json

from django.shortcuts import render
from django.db.models import Q
import json
#from .models import TrainingSchedule, IndependentWorker

from django.db.models import Q
import json

def dashboard(request):
    areas = AreaMaster.objects.all().order_by('area_name')
    area_data = []

    for area in areas:
        area_name = area.area_name

        trained_count = TrainingSchedule.objects.filter(
            mm_status='approved',
            area_name=area_name
        ).count()

        under_training_count = TrainingSchedule.objects.filter(
            Q(mm_status__isnull=True) | Q(mm_status='Pending'),
            area_name=area_name
        ).count()

        total_trainings_count = TrainingSchedule.objects.filter(
            area_name=area_name
        ).count()

#        total_workers_count = IndependentWorker.objects.filter(
 #           area_name=area_name
  #      ).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,
        })

    area_data = sorted(area_data, key=lambda x: x['trained'], reverse=True)

    context = {
        "area_data": area_data,
        "area_labels": json.dumps([a["name"] for a in area_data]),
        "trained_counts": json.dumps([a["trained"] for a in area_data]),
        "under_training_counts": json.dumps([a["under_training"] for a in area_data]),
        "total_trainings_counts": json.dumps([a["total_trainings"] for a in area_data]),
#        "total_workers_counts": json.dumps([a["total_workers"] for a in area_data]),
        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
#        "total_workers": sum(a['total_workers'] for a in area_data),
    }

    return render(request, "mm/dashboard.html", context)



# def hod_forwarded_workers_list(request):
#     workers =WorkerID.objects.filter(hod_approval_status='approved',mm_approval_status='pending')
#     return render(request, 'mm/forwarded_worker_list.html', {'workers': workers})

# def mm_forwarded_workers_list(request):
#     workers =WorkerID.objects.filter(hod_approval_status='approved',mm_approval_status='approved')
#     return render(request, 'mm/mm_forwarded_worker_list.html', {'workers': workers})

# from django.shortcuts import redirect, get_object_or_404
# from django.contrib import messages
# from vtc.models import IndependentWorker

# def forward_to_vtc(request, pk):
#     worker = get_object_or_404(WorkerID, pk=pk)
#     # Update status or logic to forward to VTC
#     worker.mm_approval_status = 'approved'
#     worker.save()
#     messages.success(request, f'{worker.name} has been forwarded to VTC.')
#     return redirect('mm:forwarded_workers')





def aso_forwarded_training_list(request):
    user_areas = request.user.areas.all()
    trainings = TrainingSchedule.objects.filter(
        aso_status='approved',
        area_name__in=[a.area_name for a in request.user.areas.all()]
        )
    return render(request, 'mm/forwarded_training_list.html', {'trainings': trainings})

def approved_worker_detail(request, pk):
    training = get_object_or_404(TrainingSchedule, pk=pk)
    attendances = training.attendances.all()
    result = getattr(training, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            training.mm_status = 'approved'
            training.mm_approved_by = request.user
            training.mm_approved_at = timezone.now()
            training.save()
            messages.success(request, 'Training approved successfully.')
        elif action == 'reject':
            training.mm_status = 'Pending'
            training.aso_status = 'Pending'
            messages.success(request, f"Training for {training.worker.name} has been sent back to ASO for review.")
            training.save()
            
        return redirect('mm:approved_worker_detail', pk=pk)

    return render(request, 'mm/approved_worker_detail.html', {
        'training': training,
        'attendances': attendances,
        'result': result
    })

import random
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from vtc.models import IndependentWorker
from vtc.models import TrainingSchedule

def generate_unique_serial_number():
    last_number = TrainingSchedule.objects.filter(certificate_serial_number__isnull=False).order_by('-certificate_serial_number').first()
    if last_number:
        return last_number.certificate_serial_number + 1
    else:
        return 10000000  # Start from an 8-digit number
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from vtc.models import IndependentWorker
from vtc.models import TrainingSchedule
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import enums
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import enums

def generate_form_a_pdf(request, training_id):

    training = get_object_or_404(TrainingSchedule, pk=training_id)
    worker = training.worker

    user_area = request.user.areas.first()

    area_code = user_area.area_code if user_area else "Unknown"
    area_name = user_area.area_name if user_area else "Unknown"
    subsidiary_name = (
        user_area.subsidiary.subsidiary_name
        if user_area and user_area.subsidiary
        else "Unknown"
    )

    # Generate Serial Number
    if not training.certificate_serial_number:

        last = TrainingSchedule.objects.filter(
            certificate_serial_number__isnull=False
        ).order_by('-certificate_serial_number').first()

        new_serial = (last.certificate_serial_number + 1) if last else 10000000

        training.certificate_serial_number = new_serial
        training.certificate_serial_number_final = f"VTC{area_code}{new_serial}"
        training.certificate_created_date = timezone.now()
        training.save()

    serial_number = training.certificate_serial_number_final

    # Create Response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=VTC_certificate_{worker.name}.pdf'

    c = canvas.Canvas(response, pagesize=A4)

    width, height = A4

    # Logo
    logo_path = "E:/VTC training/mysite/static/ncl_logo.jpeg"

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 40, height - 110, width=120, height=100)

    y = height - 50
    line_gap = 16

    # Header
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width / 2, y, subsidiary_name)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, f"{area_name} MINE")

    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "Certificate of Vocational Training")

    y -= 15
    c.line(50, y, width - 50, y)

    y -= 15
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "Mines Vocation Training Rules, 1966")

    y -= 15

    form_type = "FORM - A" if training.type_of_training == "Basic" else "FORM - B"

    c.drawCentredString(width / 2, y, form_type)

    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, y, "{Rule 28(1)}")

    y -= 15
    c.setFont("Helvetica", 10)

    form_desc = (
        "Certificate of Training for employment in mine on surface and in opencast working"
        if training.type_of_training == "Basic"
        else "Certificate of Refresher Training/Training of special categories of workmen"
    )

    c.drawCentredString(width / 2, y, form_desc)

    y -= 20

    date_only = training.certificate_created_date.strftime('%d/%m/%Y')

    c.drawString(
        50,
        y,
        f"Certificate No.- {serial_number}                         Issue Date:{date_only}"
    )

    y -= 50

    # Paragraph Style
    styles = getSampleStyleSheet()

    justified_style = ParagraphStyle(
        name='Justified',
        parent=styles['Normal'],
        alignment=enums.TA_JUSTIFY,
        fontName='Helvetica',
        fontSize=10,
        leading=18,
    )

    from_date = training.from_date.strftime("%d-%m-%Y")
    to_date = training.to_date.strftime("%d-%m-%Y")

    chapter = "Chapter III" if training.type_of_training == "Basic" else "Chapter IV/Chapter V"

    para_text = f"""
    I hereby certify that Shri/Shrimati <b>{worker.name}</b>,
    S/o/D/o/W/o <b>{worker.father_or_spouse_name}</b>,
    of Village <b>{worker.village}</b>, Thana <b>{worker.thana}</b>,
    PO <b>{worker.po}</b>, District <b>{worker.district}</b>,
    State <b>{worker.state}</b>, has between {from_date} to {to_date}
    duly undergone the training required under {chapter} of the Mine
    Vocational Training Rules, 1966.
    """

    paragraph = Paragraph(para_text, justified_style)

    frame = Frame(50, y - 80, width - 100, 120, showBoundary=0)

    frame.addFromList([paragraph], c)

    y -= line_gap * 6

    # Training Type
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Type of Training: {training.type_of_training} Training")

    y -= line_gap

    c.drawString(50, y, f"Training For: {training.nature_of_training}")

    c.drawRightString(width - 50, y, "Signed...................................")

    y -= line_gap

    present_days = training.attendances.filter(
        Q(present=True) | Q(present='Present') | Q(present='present')
    ).count()

    c.drawString(
        50,
        y,
        f"Period of training: {from_date} to {to_date} (Days Present: {present_days})"
    )

    y -= line_gap * 2

    c.drawRightString(width - 50, y, "Training Officer............................")

    y -= line_gap

    c.drawRightString(width - 50, y, f"Mine/Training Center: {area_name}")

    y -= line_gap

    c.drawRightString(width - 50, y, "Registration No. of Training Centre: ......")

    # Photo
    photo_x = 50
    photo_y = y - 120

    if worker.photo and os.path.exists(worker.photo.path):
        c.drawImage(worker.photo.path, photo_x, photo_y, width=100, height=120)
    else:
        c.rect(photo_x, photo_y, 100, 120)
        c.drawString(photo_x + 20, photo_y + 60, "No Photo")

    # Footer
    y = photo_y - 30

    c.line(50, y, width - 50, y)

    y -= line_gap

    c.drawString(50, y, "Personal Details of Trainee")

    y -= line_gap

    full_adhar = worker.aadhar_number or ""
    masked_adhar = "XXXX-XXXX-" + full_adhar[-4:] if len(full_adhar) >= 4 else "Invalid"

    c.drawString(50, y, f"* Aadhar No. - {masked_adhar}")

    y -= line_gap

    dob = worker.dob.strftime("%d-%m-%Y")

    c.drawString(50, y, f"* Date of Birth - {dob}")

    y -= line_gap

    c.drawString(50, y, f"* Blood Group - {worker.blood_group}")

    y -= line_gap * 2

    c.setFont("Helvetica-BoldOblique", 10)

    c.drawString(50, y, "* This certificate will have no claim for employment in NCL.")

    y -= line_gap

    validity = "5"

    c.drawString(50, y, f"* This certificate is valid for {validity} years from date of issue.")

    c.showPage()
    c.save()

    return response






def verify_certificate(request, serial_number):
    training = get_object_or_404(TrainingSchedule, certificate_serial_number=serial_number)
    worker = training.worker
    return render(request, 'mm/verify.html', {'training': training, 'worker': worker})


from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from vtc.models import TrainingSchedule

def certificate_verification(request):
    serial_number = request.GET.get('serial_number')
    aadhar_number = request.GET.get('aadhar_number')
    training = None
    searched = False
    present_days = 0

    if serial_number or aadhar_number:
        searched = True
        try:
            if serial_number:
                training = TrainingSchedule.objects.select_related('worker').get(
                    certificate_serial_number_final=serial_number
                )
            
        except TrainingSchedule.DoesNotExist:
            training = None

    if training:
        present_days = training.attendances.filter(
            Q(present=True) | Q(present='Present') | Q(present='present')
            ).count()

    return render(request, 'mm/certificate_verification.html', {
        'training': training,
        'present_days': present_days,
        'searched': searched
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

    return render(request, 'mm/certificate_detail.html', context)



























