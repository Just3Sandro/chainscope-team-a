# ChainScope : rapport QA (équipe A)

- **Auteur :** rôle QA / Reviewer
- **Statut :** squelette J1 (issue #4). Le document est alimenté à chaque PR mergée puis finalisé dans #28.
- **Sources normatives :** `01_SPECIFICATIONS_ET_ARCHITECTURE.md` (contrats), `02_PLAN_DE_TEST_ET_SECURITE.md` (F01–F20, §3, §4, §6), `04_GIT_ISSUES_PR_CI.md` (CI).
- **Règle absolue (03_ROLES) :** un test n'est déclaré `OK` que s'il a été **réellement exécuté**, avec une commande et un journal consigné (§5). Sinon, son statut reste `à faire` ou `non exécuté`.
- Les tests privés du commanditaire ne sont pas dans ce dépôt et ne seront pas recherchés. Toutes les données de test sont fictives (02 §1).

## 1. Stratégie de test : pyramide

| Niveau | Outil | Portée | Où | Quand |
|---|---|---|---|---|
| Unitaire backend | pytest | Fonctions pures et services : algorithme de chemins (`services/paths.py`), validation des preuves (signatures, taille), filtre de métadonnées d'audit, hachage des jetons, schémas Pydantic `extra="forbid"` | `backend/tests/unit/` | Chaque PR (CI) |
| Intégration API | pytest + HTTPX sur **PostgreSQL 16 réel** (service CI, jamais SQLite) | Routes `/api/v1` de bout en bout : codes HTTP, format d'erreur, RBAC, isolation tenant/engagement/client, CSRF, audit, migrations `alembic upgrade head` | `backend/tests/api/` | Chaque PR (CI) |
| Sécurité backend | pytest paramétré (route × rôle × ressource étrangère) | 02 §3 : substitution d'IDs, sessions, CSRF/Origin, uploads, en-têtes | `backend/tests/security/` | Chaque PR à partir de #10, complétée dans #26 |
| Composants frontend | Vitest (+ Testing Library) | États chargement/erreur/vide, rendu texte des contenus utilisateur (F15), client API (en-tête CSRF, purge du cache à la déconnexion), routage par rôle | `frontend/src/**/*.test.ts(x)` | Chaque PR frontend (CI) |
| Build / typecheck | `tsc --noEmit`, `vite build`, ruff, `docker compose build` | Compilation et lint | CI | Chaque PR |
| End-to-end | Playwright contre `docker compose up` + seed #25 | Parcours de référence de 02 §2 dans un vrai navigateur | `e2e/` | Smoke dès la sortie de J2 (#34, ADR-019), suite complète avant clôture (#27) |
| Vérifications manuelles | curl/HTTPX local, inspection navigateur | Échange d'IDs, en-têtes, logs, persistance du volume, responsive | Instance locale isolée | J4 (#26, #28) |

Principes :
- **Fixtures communes** : jeu de 02 §1 (Aegis Red Team / Acme Santé, Boreal Security / Boreal Finance, six utilisateurs, graphe Web→API→DB) construit par factories, sans mot de passe en dur (valeurs générées ou issues de la configuration de test).
- **Chaque route métier** a au moins un cas positif et un cas négatif d'autorisation : autre tenant → 404, rôle insuffisant → 403.
- **Exécutions de référence** en Python 3.12 (CI/Docker, ADR-002). Un run local en 3.14 est seulement indicatif et doit être signalé comme tel.
- Toute anomalie est ouverte en issue (`security` si elle touche une frontière de confiance), avec l'impact, les préconditions et une reproduction non destructive.

## 2. Matrice F01–F20

Niveaux : U = unitaire, I = intégration API (Postgres), S = suite sécurité, V = Vitest, E = Playwright, M = vérification manuelle.
Statuts : `à faire` / `en cours` / `OK` (avec réf. d'exécution §5) / `KO` (avec issue).

| ID | Scénario (02 §2) | Niveaux | Issue(s) porteuse(s) | Statut | Réf. exécution |
|---|---|---|---|---|---|
| F01 | Login, logout, re-login ; ancienne session refusée | I, V, E | #8, #17, #34, #27 | à faire | — |
| F02 | Invitation client consommée puis rejouée | I, E | #16, #17, #27 | à faire | — |
| F03 | Admin Aegis crée client + engagement | I, E | #13, #34, #27 | à faire | — |
| F04 | Pentester crée actif + constat (validation, visibilité cabinet) | I, E | #14, #34, #27 | à faire | — |
| F05 | Client lit un finding non publié (UUID connu) → absent | I, S | #19, #26 | à faire | — |
| F06 | Finding publié visible client autorisé, invisible autre client | I, S, E | #19, #23, #26, #27 | à faire | — |
| F07 | Client tente de modifier un finding → refus backend | I, S | #14, #19 | à faire | — |
| F08 | Graphe Web→API→DB : un chemin, score 75.0 | U, I, E | #21, #22, #25, #27 | à faire | — |
| F09 | F2 REMEDIATED → chemin disparu, edge conservé | U, I, E | #21, #22, #27 | à faire | — |
| F10 | F2 ACCEPTED_RISK → chemin de nouveau actif | U, I, E | #21, #27 | à faire | — |
| F11 | Edge vers actif d'un autre engagement → rejet, état inchangé | I, S | #7, #21, #26 | à faire | — |
| F12 | Upload PNG/PDF : stockage privé, SHA-256, download autorisé | U, I, E | #20, #23, #27 | à faire | — |
| F13 | Client devine un evidence ID privé → refus | I, S | #20, #23, #26 | à faire | — |
| F14 | Fichier interdit ou > 10 Mio → rejet, aucun objet durable | U, I | #20 | à faire | — |
| F15 | XSS dans titre/description → aucun script exécuté | V, E, S | #14, #18, #23, #26, #27 | à faire | — |
| F16 | Mutation sans jeton CSRF correct → refus | I, S, E | #8, #17, #34, #26 | à faire | — |
| F17 | Rôle/tenant injecté dans le body → sans effet (mass assignment) | U, I, S | #10, #13, #16, #26 | à faire | — |
| F18 | Action sensible → audit event sans jeton ni mot de passe | U, I | #11 (+ chaque issue émettrice) | à faire | — |
| F19 | Refresh + redémarrage Compose → données et sessions persistées | E, M | #5, #26, #27 | à faire | — |
| F20 | Clone propre → `docker compose up --build`, migrations/seed, aucun secret | M | #5, #28 | à faire | — |

Notes de couverture :
- F19 : tester `docker compose restart` **et** `docker compose down` puis `up` (sans `-v`). Une session non expirée doit rester valide, et les preuves comme la base doivent survivre.
- F20 : rejouer l'installation dans un répertoire temporaire depuis `git clone`, sans fichier local hérité, et consigner le journal complet.
- F18 : chaque issue qui émet un événement d'audit (#8, #9, #12, #13, #14, #15, #16, #19, #20, #21) inclut un test de présence de l'événement et de recherche de chaînes sensibles dans `metadata_json`.

## 3. Tests sécurité complémentaires (02 §3)

Ces tests sont distincts des scénarios F. Ils sont portés par `backend/tests/security/` (#26) et par les issues citées.

| Domaine | Cas | Niveau | Issue | Statut |
|---|---|---|---|---|
| Isolation | Substitution de `tenant_id`, `engagement_id`, `finding_id`, `client_org_id` dans l'URL, le JSON et les filtres (lecture, écriture, téléchargement, agrégation) → 404 | S | #10, #26 | à faire |
| Isolation | Listes sans donnée du voisin ; réponses client sans champ interne (assertion sur les clés) | S | #19, #26 | à faire |
| Isolation | Publication/rétractation par un client ; élévation par paramètres | S | #19, #26 | à faire |
| Isolation | `PLATFORM_ADMIN` sans membership : aucun accès aux findings, preuves, actifs, edges, clients | S | #10 | à faire |
| Sessions | Cookie expiré, révoqué ou altéré → 401 | I, S | #8, #26 | à faire |
| Sessions | Reset token réutilisé ou expiré ; invitation expirée ou rejouée | I | #15, #16 | à faire |
| Sessions | Reset de mot de passe → anciennes sessions révoquées | I | #15 | à faire |
| Sessions | CSRF absent ou faux sur chaque méthode mutante ; contrôle de `Origin` | S | #8, #26 | à faire |
| Sessions | Cookie de session absent du JS (HttpOnly), des logs, des URL et du HTML | S, M | #26 | à faire |
| Sessions | Rate limit login/reset → 429 sans révéler l'existence du compte | I | #8, #15 | à faire |
| Contenu | Payloads HTML/JS inoffensifs dans tous les champs texte → rendus comme texte | V, E | #18, #23, #26 | à faire |
| Stockage | Faux MIME, faux suffixe, nom avec `../`, PDF volumineux, content-type dangereux ; nettoyage du temporaire | U, I | #20 | à faire |
| Stockage | Download : `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, aucun accès statique au volume | I, M | #20, #26 | à faire |
| Logique | Cycles, edges doublons, éléments supprimés, aucun crown jewel, CVSS 0/10, plus de 6 sauts, égalité de scores, plus de 20 chemins, recalcul après correction | U | #21 | à faire |
| Logique | Mutations sur mission `CLOSED` (hypothèse AQ #30) ; finding d'un autre engagement dans un edge ; preuve non publiée | I | #13, #14, #20, #21 | à faire |
| Production | En-têtes CSP, `frame-ancestors`, `Referrer-Policy`, CORS explicite, `Secure`, debug désactivé, erreurs sans secret | M, S | #26 | à faire |

### 3.1 Tests complémentaires issus de `docs/THREAT_MODEL.md` (§7.2, §10, PR #37)

Ces tests sont à créer dans `backend/tests/security/`, sauf mention contraire. Ils sont référencés par leur identifiant dans le threat model.

| ID | Cas | Menace | Niveau | Issue | Statut |
|---|---|---|---|---|---|
| SEC-RBAC | Matrice route × rôle paramétrée : 44 routes × 7 profils (ANO, PA, TA, PT, CV, XT, XC), codes attendus de THREAT_MODEL §7.2 | T-API-01/07, T-EVD-06, T-GRA-04, T-INV-04 | S | #10, #26 | à faire |
| SEC-fixation | Session présentée au login révoquée, nouveau token émis | T-AUTH-04 | I | #8 | à faire |
| SEC-login-origin | Login et routes à token refusés si `Origin` est étranger | T-AUTH-08 | S | #8, #26 | à faire |
| SEC-token-url | Jeton d'invitation/reset absent des logs, du `Referer` et de la query | T-INV-05 | I, E | #15, #16, #17 | à faire |
| SEC-invite-existing | Invitation vers un compte existant : preuve de possession exigée (hypothèse #16) | T-INV-07 | I | #16 | à faire |
| SEC-reassign | **Obligatoire (ADR-025)** : `client_org_id` d'un engagement non modifiable après création (`PATCH` avec ce champ → 422, aucun changement en base, constats publiés toujours rattachés au client d'origine) | T-API-06 | I | #13, #26 | à faire |
| SEC-unpublish | Après rétractation : constat et preuves à nouveau en 404 côté client | T-CLI-06 | I | #19, #20 | à faire |
| SEC-sqli | Payloads d'injection dans `q`, tri et filtres sans effet (liste blanche) | T-API-09 | S | #10, #13, #14 | à faire |
| SEC-dos-paths | Graphe dense au plafond (150/300) : réponse bornée en temps, au plus 20 chemins | T-GRA-02 | U, I | #21 | à faire |
| SEC-RL-login / SEC-RL-forgot | 429 normalisé au seuil, message identique pour un compte existant ou inexistant | T-AUTH-01, T-INV-09 | I | #8, #15 | à faire |
| SEC-suspended | Tenant suspendu (ADR-026, ordre ADR-025) : (a) membre cabinet → 403 `TENANT_SUSPENDED` sur `/tenants/{t}/*` et `/engagements/{e}/*` ; (b) non-membre → 404 (périmètre avant suspension) ; (c) `CLIENT_VIEWER` → `GET /client/engagements` sans ses engagements, puis détail, constats et download en 404, sans code spécifique ; (d) `POST /auth/login` → 200 et `GET /auth/me` sans ce tenant ni ses client_orgs ; (e) `PLATFORM_ADMIN` garde `/platform/*` ; (f) réactivation → accès rétablis sans autre action ; (g) audit `tenant.suspend` et `tenant.reactivate` présents | T-API-08 | I | #12, #26 | à faire |
| SEC-audit-immutable | `UPDATE`/`DELETE` sur `audit_events` refusés par trigger | T-AUD-01 | I | #7, #11 | à faire |
| SEC-forgot-204 | `POST /auth/forgot-password` → 204 sans corps, réponses identiques octet pour octet (statut, en-têtes pertinents, corps) pour un compte existant, inexistant ou inactif (ADR-026, THREAT_MODEL R7) | T-INV-06 | I | #15 | à faire |
| SEC-returnTo | Validation de `returnTo` après connexion (ADR-026, voir §3.2) | open redirect | V, E | #17, #34 | à faire |

### 3.2 Cas de test `returnTo` (ADR-026 + remarque Cyber sur le double encodage)

Test Vitest table-driven sur la fonction de validation (#17), complété par un cas Playwright (#34 ou #27) : après connexion avec un `returnTo` refusé, l'utilisateur doit arriver sur l'accueil de son espace.

| Entrée | Attendu | Motif |
|---|---|---|
| `/t/<tenantId>/engagements` (route connue) | accepté | chemin interne relatif valide |
| `/route-inconnue` | refusé → accueil | absent de la table des routes connues |
| `//evil.example` | refusé | protocol-relative |
| `/\evil.example` | refusé | antislash normalisé en `/` par les navigateurs |
| `/\/evil.example` | refusé | antislash |
| `https://evil.example` | refusé | schéma |
| `javascript:alert(1)` | refusé | schéma (`:` avant le premier `/`) |
| `%2F%2Fevil.example` | refusé | `//` encodé |
| `%252F%252Fevil.example` | refusé | **double encodage** : on valide la valeur décodée une seule fois, et on refuse si un second décodage la modifie (remarque Cyber, PR #38) |
| `/\tevil` , `/%09/evil`, `/\nevil`, `/%0A/evil` | refusé | caractères de contrôle, dont `\t` et `\n` tolérés par les navigateurs |
| `` (vide) ou absent | accueil de l'espace | valeur par défaut |
| route d'un autre espace (ex. lien portail vers `/t/...` cabinet) | pas de changement d'espace sans appel serveur ; l'API décide (403/404) | l'autorisation reste côté backend |

Données d'entrée fictives uniquement (`evil.example`, domaine réservé RFC 2606).

## 4. Critères de refus de PR (verdict QA)

Chaque review QA commence par `VERDICT QA: APPROUVÉ` ou `VERDICT QA: CHANGEMENTS DEMANDÉS` suivi de la liste des points. Une PR est **refusée** si :

1. La CI est rouge, ou un test connu est cassé, désactivé ou supprimé (PLAN §6.5) :
   - **test de sécurité** (autorisation, isolation, session/CSRF, upload, échappement) rouge, supprimé, désactivé (`skip`/`xfail`) ou affaibli : refus **quelle que soit la justification**. Toute modification légitime d'un tel test exige une review Cyber explicite ;
   - **autre test** : un `skip`/`xfail` n'est toléré que s'il est justifié par une issue de suivi ouverte, citée dans le code et dans la PR.
2. La PR n'indique aucune commande de test réellement exécutée avec son résultat, ou déclare un résultat sans journal. Avant l'existence de la CI (#5, #6), la sortie locale Python 3.12/Docker doit être jointe.
3. Elle introduit une **régression de sécurité** : cas négatif d'autorisation retiré ou affaibli, route métier sans contrôle par ressource, `tenant_id` lu depuis le client, schéma d'entrée acceptant des champs sensibles, CSRF contourné, en-têtes de téléchargement manquants, rendu HTML brut de contenu utilisateur.
4. Elle viole un critère bloquant de 02 §6 : fuite cross-tenant, preuve accessible sans autorisation, escalade, login cassé, démarrage impossible, injection de rendu.
5. Elle modifie silencieusement un contrat de 01 (route, code HTTP, format d'erreur, règle métier, algorithme) sans issue `architecture-question` ni réponse du commanditaire.
6. Le diff contient un secret, un token, un mot de passe ou une donnée réelle, ou ne contient pas la migration requise par un changement de schéma.
7. Une route métier nouvelle n'a pas de test d'intégration avec son cas négatif (autre tenant → 404, rôle insuffisant → 403).
8. Un critère d'acceptation de l'issue n'est ni satisfait ni reporté explicitement dans une issue de suivi.

La review QA ne remplace pas la review Cyber obligatoire sur les PR sensibles (`docs/PLAN.md` §5). Elle ne compte pas non plus comme une revue humaine indépendante.

## 5. Journal des exécutions

Format obligatoire, une ligne par exécution. On n'efface jamais une ligne : un échec reste consigné, et la ligne de la correction s'y ajoute.

| Date (Europe/Paris) | Commit (SHA court) | PR / issue | Commande exacte | Environnement | Résultat (passés/échoués/ignorés, durée) | Journal (lien run CI ou artefact) | F-IDs |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

Règles :
- **Commande exacte** reproductible (ex. `uv run pytest backend/tests -q`, `npm --prefix frontend run test -- --run`, `npx playwright test`).
- **Environnement** : `CI (Python 3.12 / postgres:16)`, `Docker Compose local` ou `local Python 3.14 (indicatif)`.
- **Journal** : URL du run GitHub Actions, chemin de l'artefact Playwright (traces, captures) ou extrait de la sortie conservé dans la PR.
- Le taux de réussite et la durée sont consignés (02 §4).

## 6. Reviews QA effectuées

| PR | Issue | Date | Verdict | Points principaux |
|---|---|---|---|---|
| #32 | #1 | 2026-11-19 | CHANGEMENTS DEMANDÉS | Priorités P1 sur des exigences obligatoires ; chemin critique sans #16 ; DoD sans lien de journal ni règle pré-CI |
| #32 | #1 | 2026-11-19 | APPROUVÉ | Corrections du commit 791386f vérifiées (P0, chemin critique via #16, DoD §6.3–6.5, #34, ADR-019/020) |
| #36 | #2 | 2026-11-19 | APPROUVÉ | `check_contrast.py` relancé : 38/38, exit 0 ; `json.tool` OK ; remarques : 415 → 400 `UNSUPPORTED_MEDIA_TYPE`, suspension à aligner avec THREAT_MODEL R6 |
| #37 | #3 | 2026-11-19 | CHANGEMENTS DEMANDÉS | 202 sur forgot-password hors codes de 01 §6 ; R6 `TENANT_SUSPENDED` absent d'ADR-013 et contradictoire avec DESIGN P8 |
| #37 | #3 | 2026-11-19 | APPROUVÉ | `a18b569` : 204 (R7), R6 aligné sur ADR-025, matrice de 44 lignes sans 202 ; reste : critères `sandbox`/`#token=` seulement en commentaires d'issues (#15, #16, #20, #26) |
| #38 | #12 | — | **Pas de review QA** | Mergée le 2026-11-19 avec une seule review Cyber (APPROUVÉ). Relecture QA a posteriori d'ADR-026 : cohérente avec THREAT_MODEL R6/R7 et ADR-025, intégrée en §3.1/§3.2 (SEC-suspended, SEC-forgot-204, SEC-returnTo) |

Résumé de l'état des PR revues : #32, #33, #36, #37 et #38 sont mergées.

## 7. Anomalies ouvertes

| Issue | Gravité | Résumé | F-ID / 02 §3 | Statut |
|---|---|---|---|---|
| — | — | — | — | — |
