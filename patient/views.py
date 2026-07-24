from django.shortcuts import render, redirect, get_object_or_404
#from .forms import PatientForm
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, StreamingHttpResponse
from .models import Patient, Constante, Vaccination, Rdv, Nutrition
from datetime import datetime, date
import calendar
import io
import json
import ast
import os
import zipfile
from django.conf import settings
from django.contrib import messages
from docx import Document
from docx.shared import Pt
from django.template import loader
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.utils.timezone import now, localtime
from django.db.models.functions import TruncMonth
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import tempfile
from django.http import FileResponse

try:
    from docx import Document
except:
    Document = None

try:
    import weasyprint
except:
    weasyprint = None


#la vue pour la page d'accueil
@login_required
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
    today = date.today()
    years = today.year - patient.date_naissance.year
    months = today.month - patient.date_naissance.month
    if months < 0:
        years -= 1
        months += 12
    age_affichage = f"{years} ans {months} mois"
    return render(request, "patient/constante.html", {"patient": patient, "age_affichage": age_affichage})

#la vue pour la page rendez-vous
#@login_required
def rdv(request):
    return render(request, 'patient/rdv.html')

#la vue pour la page de saisie des vaccinations
def vaccination(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    today = date.today()
    years = today.year - patient.date_naissance.year
    months = today.month - patient.date_naissance.month
    if months < 0:
        years -= 1
        months += 12
    age_affichage = f"{years} ans {months} mois"

    vaccins_faits_raw = Vaccination.objects.filter(patient=patient).values_list('vaccin', flat=True)

    vaccins_faits = []

    for entry in vaccins_faits_raw:
        try:
            # Cas où entry est une liste sous forme de chaîne : "['vpo1','hpv']"
            parsed = ast.literal_eval(entry)
            if isinstance(parsed, list):
                vaccins_faits.extend(parsed)
            else:
                vaccins_faits.append(parsed)
        except Exception:
            # Cas où entry = "vpo1" simple
            vaccins_faits.append(entry)

    #print("VACCINS FINAUX =", vaccins_faits)

    return render(request, 'patient/vaccination.html', {
        "patient": patient,
        "age_affichage": age_affichage,
        "vaccins_faits_json": json.dumps(vaccins_faits),
    })

# la vue pour la page nutrition
def nutrition(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    nutrition = Nutrition.objects.filter(patient=patient).first()
    today = date.today()
    years = today.year - patient.date_naissance.year
    months = today.month - patient.date_naissance.month
    if months < 0:
        years -= 1
        months += 12
    age_affichage = f"{years} ans {months} mois"
    
    context = {
        "patient": patient,
        "nutrition": nutrition,
        "age_affichage": age_affichage,
    }
    return render(request, 'patient/nutrition.html', context)

#la vue pour la page de liste des patients
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "patient/liste_patients.html", {"patients": patients})

# bouton rechercher dans la liste des patients
def rechercher_patients(request):
    query = request.GET.get("search", "").strip()

    # Si l'utilisateur vide le champ, on retourne à la liste complète
    if query == "":
        return redirect('liste_patients')   # 👉 remplacer par ton URL d'affichage normal

    # Sinon, filtrer
    patients = Patient.objects.filter(
        Q(nom__icontains=query) |
        Q(prenom__icontains=query) |
        Q(telephone__icontains=query) |
        Q(quartier__icontains=query)
    )

    aucun_resultat = (not patients.exists())

    return render(request, "patient/liste_patients.html", {
        "patients": patients,
        "query": query,
        "aucun_resultat": aucun_resultat
    })



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
        statut = request.POST.get('statut')
        
        date_creation = date.today()
        patient = Patient(
           # code="PT" + str(Patient.objects.count() + 1).zfill(4),
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            date_creation=date_creation,
            sexe=sexe,
            nom_parent=nom_parent,
            quartier=quartier,
            telephone=telephone,
            statut=statut,
        )
        patient.save()
        return redirect('liste_patients')  # Rediriger vers la liste des patients après l'enregistrement
    return render(request, 'patient/creer_patient.html')

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
    nutritions = Nutrition.objects.filter(patient_id__in=patients_ids, date_visite__range=[date_debut, date_fin])
    vaccinations = Vaccination.objects.filter(patient_id__in=patients_ids, date__range=[date_debut, date_fin])
    rdvs = Rdv.objects.filter(patient_id__in=patients_ids,  date_enregistrement__date__range=[date_debut, date_fin])

    # 🔹 Construire la structure de données à afficher
    data = []
    for patient in patients:
        constante = constantes.filter(patient=patient).last()
        nutrition = nutritions.filter(patient=patient).last()
        vaccination = vaccinations.filter(patient=patient).last()
        rdv = rdvs.filter(patient=patient).last()

        data.append({
            'patient': patient,
            'constante': constante,
            'nutrition': nutrition,
            'vaccination': vaccination,
            'rdv': rdv,
        })

    # 🔹 Envoyer les données au template
    context = {
        'data': data,
        'today': today,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }

    return render(request, 'patient/rdv.html', context)

#enregistrement des vaccinations
def enregistrement_vaccin(request, patient_id):
    if request.method == "POST":
        vaccins = request.POST.getlist('vaccins')  # récupère tous les vaccins cochés
        patient = get_object_or_404(Patient, id=patient_id)
        date_vaccin = date.today()

        #for v in vaccins:
        Vaccination.objects.create(
            patient=patient,
            date=date_vaccin,
            vaccin=vaccins,
        )
        return redirect('rdv')  # ou 'liste_patients', selon ta page de retour

    return render(request, 'patient/vaccination.html')

# enregistrement des infos d'admission en nutrition
def enregistrement_nutrition(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # On vérifie s’il existe déjà une donnée Nutrition pour ce patient
    nutrition = Nutrition.objects.filter(patient=patient).first()

    if request.method == "POST":
        date_admission = request.POST.get("date_admission")
        etat_nutri = request.POST.get("etat_nutri")
        date_sortie = request.POST.get("date_sortie") or None
        motif_sortie = request.POST.get("motif_sortie") or None

        code_unique = f"NUT-{date.today().year}-{str(Nutrition.objects.count() + 1).zfill(4)}"

        date_visite = date.today()
        if nutrition:
            # Mise à jour
            nutrition.code_nutrition = code_unique
            nutrition.date_admission = date_admission
            nutrition.date_visite=date_visite
            nutrition.etat_nutrition = etat_nutri
            nutrition.date_sortie = date_sortie
            nutrition.motif_sortie = motif_sortie
            nutrition.save()
        else:
            # Création
            Nutrition.objects.create(
                patient=patient,
                code_nutrition=code_unique,
                date_admission=date_admission,
                date_visite=date_visite,
                etat_nutrition=etat_nutri,
                date_sortie=date_sortie,
                motif_sortie=motif_sortie,
            )

        return redirect("rdv")  # redirection après enregistrement

    # Préparer les données à envoyer au template
    #context = {
    #    "patient": patient,
     #   "code": nutrition.code_nutrition if nutrition else f"NUT-{patient.id:05d}",
     #   "date_admission": nutrition.date_admission if nutrition else "",
     #   "etat_nutri": nutrition.etat_nutri if nutrition else "",
      #  "date_sortie": nutrition.date_sortie if nutrition else "",
      #  "motif_sortie": nutrition.motif_sortie if nutrition else "",
    #}

    return render(request, "patient/nutrition.html")

def enregistrer_apport_nutrition(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        depiste = request.POST.get("depiste", "non").lower()
        code_depistage = request.POST.get("code_depistage") or None
        resultat = request.POST.get("resultat") or None
        produits = request.POST.getlist("produits") or None  # car c’est une liste de checkboxes

        # Création du rapport
        Rdv.objects.create(
            patient=patient,
            depiste=depiste,
            code_depistage=code_depistage,
            resultat=resultat,
            produits=produits,
        )

        return redirect("rdv")  # après enregistrement

    return render(request, "patient/nutrition.html", {"patient": patient})


# Génération du rapport périodique

def rapports(request):
    # --- Récupération des dates depuis le formulaire ou par défaut sur le mois courant ---
    today = timezone.localdate()
    start_date_str = request.GET.get("date_debut")
    end_date_str = request.GET.get("date_fin")

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return HttpResponseBadRequest("Format de date invalide (utiliser AAAA-MM-JJ)")
    else:
        # par défaut : le mois courant
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)

    # --- Agrégations ---
    constantes = Constante.objects.filter(date__range=(start_date, end_date)).select_related('patient')
    #patient = Patient.objects.filter(date__range=(start_date, end_date)).select_related('patient')
    vaccinations = Vaccination.objects.filter(date__range=(start_date, end_date)).select_related('patient')
    rdvs = Rdv.objects.filter(date_enregistrement__date__range=(start_date, end_date)).select_related('patient')

    # groupement d’âge
    age_groups = {
        "0-5": (0, 5),
        "6-11": (6, 11),
        "12-23": (12, 23),
        "24-59": (24, 59),
    }
    peses = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}
    total_peses = {"M": 0, "F": 0, "TOTAL": 0}

    for c in constantes:
        age_mois = c.patient.age
        sexe = c.patient.sexe[0].upper() if c.patient.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:
                peses[g][sexe] += 1
                peses[g]["TOTAL"] += 1
                total_peses[sexe] += 1
                total_peses["TOTAL"] += 1
                break
    #total_peses = sum(p["TOTAL"] for p in peses.values())
    
     # --- 🧒 Nouveaux enfants (première visite / création du patient) ---
    nouveaux_patients = Patient.objects.filter(date_creation__range=(start_date, end_date), vaccination__date__range=(start_date, end_date)
).distinct()

    premieres_visites = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}
    total_premieres_visites = {"M": 0, "F": 0, "TOTAL": 0}
    for p in nouveaux_patients:
        age_mois = p.age
        sexe = p.sexe[0].upper() if p.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:
                premieres_visites[g][sexe] += 1
                premieres_visites[g]["TOTAL"] += 1
                total_premieres_visites[sexe] += 1
                total_premieres_visites["TOTAL"] += 1
                break
    
        # --- Constantes dans la période sélectionnée ---
    constantes = Constante.objects.filter(date__range=(start_date, end_date))


    ### DICTIONNAIRES POUR CHAQUE INDICATEUR ###
    def dict_group():
        return {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}

    obeses = dict_group()
    mam = dict_group()
    mas = dict_group()
    surpoids = dict_group()

    total_obeses = {"M": 0, "F": 0, "TOTAL": 0}
    total_mam = {"M": 0, "F": 0, "TOTAL": 0}
    total_mas = {"M": 0, "F": 0, "TOTAL": 0}
    total_surpoids = {"M": 0, "F": 0, "TOTAL": 0}

    ### 🔍 ANALYSE DES CONSTANTES ###
    for c in constantes:
        patient = c.patient
        age_mois = patient.age

        sexe = patient.sexe[0].upper() if patient.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"

        # Trouver la tranche d'âge
        groupe = None
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:
                groupe = g
                break
        if not groupe:
            continue

        categorie = c.indicecorporel.strip().lower()

        # --- Obésité ---
        if categorie == "Obesite" or categorie == "obesite":
            obeses[groupe][sexe] += 1
            obeses[groupe]["TOTAL"] += 1
            total_obeses[sexe] += 1
            total_obeses["TOTAL"] += 1

        # --- MAM ---
        elif categorie == "MAM" or categorie == "mam":
            mam[groupe][sexe] += 1
            mam[groupe]["TOTAL"] += 1
            total_mam[sexe] += 1
            total_mam["TOTAL"] += 1

        # --- MAS ---
        elif categorie == "MAS" or categorie == "mas":
            mas[groupe][sexe] += 1
            mas[groupe]["TOTAL"] += 1
            total_mas[sexe] += 1
            total_mas["TOTAL"] += 1

        # --- Surpoids ---
        elif categorie == "Surpoids" or categorie == "surpoids":
            surpoids[groupe][sexe] += 1
            surpoids[groupe]["TOTAL"] += 1
            total_surpoids[sexe] += 1
            total_surpoids["TOTAL"] += 1

    # --- 🟩 Enfants vus en séance de vaccination PEV (routine) ---
    patient_ids = (
        Vaccination.objects
        .filter(date__range=(start_date, end_date))
        .values_list("patient_id", flat=True)
        .distinct()
    )

    # 2. Charger 1 vaccination par patient
    vaccinations = (
        Vaccination.objects
        .filter(patient_id__in=patient_ids)
        .select_related("patient")
    )

    # Préparation dictionnaires
    pev_routine = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}
    milda = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}
    total_pev_routine = {"M": 0, "F": 0, "TOTAL": 0}
    total_milda = {"M": 0, "F": 0, "TOTAL": 0}

    # Parcours
    for entry in vaccinations:
        patient = entry.patient #patient = Patient.objects.get(id=entry["patient"])
        age_mois = patient.age

        sexe = patient.sexe[0].upper() if patient.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"

        # Trouver la tranche d’âge correspondante
        groupe = None
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:
                groupe = g
                break
        if not groupe:
            continue

        # Comptage
        pev_routine[groupe][sexe] += 1
        pev_routine[groupe]["TOTAL"] += 1
        total_pev_routine[sexe] += 1
        total_pev_routine["TOTAL"] += 1
         # ---- 1️⃣ MILDA ----
        if "eabmilda" in entry.vaccin.lower():
            milda[groupe][sexe] += 1
            milda[groupe]["TOTAL"] += 1
            total_milda[sexe] += 1
            total_milda["TOTAL"] += 1

        # --- 🟩 Rdv PEV : MILDA, dépistés, dépistés positifs ---

    # 1. Charger les enregistrements RDV dans la période
    rdvs = (
        Rdv.objects
        .filter(date_enregistrement__date__range=(start_date, end_date))
        .select_related("patient")
    )

    # Structures d'âge et sexe
   
    depistes = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}
    positifs = {g: {"M": 0, "F": 0, "TOTAL": 0} for g in age_groups}

    total_depistes = {"M": 0, "F": 0, "TOTAL": 0}
    total_positifs = {"M": 0, "F": 0, "TOTAL": 0}

    for r in rdvs:
        p = r.patient
        age_mois = p.age

        sexe = p.sexe[0].upper() if p.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"

        # Trouver la tranche d'âge
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:

                # ---- 2️⃣ Dépistés ----
                if r.depiste == "oui":
                    depistes[g][sexe] += 1
                    depistes[g]["TOTAL"] += 1
                    total_depistes[sexe] += 1
                    total_depistes["TOTAL"] += 1

                # ---- 3️⃣ Dépistés positifs ----
                if r.depiste == "oui" and r.resultat == "positif":
                    positifs[g][sexe] += 1
                    positifs[g]["TOTAL"] += 1
                    total_positifs[sexe] += 1
                    total_positifs["TOTAL"] += 1

                break
  
    # Vaccination
    ANTIGEN_MAP = {
        "BCG": ["bcg"],
       # "Polio 0": ["polio0", "polio 0"],
        "VPO 0": ["VPO0"],
        "VPO 1": ["VPO1"],
        "VPO 2": ["VPO2"],
        "VPO 3": ["VPO3"],
        "VPI 1": ["VPI1"],
        "VPI 2": ["VPI2"],
        "DTC 0": ["Dtc_HepB_Hib_0"],
        "DTC 1": ["Dtc_HepB_Hib_1"],
        "DTC 2": ["Dtc_HepB_Hib_2"],
        "DTC 3": ["Dtc_HepB_Hib_3"],
        "PCV 1": ["PCV1"],
        "PCV 2": ["PCV2"],
        "PCV 3": ["PCV3"],
        "ROTA 1": ["rota1"],
        "ROTA 2": ["rota2"],
        "Rougeole 1": ["RR1"],
        "Rougeole 2": ["RR2"],
        "VAP 1": ["VAP1"],
        "VAP 2": ["VAP2"],
        "VAP 3": ["VAP3"],
        "VAP 4": ["VAP4"],
        "HPV ": ["HPV"],
        "MEN A": ["MenA"],
        "VAA": ["VAA"],
        "Vaccin anti-meningocique": ["vam"],
        "Enfant complètement vacciné": ["vam"],
        "Enfant protégé à la naissance": ["epn"],
        "Enfant ayant bénéficié de MILDA": ["eabmilda"],
        "Vaccin anti-hépatite B": ["ahb"],
        "Vaxigrip": ["Vaxigrip"],
        "VAT 1": ["vat1"],
        "VAT 2": ["vat2"],
        "VAT 1er rappel": ["vatrap1"],
        "VAT 2e rappel": ["vatrap2"],
        "VAT 3e rappel": ["vatrap3"],
    }
    antigen_counts = {k: 0 for k in ANTIGEN_MAP.keys()}
    for v in vaccinations:
        val = v.vaccin.lower()
        for key, patterns in ANTIGEN_MAP.items():
            if any(p in val for p in patterns):
                antigen_counts[key] += 1

    # Produits
    PRODUIT_KEYS = {
        "lait": "Lait",
        "plumpy": "Plumpy Nut",
        "deparasitant": "Déparasitant",
        "vitA100": "Vitamine A100",
        "vitA200": "Vitamine A200",
    }
    produit_counts = {v: 0 for v in PRODUIT_KEYS.values()}
    for r in rdvs:
        for p in (r.produits or []):
            label = PRODUIT_KEYS.get(p)
            if label:
                produit_counts[label] += 1
                    
                    
        # --- RÉCUPÉRATION DES DONNÉES nutrition---
    # Nutrition filtrée sur la date d’admission
    nutritions = (
        Nutrition.objects
        .filter(date_admission__range=(start_date, end_date))
        .select_related("patient")
    )

    # Tranches d'âge (en mois)
    age_groups = {
        "0-5": (0, 5),
        "6-11": (6, 11),
        "12-23": (12, 23),
        "24-59": (24, 59),
        "5-9": (60, 119),
        "10-14": (120, 179),
        "15-19": (180, 239),
        "20-24": (240, 299),
        "25+": (300, 2000),
    }

    # Fonction utilitaire
    def empty():
        return {"M": 0, "F": 0, "TOTAL": 0}

    # Dictionnaires du rapport
    mas_pris = {g: empty() for g in age_groups}
    mam_pris = {g: empty() for g in age_groups}

    mas_gueris = {g: empty() for g in age_groups}
    mam_gueris = {g: empty() for g in age_groups}

    abandon = {g: empty() for g in age_groups}
    deces = {g: empty() for g in age_groups}

    # Totaux globaux
    tot_mas_pris = empty()
    tot_mam_pris = empty()
    tot_mas_gueris = empty()
    tot_mam_gueris = empty()
    tot_abandon = empty()
    tot_deces = empty()


    # Parcours des données
    for n in nutritions:
        p = n.patient
        age_m = p.age

        sexe = p.sexe[0].upper() if p.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"

        # Groupe d'âge
        groupe = None
        for g, (low, high) in age_groups.items():
            if low <= age_m <= high:
                groupe = g
                break
        if not groupe:
            continue

        # Normalisation
        etat = (n.etat_nutrition or "").lower().strip()
        motif = (n.motif_sortie or "").lower().strip()
        date_sortie = n.date_sortie

        # ==========================
        #       PRISE EN CHARGE
        # ==========================

        # MAS
        if etat == "severe_sans_comp":
            mas_pris[groupe][sexe] += 1
            mas_pris[groupe]["TOTAL"] += 1
            tot_mas_pris[sexe] += 1
            tot_mas_pris["TOTAL"] += 1

        # MAM
        if etat == "modere":
            mam_pris[groupe][sexe] += 1
            mam_pris[groupe]["TOTAL"] += 1
            tot_mam_pris[sexe] += 1
            tot_mam_pris["TOTAL"] += 1


        # ==========================
        #        SORTIES
        # ==========================

        # On doit vérifier la date_sortie !
        if not date_sortie:
            continue

        if not (start_date <= date_sortie <= end_date):
            continue

        # --- Guéris MAS ---
        if etat == "severe_sans_comp" and motif == "gueris":
            mas_gueris[groupe][sexe] += 1
            mas_gueris[groupe]["TOTAL"] += 1
            tot_mas_gueris[sexe] += 1
            tot_mas_gueris["TOTAL"] += 1

        # --- Guéris MAM ---
        if etat == "modere" and motif == "gueris":
            mam_gueris[groupe][sexe] += 1
            mam_gueris[groupe]["TOTAL"] += 1
            tot_mam_gueris[sexe] += 1
            tot_mam_gueris["TOTAL"] += 1

        # --- Abandon ---
        if motif == "abandon":
            abandon[groupe][sexe] += 1
            abandon[groupe]["TOTAL"] += 1
            tot_abandon[sexe] += 1
            tot_abandon["TOTAL"] += 1

        # --- Décès ---
        if motif == "deces":
            deces[groupe][sexe] += 1
            deces[groupe]["TOTAL"] += 1
            tot_deces[sexe] += 1
            tot_deces["TOTAL"] += 1


    # --- 🟩 Enfants ayant reçu du lait ---
    age_groups = {
        "0-5": (0, 5),
        "6-11": (6, 11),
        "12-23": (12, 23),
        "24-59": (24, 59),
    }

    def empty():
        return {"F": 0, "M": 0, "TOTAL": 0}

    lait = {g: empty() for g in age_groups}
    lait["TOTAL"] = empty()

    lait_nouveaux = {g: empty() for g in age_groups}
    lait_nouveaux["TOTAL"] = empty()

    # Récupération des RDV dans la période
    rdvs = Rdv.objects.filter(
        date_enregistrement__range=(start_date, end_date)
    ).select_related("patient")

    # Filtrer lait (compatible SQLite)
    rdvs_lait = [r for r in rdvs if "lait" in r.produits]

    # ───────────────────────────────────────
    # 1. Enfants ayant reçu du lait
    # ───────────────────────────────────────
    for r in rdvs_lait:
        p = r.patient
        age_m = p.age
        sexe = p.sexe.upper()[0] if p.sexe else "M"

        for grp, (low, high) in age_groups.items():
            if low <= age_m <= high:
                lait[grp][sexe] += 1
                lait[grp]["TOTAL"] += 1

                lait["TOTAL"][sexe] += 1
                lait["TOTAL"]["TOTAL"] += 1
                break

    # ───────────────────────────────────────
    # 2. Nouveaux enfants
    # ───────────────────────────────────────
    nouveaux_ids = list(
        Patient.objects.filter(
            date_creation__range=(start_date, end_date)
        ).values_list("id", flat=True)
    )

    # Filtrer dans rdvs_lait (LISTE ➜ list comprehension obligatoire)
    rdvs_nouveaux_lait = [r for r in rdvs_lait if r.patient_id in nouveaux_ids]

    for r in rdvs_nouveaux_lait:
        p = r.patient
        age_m = p.age
        sexe = p.sexe.upper()[0] if p.sexe else "M"

        for grp, (low, high) in age_groups.items():
            if low <= age_m <= high:
                lait_nouveaux[grp][sexe] += 1
                lait_nouveaux[grp]["TOTAL"] += 1

                lait_nouveaux["TOTAL"][sexe] += 1
                lait_nouveaux["TOTAL"]["TOTAL"] += 1
                break
            
    # --- 🟩 Enfants ayant reçu de la vitamine A et déparasitant ---
    age_groups = {
        "6-11": (6, 11),
        "12-59": (12, 59),
        "60+": (60, 200),
    }

    def empty():
        return {"F": 0, "M": 0, "TOTAL": 0}

    # Conteneurs
    vitA100 = {g: empty() for g in age_groups}; vitA100["TOTAL"] = empty()
    vitA200 = {g: empty() for g in age_groups}; vitA200["TOTAL"] = empty()
    deparasitant = {g: empty() for g in age_groups}; deparasitant["TOTAL"] = empty()

    # RDV filtrés par date
    rdvs = Rdv.objects.filter(
        date_enregistrement__range=(start_date, end_date)
    ).select_related("patient")

    # Fonction de comptage générique
    def count_product(rdv_list, container):
        for r in rdv_list:
            p = r.patient
            age = p.age
            sexe = p.sexe.upper()[0] if p.sexe else "M"

            for grp, (low, high) in age_groups.items():
                if low <= age <= high:
                    container[grp][sexe] += 1
                    container[grp]["TOTAL"] += 1

                    container["TOTAL"][sexe] += 1
                    container["TOTAL"]["TOTAL"] += 1
                    break

    # Produits
    rdv_vitA100 = [r for r in rdvs if "vitA100" in r.produits]
    rdv_vitA200 = [r for r in rdvs if "vitA200" in r.produits]
    rdv_deparasitant = [r for r in rdvs if "deparasitant" in r.produits]

    # Comptages
    count_product(rdv_vitA100, vitA100)
    count_product(rdv_vitA200, vitA200)
    count_product(rdv_deparasitant, deparasitant)

    context = {
        #============ rapport: tableau : Evaluation nutritionnelle ===============
        "date_debut": start_date,
        "date_fin": end_date,
        "peses": peses,
        "total_peses": total_peses,
        "premieres_visites": premieres_visites,
        "total_premieres_visites": total_premieres_visites,
        "obeses": obeses,
        "total_obeses": total_obeses,
        "mam": mam,
        "total_mam": total_mam,
        "mas": mas,
        "total_mas": total_mas,
        "surpoids": surpoids,
        "total_surpoids": total_surpoids,
            ############ rapport: tableau : Vaccinations ############
        "vaccinations": vaccinations,
        "antigen_counts": antigen_counts,
        "produit_counts": produit_counts,
        "rdv_count": rdvs.count(),
        
         ############ rapport: tableau : PEV de routine ############
        "pev_routine": pev_routine,
        "total_pev_routine": total_pev_routine,
        "milda": milda,
        "total_milda": total_milda,
        "depistes": depistes,
        "total_depistes": total_depistes,
        "positifs": positifs,
        "total_positifs": total_positifs,
        "age_groups": age_groups,
        
        ############ rapport: tableau : Nutrition ############
        "mas_pris": mas_pris,
        "tot_mas_pris": tot_mas_pris,
        "mam_pris": mam_pris,
        "tot_mam_pris": tot_mam_pris,
        "mas_gueris": mas_gueris,
        "tot_mas_gueris": tot_mas_gueris,
        "mam_gueris": mam_gueris,
        "tot_mam_gueris": tot_mam_gueris,
        "abandon": abandon,
        "tot_abandon": tot_abandon,
        "deces": deces,
        "tot_deces": tot_deces,
        ############ rapport: tableau : Enfants ayant reçu du lait ############
        "lait": lait,
        "lait_nouveaux": lait_nouveaux,
        ############ rapport: tableau : Enfants ayant reçu du Vitamine A et déparasitant ############
        "vitA100": vitA100,
        "vitA200": vitA200,
        "deparasitant": deparasitant,
        
    }

    fmt = request.GET.get("format")
    if fmt == "docx":
        return _report_to_docx(context)
    elif fmt == "pdf":
        return _report_to_pdf(request, context)
    elif fmt == "excel":
        return export_rapport_excel(context)

    elif fmt == "html_download":
        html = loader.render_to_string("patient/rapport.html", context)
        response = HttpResponse(html, content_type="text/html")
        response["Content-Disposition"] = f'attachment; filename="rapport_{start_date}_{end_date}.html"'
        return response

    return render(request, "patient/rapport.html", context)

