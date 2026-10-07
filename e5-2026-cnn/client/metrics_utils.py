# client/metrics_utils.py
import requests
from prometheus_client.parser import text_string_to_metric_families

from config import API_METRICS_URL


def lire_metrics():
    """Télécharge /metrics et renvoie la liste de tous les échantillons."""
    r = requests.get(API_METRICS_URL, timeout=(5, 10))
    r.raise_for_status()
    return [
        sample
        for famille in text_string_to_metric_families(r.text)
        for sample in famille.samples
    ]


def somme(samples, nom):
    """Somme toutes les séries d'une métrique (0 si elle n'existe pas encore)."""
    return sum(s.value for s in samples if s.name == nom)


def par_label(samples, nom, cle):
    """Regroupe une métrique par label, ex. les prédictions par classe."""
    resultat = {}
    for s in samples:
        if s.name == nom:
            k = s.labels.get(cle, "?")
            resultat[k] = resultat.get(k, 0) + s.value
    return resultat


def moyenne_ms(samples, base):
    """Durée moyenne en ms d'un histogramme (None s'il n'y a pas de mesure)."""
    total = somme(samples, f"{base}_sum")
    nombre = somme(samples, f"{base}_count")
    return None if nombre == 0 else total / nombre * 1000