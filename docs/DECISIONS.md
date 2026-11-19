# Journal des décisions (ADR courts) — équipe A

Décisions **non prescrites** par `01_SPECIFICATIONS_ET_ARCHITECTURE.md`. Aucune ne modifie un contrat normatif ; les points qui en changeraient un sont des issues `architecture-question` (#29, #30, #31). Format : contexte, décision, alternatives, compromis, impact. Statut `Acceptée` = adoptée pour l'implémentation, révisable par PR.

---

## ADR-001 — Structure du monorepo
- **Date / statut :** 2026-11-19 — Acceptée (Tech Lead, #1)
- **Contexte :** 01 §2 impose un monolithe modulaire (couches `api / services / repositories / models / schemas / security`) et un frontend React séparé ; 04_GIT impose une CI unique.
- **Décision :** un seul dépôt :
  - `backend/` : paquet Python `app/` avec `api/` (routeurs v1), `services/`, `repositories/`, `models/`, `schemas/`, `security/`, `core/` (config, erreurs, middleware), `cli/` ; `alembic/` ; `tests/` (`unit/`, `api/`, `security/`).
  - `frontend/` : Vite + React + TypeScript strict + Tailwind + React Router + TanStack Query + `@xyflow/react`.
  - `e2e/` : projet Playwright autonome.
  - `docs/`, `docker-compose.yml`, `.env.example`, `.github/workflows/` à la racine.
- **Alternatives :** dépôts séparés (CI et revue fragmentées) ; backend servant le build frontend (couplage du déploiement).
- **Compromis :** deux écosystèmes d'outillage dans un dépôt ; jobs CI distincts.
- **Impact :** chemins de toutes les issues ; #5.

## ADR-002 — Version Python et images Docker
- **Date / statut :** 2026-11-19 — Acceptée (#5)
- **Contexte :** la stack exige Python 3.12+ ; la machine locale a Python 3.14, ce qui peut masquer des écarts (wheels, dépréciations).
- **Décision :** cible de référence **Python 3.12** : image `python:3.12-slim` (tag mineur figé, digest/patch fixé dans #5), CI `actions/setup-python` 3.12, `requires-python = ">=3.12"`. Les exécutions faisant foi (CI, Compose) se font en 3.12 ; un run local 3.14 n'est qu'indicatif. PostgreSQL `postgres:16` (alpine), Node **22 LTS** (image `node:22` pour le build, serveur statique/reverse proxy nginx pour le runtime), Mailpit en dev uniquement.
- **Alternatives :** Python 3.13/3.14 (plus récent mais écart possible avec l'image et les wheels) ; image `python:3.12` complète (plus lourde).
- **Compromis :** la version locale n'est pas celle de référence ; les développeurs utilisent `uv` (qui sait provisionner 3.12) ou Docker.
- **Impact :** #5, #6.

## ADR-003 — Gestion des dépendances
- **Date / statut :** 2026-11-19 — Acceptée (#5)
- **Décision :**
  - Backend : **uv** avec `pyproject.toml` + `uv.lock` commité ; `uv sync --frozen` en CI et Docker. Dépendances principales : FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2, Alembic, psycopg 3, argon2-cffi, python-multipart, uvicorn ; dev : pytest, httpx, ruff.
  - Frontend et e2e : **npm** avec `package-lock.json` commité ; `npm ci` en CI.
  - Versions exactes figées par les lockfiles (pas de plages flottantes en exécution) ; aucune dépendance SaaS payante ni Redis/broker (01 §2).
  - Détection du type de fichier des preuves par signatures internes (pas de dépendance système `libmagic`) — voir ADR-010.
- **Alternatives :** pip + requirements.txt hashés (plus verbeux, pas de résolution lockfile native), Poetry (plus lent en CI) ; pnpm (moins standard sur les images).
- **Compromis :** `uv` à installer en CI/Docker (binaire unique).
- **Impact :** #5, #6, reproductibilité F20.

## ADR-004 — Stratégie CI GitHub Actions
- **Date / statut :** 2026-11-19 — Acceptée (#6)
- **Décision :** `ci.yml` sur `pull_request` et `push` sur `main` avec jobs parallèles : **backend** (service `postgres:16`, ruff check/format, `alembic upgrade head`, pytest incluant tests API sur Postgres réel), **frontend** (lint, typecheck, `vitest run`, build), **compose** (`docker compose build`). `e2e.yml` en `workflow_dispatch` (Playwright sur Compose + seed), exécuté au moins avant clôture (04_GIT). Caches uv/npm. Variables de test fictives en clair dans le workflow, aucun secret externe.
- **Alternatives :** E2E à chaque PR (trop lent pour 48 h) ; SQLite en tests (non représentatif des FK composites et du trigger d'audit).
- **Compromis :** E2E non systématique ; compensé par les tests API d'intégration à chaque PR.
- **Impact :** règle « CI verte avant merge ».

## ADR-005 — Rôle developer = relais Codex CLI
- **Date / statut :** 2026-11-19 — Acceptée (cadre équipe A)
- **Contexte :** l'équipe A est « Claude lead / Codex développeur ». 03_ROLES exige la traçabilité de toute intervention de modèle.
- **Décision :** le code applicatif est produit par **Codex CLI** lancé par le rôle developer (`codex exec --sandbox workspace-write` sur une branche dédiée, brief = issue + critères d'acceptation). Le rôle developer contrôle le diff et les tests, puis ouvre la PR. Si Codex est absent, refuse ou échoue de façon persistante : **arrêt et signalement au commanditaire**, sans remplacement silencieux par Claude. Jamais de `danger-full-access`.
- **Alternatives :** implémentation directe par Claude (contraire au cadre de l'équipe).
- **Compromis :** dépendance à un outil externe ; latence de relais.
- **Impact :** toutes les issues `role:developer` ; chaque PR mentionne qu'elle a été produite via Codex.

## ADR-006 — Sessions, cookies et CSRF
- **Date / statut :** 2026-11-19 — Acceptée (#8), review Cyber requise
- **Décision :** token de session 32 octets aléatoires (`secrets`), seul `SHA-256(token)` est stocké (haute entropie : pas besoin de sel/KDF). Cookie `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` piloté par config (obligatoire hors dev). Expiration absolue configurable (variable d'env, défaut documenté dans #8). Jeton CSRF distinct par session, stocké haché, obtenu via `GET /auth/csrf`, envoyé dans l'en-tête `X-CSRF-Token` pour toute méthode mutante ; vérification en temps constant. Contrôle complémentaire de l'en-tête `Origin` sur mutations (#26). Révocation à la déconnexion et de toutes les sessions au changement/réinitialisation de mot de passe. Argon2id via argon2-cffi (paramètres par défaut de la bibliothèque, re-hash si paramètres changent).
- **Alternatives :** JWT (interdit de fait : sessions opaques imposées) ; double-submit cookie sans stockage (moins lié à la session).
- **Impact :** #8, #15, #16, #17.

## ADR-007 — Limitation de débit sans Redis
- **Date / statut :** 2026-11-19 — Acceptée (#8, #15)
- **Décision :** limiteur à fenêtre glissante **en mémoire du processus** (clés : IP et e-mail normalisé haché), seuils en configuration ; backend lancé avec **un seul worker** uvicorn dans Compose. Réponse 429 au format normalisé, message non révélateur.
- **Alternatives :** table PostgreSQL de tentatives (multi-worker, plus de charge DB) ; Redis (exclu par 01 §2).
- **Compromis :** compteurs perdus au redémarrage et non partagés entre workers — limite documentée (THREAT_MODEL) ; évolution possible vers stockage DB.
- **Impact :** #8, #15.

## ADR-008 — Sémantique 403/404 et chargement des ressources
- **Date / statut :** 2026-11-19 — Acceptée (#10), review Cyber requise
- **Décision :** chaque route charge la ressource **avec** le contrôle de membership (une requête filtrée par tenant/engagement dérivés de la base). Ressource inexistante ou hors périmètre → **404** identique (01 §6) ; ressource dans le périmètre mais rôle insuffisant → **403**. Références invalides dans un body (ex. `client_org_id`, asset d'un autre engagement) → **400 `INVALID_REFERENCE`** avec le même message qu'une référence inexistante. Schémas d'entrée `extra="forbid"` (F17).
- **Alternatives :** 403 systématique (révèle l'existence de la ressource).
- **Impact :** toutes les routes métier ; tests #26.

## ADR-009 — Origine unique navigateur ↔ backend
- **Date / statut :** 2026-11-19 — Acceptée (#5)
- **Décision :** en dev, proxy Vite `/api` → backend ; dans Compose, le conteneur frontend (nginx) sert le build statique et reverse-proxy `/api` vers le backend. Le navigateur ne voit qu'une origine ; CORS désactivé par défaut et, si activé, liste explicite sans `*`.
- **Impact :** cookies `SameSite=Lax` sans cross-site ; CSP `default-src 'self'` possible (#26).

## ADR-010 — Stockage et validation des preuves
- **Date / statut :** 2026-11-19 — Acceptée (#20), review Cyber requise
- **Décision :** interface `EvidenceStorage` (put/open/delete) avec implémentation locale sur volume Docker privé monté hors de tout répertoire servi ; `storage_key` = UUID4 aléatoire, jamais dérivé du nom utilisateur ; écriture en flux vers fichier temporaire avec coupure à 10 Mio (413), calcul SHA-256 à la volée, validation extension + Content-Type + signature (PDF `%PDF-`, PNG, JPEG ; TXT = UTF-8 valide sans NUL), puis `rename` atomique ; suppression du temporaire en cas de rejet (F14). Nom d'origine conservé uniquement en métadonnée assainie pour `Content-Disposition`.
- **Alternatives :** `python-magic`/libmagic (dépendance système) ; stockage en base (BLOB) — moins évolutif vers stockage objet.
- **Impact :** #20, #26.

## ADR-011 — Implémentation de l'algorithme de chemins
- **Date / statut :** 2026-11-19 — Acceptée (#21)
- **Décision :** fonction pure (`services/paths.py`) prenant actifs et edges actifs déjà filtrés par engagement ; DFS depuis chaque entry point, chemins simples de 1 à 6 edges, cible crown jewel ; score calculé en `Decimal` (règle d'arrondi : hypothèse AQ #31) ; tri (score desc, longueur asc, liste des UUID d'edges en texte minuscule canonique asc), troncature à 20 ; garde d'expansions maximale (constante nommée) pour borner le temps. Réponse = tableau JSON (pas d'enveloppe) conformément à 01 §6 « liste ordonnée ».
- **Alternatives :** requête SQL récursive (CTE) — plus difficile à tester et à borner finement.
- **Impact :** F08–F11 ; tests unitaires exhaustifs des cas 02 §3.

## ADR-012 — Forme des listes paginées
- **Date / statut :** 2026-11-19 — Acceptée (#5)
- **Décision :** les routes de liste (hors `graph/paths`) renvoient `{ "items": [...], "total": n, "limit": l, "offset": o }` ; `limit` défaut 20, max 100 (au-delà → 422), `offset >= 0`. Tri par défaut déterministe documenté par route.
- **Alternatives :** tableau nu + en-têtes de pagination (moins lisible côté client).
- **Impact :** toutes les listes ; client API frontend.

## ADR-013 — Format d'erreur et request ID
- **Date / statut :** 2026-11-19 — Acceptée (#5)
- **Décision :** middleware générant un `request_id` UUID serveur (renvoyé en `X-Request-ID`, inscrit dans les logs et `audit_events.request_id`) ; tous les handlers (HTTPException, validation Pydantic 422, erreurs métier, 500) produisent `{ "error": { "code", "message", "request_id" } }` ; codes symboliques (`UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `CONFLICT`, `ENGAGEMENT_CLOSED`, `LIMIT_REACHED`, `INVALID_REFERENCE`, `CSRF_FAILED`, `RATE_LIMITED`, `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `INTERNAL_ERROR`). Jamais de trace ni de secret dans la réponse.
- **Impact :** toutes les routes ; F18 (corrélation).

## ADR-014 — État côté frontend
- **Date / statut :** 2026-11-19 — Acceptée (#17)
- **Décision :** aucune donnée sensible en `localStorage`/`sessionStorage` ; jeton CSRF en mémoire ; TanStack Query vidé à la déconnexion/changement d'utilisateur ; portail client ne consomme que les routes `/client/*` ; rendu de tout contenu utilisateur en texte (pas de `dangerouslySetInnerHTML`, pas de rendu Markdown HTML).
- **Impact :** #17, #18, #22–#24 ; F15 et invariant 10_UX.

## ADR-015 — Conflits d'état et plafonds
- **Date / statut :** 2026-11-19 — Acceptée (#13, #14, #21)
- **Décision :** mutation sur mission `CLOSED` → **409 `ENGAGEMENT_CLOSED`** (hypothèse AQ #30) ; plafonds 150 actifs / 300 edges par engagement → **409 `LIMIT_REACHED`** ; edge doublon exact (source, cible, finding) → 409 ; suppression d'un actif référencé par des edges → 409 `ASSET_IN_USE` (pas de cascade silencieuse).
- **Alternatives :** 400 pour tout écart métier ; suppression en cascade des edges.
- **Compromis :** la distinction 400 (donnée invalide) / 409 (état courant) est une interprétation de 01 §6, réversible si le commanditaire tranche autrement.

## ADR-016 — Audit append-only
- **Date / statut :** 2026-11-19 — Acceptée (#7, #11)
- **Décision :** aucune route ni méthode de repository de mise à jour/suppression ; trigger PostgreSQL refusant `UPDATE`/`DELETE` sur `audit_events` ; écriture dans la même transaction que la mutation ; liste blanche de clés de métadonnées, filtrage des clés sensibles.
- **Impact :** F18.

## ADR-017 — Horodatage et identifiants
- **Date / statut :** 2026-11-19 — Acceptée (#7)
- **Décision :** UUID4 générés côté serveur (01 §5) ; `timestamptz` en UTC ; e-mails normalisés en minuscules pour l'unicité.

## ADR-018 — Stratégie de branches, review et merge
- **Date / statut :** 2026-11-19 — Acceptée (#1)
- **Décision :** voir `docs/PLAN.md` §5 : une issue = une PR ; QA systématique ; Cyber sur les PR sensibles ; Designer sur les PR frontend ; merge squash après CI verte et approbations, par le coordinateur ; aucun push direct sur `main`.

## ADR-019 — Smoke Playwright dès la sortie de J2
- **Date / statut :** 2026-11-19 — Acceptée (review QA de PR #32, issue #34)
- **Contexte :** la suite E2E complète (#27) n'arrive qu'en J4 ; les défauts d'intégration proxy / cookies `SameSite` / CSRF ne sont visibles qu'en navigateur réel à travers le reverse proxy (ADR-009).
- **Décision :** recommandation QA **retenue**. Issue #34 (P0, J2) : smoke Playwright local connexion → client → mission → constat → déconnexion, contre `docker compose up`, sans mock ; il initialise le projet `e2e/` réutilisé par #27. Exécution locale documentée, sortie jointe à la PR ; intégration CI via `e2e.yml` (`workflow_dispatch`) comme #27.
- **Alternatives :** attendre #27 (risque de découverte tardive) ; E2E complet à chaque PR (trop coûteux en 48 h).
- **Compromis :** une PR supplémentaire en J2 sur le chemin de sortie du jalon ; coût faible car le projet `e2e/` sert ensuite à #27.

## ADR-020 — Preuve de persistance F19 par `down`/`up`
- **Date / statut :** 2026-11-19 — Acceptée (review QA de PR #32, issue #27)
- **Décision :** recommandation QA **retenue**. F19 est vérifié par `docker compose restart` **et** `docker compose down` (sans `-v`) puis `up` : les données Postgres et les fichiers du volume de preuves restent présents, et une session non expirée reste valide (cookie réutilisé). `down -v` est explicitement exclu du test (il détruit les volumes nommés).
- **Justification :** `restart` ne recrée pas les conteneurs et ne prouve pas que les données sont dans des volumes nommés plutôt que dans la couche du conteneur.
