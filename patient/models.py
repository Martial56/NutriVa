from django.db import models
from datetime import date
from django.utils import timezone

class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=300)
    date_naissance = models.DateField()
    date_creation = models.DateField()
    sexe = models.CharField(max_length=10)
    nom_parent= models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def age(self):
        # Calcul de l'âge approximatif en mois pour l'agrégation dans les rapports
        today = date.today()
        return (today.year - self.date_naissance.year) * 12 + today.month - self.date_naissance.month

class Constante(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    poids = models.FloatField()
    taille = models.FloatField()
    perimetre_brachial = models.FloatField(null=True, blank=True)
    zscore = models.FloatField()
    #tension = models.CharField(max_length=20)
    imc = models.FloatField()
    indicecorporel = models.CharField(max_length=50)
    def __str__(self):
        return f"Constantes de {self.patient} le {self.date}"

class Vaccination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    vaccin= models.CharField(max_length=500)
    
    def __str__(self):
        return f"Vaccination {self.vaccin} de {self.patient} le {self.date}"
    
class Nutrition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    code_nutrition = models.CharField(max_length=100)
    date_visite = models.DateField()
    date_admission = models.DateField()
    date_sortie = models.DateField(null=True, blank=True) 
    etat_nutrition = models.CharField(max_length=500)
    motif_sortie = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Nutrition {self.etat_nutrition} de {self.patient} le {self.date_visite}"
    
class Rdv(models.Model):
    RESULTAT_CHOICES = [
        ("positif", "Positif"),
        ("negatif", "Négatif"),
    ]

    DEPISTE_CHOICES = [
        ("oui", "Oui"),
        ("non", "Non"),
    ]

    PRODUITS_CHOICES = [
        ("lait", "Lait"),
        ("plumpy", "Plumpy Nut"),
        ("deparasitant", "Déparasitant"),
        ("vitA100", "Vitamine A100"),
        ("vitA200", "Vitamine A200"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    depiste = models.CharField(max_length=5, choices=DEPISTE_CHOICES)
    code_depistage = models.CharField(max_length=50, blank=True, null=True)
    resultat = models.CharField(max_length=10, choices=RESULTAT_CHOICES, blank=True, null=True)
    produits = models.JSONField(default=list)  # pour enregistrer plusieurs produits
    date_enregistrement = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Rapport nutrition - {self.patient.nom} {self.patient.prenom}"

    def produits_list(self):
       # Créer un dictionnaire de mapping clé -> libellé pour une recherche facile
        choices_dict = dict(self.PRODUITS_CHOICES)
        
        # Mapper chaque clé (ex: "lait") dans self.produits à son libellé (ex: "Lait")
        # Si une clé n'est pas trouvée (ce qui ne devrait pas arriver), utiliser la clé elle-même
        produits_libelles = [choices_dict.get(key, key) for key in self.produits]

        # Joindre les libellés par une virgule pour l'affichage
        return ", ".join(produits_libelles) if produits_libelles else "-"