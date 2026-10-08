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

from django.shortcuts import redirect
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



from django.shortcuts import render, redirect
import json

def dashboard(request):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')

    # Get all areas assigned to the current user
    if hasattr(request.user, 'areas'):
        areas = request.user.areas.all().order_by('area_name')
    else:
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
            "total_workers": 0,
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

from django.shortcuts import render, redirect

def aso_forwarded_training_list(request):
    # ✅ AUTH + ROLE CHECK (must be first)
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')

    user_areas = request.user.areas.all()

    trainings = TrainingSchedule.objects.filter(
        aso_status='approved',
        area_name__in=[a.area_name for a in user_areas]
    ).order_by('-to_date')

    return render(request, 'mm/forwarded_training_list.html', {
        'trainings': trainings
    })


# ---------------- Approved Worker Detail ----------------

from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages

def approved_worker_detail(request, pk):
    # ✅ AUTH + ROLE CHECK
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')

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
            messages.success(
                request,
                f"Training for {training.worker.name} has been sent back to ASO for review."
            )
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

import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY


def generate_form_a_pdf(request, training_id):

    # =========================================================
    # GET TRAINING
    # =========================================================

    training = get_object_or_404(
        TrainingSchedule,
        pk=training_id
    )

    worker = training.worker

    # =========================================================
    # CREATOR / TRAINING CENTRE DETAILS
    # =========================================================

    created_user = training.created_by

    created_first_name = (
        created_user.first_name
        if created_user
        else "Unknown"
    )

    user_area = request.user.areas.first()

    area_code = (
        user_area.area_code
        if user_area
        else "UNKNOWN"
    )

    area_name = (
        user_area.area_name
        if user_area
        else "Unknown"
    )

    subsidiary_name = (
        user_area.subsidiary.subsidiary_name
        if user_area and user_area.subsidiary
        else "Unknown"
    )

    subsidiary_code = (
        user_area.subsidiary.subsidiary_code
        if user_area and user_area.subsidiary
        else "NCL"
    )

    # =========================================================
    # CERTIFICATE SERIAL NUMBER
    # =========================================================

    if not training.certificate_serial_number:

        new_serial = generate_unique_serial_number()

        training.certificate_serial_number = new_serial

        training.certificate_serial_number_final = (
            f"VTC{area_code}{new_serial}"
        )

        training.certificate_created_date = timezone.now()

        training.save()

    serial_number = (
        training.certificate_serial_number_final
    )

    # =========================================================
    # CERTIFICATE DATE
    # =========================================================

    date_only = (
        training.certificate_created_date.strftime("%d/%m/%Y")
        if training.certificate_created_date
        else timezone.now().strftime("%d/%m/%Y")
    )

    # =========================================================
    # TRAINING TYPE
    # =========================================================

    training_type = (
        training.type_of_training or ""
    ).strip()

    training_type_lower = (
        training_type.lower()
    )

    is_special = (
        training_type_lower == "special"
    )

    # =========================================================
    # FORM VARIABLES
    # =========================================================

    if is_special:

        form_type = "FORM – T(3)"

        form_description = (
            "The form for the certificate of special training"
        )

        certificate_description = (
            "Certificate of Special Training of persons employed "
            "in coal/metalliferous/oil mine*"
        )

        rule_number = "Rule 162"

    else:

        form_type = "FORM – T(2)"

        form_description = (
            "The form for the certificate of "
            "initial/refresher training"
        )

        certificate_description = (
            "Certificate of Initial/Refresher Training for "
            "employment in a mine on surface and in opencast "
            "workings/belowground degree I/II/III gassy coal/"
            "belowground metalliferous/oil mine*"
        )

        rule_number = (
            "Rule 158/Rule 159/Rule 161*"
        )

    # =========================================================
    # TRAINING DATES
    # =========================================================

    from_date = (
        training.from_date.strftime("%d-%m-%Y")
        if training.from_date
        else "................"
    )

    to_date = (
        training.to_date.strftime("%d-%m-%Y")
        if training.to_date
        else "................"
    )

    # =========================================================
    # WORKER DETAILS
    # =========================================================

    worker_name = (
        worker.name
        or "........................."
    )

    father_name = (
        worker.father_or_spouse_name
        or "........................."
    )

    village = (
        worker.village
        or "........................."
    )

    thana = (
        worker.thana
        or "........................."
    )

    po = (
        worker.po
        or "........................."
    )

    district = (
        worker.district
        or "........................."
    )

    state = (
        worker.state
        or "........................."
    )

    # =========================================================
    # TRAINING FOR
    # =========================================================

    nature = (
        training.nature_of_training
        or "Initial/Refresher Training"
    )

    # =========================================================
    # ATTENDANCE
    # =========================================================

    present_days = training.attendances.filter(
        Q(present=True)
        | Q(present="Present")
        | Q(present="present")
    ).count()

    # =========================================================
    # PDF RESPONSE
    # =========================================================

    response = HttpResponse(
        content_type="application/pdf"
    )

    safe_worker_name = (
        worker.name
        or "worker"
    )

    response["Content-Disposition"] = (
        f'attachment; filename=VTC_certificate_{safe_worker_name}.pdf'
    )

    c = canvas.Canvas(
        response,
        pagesize=A4
    )

    width, height = A4

    # =========================================================
    # SPACING SETTINGS
    # =========================================================

    line_gap = 15

    one_line_gap = 15

    small_gap = 5

    section_gap = 10

    # =========================================================
    # LOGO
    # =========================================================

    logo_path = (
        "E:/VTC training/mysite/static/ncl_logo.jpeg"
    )

    if os.path.exists(logo_path):

        c.drawImage(
            ImageReader(logo_path),
            40,
            height - 110,
            width=120,
            height=100,
            preserveAspectRatio=True
        )

    # =========================================================
    # HEADER
    # =========================================================

    y = height - 50

    # ---------------------------------------------------------
    # SUBSIDIARY
    # ---------------------------------------------------------

    c.setFont(
        "Helvetica-Bold",
        15
    )

    c.drawCentredString(
        width / 2,
        y,
        subsidiary_name
    )

    y -= 20

    # ---------------------------------------------------------
    # CREATED USER
    # ---------------------------------------------------------

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawCentredString(
        width / 2,
        y,
        created_first_name
    )

    y -= 20

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    c.drawCentredString(
        width / 2,
        y,
        "Certificate of Vocational Training"
    )

    y -= 18

    # ---------------------------------------------------------
    # HEADER LINE
    # ---------------------------------------------------------

    c.line(
        50,
        y,
        width - 50,
        y
    )

    y -= section_gap

    # =========================================================
    # FORM NUMBER
    # =========================================================

    c.setFont(
        "Helvetica-Bold",
        11
    )

    c.drawCentredString(
        width / 2,
        y,
        form_type
    )

    y -= line_gap

    # =========================================================
    # FORM DESCRIPTION
    # =========================================================

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawCentredString(
        width / 2,
        y,
        form_description
    )

    y -= line_gap

    # =========================================================
    # RULE REFERENCE
    # =========================================================

    c.setFont(
        "Helvetica",
        9.5
    )

    rule_text = (
        "{See Rule 173(1) of the Occupational Safety, "
        "Health and Working Conditions (Central) Rules, 2026}"
    )

    c.drawCentredString(
        width / 2,
        y,
        rule_text
    )

    # =========================================================
    # NO EXTRA SPACE BETWEEN RULE AND DESCRIPTION
    # =========================================================

    y -= 14

    # =========================================================
    # PARAGRAPH STYLES
    # =========================================================

    styles = getSampleStyleSheet()

    # ---------------------------------------------------------
    # NORMAL JUSTIFIED STYLE
    # ---------------------------------------------------------

    justified_style = ParagraphStyle(
        name="CertificateText",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        spaceBefore=0,
        spaceAfter=0,
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0,
    )

    # ---------------------------------------------------------
    # DESCRIPTION STYLE
    # ---------------------------------------------------------

    description_style = ParagraphStyle(
        name="CertificateDescription",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=14,
        spaceBefore=0,
        spaceAfter=0,
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0,
    )

    # =========================================================
    # CERTIFICATE DESCRIPTION
    # =========================================================

    description_paragraph = Paragraph(
        certificate_description,
        description_style
    )

    description_width = (
        width - 100
    )

    description_w, description_h = (
        description_paragraph.wrap(
            description_width,
            height
        )
    )

    description_paragraph.drawOn(
        c,
        50,
        y - description_h
    )

    # Move exactly after description
    y -= description_h

    # =========================================================
    # ONE LINE GAP BEFORE CERTIFICATE NUMBER
    # =========================================================

    y -= one_line_gap

    # =========================================================
    # CERTIFICATE NUMBER / DATE
    # =========================================================

    c.setFont(
        "Helvetica",
        9
    )

    c.drawString(
        50,
        y,
        f"Certificate No.- {serial_number}"
    )

    c.drawRightString(
        width - 50,
        y,
        f"Date: {date_only}"
    )

    # =========================================================
    # ONE LINE GAP AFTER CERTIFICATE NUMBER
    # =========================================================

    y -= one_line_gap

    # =========================================================
    # MAIN CERTIFICATE PARAGRAPH
    # =========================================================

    if is_special:

        # -----------------------------------------------------
        # DESIGNATION
        # -----------------------------------------------------

        designation = (
            getattr(
                worker,
                "designation",
                None
            )
            or "........................."
        )

        # -----------------------------------------------------
        # SUBJECT
        # -----------------------------------------------------

        subject = (
            training.nature_of_training
            or "........................."
        )

        para_text = f"""
        I, hereby certify that Shri/Smt/Miss
        <b>{worker_name}</b>, Designation
        <b>{designation}</b>, S/o/D/o/W/o
        <b>{father_name}</b>, Village <b>{village}</b>,
        Thana (Police Station) <b>{thana}</b>,
        P.O. <b>{po}</b>, District <b>{district}</b>,
        State <b>{state}</b>, has undergone special training,
        as per provisions of {rule_number} of the Occupational
        Safety, Health and Working Conditions (Central)
        Rules, 2026, during the period from
        <b>{from_date}</b> to <b>{to_date}</b> on the
        subject <b>{subject}</b>. After completion of the
        training the trainee was assessed for his/her
        performance and found to be satisfactory.
        """

    else:

        # -----------------------------------------------------
        # INITIAL / REFRESHER
        # -----------------------------------------------------

        certificate_wording = (
            "certificate of refresher training"
            if training_type_lower == "refresher"
            else "certificate of initial training"
        )

        para_text = f"""
        I, hereby certify that Shri/Smt/Miss
        <b>{worker_name}</b>, S/o/D/o/W/o
        <b>{father_name}</b>, Village <b>{village}</b>,
        Thana (Police Station) <b>{thana}</b>,
        P.O. <b>{po}</b>, District <b>{district}</b>,
        State <b>{state}</b>, has duly undergone
        {certificate_wording} from
        <b>{from_date}</b> to <b>{to_date}</b> as required
        under the provisions of {rule_number} of the
        Occupational Safety, Health and Working Conditions
        (Central) Rules, 2026, for employment in a mine on
        surface and in opencast workings/belowground degree
        I/II/III gassy coal/belowground metalliferous/oil
        mines*. After completion of training the trainee was
        assessed for his/her performance and found to be
        satisfactory.
        """

    main_paragraph = Paragraph(
        para_text,
        justified_style
    )

    paragraph_width = (
        width - 100
    )

    paragraph_w, paragraph_h = (
        main_paragraph.wrap(
            paragraph_width,
            height
        )
    )

    main_paragraph.drawOn(
        c,
        50,
        y - paragraph_h
    )

    # Move exactly below paragraph
    y -= paragraph_h

    # =========================================================
    # ONE LINE GAP BEFORE TRAINING INFORMATION
    # =========================================================

    y -= one_line_gap

    # =========================================================
    # TRAINING INFORMATION
    # =========================================================

    c.setFont(
        "Helvetica",
        9
    )

    # ---------------------------------------------------------
    # TRAINING TYPE
    # ---------------------------------------------------------

    c.drawString(
        50,
        y,
        f"Training Type: {training_type}"
    )

    y -= line_gap

    # ---------------------------------------------------------
    # TRAINING FOR
    # ---------------------------------------------------------

    c.drawString(
        50,
        y,
        f"Training For: {nature}"
    )

    y -= line_gap

    # ---------------------------------------------------------
    # PERIOD OF TRAINING
    # ---------------------------------------------------------

    c.drawString(
        50,
        y,
        f"Period of Training: {from_date} to {to_date}"
    )

    y -= line_gap

    # ---------------------------------------------------------
    # DAYS PRESENT
    # ---------------------------------------------------------

    c.drawString(
        50,
        y,
        f"Days Present: {present_days}"
    )

    y -= section_gap

    # =========================================================
    # PHOTO + SIGNATURE SECTION
    # =========================================================

    def draw_photo_signature(current_y):

        # -----------------------------------------------------
        # PHOTO POSITION
        # -----------------------------------------------------

        photo_x = 50

        photo_width = 100
        photo_height = 110

        photo_y = (
            current_y - photo_height
        )

        # -----------------------------------------------------
        # PHOTO BORDER
        # -----------------------------------------------------

        c.setFont(
            "Helvetica",
            8
        )

        c.rect(
            photo_x,
            photo_y,
            photo_width,
            photo_height
        )

        # -----------------------------------------------------
        # PHOTO
        # -----------------------------------------------------

        if (
            worker.photo
            and os.path.exists(worker.photo.path)
        ):

            c.drawImage(
                worker.photo.path,
                photo_x,
                photo_y,
                width=photo_width,
                height=photo_height,
                preserveAspectRatio=True,
                anchor="c"
            )

        else:

            c.drawCentredString(
                photo_x + photo_width / 2,
                photo_y + 62,
                "Photograph"
            )

            c.drawCentredString(
                photo_x + photo_width / 2,
                photo_y + 50,
                "of Person"
            )

            c.drawCentredString(
                photo_x + photo_width / 2,
                photo_y + 38,
                "Trained"
            )

        # =====================================================
        # SIGNATURE SECTION
        # =====================================================

        signature_top = (
            photo_y - section_gap
        )

        left_x = 50

        right_x = (
            width / 2 + 35
        )

        c.setFont(
            "Helvetica",
            9
        )

        # -----------------------------------------------------
        # SPECIMEN SIGNATURE
        # -----------------------------------------------------

        c.drawString(
            left_x,
            signature_top,
            "Specimen Signature or"
        )

        c.drawString(
            left_x,
            signature_top - line_gap,
            "Left Hand Thumb Impression"
        )

        c.drawString(
            left_x,
            signature_top - (line_gap * 2),
            "of the Person Trained"
        )

        # -----------------------------------------------------
        # TRAINING OFFICER
        # -----------------------------------------------------

        c.drawString(
            right_x,
            signature_top,
            "Signature of Training Officer"
        )

        c.drawString(
            right_x,
            signature_top - line_gap,
            "Name of Training Centre"
        )

        c.drawString(
            right_x,
            signature_top - (line_gap * 2),
            "Training Center Code/ Registration no:"
        )

        # -----------------------------------------------------
        # FIRST DATE
        # -----------------------------------------------------

        c.drawString(
            left_x,
            signature_top - (line_gap * 5),
            "Date..."
        )

        # -----------------------------------------------------
        # COUNTER SIGNATURE
        # -----------------------------------------------------

        c.drawString(
            right_x + 25,
            signature_top - (line_gap * 5),
            "Counter signature of"
        )

        c.drawString(
            right_x + 25,
            signature_top - (line_gap * 6),
            "The Agent or Manager:"
        )

        # -----------------------------------------------------
        # SECOND DATE
        # -----------------------------------------------------

        c.drawString(
            left_x,
            signature_top - (line_gap * 8),
            "Date..."
        )

        return (
            signature_top - (line_gap * 9)
        )

    y = draw_photo_signature(y)

    # =========================================================
    # PERSONAL DETAILS
    # =========================================================

    y -= section_gap

    c.line(
        50,
        y,
        width - 50,
        y
    )

    y -= line_gap

    # ---------------------------------------------------------
    # PERSONAL DETAILS HEADING
    # ---------------------------------------------------------

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        50,
        y,
        "Personal Details of Trainee"
    )

    y -= line_gap

    c.setFont(
        "Helvetica",
        9
    )

    # =========================================================
    # AADHAAR
    # =========================================================

    full_aadhar = (
        worker.aadhar_number or ""
    )

    masked_aadhar = (
        "XXXX-XXXX-" + full_aadhar[-4:]
        if len(full_aadhar) >= 4
        else "Invalid"
    )

    c.drawString(
        50,
        y,
        f"* Aadhaar No. - {masked_aadhar}"
    )

    y -= line_gap

    # =========================================================
    # DATE OF BIRTH
    # =========================================================

    dob = (
        worker.dob.strftime("%d-%m-%Y")
        if worker.dob
        else "Not Available"
    )

    c.drawString(
        50,
        y,
        f"* Date of Birth - {dob}"
    )

    y -= line_gap

    # =========================================================
    # BLOOD GROUP
    # =========================================================

    blood = (
        worker.blood_group
        or "Not Available"
    )

    c.drawString(
        50,
        y,
        f"* Blood Group - {blood}"
    )

    y -= section_gap

    # =========================================================
    # EMPLOYMENT DISCLAIMER
    # =========================================================

    c.setFont(
        "Helvetica-BoldOblique",
        10
    )

    c.drawString(
        50,
        y,
        f"* This certificate will have no claim for employment "
        f"in {subsidiary_code}."
    )

    y -= line_gap

    # =========================================================
    # CERTIFICATE VALIDITY
    # =========================================================

    validity_years = {
        "basic": "....",
        "refresher": "...."
    }.get(
        training_type_lower,
        "...."
    )

    c.setFont(
        "Helvetica",
        9
    )

    c.drawString(
        50,
        y,
        f"* This certificate is valid for {validity_years} years "
        "from date of issue of certificate."
    )

    # =========================================================
    # SAVE PDF
    # =========================================================

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
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q

def certificate_verification(request):
    # ✅ AUTH + ROLE CHECK (add this)
    if not request.user.is_authenticated or request.user.user_type != 'mm':
        return redirect('accounts:login')
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
    if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'mm':
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
        'mm/certificate_detail.html',
        context
    )
