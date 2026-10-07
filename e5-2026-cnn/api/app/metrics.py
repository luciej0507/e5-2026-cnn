from functools import wraps

from prometheus_client import Counter, Histogram

PREDICTIONS_TOTAL = Counter(
    "predictions_total", "Prédictions du modèle CNN", ["label", "modele"]
)
PREDICTION_DURATION = Histogram(
    "prediction_duration_seconds", "Durée d'inférence du modèle CNN", ["modele"]
)
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds", "Durée des opérations BDD", ["operation"]
)
DB_ERRORS = Counter("db_errors_total", "Erreurs base de données", ["operation"])
LISTING_MISMATCH = Counter(
    "liste_predictions_incoherences_total",
    "Liste renvoyée avec moins de lignes que la base (ticket 4)",
)


def mesurer_bdd(operation):
    """Décorateur : mesure la durée et compte les erreurs d'une opération BDD."""
    def decorateur(fonction):
        @wraps(fonction)
        def wrapper(*args, **kwargs):
            with DB_QUERY_DURATION.labels(operation).time():
                try:
                    return fonction(*args, **kwargs)
                except Exception:
                    DB_ERRORS.labels(operation).inc()
                    raise
        return wrapper
    return decorateur