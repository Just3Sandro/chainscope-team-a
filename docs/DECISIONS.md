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
- **Décision :** middleware générant un `request_id` UUID serveur (renvoyé en `X-Request-ID`, inscrit dans les logs et `audit_events.request_id`) ; tous les handlers (HTTPException, validation Pydantic 422, erreurs métier, 500) produisent `{ "error": { "code", "message", "request_id" } }` ; codes symboliques (`UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `CONFLICT`, `ENGAGEMENT_CLOSED`, `LIMIT_REACHED`, `INVALID_REFERENCE`, `CSRF_FAILED`, `RATE_LIMITED`, `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `TENANT_SUSPENDED`, `ASSET_IN_USE`, `INTERNAL_ERROR`). Jamais de trace ni de secret dans la réponse.
- **Correspondance HTTP** (01 §6, aucun autre statut) : `UNSUPPORTED_MEDIA_TYPE` → **400** (pas de 415) ; `PAYLOAD_TOO_LARGE` → 413 ; `TENANT_SUSPENDED` → 403 (ADR-026) ; `ENGAGEMENT_CLOSED`, `LIMIT_REACHED`, `ASSET_IN_USE`, `CONFLICT` → 409 ; `RATE_LIMITED` → 429.
- **Impact :** toutes les routes ; F18 (corrélation). Complété le 2026-11-19 (PR de suivi de #12, ADR-026).

## ADR-014 — État côté frontend
- **Date / statut :** 2026-11-19 — Acceptée (#17)
- **Décision :** aucune donnée sensible en `localStorage`/`sessionStorage` ; aucun état d'autorisation persisté côté navigateur : après un rechargement de page, la coquille reconstruit l'espace courant et les memberships via `GET /auth/me` (ADR-021), puis récupère un nouveau jeton CSRF via `GET /auth/csrf` ; jeton CSRF en mémoire ; TanStack Query vidé à la déconnexion/changement d'utilisateur ; portail client ne consomme que les routes `/client/*` ; rendu de tout contenu utilisateur en texte (pas de `dangerouslySetInnerHTML`, pas de rendu Markdown HTML).
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

---

## Décisions UX du designer (PR #36, issue #2)

Décisions non prescrites proposées par le rôle Designer dans `docs/DESIGN.md` et validées par le Tech Lead. Elles portent sur l'interface uniquement, aucun contrat de 01 n'est modifié. Les invariants restent ceux de 01 §7 et de 10_UX : vérité serveur, aucune fuite dans le DOM, parcours complets.

| ID | Décision | Alternatives écartées | Compromis / impact |
|---|---|---|---|
| D-UX-01 | Design system « Relevé » (relevé topographique), palette encre et papier, accent sarcelle, glyphe original | Reprendre l'identité d'une référence (interdit par 10_UX) | Toutes les pages front |
| D-UX-02 | Polices système uniquement, aucune webfont | Police distante (incompatible avec CSP `'self'`, ADR-009), police embarquée (poids) | Compatible avec la CSP de #26 |
| D-UX-03 | Thème clair seul pour le socle, mode sombre reporté après les bonus | Clair et sombre dès J2 | Moins de surface à vérifier en contraste |
| D-UX-04 | Sévérité : badge rectangulaire, jauge à 4 barres et libellé, `CRITICAL` seul plein. Statut : pastille ronde à contour avec icône | Couleur seule (non accessible) | Composants badges (#18, #23) |
| D-UX-05 | Routes front `/t/:tenantId/...`, `/portal/...`, `/platform/...`, sélecteur `/spaces` ; trois coquilles visuellement distinctes. Le `tenantId` d'URL est un simple contexte, jamais une autorisation | Une seule coquille avec menus conditionnels (confusion, risque de fuite) | #17 ; s'appuie sur ADR-021 |
| D-UX-06 | Création d'edge par formulaire (Source, Cible, Constat) en parcours principal ; glisser-relier en raccourci ; déplacement des nœuds au clavier avec `Maj+flèches` | Glisser-relier seul (inaccessible au clavier) | #22 |
| D-UX-07 | Panneau textuel (chemins et relations) comme équivalent accessible complet du canvas, avec un bouton « Liste » | Canvas seul avec ARIA | #22, tablette |
| D-UX-08 | Edges dont le constat est `REMEDIATED` affichés en pointillé « neutralisée », pas masqués ; l'état vient du serveur (ADR-024) | Masquer les edges inactifs | #22, F09 visible |
| D-UX-09 | Toasts en bas à droite, 3 au plus ; succès 5 s avec pause au survol ; erreurs persistantes avec `request_id` | Toasts bloquants ou modales | Tous les écrans |
| D-UX-10 | Suppression : focus initial sur « Annuler ». Publication : le dialog liste ce que verra le client | Confirmation générique | #18, #22, #23 |
| D-UX-11 | Tablette : rail de navigation de 64 px, colonnes prioritaires, panneau du graphe en tiroir | Mise en page desktop compressée | #17, #18, #22 |
| D-UX-12 | Contrastes vérifiés par un script versionné (`docs/tools/check_contrast.py`) sur les paires déclarées dans les tokens | Vérification manuelle ponctuelle | Reproductible, branchable en CI |

## ADR-021 — Contenu de `GET /auth/me` et de la réponse de login (Q1 du designer)
- **Date / statut :** 2026-11-19 — Acceptée (#8). Ajoute des champs de réponse, aucun nouveau contrat.
- **Contexte :** 01 §6 définit `GET /auth/me` et « résultat utilisateur » au login sans en donner la forme. Le front a besoin de savoir quels espaces proposer (D-UX-05).
- **Décision :** `POST /auth/login` et `GET /auth/me` renvoient le même objet :
  ```json
  { "user": { "id": "uuid", "email": "..." },
    "is_platform_admin": false,
    "tenant_memberships": [ { "tenant_id": "uuid", "tenant_name": "...", "tenant_slug": "...", "role": "TENANT_ADMIN|PENTESTER" } ],
    "client_memberships": [ { "client_org_id": "uuid", "client_org_name": "...", "tenant_name": "...", "role": "CLIENT_VIEWER" } ] }
  ```
  - Les memberships sont lus en base à chaque appel, jamais mis en cache côté client au-delà de la session TanStack Query (ADR-014).
  - Les tenants suspendus sont exclus de `tenant_memberships` (#12), tout comme leurs client_orgs.
  - Ne figurent jamais dans la réponse : `password_hash`, identifiant ou jetons de session, jeton CSRF. Le jeton CSRF reste servi par `GET /auth/csrf`. `client_memberships` n'expose pas de `tenant_id`, qui est inutile au portail.
  - Ces informations ne servent qu'à l'affichage : l'autorisation reste vérifiée par ressource côté serveur (ADR-008).
- **Alternatives :** un endpoint « espaces » dédié (contrat supplémentaire) ; déduire les espaces par essais d'appels (bruit de 403/404).

## ADR-022 — Agrégats du tableau de bord sans nouvel endpoint (Q2 du designer)
- **Date / statut :** 2026-11-19 — Acceptée (#13, #24). Ajoute des champs de réponse, aucun nouvel endpoint.
- **Contexte :** 01 §7.2 demande « constats par gravité » sur le tableau de bord, et 01 §6 ne prévoit aucune route d'agrégat. Interroger les findings mission par mission coûterait N requêtes.
- **Décision :** pas d'endpoint d'agrégat. Les éléments de `GET /tenants/{tenant_id}/engagements` (liste et détail) portent deux champs **calculés serveur** :
  - `findings_count_by_severity` : `{LOW, MEDIUM, HIGH, CRITICAL}` ;
  - `findings_count_by_status` : `{OPEN, IN_PROGRESS, REMEDIATED, ACCEPTED_RISK}`.
  
  Le dashboard appelle `GET .../engagements?status=IN_PROGRESS&limit=100` et additionne ces compteurs côté front, sans aucune logique métier.
  - Côté portail, `GET /client/engagements` peut exposer `published_findings_count` (constats publiés uniquement, jamais les non publiés).
  - « Activité récente » : flux `audit-events` pour `TENANT_ADMIN`. Pour `PENTESTER`, on utilise les constats récemment modifiés via `GET /engagements/{id}/findings?sort=-updated_at`, sur les missions en cours.
- **Alternatives :** `GET /tenants/{tenant_id}/stats` (extension hors §6, écartée pour ne pas étendre le contrat) ; N requêtes de listes (lent).
- **Compromis :** les compteurs sont recalculés à chaque liste (agrégat SQL groupé, borné par la pagination).

## ADR-023 — Filtres serveur des listes (Q3 du designer)
- **Date / statut :** 2026-11-19 — Acceptée (#11, #12, #13, #14, #16, #19). Paramètres de requête optionnels, compatibles avec 01 §6 qui exige des « filtres serveur ».
- **Décision :** tous les paramètres sont optionnels et validés. Une valeur hors enum renvoie 422, un paramètre inconnu est ignoré. Les recherches `q` portent sur les champs texte indiqués, en `ILIKE` paramétré par l'ORM, avec une longueur maximale nommée.

  | Liste | Filtres | Tri par défaut |
  |---|---|---|
  | `GET /platform/tenants` | `q` (name, slug), `is_active` | `name` |
  | `GET /tenants/{id}/clients` | `q` (name) | `name` |
  | `GET /tenants/{id}/members` | `role` | `email` |
  | `GET /tenants/{id}/clients/{id}/invitations` | `state` (`pending`, `consumed`, `expired`) | `-created_at` |
  | `GET /tenants/{id}/engagements` | `status`, `client_org_id`, `q` (name) | `-updated_at` |
  | `GET /engagements/{id}/assets` | `type`, `is_entry_point`, `is_crown_jewel`, `q` (name) | `name` |
  | `GET /engagements/{id}/findings` | `severity`, `status`, `published` (bool), `q` (title), `sort` ∈ {`-updated_at`, `-cvss`, `-created_at`} | `-updated_at` |
  | `GET /tenants/{id}/audit-events` | `action`, `entity_type`, `from`, `to` | `-created_at` |
  | `GET /client/engagements` | `status` | `-updated_at` |
  | `GET /client/engagements/{id}/findings` | `severity`, `status` | `-published_at` |

  - Les filtres multi-valeurs passent par la répétition du paramètre (`?severity=HIGH&severity=CRITICAL`).
  - `client_org_id` n'est accepté que s'il appartient au tenant chargé ; sinon la liste est vide (pas de fuite).
  - Les listes client restent restreintes aux constats publiés, quel que soit le filtre.
- **Alternatives :** filtrage côté client (interdit pour la pagination serveur, 10_UX).

## ADR-024 — Statut du constat dans `GET /graph/edges` (Q4 du designer)
- **Date / statut :** 2026-11-19 — Acceptée (#21, #22). Ajoute des champs de réponse au contrat de §6.
- **Décision :** chaque edge renvoyé par `GET /engagements/{id}/graph/edges` (et par le POST de création) contient :
  - `id`, `source_asset_id`, `target_asset_id`, `finding_id` ;
  - `finding` : `{ id, title, severity, cvss, status }` ;
  - `is_active` : booléen **calculé serveur** selon la règle de 01 §4 (`status ∈ {OPEN, IN_PROGRESS, ACCEPTED_RISK}`).
  
  Le front affiche `is_active` (D-UX-08) sans jointure avec la liste des findings et sans recalcul. `GET /graph/paths` garde exactement la forme de 01 §6 (`{edge_ids, asset_ids, score, target_asset_id}`), sans champ supplémentaire.
- **Alternatives :** jointure front avec la liste des findings (deux sources à synchroniser, risque d'incohérence transitoire et règle d'activité dupliquée côté client).
- **Impact :** une seule requête jointe côté serveur ; le front ne détient aucune règle métier de chemin (10_UX).

## ADR-025 — Précisions d'ADR-008 : codes 403/404, ordre des contrôles, tenant suspendu
- **Date / statut :** 2026-11-19 — Acceptée (proposition Cyber, `docs/THREAT_MODEL.md` §6–§7, PR #37 ; issues #10, #12, #16, #19). Précise ADR-008 sans modifier 01 §6.
- **Contexte :** 01 §6 donne la règle « 404 ressource inexistante ou hors périmètre ; 403 permission insuffisante » sans dire quand un utilisateur authentifié est hors périmètre, ni dans quel ordre les contrôles s'appliquent.
- **Décision :**
  1. **404 hors membership cabinet.** Sur `/tenants/{tenant_id}/*` et `/engagements/{engagement_id}/*`, tout principal sans membership `TENANT_ADMIN`/`PENTESTER` dans le tenant de la ressource reçoit 404. C'est le cas de `CLIENT_VIEWER` (même sur son propre engagement), de `PLATFORM_ADMIN` et des membres d'un autre tenant. **Seule exception** (hypothèse AQ #29) : `PLATFORM_ADMIN` sur `POST /tenants/{tenant_id}/members` avec `role=TENANT_ADMIN` (201 ; autre rôle → 403 ; tenant inexistant → 404).
  2. **403 pour un rôle insuffisant dans le tenant.** Exemple : PENTESTER sur une route réservée à l'admin. Il connaît déjà le tenant, la réponse ne révèle donc rien.
  3. **`/platform/*`** : 403 pour tout utilisateur authentifié non plateforme. C'est une capacité globale : il n'y a aucune ressource à masquer.
  4. **Ordre des contrôles** (invariant testé par la suite SEC-RBAC de #26) :
     - 401 (session) ;
     - 403 `CSRF_FAILED` (méthodes mutantes) ;
     - 404 (périmètre parent chargé avec les memberships) ;
     - 403 `TENANT_SUSPENDED` ;
     - 403 (rôle, **avant** tout chargement d'enfant) ;
     - 404 (enfant chargé **dans** son parent) ;
     - 422 / 400 / 409 / 413.
     
     L'authentification et l'autorisation sont des dépendances FastAPI résolues **avant** la validation du corps, pour qu'un 422 ne révèle rien à un appelant non autorisé. Seule exception tolérée : un 413 émis par le reverse proxy avant le backend. `client_max_body_size` est réglé **au-dessus** de 10 Mio + enveloppe multipart, de sorte que la limite contractuelle et son 413 restent appliqués par le backend, après autorisation.
  5. **PENTESTER** reçoit 403 sur `GET/POST /tenants/{tenant_id}/members` et sur `GET/POST /tenants/{tenant_id}/clients/{client_id}/invitations`. La gestion des membres et des invitations relève du TENANT_ADMIN (01 §1).
  6. **Tenant suspendu** (`tenants.is_active=false`, #12) :
     - ses membres cabinet reçoivent **403 `TENANT_SUSPENDED`** sur les routes du tenant. Ils connaissent déjà le tenant, et le message est explicite pour l'interface ;
     - ses engagements disparaissent du portail client (listes vides, détail et téléchargement en 404) ;
     - le tenant est exclu de `GET /auth/me` (ADR-021) ;
     - les routes `/platform/*` restent accessibles au PLATFORM_ADMIN.
     
     Le code `TENANT_SUSPENDED` s'ajoute à la liste d'ADR-013.
  7. **Droits cumulés par ressource** : un utilisateur à la fois membre cabinet et client voit chaque ressource selon le membership qui s'y applique, jamais selon un « rôle principal » (01 §1).
- **Recommandations Cyber associées, validées** (commentaires #13, #16, #17) :
  - `client_org_id` d'un engagement non modifiable après création, pour éviter de basculer des constats publiés vers un autre client (`PATCH` → 422 sur ce champ) ;
  - `POST /auth/accept-invitation` pour un e-mail déjà inscrit : le `password` du body doit correspondre au mot de passe existant (vérification Argon2id) avant d'ajouter le membership. Le mot de passe n'est jamais remplacé par cette route ;
  - jetons d'invitation et de reset transmis dans le **fragment** d'URL (`#token=`), avec `Referrer-Policy: no-referrer`.
- **Alternatives :** 403 pour les clients sur les routes cabinet (révèle l'existence des UUID) ; 404 pour un tenant suspendu (message incompréhensible pour ses membres légitimes).
- **Impact :** #10 (policies), #12, #16, #19, #26 (tests paramétrés sur la matrice de THREAT_MODEL §7.2).

## ADR-026 — Comportement d'un tenant suspendu, réponse de forgot-password et `returnTo`
- **Date / statut :** 2026-11-19 — Acceptée (suivi de la review QA des PR #33, #36 et #37 ; issues #12, #15, #17). Précise ADR-025 §6, sans modifier les contrats de 01.
- **Tenant suspendu** (`tenants.is_active=false`, `PATCH /platform/tenants/{tenant_id}`, #12) :
  1. **La connexion est conservée.** Le login et `GET /auth/me` fonctionnent : un utilisateur peut avoir d'autres memberships (01 §1). Ni l'utilisateur ni ses sessions ne sont désactivés. Le tenant suspendu et ses client_orgs sont absents de `/auth/me` (ADR-021). Un utilisateur sans aucun autre espace voit l'état « aucun espace disponible » dans l'interface.
  2. **L'accès aux données du cabinet est refusé.** Toute route `/tenants/{tenant_id}/*` et `/engagements/{engagement_id}/*` de ce tenant renvoie **403 `TENANT_SUSPENDED`** à ses membres cabinet, après le contrôle de périmètre (404) et avant le contrôle de rôle (ordre d'ADR-025). Les non-membres continuent de recevoir 404.
  3. **Les engagements sont retirés du portail client.** `GET /client/engagements` ne liste plus les engagements de ce tenant. Le détail, les constats et le téléchargement de preuves renvoient **404**, sans code spécifique, pour ne pas révéler l'état d'un cabinet à ses clients.
  4. **Les routes plateforme restent ouvertes.** `PLATFORM_ADMIN` garde l'accès à `/platform/*`. La réactivation (`is_active=true`) rétablit les accès sans autre action. Les événements `tenant.suspend` et `tenant.reactivate` sont journalisés (#11).
  5. **Libellé UI** (DESIGN P8) : « Les membres de ce cabinet n'auront plus accès à ses données et ses clients ne verront plus ses missions. » La formulation « ne pourront plus se connecter » est inexacte.
  6. **Tests** (SEC-suspended, #12 et #26) :
     - membre cabinet → 403 `TENANT_SUSPENDED` ;
     - non-membre → 404 ;
     - client → liste vide et 404 ;
     - login toujours 200 et `/auth/me` sans ce tenant ;
     - réactivation → accès rétabli.
- **`POST /auth/forgot-password`** (#15) : la réponse est **204 sans corps**, identique que le compte existe ou non. Le 202 initialement écrit dans #15 ne fait pas partie des statuts de 01 §6.
- **`returnTo` après connexion** (#17) : seul un chemin interne relatif est accepté. Il doit commencer par un seul `/`, ne pas commencer par `//` ni par `/\`, et ne contenir ni antislash, ni schéma (`:` avant le premier `/`), ni caractère de contrôle. Il est en outre comparé à la table des routes connues. Sinon, on redirige vers l'accueil de l'espace. Test Vitest attendu avec les cas `//evil`, `/\evil`, `/\/evil`, `https://evil`, `javascript:` et un chemin encodé (`%2F%2Fevil`).
- **Alternatives :** désactiver les utilisateurs du tenant suspendu (destructif pour les utilisateurs multi-memberships) ; 403 `TENANT_SUSPENDED` côté client (révèle l'état interne du cabinet).
- **Impact :** #12, #15, #17, #19, #24, #26 ; DESIGN P8 ; THREAT_MODEL R6, dont la matrice doit afficher 204 pour forgot-password.