# Fonction utilitaire pour ajouter une table simple dans le document
def add_simple_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h

    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)

# Génération DOCX
def _report_to_docx(context):
    if Document is None:
        return HttpResponseBadRequest("python-docx n'est pas installé.")

    doc = Document()

    # =====================================================
    # TITRE
    # =====================================================
    doc.add_heading(
        f"Rapport mensuel Vaccination & Nutrition\n"
        f"Période : {context['date_debut']} au {context['date_fin']}",
        level=1
    )

    # =====================================================
    # 1 & 2. ÉVALUATION NUTRITIONNELLE + VACCINATION DE ROUTINE (tableau unique)
    # =====================================================
    doc.add_heading("Évaluation nutritionnelle", level=2)

    NUM_COLS = 13  # SEXE + 4 tranches × 2 (M/F) + sous-total M/F + Total + Total référé
    headers_eval = [
        "SEXE",
        "0-5 M", "0-5 F",
        "6-11 M", "6-11 F",
        "12-23 M", "12-23 F",
        "24-59 M", "24-59 F",
        "Sous-total M", "Sous-total F",
        "Total", "Total référé"
    ]

    def mk_eval_row(label, data, total):
        row = [label]
        for c in data.values():
            row.extend([c["M"], c["F"]])
        row += [total["M"], total["F"], total["TOTAL"], ""]
        return row

    table1 = doc.add_table(rows=1, cols=NUM_COLS)
    table1.style = "Table Grid"
    for i, h in enumerate(headers_eval):
        table1.rows[0].cells[i].text = h

    for label, data_key, total_key in [
        ("Nombre d'enfants pesés", "peses", "total_peses"),
        ("Nombre d'enfants venus pour la première fois à une séance de vaccination",
         "premieres_visites", "total_premieres_visites"),
        ("Nombre d'enfants en surpoids", "surpoids", "total_surpoids"),
        ("Nombre d'enfants obèses (Obésité)", "obeses", "total_obeses"),
        ("Malnutrition aiguë modérée (MAM)", "mam", "total_mam"),
        ("Malnutrition aiguë sévère sans complication", "mas", "total_mas"),
    ]:
        r = table1.add_row()
        for i, val in enumerate(mk_eval_row(label, context[data_key], context[total_key])):
            r.cells[i].text = str(val)

    # Ligne de section "Vaccination de routine"
    sec_row = table1.add_row()
    sec_row.cells[0].merge(sec_row.cells[NUM_COLS - 1])
    sec_row.cells[0].text = "Vaccination de routine"

    for label, data_key, total_key in [
        ("Nombre d'enfants vus en séance de vaccination PEV de routine",
         "pev_routine", "total_pev_routine"),
        ("Nombre d'enfants ayant reçu une MILDA en PEV", "milda", "total_milda"),
        ("Nombre d'enfants dépistés au PEV", "depistes", "total_depistes"),
        ("Nombre d'enfants dépistés et déclarés positifs au PEV", "positifs", "total_positifs"),
    ]:
        r = table1.add_row()
        for i, val in enumerate(mk_eval_row(label, context[data_key], context[total_key])):
            r.cells[i].text = str(val)

    # Ligne "Total des mères"
    meres_row = table1.add_row()
    meres_row.cells[0].merge(meres_row.cells[NUM_COLS - 1])
    meres_row.cells[0].text = (
        "Total des mères venues pour la première fois aux activités "
        "(Ne pas compter la même personne deux fois)"
    )

    # =====================================================
    # 3. DÉTAILS DES VACCINATIONS
    # =====================================================
    doc.add_heading("Détails des vaccinations effectuées", level=2)

    add_simple_table(
        doc,
        ["Antigène", "Nombre d’enfants vaccinés"],
        [(ag, n) for ag, n in context["antigen_counts"].items()]
    )

    # =====================================================
    # 4. PRODUITS NUTRITIONNELS DISTRIBUÉS
    # =====================================================
    doc.add_heading("Produits nutritionnels distribués", level=2)

    add_simple_table(
        doc,
        ["Produit", "Quantité distribuée"],
        [(p, n) for p, n in context["produit_counts"].items()]
    )

    # =====================================================
    # 5. PRISE EN CHARGE DE LA MALNUTRITION AIGUË
    # =====================================================
    doc.add_heading("Prise en charge de la malnutrition aiguë", level=2)

    headers_mal = ["Indicateur"]
    for g in context["mas_pris"]:
        if g != "TOTAL":
            headers_mal.extend([f"{g} M", f"{g} F"])
    headers_mal.extend(["Total M", "Total F"])

    def mal_row(label, data, total):
        row = [label]
        for g, c in data.items():
            if g != "TOTAL":
                row.extend([c["M"], c["F"]])
        row.extend([total["M"], total["F"]])
        return row

    rows_mal = [
        mal_row("Nombre de malnutris sans complication pris en charge", context["mas_pris"], context["tot_mas_pris"]),
        mal_row("Nombre de malnutris modéré pris en charge", context["mam_pris"], context["tot_mam_pris"]),
        mal_row("Nombre de malnutris sans complication déclarés guéris", context["mas_gueris"], context["tot_mas_gueris"]),
        mal_row("Nombre de malnutris modéré déclarés guéris", context["mam_gueris"], context["tot_mam_gueris"]),
        mal_row("Abandon", context["abandon"], context["tot_abandon"]),
        mal_row("Décès", context["deces"], context["tot_deces"]),
    ]

    add_simple_table(doc, headers_mal, rows_mal)

    # =====================================================
    # 6. VITAMINE A & DÉPARASITANT
    # =====================================================
    doc.add_heading("Vitamine A et Déparasitant", level=2)

    vit_headers = ["Indicateur"]
    for g in context["vitA100"]:
        if g != "TOTAL":
            vit_headers.extend([f"{g} M", f"{g} F"])
    vit_headers.extend(["Total M", "Total F"])

    def vit_row(label, data):
        row = [label]
        for g, c in data.items():
            if g != "TOTAL":
                row.extend([c["M"], c["F"]])
        row.extend([data["TOTAL"]["M"], data["TOTAL"]["F"]])
        return row

    add_simple_table(
        doc,
        vit_headers,
        [
            vit_row("Vitamine A – 1ère dose", context["vitA100"]),
            vit_row("Vitamine A – 2ème dose", context["vitA200"]),
            vit_row("Déparasitant", context["deparasitant"]),
        ]
    )

    # =====================================================
    # 7. DISTRIBUTION DE LAIT EN POUDRE (AVEC NOUVEAUX ENFANTS)
    # =====================================================
    doc.add_heading(
        "Distribution de lait en poudre aux enfants pour éviter la transmission du VIH",
        level=2
    )

    headers_lait = ["Indicateur"]
    for g in context["lait"]:
        if g != "TOTAL":
            headers_lait.extend([f"{g} M", f"{g} F"])
    headers_lait.extend(["Total M", "Total F"])

    def lait_row(label, data):
        row = [label]
        for g, c in data.items():
            if g != "TOTAL":
                row.extend([c["M"], c["F"]])
        row.extend([data["TOTAL"]["M"], data["TOTAL"]["F"]])
        return row

    rows_lait = [
        lait_row("Nombre d’enfant ayant bénéficié de lait", context["lait"]),
        lait_row("Nombre de nouveau enfant ayant bénéficié de lait", context["lait_nouveaux"]),
    ]

    add_simple_table(doc, headers_lait, rows_lait)

    # =====================================================
    # EXPORT
    # =====================================================
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_{context["date_debut"]}_{context["date_fin"]}.docx"'
    )

    return response



