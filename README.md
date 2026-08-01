# App Paie Burkina Faso — Bordereau comptable payant par Orange Money

Application Android qui calcule les bulletins de paie (CNSS, IUTS, TPA...)
selon la réglementation burkinabè, et génère le bordereau d'écriture
comptable. Le bordereau détaillé est débloqué après paiement Orange Money
(paiement à l'unité, par bordereau généré).

## Structure du projet

```
paie_app/
├── main.py                    # Application Kivy (interface + logique app)
├── payroll_engine.py          # Moteur de calcul (validé contre le fichier Excel)
├── buildozer.spec             # Configuration de compilation Android
├── icon.png                   # Icône de l'app (à remplacer par la tienne)
├── backend/
│   ├── app.py                 # Serveur Flask (gère les paiements Orange Money)
│   └── requirements.txt
└── .github/workflows/
    └── build-apk.yml          # Compile l'APK automatiquement (GitHub Actions)
```

## Étape 1 — Compte de paiement Orange Money

Deux options :

**A. Agrégateur (recommandé pour démarrer rapidement)**
Inscris-toi chez [LigdiCash](https://ligdicash.com) ou [PayDunya](https://paydunya.com).
Ils ont déjà l'intégration Orange Money Burkina Faso opérationnelle.
L'inscription se fait en ligne, sans contrat direct avec Orange.
Tu obtiens une `API Key` et un `API Token` à mettre dans le backend.

**B. API Orange directe**
Contacte Orange Burkina via [orange.bf/fr/orange-developer.html](https://www.orange.bf/fr/orange-developer.html)
pour un partenariat marchand direct. Plus long à obtenir (dossier
entreprise), mais pas de commission d'agrégateur. Le fichier
`backend/app.py` est structuré pour que tu puisses remplacer l'appel
LigdiCash par l'API Orange directe plus tard, sans toucher à l'app mobile.

## Étape 2 — Déployer le backend de paiement

Le backend (`backend/app.py`) doit tourner sur un serveur en ligne
(jamais sur le téléphone). Option gratuite simple : [Render.com](https://render.com)

1. Crée un compte Render
2. "New Web Service" → connecte ton dépôt GitHub → sélectionne le dossier `backend/`
3. Build command : `pip install -r requirements.txt`
4. Start command : `gunicorn app:app`
5. Dans "Environment", ajoute tes variables :
   - `LIGDICASH_API_KEY`
   - `LIGDICASH_API_TOKEN`
   - `WEBHOOK_SECRET`
6. Une fois déployé, note l'URL (ex : `https://paie-bf-backend.onrender.com`)

## Étape 3 — Configurer l'app mobile

Dans `main.py`, modifie :
```python
BACKEND_URL = "https://paie-bf-backend.onrender.com"   # ton URL Render
PRIX_BORDEREAU_FCFA = 500                                # ton prix
```

## Étape 4 — Compiler l'APK (GitHub Actions, sans rien installer)

1. Crée un dépôt GitHub et pousse tout le contenu de `paie_app/`
2. Va dans l'onglet **Actions** → le workflow "Build APK" se lance
   automatiquement (ou "Run workflow" pour le lancer à la main)
3. Compte 15-25 minutes la première fois (Buildozer télécharge le SDK/NDK Android)
4. Une fois terminé, télécharge l'APK dans la section **Artifacts**

## Étape 5 — Tester et distribuer

- Teste d'abord l'APK "debug" sur ton téléphone (active "Sources inconnues"
  dans les paramètres Android pour installer hors Play Store)
- Pour publier sur le Play Store, il faudra signer l'APK en mode "release"
  (`buildozer android release`) — je peux t'accompagner sur cette étape
  quand tu seras prêt

## Points importants avant de lancer en production

- **Vérifie la réglementation BCEAO/Orange** sur les paiements électroniques
  au Burkina Faso avant de facturer des utilisateurs (statut d'entreprise,
  obligations fiscales, etc.) — je ne suis pas juriste, renseigne-toi
  auprès d'un comptable ou de la Chambre de Commerce.
- **Le webhook `/webhook`** doit être sécurisé (vérifier une signature ou
  un secret) avant mise en production, pour éviter que quelqu'un ne simule
  un faux paiement — la version actuelle est un point de départ à durcir.
- **Le barème IUTS et les taux CNSS** peuvent changer d'une année à l'autre
  au Burkina Faso — pense à vérifier/mettre à jour `payroll_engine.py`
  périodiquement.

## Vérification du moteur de calcul

`payroll_engine.py` a été testé contre les valeurs réelles calculées par
ton fichier Excel (`Paie.xlsx`, salarié "KAF JUILLE") — tous les résultats
correspondent exactement (net perçu, IUTS, CNSS, TPA, coût total, etc.).
