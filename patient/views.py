from django.shortcuts import render, redirect
#from .forms import PatientForm
from django.http import HttpResponse
from .models import Patient, Constante, Vaccination, Autreservice
from datetime import date

#la vue pour la page d'accueil
def index(request):
    return render(request, 'patient/index.html')

#la vue pour la page de creation de patient
def creer_patient(request):
    return render(request, 'patient/creer_patient.html')

#la vue pour la page de saisie des constantes
def constante(request):
    return render(request, 'patient/constante.html')

#la vue pour la page de saisie des vaccinations
def vaccination(request):
    return render(request, 'patient/vaccination.html')

#la vue pour la page de liste des patients
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "patient/liste_patients.html", {"patients": patients})

#definir la date du jour dans le formulaire de constante
def my_view(request):
    return render(request, "patient/constante.html", {"today": date.today()})

#Bouton enregistrer de la page création de patient
def enregistrement_patient(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        date_naissance = request.POST.get('date_naissance')
        nom_parent = request.POST.get('nom_parent')
        quartier = request.POST.get('quartier')
        telephone = request.POST.get('phone')

        patient = Patient(
            code="PT" + str(Patient.objects.count() + 1).zfill(4),
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            nom_parent=nom_parent,
            quartier=quartier,
            telephone=telephone
        )
        patient.save()
        return redirect('liste_patients')  # Rediriger vers la liste des patients après l'enregistrement
    return render(request, 'patient/creer_patient.html')

#Générer le code unique pour le patient dans le formulaire de constante
def code_unique(request):
    patient = Patient(
        code="NUT" + str(Patient.objects.count() + 1).zfill(4),
    )
    return render(request, 'patient/constante.html', {'code': code})

#Bouton enregistrer de la page saisie des constantes
def enregistrement_constante(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        date = request.POST.get('date')
        poids = request.POST.get('poids')
        taille = request.POST.get('taille')
        perimetre_brachial = request.POST.get('perimetre_brachial')
        #temperature = request.POST.get('temperature')
        #tension = request.POST.get('tension')
        imc = request.POST.get('imc')
        indicecorporel = request.POST.get('indicecorporel')

        patient = Patient.objects.get(code=code)

        constante = Constante(
            patient=patient,
            date=date,
            poids=poids,
            taille=taille,
            perimetre_brachial=perimetre_brachial,
            #temperature=temperature,
            #tension=tension,
            imc=imc,
            indicecorporel=indicecorporel
        )
        constante.save()
        return redirect('liste_patients')  # Rediriger vers la liste des patients après l'enregistrement
    return render(request, 'patient/constante.html')