#Génération Excel
def export_rapport_excel(context):
    wb = Workbook()
    ws = wb.active
    ws.title = "Rapport Mensuel"

    bold = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center")

    def write_row(values, bold_row=False, merge_to=None):
        ws.append(values)
        row_idx = ws.max_row

        if merge_to:
            ws.merge_cells(
                start_row=row_idx,
                start_column=1,
                end_row=row_idx,
                end_column=merge_to
            )

        if bold_row:
            for cell in ws[row_idx]:
                cell.font = bold
                cell.alignment = center


    # ================= TITRE =================
    write_row(["Rapport Mensuel – Vaccination & Nutrition"], bold_row=True)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=15)

    ws.append([])

    # ================= ÉVALUATION NUTRITIONNELLE + VACCINATION DE ROUTINE (tableau unique) =================
    write_row(["ÉVALUATION NUTRITIONNELLE"], bold_row=True, merge_to=13)

    write_row([
        "SEXE",
        "0-5 M", "0-5 F",
        "6-11 M", "6-11 F",
        "12-23 M", "12-23 F",
        "24-59 M", "24-59 F",
        "Sous-total M", "Sous-total F",
        "Total", "Total référé"
    ], bold_row=True)

    def write_indicator(label, data, total):
        row = [label]
        for _, c in data.items():
            row.extend([c["M"], c["F"]])
        row.extend([total["M"], total["F"], total["TOTAL"], ""])
        write_row(row)

    write_indicator("Nombre d’enfants pesés", context["peses"], context["total_peses"])
    write_indicator("Nombre d’enfants venus pour la première fois à une séance de vaccination", context["premieres_visites"], context["total_premieres_visites"])
    write_indicator("Nombre d’enfants en surpoids", context["surpoids"], context["total_surpoids"])
    write_indicator("Nombre d’enfants obèses (Obésité)", context["obeses"], context["total_obeses"])
    write_indicator("Malnutrition aiguë modérée (MAM)", context["mam"], context["total_mam"])
    write_indicator("Malnutrition aiguë sévère sans complication", context["mas"], context["total_mas"])

    write_row(["Vaccination de routine"], bold_row=True, merge_to=13)

    write_indicator("Nombre d’enfants vus en séance de vaccination PEV de routine", context["pev_routine"], context["total_pev_routine"])
    write_indicator("Nombre d’enfants ayant reçu une MILDA en PEV", context["milda"], context["total_milda"])
    write_indicator("Nombre d’enfants dépistés au PEV", context["depistes"], context["total_depistes"])
    write_indicator("Nombre d’enfants dépistés et déclarés positifs au PEV", context["positifs"], context["total_positifs"])

    write_row(
        ["Total des mères venues pour la première fois aux activités (Ne pas compter la même personne deux fois)"],
        bold_row=True, merge_to=13
    )

    ws.append([])

    # ================= DÉTAILS DES VACCINS =================
    write_row(["DÉTAIL DES VACCINS"], bold_row=True)
    write_row(["Antigène", "Nombre vaccinés"], bold_row=True)

    for ag, n in context["antigen_counts"].items():
        write_row([ag, n])

    ws.append([])

    # ================= PRODUITS NUTRITIONNELS =================
    write_row(["PRODUITS NUTRITIONNELS DISTRIBUÉS"], bold_row=True)
    write_row(["Produit", "Quantité"], bold_row=True)

    for p, n in context["produit_counts"].items():
        write_row([p, n])
        
    # ================= PRISE EN CHARGE DE LA MALNUTRITION AIGUË =================
    ws.append([])
    write_row(["PRISE EN CHARGE DE LA MALNUTRITION AIGUË"], bold_row=True, merge_to=21)

    write_row([
        "Indicateurs",
        "0-5 M","0-5 F",
        "6-11 M","6-11 F",
        "12-23 M","12-23 F",
        "24-59 M","24-59 F",
        "5-9 M","5-9 F",
        "10-14 M","10-14 F",
        "15-19 M","15-19 F",
        "20-24 M","20-24 F",
        "25+ M","25+ F",
        "Sous-total M","Sous-total F"
    ], bold_row=True)


    def write_large_indicator(label, data, total):
        row = [label]
        for k in data.keys():
            if k != "TOTAL":
                row.extend([data[k]["M"], data[k]["F"]])
        row.extend([total["M"], total["F"]])
        write_row(row)


    write_large_indicator(
        "Nombre de malnutris sans complication pris en charge",
        context["mas_pris"],
        context["tot_mas_pris"]
    )

    write_large_indicator(
        "Nombre de malnutris modéré pris en charge",
        context["mam_pris"],
        context["tot_mam_pris"]
    )

    write_large_indicator(
        "Nombre de malnutris sans complication déclarés guéris",
        context["mas_gueris"],
        context["tot_mas_gueris"]
    )

    write_large_indicator(
        "Nombre de malnutris modéré déclarés guéris",
        context["mam_gueris"],
        context["tot_mam_gueris"]
    )

    write_large_indicator(
        "Abandon",
        context["abandon"],
        context["tot_abandon"]
    )

    write_large_indicator(
        "Décès",
        context["deces"],
        context["tot_deces"]
    )

    # ================= VITAMINE A ET DÉPARASITANT =================
    ws.append([])
    write_row(["VITAMINE A ET DÉPARASITANT"], bold_row=True)

    write_row([
        "Indicateurs",
        "6-11 M", "6-11 F",
        "12-59 M", "12-59 F",
        "60+ M", "60+ F",
        "Total M", "Total F",
    ], bold_row=True)

    def write_vit(label, data):
        row = [label]
        for k, c in data.items():
            if k != "TOTAL":
                row.extend([c["M"], c["F"]])
        row.extend([data["TOTAL"]["M"], data["TOTAL"]["F"]])
        write_row(row)

    write_vit("Vitamine A – 1ère dose", context["vitA100"])
    write_vit("Vitamine A – 2ème dose", context["vitA200"])
    write_vit("Déparasitant", context["deparasitant"])

    # ================= ENFANTS AYANT REÇU DU LAIT =================
    ws.append([])
    write_row(
        ["DISTRIBUTION DE LAIT EN POUDRE (Prévention VIH)"],
        bold_row=True,
        merge_to=11
    )

    write_row([
        "Indicateurs",
        "0-5 M","0-5 F",
        "6-11 M","6-11 F",
        "12-23 M","12-23 F",
        "24-59 M","24-59 F",
        "Total M","Total F"
    ], bold_row=True)


    def write_lait(label, data):
        row = [label]
        for k in data.keys():
            if k != "TOTAL":
                row.extend([data[k]["M"], data[k]["F"]])
        row.extend([data["TOTAL"]["M"], data["TOTAL"]["F"]])
        write_row(row)


    write_lait("Nombre d'enfant ayant bénéficié de lait", context["lait"])
    write_lait("Nombre de nouveau enfant ayant bénéficié de lait", context["lait_nouveaux"])


    # ================= EXPORT =================
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="rapport_mensuel.xlsx"'
    wb.save(response)
    return response


