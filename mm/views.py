from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
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
import random
from django.http import HttpResponseForbidden


# ---------------- Dashboard ----------------
from django.shortcuts import render
import json

def dashboard1(request):
    user_area_name = getattr(request.user, 'area_name', None)

    # Filter areas based on the current user
    if user_area_name:
        areas = AreaMaster.objects.filter(
            area_name=user_area_name
        ).order_by('area_name')
    else:
        areas = AreaMaster.objects.all().order_by('area_name')

    area_data = []

    for area in areas:
        area_name = area.area_name

        # Count trainings per status
        trained_count = TrainingSchedule.objects.filter(
            mm_status='approved',
            area_name=area_name
        ).count()

        under_training_count = TrainingSchedule.objects.filter(
            mm_status='Pending',
            area_name=area_name
        ).count()

        total_trainings_count = TrainingSchedule.objects.filter(
            area_name=area_name
        ).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,  # Optional if you have IndependentWorker model
        })

    # Sort descending by trained count
    area_data = sorted(
        area_data,
        key=lambda x: x['trained'],
        reverse=True
    )

    context = {
        "area_data": area_data,
        "area_labels": json.dumps([a["name"] for a in area_data]),
        "trained_counts": json.dumps([a["trained"] for a in area_data]),
        "under_training_counts": json.dumps([a["under_training"] for a in area_data]),
        "total_trainings_counts": json.dumps([a["total_trainings"] for a in area_data]),
        "labels": json.dumps([a["name"] for a in area_data]),
        "trained": json.dumps([a["trained"] for a in area_data]),
        "under_training": json.dumps([a["under_training"] for a in area_data]),
        "total": json.dumps([a["total_trainings"] for a in area_data]),
        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
        "level": "area",
    }

    return render(request, "mm/dashboard.html", context)

def dashboard(request):
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')
    # Get all areas assigned to the current user
    if hasattr(request.user, 'areas'):
        areas = request.user.areas.all().order_by('area_name')
    else:
        # If user has no areas, show nothing
        areas = AreaMaster.objects.none()

    area_data = []

    for area in areas:
        area_name = area.area_name

        # Count trainings per status
        trained_count = TrainingSchedule.objects.filter(
            mm_status='approved',
            area_name=area_name
        ).count()

        under_training_count = TrainingSchedule.objects.filter(
            mm_status='Pending',
            area_name=area_name
        ).count()

        total_trainings_count = TrainingSchedule.objects.filter(
            area_name=area_name
        ).count()

        area_data.append({
            "name": area_name,
            "trained": trained_count,
            "under_training": under_training_count,
            "total_trainings": total_trainings_count,
            "total_workers": 0,  # Optional if you have IndependentWorker model
        })

    # Sort descending by trained count
    area_data = sorted(
        area_data,
        key=lambda x: x['trained'],
        reverse=True
    )

    context = {
        "area_data": area_data,
        "area_labels": json.dumps([a["name"] for a in area_data]),
        "trained_counts": json.dumps([a["trained"] for a in area_data]),
        "under_training_counts": json.dumps([a["under_training"] for a in area_data]),
        "total_trainings_counts": json.dumps([a["total_trainings"] for a in area_data]),
        "labels": json.dumps([a["name"] for a in area_data]),
        "trained": json.dumps([a["trained"] for a in area_data]),
        "under_training": json.dumps([a["under_training"] for a in area_data]),
        "total": json.dumps([a["total_trainings"] for a in area_data]),
        "total_trained": sum(a['trained'] for a in area_data),
        "total_under_training": sum(a['under_training'] for a in area_data),
        "total_trainings": sum(a['total_trainings'] for a in area_data),
        "level": "area",
    }

    return render(request, "mm/dashboard.html", context)

# ---------------- ASO Forwarded Training ----------------
def aso_forwarded_training_list(request):
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')
    user_areas = request.user.areas.all()
    trainings = TrainingSchedule.objects.filter(
        aso_status='approved',
        area_name__in=[a.area_name for a in user_areas]
    ).order_by('-to_date')
    return render(request, 'mm/forwarded_training_list.html', {'trainings': trainings})


# ---------------- Approved Worker Detail ----------------
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


# ---------------- Generate Unique Serial Number ----------------
def generate_unique_serial_number():
    last_number = TrainingSchedule.objects.filter(certificate_serial_number__isnull=False).order_by('-certificate_serial_number').first()
    if last_number:
        return last_number.certificate_serial_number + 1
    else:
        return 10000000  # Start from an 8-digit number


