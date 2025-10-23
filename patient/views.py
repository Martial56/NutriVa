from django.shortcuts import render, redirect, get_object_or_404
#from .forms import PatientForm
from django.http import HttpResponse
from .models import Patient, Constante, Vaccination, Rdv, Nutrition
from datetime import datetime, date
#la vue pour la page d'accueil
def index(request):
    return render(request, 'patient/index.html')

#la vue pour la page de connexion
def login(request):
    return render(request, 'patient/login.html')

#la vue pour la page de creation de patient
def creer_patient(request):
    return render(request, 'patient/creer_patient.html')

#la vue pour la page de saisie des constantes
def constante(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, "patient/constante.html", {"patient": patient})

#la vue pour la page rendez-vous
def rdv(request):
    return render(request, 'patient/rdv.html')

#la vue pour la page de saisie des vaccinations
def vaccination(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patient/vaccination.html', {"patient": patient})

# la vue pour la page nutrition
def nutrition(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patient/nutrition.html', {"patient_id": patient_id})

#la vue pour la page de liste des patients
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "patient/liste_patients.html", {"patients": patients})

#definir la date du jour dans le formulaire de constante
def my_view(request):
    return render(request, {"today": date.today()})

#Bouton enregistrer de la page création de patient
def enregistrement_patient(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        date_naissance = request.POST.get('date_naissance')
        sexe= request.POST.get('sexe')
        nom_parent = request.POST.get('nom_parent')
        quartier = request.POST.get('quartier')
        telephone = request.POST.get('phone')

        patient = Patient(
           # code="PT" + str(Patient.objects.count() + 1).zfill(4),
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            sexe=sexe,
            nom_parent=nom_parent,
            quartier=quartier,
            telephone=telephone
        )
        patient.save()
        return redirect('liste_patients')  # Rediriger vers la liste des patients après l'enregistrement
    return render(request, 'patient/creer_patient.html')

#Générer le code unique pour le patient dans le formulaire de constante
def code_unique(request):
    # Récupère le nombre actuel de patients
    count = Patient.objects.count() + 1

    # Génère le code unique du type NUT0001
    code = "NUT" + str(count).zfill(4)

    # Envoie ce code vers le template
    return render(request, 'patient/nutrition.html', {'code': code})

#Bouton enregistrer de la page saisie des constantes
def enregistrement_constante(request, patient_id):
    if request.method == 'POST':
        date = request.POST.get('date')
        poids = request.POST.get('poids')
        taille = request.POST.get('taille')
        pb = request.POST.get('pb')
        zscore = request.POST.get('zscore')
        #tension = request.POST.get('tension')
        imc = request.POST.get('imc')
        indicec = request.POST.get('indicec')

        patient = get_object_or_404(Patient, id=patient_id)

        Constante.objects.create(
            patient=patient,
            date=date,
            poids=poids,
            taille=taille,
            perimetre_brachial=pb,
            zscore=zscore,
            #tension=tension,
            imc=imc,
            indicecorporel=indicec
        )
        return redirect('rdv')  # Rediriger vers la liste des rendez-vous patients
    return render(request, 'patient/constante.html')

# Fontion pour afficher les rendez-vous des patients
def liste_rdv(request):
    # Récupération des dates depuis le formulaire (méthode GET)
    date_debut_str = request.GET.get('datedebut')
    date_fin_str = request.GET.get('datefin')

    # Valeurs par défaut : aujourd’hui
    today = date.today()

    try:
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else today
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else today
    except ValueError:
        date_debut, date_fin = today, today

    # 🔹 Filtrer uniquement les constantes entre les deux dates
    constantes = Constante.objects.filter(date__range=[date_debut, date_fin])

    # 🔹 Extraire uniquement les patients liés à ces constantes
    patients_ids = constantes.values_list('patient_id', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patients_ids)

    # 🔹 Récupérer les nutritions et vaccinations liées à ces patients
    nutritions = Nutrition.objects.filter(patient_id__in=patients_ids)
    vaccinations = Vaccination.objects.filter(patient_id__in=patients_ids)

    # 🔹 Construire la structure de données à afficher
    data = []
    for patient in patients:
        constante = constantes.filter(patient=patient).first()
        nutrition = nutritions.filter(patient=patient).first()
        vaccination = vaccinations.filter(patient=patient).first()

        data.append({
            'patient': patient,
            'constante': constante,
            'nutrition': nutrition,
            'vaccination': vaccination,
        })

    # 🔹 Envoyer les données au template
    context = {
        'data': data,
        'today': today,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }

    return render(request, 'patient/rdv.html', context)