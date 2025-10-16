from django import forms
from .models import Patient, NutritionRecord, VaccinationRecord
from datetime import date
from django.core.exceptions import ValidationError

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['patient_id','first_name','last_name','birth_date','gender','phone','address']
        widgets = {'birth_date': forms.DateInput(attrs={'type':'date'})}

    def clean_birth_date(self):
        bd = self.cleaned_data['birth_date']
        if bd > date.today():
            raise ValidationError("Date de naissance invalide.")
        return bd

class NutritionRecordForm(forms.ModelForm):
    class Meta:
        model = NutritionRecord
        fields = ['patient','date','height_cm','weight_kg','muac_cm','note']
        widgets = {'date': forms.DateInput(attrs={'type':'date'})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('height_cm') is not None and cleaned.get('height_cm') <= 0:
            self.add_error('height_cm', "Taille doit être > 0")
        if cleaned.get('weight_kg') is not None and cleaned.get('weight_kg') <= 0:
            self.add_error('weight_kg', "Poids doit être > 0")
        return cleaned

class VaccinationRecordForm(forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = ['patient','date','vaccine','dose','provider','reaction','note']
        widgets = {'date': forms.DateInput(attrs={'type':'date'})}

    def clean_date(self):
        d = self.cleaned_data['date']
        if d > date.today():
            raise ValidationError("Date ne peut pas être dans le futur.")
        return d
