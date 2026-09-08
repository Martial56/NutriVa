from django import template

register = template.Library()


@register.filter
def age_affichage(age_mois):
    """Formate un âge exprimé en mois : "X ans" à partir de 5 ans, "X an(s) Y mois" avant."""
    try:
        mois = int(age_mois)
    except (TypeError, ValueError):
        return ""

    annees = mois // 12
    mois_restants = mois % 12

    if mois >= 60:
        return f"{annees} ans"

    if annees == 0:
        return f"{mois_restants} mois"

    return f"{annees} an{'s' if annees > 1 else ''} {mois_restants} mois"
