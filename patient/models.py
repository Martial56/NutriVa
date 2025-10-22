from django.db import models

class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=300)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10)
    nom_parent= models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Constante(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    poids = models.FloatField()
    taille = models.FloatField()
    perimetre_brachial = models.FloatField()
    zscore = models.FloatField()
    #tension = models.CharField(max_length=20)
    imc = models.FloatField()
    indicecorporel = models.CharField(max_length=50)
    def __str__(self):
        return f"Constantes de {self.patient} le {self.date}"

class Vaccination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    bcg= models.CharField(max_length=100)
    polio0= models.CharField(max_length=100)
    vpo= models.CharField(max_length=100)
    dtc= models.CharField(max_length=100)
    pcv= models.CharField(max_length=100)
    vpi= models.CharField(max_length=100)
    rota= models.CharField(max_length=100)
    vaa= models.CharField(max_length=100)
    var= models.CharField(max_length=100)
    vat= models.CharField(max_length=100)
    vam= models.CharField(max_length=100)
    vam= models.CharField(max_length=100)

    def __str__(self):
        return f"Vaccination {self.vaccin} de {self.patient} le {self.date}"
    
class Nutrition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    code_unique = models.CharField(max_length=100)
    date_visite = models.DateField()
    date_admission = models.DateField()
    date_sortie = models.DateField()
    etat_nutrition = models.CharField(max_length=500)
    status = models.CharField(max_length=500) # nouveau, en cours, sortant

    def __str__(self):
        return f"Nutrition {self.type_nutrition} de {self.patient} le {self.date}"
    
class Autreservice(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    depistage = models.CharField(max_length=100)
    codedepistage = models.TextField()
    resultattest = models.TextField()
    vitamina_dose1 = models.TextField()
    vitamina_dose2 = models.TextField()
    plumpynut = models.TextField()
    deparasitant = models.TextField()

    def __str__(self):
        return f"Service {self.type_service} de {self.patient} le {self.date}"