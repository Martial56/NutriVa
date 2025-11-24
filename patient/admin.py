from django.contrib import admin
from .models import Patient
# Register your models here.


class PatientAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'date_naissance', 'sexe','age', 'telephone')
    search_fields = ('prenom', 'nom', 'telephone')
    list_filter = ('sexe',)
    
    
admin.site.register(Patient, PatientAdmin)