# Génération PDF
def _report_to_pdf(request, context):
    if weasyprint is None:
        return HttpResponseBadRequest("WeasyPrint non installé.")
    html = loader.render_to_string("patient/rapport.html", context)
    pdf = weasyprint.HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="rapport_{context["date_debut"]}_{context["date_fin"]}.pdf"'
    return response

###############################################################"
# " historique patient
################################################################
def historique_patient(request, patient_id):
    
    patient = get_object_or_404(Patient, id=patient_id)

    # Calcul âge lisible (années + mois)
    today = date.today()
    years = today.year - patient.date_naissance.year
    months = today.month - patient.date_naissance.month
    if months < 0:
        years -= 1
        months += 12
    age_affichage = f"{years} ans {months} mois"

    constantes = Constante.objects.filter(patient=patient).order_by("-date")
    vaccinations = Vaccination.objects.filter(patient=patient).order_by("-date")
    nutritions = Nutrition.objects.filter(patient=patient).order_by("-date_visite")
    rdvs = Rdv.objects.filter(patient=patient).order_by("-date_enregistrement")

    context = {
        "patient": patient,
        "age_affichage": age_affichage,
        "constantes": constantes,
        "vaccinations": vaccinations,
        "nutritions": nutritions,
        "rdvs": rdvs,
    }

    return render(request, "patient/historique.html", context)

