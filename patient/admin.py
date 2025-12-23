from django.contrib import admin
from .models import Patient, Constante, Vaccination, Nutrition, Rdv

# Register your models here.


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "prenom",
        "sexe",
        "date_naissance",
        "age",
        "quartier",
        "telephone",
        "date_creation",
    )

    list_filter = ("sexe", "quartier", "date_creation")
    search_fields = ("nom", "prenom", "telephone", "quartier")
    ordering = ("-date_creation",)

    readonly_fields = ("date_creation",)

    fieldsets = (
        ("Identité du patient", {
            "fields": ("nom", "prenom", "sexe", "date_naissance")
        }),
        ("Informations familiales", {
            "fields": ("nom_parent", "telephone", "quartier")
        }),
        ("Informations système", {
            "fields": ("date_creation",)
        }),
    )

@admin.register(Constante)
class ConstanteAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "date",
        "poids",
        "taille",
        "imc",
        "zscore",
        "indicecorporel",
    )

    list_filter = ("date", "indicecorporel")
    search_fields = ("patient__nom", "patient__prenom")
    date_hierarchy = "date"

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("patient", "vaccin", "date")
    list_filter = ("vaccin", "date")
    search_fields = ("patient__nom", "patient__prenom", "vaccin")
    date_hierarchy = "date"

@admin.register(Nutrition)
class NutritionAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "etat_nutrition",
        "date_visite",
        "date_admission",
        "date_sortie",
    )

    list_filter = ("etat_nutrition", "date_visite")
    search_fields = ("patient__nom", "patient__prenom", "etat_nutrition")
    date_hierarchy = "date_visite"

@admin.register(Rdv)
class RdvAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "depiste",
        "resultat",
        "produits_list",
        "date_enregistrement",
    )

    list_filter = ("depiste", "resultat", "date_enregistrement")
    search_fields = ("patient__nom", "patient__prenom", "code_depistage")
    readonly_fields = ("date_enregistrement",)

    def produits_list(self, obj):
        return obj.produits_list()

    produits_list.short_description = "Produits distribués"
