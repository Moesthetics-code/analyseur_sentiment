# 🚀 Déploiement sur Render

Ce guide couvre le déploiement complet de SentimentAI sur [Render](https://render.com), de la création du compte jusqu'à la mise en production avec un domaine personnalisé. Chaque étape est détaillée avec les commandes exactes et les captures d'écran décrites.

---

## Table des matières

1. [Pourquoi Render ?](#pourquoi-render)
2. [Prérequis](#prérequis)
3. [Préparer le dépôt GitHub](#préparer-le-dépôt-github)
4. [Créer le compte Render](#créer-le-compte-render)
5. [Créer le Web Service](#créer-le-web-service)
6. [Configurer les variables d'environnement](#configurer-les-variables-denvironnement)
7. [Fichiers de configuration Render](#fichiers-de-configuration-render)
8. [Premier déploiement](#premier-déploiement)
9. [Surveiller les logs](#surveiller-les-logs)
10. [Domaine personnalisé](#domaine-personnalisé)
11. [Optimisations production](#optimisations-production)
12. [Limites du plan gratuit](#limites-du-plan-gratuit)
13. [Résolution de problèmes](#résolution-de-problèmes)
14. [Mise à jour de l'application](#mise-à-jour-de-lapplication)

---

## Pourquoi Render ?

Render est la plateforme la plus simple pour déployer une app Flask Python :

- **Plan gratuit** : 750 heures/mois, HTTPS automatique, déploiement Git
- **Zéro configuration serveur** : pas de Nginx, pas de systemd, pas de SSH
- **Build automatique** : chaque `git push` déclenche un redéploiement
- **Variables d'environnement** : interface web sécurisée
- **Logs en temps réel** : directement dans le dashboard

---

## Prérequis

Avant de commencer, assurez-vous d'avoir :

- Un compte **GitHub** avec votre dépôt du projet pushé
- Un compte **Render** (gratuit, inscription en 2 minutes)
- Python 3.11+ listé dans `runtime.txt` (créé ci-dessous)
- `gunicorn` dans `requirements.txt`

---

## Préparer le dépôt GitHub

### 1. S'assurer que gunicorn est dans les dépendances

Ouvrez `requirements.txt` et vérifiez la présence de `gunicorn` :

```
flask>=3.0
gunicorn>=21.2
nltk>=3.8
deep-translator>=1.11
langdetect>=1.0.9
wordcloud>=1.9
transformers>=4.40
torch>=2.2
Pillow>=10.0
```

### 2. Créer `runtime.txt`

Ce fichier indique à Render quelle version de Python utiliser.

```bash
echo "python-3.11.9" > runtime.txt
```

> Render supporte Python 3.8 à 3.12. Utilisez la même version que votre environnement local.

### 3. Créer `render.yaml` (optionnel mais recommandé)

Ce fichier permet de décrire toute la configuration de déploiement en code (Infrastructure as Code). Créez-le à la racine :

```yaml
# render.yaml
services:
  - type: web
    name: sentimentai
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info
    envVars:
      - key: SECRET_KEY
        generateValue: true          # Render génère automatiquement une valeur sécurisée
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.9
    healthCheckPath: /
    autoDeploy: true
```

### 4. Créer `.gitignore`

```bash
cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.py[cod]
*.pyo
.env
*.egg-info/
dist/
build/

# Modèles HuggingFace (volumineux, téléchargés au runtime)
.cache/
huggingface/

# Editors
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
EOF
```

### 5. Pousser sur GitHub

```bash
git add .
git commit -m "feat: configuration déploiement Render"
git push origin main
```

---

## Créer le compte Render

1. Allez sur [render.com](https://render.com)
2. Cliquez sur **Get Started for Free**
3. Choisissez **Sign up with GitHub** (recommandé — permet à Render d'accéder à vos repos directement)
4. Autorisez l'accès à votre organisation ou aux repos spécifiques
5. Vérifiez votre email si demandé

---

## Créer le Web Service

### Étape 1 — Nouveau service

Dans le dashboard Render :

1. Cliquez sur le bouton **New +** en haut à droite
2. Sélectionnez **Web Service**

### Étape 2 — Connecter le dépôt

Render affiche la liste de vos dépôts GitHub.

- Si votre repo apparaît : cliquez sur **Connect** en face de `sentiment-analyzer`
- Si votre repo n'apparaît pas : cliquez sur **Configure account** → dans GitHub, accordez l'accès au repo manquant → revenez sur Render

### Étape 3 — Configurer le service

Remplissez le formulaire de configuration :

| Champ | Valeur |
|-------|--------|
| **Name** | `sentimentai` (ou ce que vous voulez, détermine l'URL) |
| **Region** | `Frankfurt (EU Central)` si vous êtes en Europe, sinon `Oregon (US West)` |
| **Branch** | `main` |
| **Root Directory** | laisser vide (ou `sentiment_app` si votre code est dans un sous-dossier) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

> **Important :** La variable `$PORT` est fournie automatiquement par Render. Ne la codez pas en dur.

### Étape 4 — Choisir le plan

- **Free** : gratuit, mais le service s'endort après 15 minutes d'inactivité (cold start ~30 s)
- **Starter ($7/mois)** : toujours actif, recommandé pour la production
- **Standard ($25/mois)** : plus de RAM, adapté au modèle DistilBERT en charge

Pour commencer, sélectionnez **Free**.

### Étape 5 — Créer le service

Cliquez sur **Create Web Service**. Render lance immédiatement le premier build.

---

## Configurer les variables d'environnement

Même si vous avez défini les variables dans `render.yaml`, vous pouvez les gérer depuis l'interface :

1. Dans votre service, cliquez sur l'onglet **Environment**
2. Cliquez sur **Add Environment Variable**

### Variables à configurer

| Clé | Valeur | Remarque |
|-----|--------|----------|
| `SECRET_KEY` | (générer avec la commande ci-dessous) | **Obligatoire en production** |
| `FLASK_ENV` | `production` | Désactive le mode debug |
| `PYTHON_VERSION` | `3.11.9` | Fixe la version Python |

### Générer une SECRET_KEY sécurisée

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Exemple de sortie : a3f8e2c1d0b9a847f3e2c1d0b9a847f3e2c1d0b9a847f3e2c1d0b9a847f3e2c1
```

Copiez cette valeur dans le champ `SECRET_KEY` sur Render. Ne la commitez **jamais** dans Git.

### Cliquer sur Save Changes

Render redémarre automatiquement le service avec les nouvelles variables.

---

## Fichiers de configuration Render

### `runtime.txt`

```
python-3.11.9
```

### `Procfile` (alternative à render.yaml)

Si vous préférez ne pas utiliser `render.yaml`, créez un `Procfile` à la racine :

```
web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info
```

### `render.yaml` complet avec toutes les options

```yaml
services:
  - type: web
    name: sentimentai
    env: python
    plan: free
    region: frankfurt
    branch: main
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
      python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt_tab')"
    startCommand: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info --access-logfile -
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.9
    healthCheckPath: /
    autoDeploy: true
    scaling:
      minInstances: 1
      maxInstances: 1
```

> **Astuce :** Le `buildCommand` multi-lignes télécharge les données NLTK au moment du build plutôt qu'au premier appel — ce qui évite un délai à la première requête.

---

## Premier déploiement

### Suivre le build

Une fois le service créé, Render affiche les logs du build en temps réel :

```
==> Cloning from https://github.com/vous/sentiment-analyzer...
==> Checking out commit abc1234...
==> Running build command: pip install -r requirements.txt
    Collecting flask>=3.0
    ...
    Successfully installed flask-3.0.3 nltk-3.8.1 ...
==> Build successful 🎉
==> Starting service with: gunicorn "app:create_app()"...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
```

### Accéder à l'application

Une fois le déploiement terminé (2–5 minutes selon les dépendances), Render affiche l'URL :

```
https://sentimentai.onrender.com
```

Cliquez dessus pour ouvrir l'application. HTTPS est automatiquement activé.

---

## Surveiller les logs

### Logs en temps réel

Dans le dashboard de votre service, cliquez sur l'onglet **Logs**. Vous voyez :

- Les logs de Gunicorn (requêtes HTTP, erreurs)
- Les prints Python (si vous en avez ajouté)
- Les erreurs d'import ou de modèle

### Filtrer les logs

Utilisez la barre de recherche pour filtrer :

- `ERROR` : affiche uniquement les erreurs
- `POST /api/analyze` : affiche uniquement les appels d'analyse
- `500` : affiche les erreurs serveur

### Logs de build

L'onglet **Events** liste tous les déploiements avec leur statut (succès / échec) et les logs complets de chaque build.

---

## Domaine personnalisé

### Ajouter un domaine

1. Allez dans l'onglet **Settings** de votre service
2. Section **Custom Domains** → cliquez **Add Custom Domain**
3. Entrez votre domaine, par exemple : `sentiment.monsite.fr`
4. Render affiche un enregistrement DNS à créer

### Configurer le DNS

Chez votre registrar (OVH, Cloudflare, Namecheap, Gandi…) :

**Si vous utilisez un sous-domaine (`sentiment.monsite.fr`) :**

```
Type    : CNAME
Nom     : sentiment
Valeur  : sentimentai.onrender.com
TTL     : 300
```

**Si vous utilisez un apex domain (`monsite.fr`) :**

```
Type    : A
Nom     : @
Valeur  : 216.24.57.1   (IP fournie par Render — vérifiez dans leur interface)
TTL     : 300
```

### Vérification

La propagation DNS peut prendre 5 à 30 minutes. Render vérifie automatiquement et active le certificat TLS Let's Encrypt.

---

## Optimisations production

### 1. Pré-charger les modèles au démarrage

Pour éviter le délai au premier appel, chargez les modèles dans `app.py` :

```python
# app.py
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Pré-charger VADER au démarrage (rapide)
    with app.app_context():
        try:
            from modules.sentiment import _get_vader
            _get_vader()
            app.logger.info("VADER chargé.")
        except Exception as e:
            app.logger.warning(f"VADER non chargé : {e}")

    return app
```

### 2. Augmenter le timeout Gunicorn pour DistilBERT

Le premier appel DistilBERT peut prendre 20–60 secondes. Augmentez le timeout :

```
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 1 --timeout 180
```

> Sur le plan gratuit, utilisez `--workers 1` pour ne pas dépasser la RAM disponible (512 Mo).

### 3. Désactiver le wordcloud si la RAM est limitée

Si le service plante avec `MemoryError`, désactivez le wordcloud par défaut en modifiant `_run_analysis` dans `routes/api.py` :

```python
# Forcer generate_wc=False sur le plan gratuit
result = _run_analysis(text, source_lang, model, generate_wc=False)
```

### 4. Cache du modèle HuggingFace

Par défaut, HuggingFace télécharge les modèles dans `~/.cache/huggingface`. Sur Render, ce cache est **détruit à chaque déploiement** sur le plan gratuit.

Pour conserver le cache entre les déploiements, montez un **Disk persistant** (plan payant) :

```yaml
# render.yaml
services:
  - type: web
    ...
    disk:
      name: hf-cache
      mountPath: /opt/render/.cache
      sizeGB: 5
```

Puis définissez la variable :

```
TRANSFORMERS_CACHE=/opt/render/.cache/huggingface
HF_HOME=/opt/render/.cache/huggingface
```

### 5. Utiliser `gevent` pour gérer la concurrence

```bash
pip install gevent
```

```
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --worker-class gevent --workers 1 --timeout 120
```

### 6. Désactiver DistilBERT sur le plan gratuit

Si vous souhaitez garder l'app légère (< 512 Mo RAM), commentez l'import du pipeline Transformers et renvoyez une erreur explicite pour `model=transformers` :

```python
# modules/sentiment.py
def analyze_with_transformers(text, source_lang='fr'):
    raise RuntimeError("Le modèle Transformers est désactivé sur ce serveur. Utilisez VADER.")
```

---

## Limites du plan gratuit

| Limite | Valeur | Impact |
|--------|--------|--------|
| RAM | 512 Mo | DistilBERT + modèle émotions dépassent cette limite |
| CPU | Partagé | Analyse lente sous charge |
| Inactivité | Endormissement après 15 min | Cold start de 30–60 s |
| Heures/mois | 750 h | Suffit pour un projet perso (1 service = ~31 jours) |
| Disque | Éphémère | Cache HuggingFace perdu à chaque déploiement |
| Domaines | 1 par service | Suffisant |

**Recommandation :** Pour une app de démonstration ou un projet personnel, le plan gratuit avec VADER uniquement est parfait. Pour la production avec Transformers, passez au plan **Starter ($7/mois)** qui offre 512 Mo de RAM dédiée et pas d'endormissement.

---

## Résolution de problèmes

### ❌ `ModuleNotFoundError: No module named 'xxx'`

Le module n'est pas dans `requirements.txt`. Ajoutez-le et redéployez :

```bash
pip freeze | grep nom-du-module >> requirements.txt
git add requirements.txt && git commit -m "fix: ajout dépendance manquante" && git push
```

### ❌ `OSError: [Errno 28] No space left on device`

Le disque temporaire de Render est plein (souvent causé par les modèles HuggingFace). Solutions :

1. Utilisez un Disk persistant (plan payant)
2. Désactivez DistilBERT et le modèle d'émotions (utilisez uniquement VADER)
3. Définissez `TRANSFORMERS_OFFLINE=1` pour empêcher les téléchargements

### ❌ `Worker timeout` / `[CRITICAL] WORKER TIMEOUT`

La requête a pris trop longtemps. Causes possibles :

- Premier chargement d'un modèle Transformers
- Requête de traduction bloquée

Solutions :

```
# Augmenter le timeout
gunicorn ... --timeout 180

# Ou utiliser un worker async
gunicorn ... --worker-class gevent --timeout 60
```

### ❌ Application inaccessible après déploiement réussi

Vérifiez que la commande de démarrage utilise bien `$PORT` et non un port fixe :

```
# ✅ Correct
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT

# ❌ Incorrect (Render utilise un port dynamique)
gunicorn "app:create_app()" --bind 0.0.0.0:5000
```

### ❌ `RuntimeError: Working outside of application context`

Causé par un import de module Flask en dehors du contexte d'application. Assurez-vous que les imports lourds (modèles) se font à l'intérieur des fonctions, pas au niveau du module.

### ❌ Erreur 500 sur `/api/analyze` uniquement en production

Souvent causé par une `SECRET_KEY` manquante ou invalide. Vérifiez que la variable est bien définie dans **Environment** sur Render.

### ❌ La détection de langue échoue

`langdetect` utilise des données aléatoires. Pour des résultats reproductibles, ajoutez en haut de `modules/langdetect_module.py` :

```python
from langdetect import DetectorFactory
DetectorFactory.seed = 0
```

---

## Mise à jour de l'application

### Déploiement automatique (recommandé)

Si `autoDeploy: true` est défini dans `render.yaml`, chaque `git push` sur la branche `main` déclenche automatiquement un redéploiement.

```bash
# Modifier du code
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
# → Render détecte le push et redéploie automatiquement
```

### Déploiement manuel

1. Dans le dashboard, cliquez sur **Manual Deploy**
2. Sélectionnez **Deploy latest commit**

### Rollback

Pour revenir à une version précédente :

1. Onglet **Events** dans votre service
2. Trouvez le déploiement précédent (état "Live")
3. Cliquez sur les trois points `···` → **Rollback to this deploy**

---

## Checklist de déploiement

Avant de mettre en production, vérifiez chaque point :

- [ ] `gunicorn` présent dans `requirements.txt`
- [ ] `runtime.txt` créé avec la version Python correcte
- [ ] `SECRET_KEY` configurée (longue, aléatoire, jamais dans Git)
- [ ] `FLASK_ENV=production` défini en variable d'environnement
- [ ] La commande start utilise `$PORT`
- [ ] Le repo GitHub est public ou Render a accès au repo privé
- [ ] Le fichier `.gitignore` exclut `venv/`, `.env`, `__pycache__/`
- [ ] Le build passe sans erreur dans les logs Render
- [ ] L'URL `https://votre-app.onrender.com` répond avec un HTTP 200
- [ ] L'analyse d'un texte de test fonctionne correctement

---

Développé par [Mohamed Ndiaye](https://github.com/Moesthetics-code/sentiment-analyzer) · Guide de déploiement SentimentAI