# ---------------- Generate Form A PDF ----------------
def generate_form_a_pdf(request, training_id):
    training = get_object_or_404(TrainingSchedule, pk=training_id)
    worker = training.worker

    user_area = request.user.areas.first()
    area_code = user_area.area_code if user_area else "UNKNOWN"
    area_name = user_area.area_name if user_area else "Unknown"
    subsidiary_name = user_area.subsidiary.subsidiary_name if user_area and user_area.subsidiary else "Unknown"
    subsidiary_code = user_area.subsidiary.subsidiary_code if user_area and user_area.subsidiary else "NCL"

    if not training.certificate_serial_number:
        new_serial = generate_unique_serial_number()
        training.certificate_serial_number = new_serial
        training.certificate_serial_number_final = f"VTC{area_code}{new_serial}"
        training.certificate_created_date = timezone.now()
        training.save()

    serial_number = training.certificate_serial_number_final

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=VTC_certificate_{worker.name}.pdf'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    logo_path = "E:/VTC training/mysite/static/ncl_logo.jpeg"

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 40, height - 110, width=120, height=100, preserveAspectRatio=True)

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
    description = (
        "Certificate of Training for employment in mine on surface and in opencast working"
        if training.type_of_training == "Basic"
        else "Certificate of Refresher Training / Training of special categories of workmen"
    )
    c.drawCentredString(width / 2, y, description)
    y -= 20

    date_only = training.certificate_created_date.strftime('%d/%m/%Y')
    c.drawString(50, y, f"Certificate No.- {serial_number}                                                                                       Issue Date:{date_only}")
    y -= 50

    # Paragraph
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
    chapter = "Chapter III" if training.type_of_training == "Basic" else "Chapter IV / Chapter V"

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
    y -= line_gap * 4

    # Training info
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Type of Training: ")
    label_width = c.stringWidth("Type of Training :", "Helvetica", 10)
    c.drawString(50 + label_width + 5, y, f"{training.type_of_training} Training")

    y -= line_gap
    c.drawString(50, y, "Training For:")
    label_width = c.stringWidth("Training For:", "Helvetica", 10)
    c.drawString(50 + label_width + 5, y, f"{training.nature_of_training}")
    c.drawRightString(width - 50, y, "Signed...................................................")

    y -= line_gap
    present_days = training.attendances.filter(Q(present=True) | Q(present='Present') | Q(present='present')).count()
    c.drawString(50, y, f"Period of training: {from_date} to {to_date} (Days Present: {present_days})")
    y -= line_gap * 2
    c.drawRightString(width - 50, y, "Training Officer..........................................")

    right_x = width / 2 + 50
    right_y = y - 20
    c.drawString(right_x, right_y, f"Mine/Training Center: {area_name}")
    y -= line_gap
    right_y = y - 20
    c.drawString(right_x, right_y, "Registration No. of the Training Centre: .......")

    # Photo
    photo_x = 50
    photo_y = y - 120
    if worker.photo and os.path.exists(worker.photo.path):
        c.drawImage(worker.photo.path, photo_x, photo_y, width=100, height=120)
    else:
        c.rect(photo_x, photo_y, 100, 120)
        c.drawString(photo_x + 20, photo_y + 60, "No Photo")

    # Counter Signature
    right_x = width / 2 + 50
    right_y = photo_y + 40
    c.drawString(right_x, right_y, "Counter Signature of")
    right_y -= line_gap
    c.drawString(right_x, right_y, "The Agent or Manager.............")

    y -= 200
    # Footer
    c.line(50, y, width - 50, y)
    y -= line_gap
    c.drawString(50, y, "Personal Details of Trainee")
    y -= line_gap

    full_aadhar = worker.aadhar_number or ""
    masked_aadhar = "XXXX-XXXX-" + full_aadhar[-4:] if len(full_aadhar) >= 4 else "Invalid"
    c.drawString(50, y, f"* Aadhaar No. - {masked_aadhar}")
    y -= line_gap

    dob = worker.dob.strftime("%d-%m-%Y") if worker.dob else "Not Available"
    c.drawString(50, y, f"* Date of Birth - {dob}")
    y -= line_gap

    blood = worker.blood_group if worker.blood_group else "Not Available"
    c.drawString(50, y, f"* Blood Group - {blood}")
    y -= line_gap * 2

    c.setFont("Helvetica-BoldOblique", 10)
    c.drawString(50, y, f"* This certificate will have no claim for employment in {subsidiary_code}.")
    y -= line_gap

    validity_years = {"Basic": "5", "Refresher": "5"}.get(training.type_of_training, "....")
    c.drawString(50, y, f"* This certificate is valid for {validity_years} years from date of issue of certificate.")

    c.showPage()
    c.save()
    return response


# ---------------- Verify Certificate ----------------
def verify_certificate(request, serial_number):
    training = get_object_or_404(TrainingSchedule, certificate_serial_number=serial_number)
    worker = training.worker
    return render(request, 'mm/verify.html', {'training': training, 'worker': worker})


# ---------------- Certificate Verification ----------------
# def certificate_verification(request):
#     serial_number = request.GET.get('serial_number')
#     aadhar_number = request.GET.get('aadhar_number')
#     training = None
#     searched = False
#     present_days = 0

#     if serial_number or aadhar_number:
#         searched = True
#         try:
#             if serial_number:
#                 training = TrainingSchedule.objects.select_related('worker').get(
#                     certificate_serial_number_final=serial_number
#                 )
#         except TrainingSchedule.DoesNotExist:
#             training = None

#     if training:
#         present_days = training.attendances.filter(Q(present=True) | Q(present='Present') | Q(present='present')).count()

#     return render(request, 'mm/certificate_verification.html', {
#         'training': training,
#         'present_days': present_days,
#         'searched': searched
#     })


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
            return render(request, 'mm/certificate_verification.html', {
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
                url = reverse('mm:certificate_detail')
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

    return render(request, 'mm/certificate_verification.html', {
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
        schedule_number = "First" if training.type_of_training == "Basic" else "Fourth" if training.type_of_training == "Refresher" else ""
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
