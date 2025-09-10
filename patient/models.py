from django.db import models

class Patient(models.Model):
    code = models.CharField(max_length=6)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=300)
    date_naissance = models.DateField()
    nom_parent= models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
