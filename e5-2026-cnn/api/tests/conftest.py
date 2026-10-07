import os

# Doit s'exécuter avant l'import de app.config (donc avant les tests).
# setdefault ne remplace pas une variable déjà définie.
os.environ.setdefault("MYSQL_DATABASE", "test_db")
os.environ.setdefault("MYSQL_USER", "test_user")
os.environ.setdefault("MYSQL_PASSWORD", "test_password")