from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse

from vtc.models import TrainingSchedule, IndependentWorker
from accounts.models import AreaMaster

import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import enums

# -----------------------------
# Dashboard
# -----------------------------
def dashboard(request):
    user_area_name = getattr(request.user, 'area_name', None)
    
    if user_area_name:
        areas = AreaMaster.objects.filter(area_name=user_area_name).order_by('area_name')
    else:
        areas = AreaMaster.objects.all().order_by('area_name')

    area_data = []
    for area in areas:
        area_name = area.area_name
        trained_count = TrainingSchedule.objects.filter(mm_status='approved', area_name=area_name).count()
        under_training_count = TrainingSchedule.objects.filter(Q(mm_status__isnull=True) | Q(mm_status='Pending'), area_name=area_name).count()
        total_trainings_count = TrainingSchedule.objects.filter(area_name=area_name).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,  # Optional if you have IndependentWorker model
        })

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
        "level": "area",
    }
    return render(request, "mm/dashboard.html", context)

# -----------------------------
# ASO Forwarded Trainings
# -----------------------------
def aso_forwarded_training_list(request):
    user_areas = request.user.areas.all()
    trainings = TrainingSchedule.objects.filter(
        aso_status='approved',
        area_name__in=[a.area_name for a in user_areas]
    )
    return render(request, 'mm/forwarded_training_list.html', {'trainings': trainings})

# -----------------------------
# Approved Worker Detail
# -----------------------------
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
            training.save()
            messages.success(request, f"Training for {training.worker.name} has been sent back to ASO for review.")
        return redirect('mm:approved_worker_detail', pk=pk)

    return render(request, 'mm/approved_worker_detail.html', {
        'training': training,
        'attendances': attendances,
        'result': result
    })

# -----------------------------
# Certificate Serial Number
# -----------------------------
def generate_unique_serial_number():
    last_number = TrainingSchedule.objects.filter(certificate_serial_number__isnull=False).order_by('-certificate_serial_number').first()
    return last_number.certificate_serial_number + 1 if last_number else 10000000

# -----------------------------
# Generate Form-A PDF
# -----------------------------
def generate_form_a_pdf(request, training_id):
    training = get_object_or_404(TrainingSchedule, pk=training_id)
    worker = training.worker

    # Area & Subsidiary
    user_area = request.user.areas.first()
    area_code = user_area.area_code if user_area else "UNKNOWN"
    area_name = user_area.area_name if user_area else "Unknown"
    subsidiary_name = user_area.subsidiary.subsidiary_name if user_area and user_area.subsidiary else "Unknown"
    subsidiary_code = user_area.subsidiary.subsidiary_code if user_area and user_area.subsidiary else "NCL"

    # Serial Number
    if not training.certificate_serial_number:
        new_serial = generate_unique_serial_number()
        training.certificate_serial_number = new_serial
        training.certificate_serial_number_final = f"VTC{area_code}{new_serial}"
        training.certificate_created_date = timezone.now()
        training.save()

    serial_number = training.certificate_serial_number_final

    # PDF Response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=VTC_certificate_{worker.name}.pdf'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    line_gap = 16

    # Logo
    logo_path = "E:/VTC training/mysite/static/ncl_logo.jpeg"
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 40, height - 110, width=120, height=100, preserveAspectRatio=True)

    # Header
    y = height - 50
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

    # Certificate details
    from_date = training.from_date.strftime("%d-%m-%Y")
    to_date = training.to_date.strftime("%d-%m-%Y")
    date_only = training.certificate_created_date.strftime('%d/%m/%Y')
    chapter = "Chapter III" if training.type_of_training == "Basic" else "Chapter IV / Chapter V"
    form_type = "FORM - A" if training.type_of_training == "Basic" else "FORM - B"

    # Paragraph
    styles = getSampleStyleSheet()
    justified_style = ParagraphStyle(
        name='Justified', parent=styles['Normal'], alignment=enums.TA_JUSTIFY,
        fontName='Helvetica', fontSize=10, leading=18
    )
    para_text = f"""
    I hereby certify that Shri/Shrimati <b>{worker.name}</b>, 
    S/o/D/o/W/o <b>{worker.father_or_spouse_name}</b>,
    of Village <b>{worker.village}</b>, Thana <b>{worker.thana}</b>,
    PO <b>{worker.po}</b>, District <b>{worker.district}</b>,
    State <b>{worker.state}</b>, has between {from_date} to {to_date}
    duly undergone the training required under {chapter} of the
    Mine Vocational Training Rules, 1966.
    """
    paragraph = Paragraph(para_text, justified_style)
    frame = Frame(50, y - 80, width - 100, 120, showBoundary=0)
    frame.addFromList([paragraph], c)

    # Footer, photo, training info, etc.
    # (Keep same as your existing implementation)
    c.showPage()
    c.save()
    return response

# -----------------------------
# Certificate Verification / Detail
# -----------------------------
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
        present_days = training.attendances.filter(Q(present=True) | Q(present='Present') | Q(present='present')).count()

    return render(request, 'mm/certificate_verification.html', {
        'training': training,
        'present_days': present_days,
        'searched': searched
    })


def certificate_detail(request):
    serial_number = request.GET.get('serial_number')
    training = None
    searched = False
    area_name = "Unknown"

    if serial_number:
        searched = True
        try:
            training = TrainingSchedule.objects.select_related('worker').get(certificate_serial_number_final=serial_number)
            area_code = serial_number[3:6]
            area = AreaMaster.objects.filter(area_code=area_code).first()
            if area:
                area_name = area.area_name
        except TrainingSchedule.DoesNotExist:
            training = None

    if training:
        worker = training.worker
        from_date_str = training.from_date.strftime("%d-%m-%Y")
        to_date_str = training.to_date.strftime("%d-%m-%Y")
        present_days = training.attendances.filter(present="Present").count()
        schedule_number = "First" if training.type_of_training == "Basic" else "Fourth"
        chapter = "Chapter III" if training.type_of_training == "Basic" else "Chapter IV/Chapter V"
        form_type = "FORM - A" if training.type_of_training == "Basic" else "FORM - B"
        validity_years = {"Basic": "5", "Refresher": "3"}.get(training.type_of_training, "....")
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
        context = {"training": None, "worker": None, "searched": searched}

    return render(request, 'mm/certificate_detail.html', context)
