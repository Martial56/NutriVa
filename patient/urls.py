from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('index', views.index, name="index"),
    path('ajouter/', views.creer_patient, name="creer_patient"),
    path('liste/', views.liste_patients, name="liste_patients"),
    path('constante/<int:patient_id>/', views.constante, name="constante"),
    path('vaccination/<int:patient_id>/', views.vaccination, name="vaccination"),
    
    path('nutrition/<int:patient_id>/', views.nutrition, name="nutrition"),
    path('rdv/', views.rdv, name="rdv"),
    path('liste_rdv/', views.liste_rdv, name="liste_rdv"),
 # urls.py
    path('rechercher_patients/', views.rechercher_patients, name="rechercher_patients"),
    path("rapport/", views.rapports, name="rapport"),
 
    path("enregistrement_patient/", views.enregistrement_patient, name="enregistrement_patient"),
    path('enregistrement_constante/<int:patient_id>/', views.enregistrement_constante, name='enregistrement_constante'),
    path('enregistrement_vaccin/<int:patient_id>/', views.enregistrement_vaccin, name='enregistrement_vaccin'),
    path('enregistrement_nutrition/<int:patient_id>/', views.enregistrement_nutrition, name='enregistrement_nutrition'),
    path('enregistrer_apport_nutrition/<int:patient_id>/', views.enregistrer_apport_nutrition, name='enregistrer_apport_nutrition'),
    path('historique_patient/<int:patient_id>/', views.historique_patient, name="historique_patient"),

    
]
