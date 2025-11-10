from django.shortcuts import render, redirect, get_object_or_404
#from .forms import PatientForm
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from .models import Patient, Constante, Vaccination, Rdv, Nutrition
from datetime import datetime, date
import calendar
import io
from django.template.loader import render_to_string
from django.utils import timezone


try:
    from docx import Document
except:
    Document = None

try:
    import weasyprint
except:
    weasyprint = None


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
    nutrition = Nutrition.objects.filter(patient=patient).first()
    
    context = {
        "patient": patient,
        "nutrition": nutrition,
    }
    return render(request, 'patient/nutrition.html', context)

#la vue pour la page de liste des patients
def liste_patients(request):
    patients = Patient.objects.all()
    return render(request, "patient/liste_patients.html", {"patients": patients})

# bouton rechercher dans la liste des patients
def rechercher_patients(request):
    query = request.GET.get('search')
    patients = Patient.objects.all()
    if query:
        
        patients = Patient.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query)|
            Q(telephone__icontains=query)
        ).distinct()
    context = {
        "patients": patients,
        "query": query,}
    return render(request, "patient/liste_patients.html", context)

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
    nutritions = Nutrition.objects.filter(patient_id__in=patients_ids, date_visite__range=[date_debut, date_fin])
    vaccinations = Vaccination.objects.filter(patient_id__in=patients_ids, date__range=[date_debut, date_fin])
    rdvs = Rdv.objects.filter(patient_id__in=patients_ids, date_enregistrement__range=[date_debut, date_fin])

    # 🔹 Construire la structure de données à afficher
    data = []
    for patient in patients:
        constante = constantes.filter(patient=patient).first()
        nutrition = nutritions.filter(patient=patient).first()
        vaccination = vaccinations.filter(patient=patient).first()
        rdv = rdvs.filter(patient=patient).first()

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

        code_unique = f"NUT-{date.today().year}-{str(Nutrition.objects.count() + 1).zfill(4)}",
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
        depiste = request.POST.get("depiste") or None
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

    for c in constantes:
        age_mois = c.patient.age
        sexe = c.patient.sexe[0].upper() if c.patient.sexe else "M"
        if sexe not in ["M", "F"]:
            sexe = "M"
        for g, (low, high) in age_groups.items():
            if low <= age_mois <= high:
                peses[g][sexe] += 1
                peses[g]["TOTAL"] += 1
                break
    total_peses = sum(p["TOTAL"] for p in peses.values())

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

    context = {
        "date_debut": start_date,
        "date_fin": end_date,
        "peses": peses,
        "total_peses": total_peses,
        "vaccinations": vaccinations,
        "antigen_counts": antigen_counts,
        "produit_counts": produit_counts,
        "rdv_count": rdvs.count(),
    }

    fmt = request.GET.get("format")
    if fmt == "docx":
        return _report_to_docx(context)
    elif fmt == "pdf":
        return _report_to_pdf(request, context)
    elif fmt == "html_download":
        html = render_to_string("patient/rapport.html", context)
        response = HttpResponse(html, content_type="text/html")
        response["Content-Disposition"] = f'attachment; filename="rapport_{start_date}_{end_date}.html"'
        return response

    return render(request, "patient/rapport.html", context)


# Génération DOCX
def _report_to_docx(context):
    if Document is None:
        return HttpResponseBadRequest("python-docx n'est pas installé.")
    doc = Document()
    doc.add_heading(f"Rapport du {context['date_debut']} au {context['date_fin']}", level=1)

    doc.add_heading("Séances de pesée", level=2)
    t = doc.add_table(rows=1, cols=4)
    hdr = t.rows[0].cells
    hdr[0].text = "Tranche"
    hdr[1].text = "M"
    hdr[2].text = "F"
    hdr[3].text = "Total"
    for g, c in context["peses"].items():
        row = t.add_row().cells
        row[0].text = g
        row[1].text = str(c["M"])
        row[2].text = str(c["F"])
        row[3].text = str(c["TOTAL"])

    doc.add_heading("Vaccinations", level=2)
    t2 = doc.add_table(rows=1, cols=2)
    t2.rows[0].cells[0].text = "Antigène"
    t2.rows[0].cells[1].text = "Nombre"
    for ag, n in context["antigen_counts"].items():
        r = t2.add_row().cells
        r[0].text = ag
        r[1].text = str(n)

    doc.add_heading("Produits distribués", level=2)
    t3 = doc.add_table(rows=1, cols=2)
    t3.rows[0].cells[0].text = "Produit"
    t3.rows[0].cells[1].text = "Quantité"
    for p, n in context["produit_counts"].items():
        r = t3.add_row().cells
        r[0].text = p
        r[1].text = str(n)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    response = HttpResponse(
        bio.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = f'attachment; filename="rapport_{context["date_debut"]}_{context["date_fin"]}.docx"'
    return response


# Génération PDF
def _report_to_pdf(request, context):
    if weasyprint is None:
        return HttpResponseBadRequest("WeasyPrint non installé.")
    html = render_to_string("patient/rapport.html", context)
    pdf = weasyprint.HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="rapport_{context["date_debut"]}_{context["date_fin"]}.pdf"'
    return response