###############################################################"
# " tableau de bord
################################################################

def dashboard(request):
    month = request.GET.get("month")

    # --- PATIENTS ---
    if month:
        total_patients = Patient.objects.filter(date_creation__month=month).count()
        this_month_patients = total_patients
    else:
        total_patients = Patient.objects.count()
        this_month_patients = Patient.objects.filter(date_creation__month=now().month).count()

    sexe_stats = Patient.objects.values("sexe").annotate(total=Count("id"))

    # --- VACCINS ---
    if month:
        total_vaccins = Vaccination.objects.filter(date__month=month).count()
        vaccins_stats = (
            Vaccination.objects.filter(date__month=month)
            .values("vaccin")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )
    else:
        total_vaccins = Vaccination.objects.count()
        vaccins_stats = Vaccination.objects.values("vaccin").annotate(total=Count("id")).order_by("-total")[:5]

    # --- DÉPISTAGE ---
    if month:
        depistage_total = Rdv.objects.filter(date_enregistrement__month=month).count()
        cas_positifs = Rdv.objects.filter(date_enregistrement__month=month, resultat="positif").count()
    else:
        depistage_total = Rdv.objects.count()
        cas_positifs = Rdv.objects.filter(resultat="positif").count()
    # --- MALNUTRIS ---
    if month:
        malnutrition_total = Nutrition.objects.filter(date_admission__month=month).count()
    else:
        malnutrition_total  = Nutrition.objects.count()
       

    # --- PRODUITS DISTRIBUÉS ---
    produits_totaux = {
        "lait": 0,
        "plumpy": 0,
        "deparasitant": 0,
        "vitA100": 0,
        "vitA200": 0,
    }

    rdv_query = Rdv.objects.all()
    if month:
        rdv_query = rdv_query.filter(date_enregistrement__month=month)

    for rdv in rdv_query:
        for p in rdv.produits:
            if p in produits_totaux:
                produits_totaux[p] += 1

    # --- CONSTANTES ---
    if month:
        constantes = Constante.objects.filter(date__month=month)
    else:
        constantes = Constante.objects.all()

    poids_moyen = constantes.aggregate(Avg("poids"))["poids__avg"]
    taille_moyen = constantes.aggregate(Avg("taille"))["taille__avg"]

    # --- COURBE DES VISITES ---
    visites_mensuelles = (
        Constante.objects.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    # --- ÉTAT NUTRITIONNEL ---
    LABELS_MAP = {
        "MAM": "Modéré",
        "MAS": "Sévère sans complication",
        "MAC": "Sévère avec complication",
        "Obésité": "Obésité",
        "Surpoids": "Surpoids",
        "Normal": "Normal",
    }

    raw_data = constantes.values('indicecorporel').annotate(total=Count('id')).order_by('indicecorporel')

    labels = [LABELS_MAP.get(item["indicecorporel"], item["indicecorporel"]) for item in raw_data]
    values = [item["total"] for item in raw_data]

    context = {
        "total_patients": total_patients,
        "this_month_patients": this_month_patients,
        "sexe_stats": sexe_stats,
        "total_vaccins": total_vaccins,
        "vaccins_stats": vaccins_stats,
        "depistage_total": depistage_total,
        "cas_positifs": cas_positifs,
        "produits_totaux": produits_totaux,
        "poids_moyen": round(poids_moyen or 0, 1),
        "taille_moyen": round(taille_moyen or 0, 1),
        "visites_mensuelles": list(visites_mensuelles),
        "labels": labels,
        "values": values,
        "malnutrition_total": malnutrition_total,
        "selected_month": month or "",
    }

    return render(request, "patient/dashboard.html", context)

###############################################################"
# " formatage des produits dans la liste des rdv
################################################################

def format_produits(rdv):
    if not rdv:
        return "-"

    produits = rdv.produits_list

    # Si c’est une fonction
    if callable(produits):
        produits = produits()

    # Si c’est un QuerySet
    if hasattr(produits, "values_list"):
        produits = produits.values_list("nom", flat=True)

    # Si c’est une liste ou un tuple
    if isinstance(produits, (list, tuple)):
        return ", ".join(str(p) for p in produits)

    # Sinon (string ou autre)
    return str(produits)


###############################################################"
# " exportation excel des patients
################################################################

def exporter_patients_excel(request):

    date_debut_str = request.GET.get("datedebut")
    date_fin_str = request.GET.get("datefin")

    today = date.today()

    try:
        date_debut = datetime.strptime(date_debut_str, "%Y-%m-%d").date() if date_debut_str else today
        date_fin = datetime.strptime(date_fin_str, "%Y-%m-%d").date() if date_fin_str else today
    except ValueError:
        date_debut = date_fin = today

    # === MÊME LOGIQUE QUE liste_rdv ===
    constantes = Constante.objects.filter(date__range=[date_debut, date_fin])
    patients_ids = constantes.values_list("patient_id", flat=True).distinct()
    patients = Patient.objects.filter(id__in=patients_ids)

    nutritions = Nutrition.objects.filter(
        patient_id__in=patients_ids,
        date_visite__range=[date_debut, date_fin]
    )
    vaccinations = Vaccination.objects.filter(
        patient_id__in=patients_ids,
        date__range=[date_debut, date_fin]
    )
    rdvs = Rdv.objects.filter(
        patient_id__in=patients_ids,
        date_enregistrement__date__range=[date_debut, date_fin]
    )

    # === CRÉATION EXCEL ===
    wb = Workbook()
    ws = wb.active
    ws.title = "RDV"

    ws.append([
        "Nom", "Prénom", "Sexe", "Âge (mois)", "Téléphone", "Quartier",
        "Date constante", "Poids", "Taille", "PB", "Z-score", "IMC", "Indice corporel",
        "Code nutrition", "Date visite", "État nutritionnel",
        "Date admission", "Date sortie", "Motif sortie",
        "Date RDV", "Dépisté", "Code dépistage", "Résultat", "Produits",
        "Vaccin", "Date vaccination",
    ])

    # === MÊME BOUCLE QUE LA PAGE ===
    for patient in patients:
        constante = constantes.filter(patient=patient).last()
        nutrition = nutritions.filter(patient=patient).last()
        vaccination = vaccinations.filter(patient=patient).last()
        rdv = rdvs.filter(patient=patient).last()

        ws.append([
            patient.nom,
            patient.prenom,
            patient.sexe,
            patient.age if patient.date_naissance else "",
            patient.telephone or "",
            patient.quartier or "",

            constante.date.strftime("%d/%m/%Y") if constante else "",
            constante.poids if constante else "",
            constante.taille if constante else "",
            constante.perimetre_brachial if constante else "",
            constante.zscore if constante else "",
            constante.imc if constante else "",
            constante.indicecorporel if constante else "",

            nutrition.code_nutrition if nutrition else "",
            nutrition.date_visite.strftime("%d/%m/%Y") if nutrition else "",
            nutrition.etat_nutrition if nutrition else "",
            nutrition.date_admission.strftime("%d/%m/%Y") if nutrition and nutrition.date_admission else "",
            nutrition.date_sortie.strftime("%d/%m/%Y") if nutrition and nutrition.date_sortie else "",
            nutrition.motif_sortie if nutrition else "",

            rdv.date_enregistrement.strftime("%d/%m/%Y") if rdv else "",
            "Oui" if rdv and rdv.depiste else "Non",
            rdv.code_depistage if rdv else "",
            rdv.resultat if rdv else "",
            format_produits(rdv),

            #", ".join(rdv.produits_list()) if rdv and rdv.produits_list() else "",

            vaccination.vaccin if vaccination else "",
            vaccination.date.strftime("%d/%m/%Y") if vaccination else "",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f"attachment; filename=rdv_{date_debut}_{date_fin}.xlsx"
    )

    wb.save(response)
    return response


def _dump_sqlite(db_path, now_str, zf):
    if db_path.exists():
        zf.write(str(db_path), arcname=f'backup_{now_str}/database/db.sqlite3')
    from django.db import connection
    lines = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY rootpage")
        for row in cursor.fetchall():
            lines.append(row[0] + ';\n')
    zf.writestr(f'backup_{now_str}/database/dump.sql', '\n'.join(lines))


def _dump_postgresql(db_conf, now_str, zf):
    import subprocess
    import tempfile
    host = db_conf.get('HOST', 'localhost')
    port = str(db_conf.get('PORT', '5432'))
    name = db_conf.get('NAME', '')
    user = db_conf.get('USER', '')
    password = db_conf.get('PASSWORD', '')
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ['pg_dump', '-h', host, '-p', port, '-U', user, name, '-f', tmp_path],
            env=env, check=True
        )
        zf.write(tmp_path, arcname=f'backup_{now_str}/database/{name}_dump.sql')
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@login_required
def backup_db(request):
    """
    Sauvegarde universelle : fonctionne avec SQLite ET PostgreSQL.
    - SQLite  → copie du fichier .sqlite3 + dump SQL texte
    - PostgreSQL → dump via pg_dump (nécessite pg_dump installé sur le serveur)
    """
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"NutriVa_backup_{now_str}.zip"

    buf = io.BytesIO()
    base_dir = settings.BASE_DIR
    db_conf  = settings.DATABASES.get('default', {})
    engine   = db_conf.get('ENGINE', '')

    INCLUDE_DIRS    = ['NutriVa', 'patient', 'templates', 'static', 'media']
    INCLUDE_FILES   = ['manage.py', 'requirements.txt', 'CLAUDE.md']
    EXCLUDE_IN_PATH = ('__pycache__', '.git')
    EXCLUDE_EXTS    = ('.pyc', '.pyo')

    def should_exclude(path_str):
        p = str(path_str)
        return (any(e in p for e in EXCLUDE_IN_PATH) or
                any(p.endswith(ext) for ext in EXCLUDE_EXTS))

    db_error = None

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:

        # ── 1. Sauvegarde de la base de données ──────────────────────────────
        try:
            if 'sqlite3' in engine:
                db_path = settings.BASE_DIR / 'db.sqlite3'
                _dump_sqlite(db_path, now_str, zf)
            elif 'postgresql' in engine or 'postgis' in engine:
                _dump_postgresql(db_conf, now_str, zf)
            else:
                zf.writestr(
                    f'backup_{now_str}/database/README.txt',
                    f"Moteur de base de données non supporté automatiquement : {engine}\n"
                    "Veuillez effectuer la sauvegarde manuellement."
                )
        except Exception as exc:
            db_error = str(exc)
            zf.writestr(
                f'backup_{now_str}/database/ERREUR.txt',
                f"Erreur lors de la sauvegarde de la base :\n{db_error}"
            )

        # ── 2. Fichiers racine ────────────────────────────────────────────────
        for fname in INCLUDE_FILES:
            fpath = base_dir / fname
            if fpath.exists():
                zf.write(fpath, arcname=f'backup_{now_str}/{fname}')

        # ── 3. Dossiers applicatifs ───────────────────────────────────────────
        for dirname in INCLUDE_DIRS:
            dir_path = base_dir / dirname
            if not dir_path.exists():
                continue
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_IN_PATH]
                for file in files:
                    full_path = os.path.join(root, file)
                    if should_exclude(full_path):
                        continue
                    rel_path = os.path.relpath(full_path, base_dir)
                    zf.write(full_path, arcname=f'backup_{now_str}/{rel_path}')

        # ── 4. Fiche de synthèse ──────────────────────────────────────────────
        info_lines = [
            "NutriVa — Sauvegarde système",
            f"Date       : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
            f"Moteur DB  : {engine}",
            f"Statut DB  : {'OK' if not db_error else 'ERREUR : ' + db_error}",
            "",
            "Contenu du backup :",
            f"  backup_{now_str}/database/  → dump de la base de données",
            f"  backup_{now_str}/NutriVa/   → configuration Django (settings, urls)",
            f"  backup_{now_str}/patient/   → application patient (models, views, templates)",
            f"  backup_{now_str}/templates/ → templates HTML globaux",
            f"  backup_{now_str}/static/    → fichiers CSS/JS",
            f"  backup_{now_str}/manage.py  → script Django",
            "",
            "Restauration SQLite  : copier db.sqlite3 à la racine du projet (NutriVa/)",
            "Restauration Postgres: psql -U <user> -d <dbname> < database/<name>_dump.sql",
        ]
        zf.writestr(f'backup_{now_str}/BACKUP_INFO.txt', '\n'.join(info_lines))

    buf.seek(0)

    if db_error:
        messages.warning(request, f"Backup généré avec une erreur DB : {db_error}")

    response = HttpResponse(buf.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    return response
