from django.shortcuts import render, redirect
#from .forms import PatientForm
from django.http import HttpResponse
from .models import Patient
from datetime import date


def index(request):
    return render(request, 'patient/index.html')

def creer_patient(request):
    return render(request, 'patient/creer_patient.html')

def constante(request):
    return render(request, 'patient/constante.html')
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "patient/liste_patients.html", {"patients": patients})
#definir la date du jour dans le formulaire de constante
def my_view(request):
    return render(request, "patient/constante.html", {"today": date.today()})