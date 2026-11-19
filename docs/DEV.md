# Développement

Prérequis : Docker avec Compose v2, uv 0.13.9, Node.js 22 et npm (Vite 8).
L’exécution de référence utilise Python 3.12.16 (Docker et future CI) ;
`requires-python >=3.12` autorise aussi les versions ultérieures en local.

## Installation et Compose

```sh
cp .env.example .env
# Remplacer tous les change-me ; synchroniser le mot de passe dans DATABASE_URL.
docker compose up --build
```

Interface : http://localhost:8080 (ou `FRONTEND_PORT`). L’API est accessible
via le frontend à `/api/v1/health`. Postgres et le backend ne publient aucun port.
Mailpit : http://127.0.0.1:8025 (ou `MAILPIT_UI_PORT`), uniquement pour le développement.
Le profil `dev` est activé par `COMPOSE_PROFILES=dev` dans l’exemple ; supprimer
cette valeur pour ne pas démarrer Mailpit. Aucun e-mail applicatif n’est encore envoyé.

Les builds utilisent `uv sync --frozen` et `npm ci` sur les lockfiles commités
`backend/uv.lock` et `frontend/package-lock.json`. Pour changer une dépendance,
exécuter `uv lock` dans `backend/` ou `npm install` dans `frontend/`, puis commiter
le lockfile correspondant.

Relire la configuration résolue (ports, volumes et utilisateur ; le backend
déclare `USER app` dans son Dockerfile) avant le démarrage :

```sh
docker compose config
```

Le backend exécute `alembic upgrade head` avant Uvicorn (un worker).
Le dossier de migrations est vide : aucune table métier ni seed dans cette issue.
Alembic nécessite un Postgres accessible même sans révision métier.
Les volumes nommés `pgdata` et `evidences` persistent entre redémarrages.
`EVIDENCE_STORAGE_DIR` désigne un chemin absolu interne ; il sert aussi d’argument
au build pour créer le répertoire privé appartenant à l’utilisateur non-root.
Ce volume n’est jamais monté ni servi par le frontend.

```sh
docker compose down
```

Ne pas ajouter `-v` pour conserver les données. Un rafraîchissement sur une route
frontend passe par le fallback SPA Nginx. La persistance des sessions sera couverte
avec l’authentification ; le scaffold ne crée aucune session.

## Backend local

Depuis la racine, exporter les variables nécessaires de `.env` dans le shell
(uvicorn lancé dans `backend/` ne charge pas automatiquement le `.env` racine).
`DATABASE_URL` est obligatoire et doit utiliser `postgresql+psycopg://`.
Le nom `postgres` désigne le service dans Compose ; pour un backend local,
utiliser une instance PostgreSQL locale dédiée et adapter l’URL sans publier
le port du service Compose. Ne pas utiliser de secrets de production.

```sh
cd backend
uv sync --frozen
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --no-access-log
```

Les tests injectent une URL fictive et n’ouvrent aucune connexion PostgreSQL.
Le healthcheck est un contrôle de liveness uniquement. CORS est désactivé par
défaut ; si nécessaire, `CORS_ALLOWED_ORIGINS` accepte une liste d’origines HTTP(S)
explicites séparées par des virgules, sans joker. En `APP_ENV=prod`, debug et
les routes `/docs`, `/redoc`, `/openapi.json` sont désactivés.

## Frontend local

```sh
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
npm run dev
```

Vite sert normalement http://localhost:5173 et relaie `/api` vers
`http://localhost:8000` par défaut. Pour changer cette cible, exporter
`VITE_API_PROXY_TARGET` avant `npm run dev`, ou la définir dans
`frontend/.env.local`. Cette variable n’est pas nécessaire dans le build Docker :
Nginx relaie `/api/` vers le backend en conservant le préfixe.
Le navigateur utilise des appels same-origin et ne stocke rien dans Web Storage.

## Journalisation

Nginx écrit sur stdout avec le format `chainscope_access` : adresse distante,
date, méthode, chemin (`$uri`), protocole, statut, octets envoyés, durée et
request ID renvoyé par le backend (`$upstream_http_x_request_id`).
Le journal d’accès backend est celui du middleware : méthode, chemin ASGI
(`scope["path"]`), statut et request ID serveur ajouté par le filtre de logs.
Les logs d’accès Uvicorn sont désactivés avec `--no-access-log`.

Ces logs d’accès excluent la query string, les en-têtes `Cookie` et
`X-CSRF-Token`, et le corps des requêtes. Les jetons d’invitation et de reset
passent par le fragment d’URL (`#token=`, ADR-025), qui n’est pas envoyé au serveur.

## Limites du scaffold

Ce socle ne comprend ni auth, ni routes métier, ni migrations de tables,
ni seed, ni tests Playwright (issue #27). Il ne valide donc pas encore
la persistance fonctionnelle F19 complète.
