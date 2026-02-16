from django import forms
from .models import IndependentWorker

class IndependentWorkerForm(forms.ModelForm):
    class Meta:
        model = IndependentWorker
        exclude = ['created_by','delete_flag','form_o','ID_Card_number','do_form']

        widgets = {
            'dob': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'aadhar_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf'   # ✅ Browser shows PDF only
            }),
        }

    # ✅ Server-side validation (IMPORTANT)
    def clean_aadhar_file(self):
        file = self.cleaned_data.get('aadhar_file')

        if file:
            if not file.name.endswith('.pdf'):
                raise ValidationError("Only PDF files are allowed for Aadhar upload.")

            if file.content_type != 'application/pdf':
                raise ValidationError("File must be a valid PDF.")

        return file 


from django import forms
from .models import TrainingSchedule, TrainingResult, TrainingAttendance
from django.core.exceptions import ValidationError

class TrainingScheduleForm(forms.ModelForm):
    area_name = forms.CharField(required=False)

    class Meta:
        model = TrainingSchedule
        fields = [
            'worker',
            'from_date',
            'to_date',
            'type_of_training',
            'nature_of_training',
            'contractor_name',
            'area_name',   # 👈 added
        ]
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'type_of_training': forms.Select(attrs={'class': 'form-select'}),
            'nature_of_training': forms.TextInput(attrs={'class': 'form-control'}),
            'contractor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'area_name': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nature_of_training': 'Nature of Training',
            'contractor_name': 'Name of Contractor',
            'area_name': 'Area',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            user_areas = user.areas.all()

            # One area → auto-fill & hide
            if user_areas.count() == 1:
                self.fields['area_name'].initial = user_areas.first().area_name
                self.fields['area_name'].widget = forms.HiddenInput()

            # Multiple areas → dropdown
            elif user_areas.count() > 1:
                self.fields['area_name'] = forms.ChoiceField(
                    choices=[(a.area_name, a.area_name) for a in user_areas],
                    required=True,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )

            # No areas → manual input
            else:
                self.fields['area_name'] = forms.CharField(
                    required=True,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance
        worker = cleaned_data.get('worker')
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if worker and from_date and to_date:
            conflict = TrainingSchedule.objects.filter(
                worker=worker,
                from_date__lt=to_date,
                to_date__gt=from_date
            )
            if instance.pk:
                conflict = conflict.exclude(pk=instance.pk)

            if conflict.exists():
                raise ValidationError("Overlapping training dates for this worker.")

        return cleaned_data


class TrainingResultForm(forms.ModelForm):
    class Meta:
        model = TrainingResult
        fields = ['attendance_field_file','performance_appraisal', 'remarks']

class TrainingAttendanceForm(forms.ModelForm):
    class Meta:
        model = TrainingAttendance
        fields = ['date', 'present']


