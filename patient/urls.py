from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('ajouter/', views.creer_patient, name="creer_patient"),
    path('liste/', views.liste_patients, name="liste_patients"),
    path('constante/', views.constante, name="constante"),
    path('vaccination/', views.vaccination, name="vaccination"),
 # urls.py
    path("enregistrement_patient/", views.enregistrement_patient, name="enregistrement_patient")

    
]
