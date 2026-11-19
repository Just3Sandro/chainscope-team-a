# ChainScope — Plan de livraison (équipe A)

- **Auteur :** rôle Tech Lead / PM
- **Départ officiel (48 h murales) :** 2026-11-19 15:36 Europe/Paris — échéance 2026-11-21 15:36 Europe/Paris
- **Sources normatives :** `01_SPECIFICATIONS_ET_ARCHITECTURE.md` (contrats), `02_PLAN_DE_TEST_ET_SECURITE.md` (F01–F20). Ce plan ne modifie aucun contrat ; les ambiguïtés sont remontées en issues `architecture-question` (#29, #30, #31).
- **Décisions non prescrites :** `docs/DECISIONS.md`.

## 1. Objectifs

1. Livrer le périmètre **obligatoire** de 01 §9 : auth réelle et rôles, multi-tenant, clients, missions, actifs, constats, publication client, preuves privées, graphe dirigé + chemins, UI utilisable, migrations, Docker Compose, seed fictif, tests, documentation.
2. Zéro critère bloquant de 02 §6 (fuite cross-tenant, accès preuve non autorisé, escalade, login cassé, démarrage impossible, injection de rendu).
3. Processus traçable : une issue → une branche → une PR revue (QA, + Cyber si sensible) → CI verte → merge validé.
4. Bonus (10_UX) uniquement après stabilisation du socle (fin J4).

## 2. Jalons (milestones GitHub)

| Jalon | Contenu | Issues |
|---|---|---|
| J1 Planification | Backlog, plan, décisions, design system, threat model, stratégie QA | #1, #2, #3, #4 |
| J2 Vertical slice | Scaffold, CI, DB, auth, authz, audit, tenants, clients/missions, actifs/constats, reset, invitations, front auth + cabinet, smoke Playwright | #5 – #18, #34, AQ #29, #30 |
| J3 Cœur métier | Publication + portail client, preuves, graphe + paths, front graphe/portail/admin, seed | #19 – #25, AQ #31 |
| J4 Finition | Isolation cross-tenant + durcissement prod, E2E Playwright, documentation de livraison | #26, #27, #28 |

Critère de sortie J2 : connexion réelle → création d'une mission → un constat visible côté cabinet (03_ROLES), démontré par le smoke Playwright #34.
Critère de sortie J3 : chemins calculés serveur (F08–F11), publication client (F05–F07), preuves privées (F12–F14).

## 3. Chemin critique

```
#5 scaffold ─┬─ #6 CI
             └─ #7 DB ── #8 auth ─┬─ #9 CLI admin
                                  ├─ #15 reset/mail ──────────────────────────────┐
                                  └─ #10 authz ─ #11 audit ─┬─ #12 tenants ────────┤
                                                            └─ #13 clients/missions┼─ #16 invitations ─┐
                                                                    └─ #14 assets/findings ────────────┼─ #19 publication/portail ─ #20 preuves ─┐
                                                                                                       └─ #21 graphe/paths ─────────────────────┼─ #25 seed ─ #26 isolation ─ #27 E2E ─ #28 livraison
Front : #2 design + #8 ─ #17 shell ─ #18 cabinet ─┬─ #34 smoke E2E (sortie J2, + #9, #16) ───────────────────────────────────────────────────┘ (#27)
                                                  ├─ #22 graphe (#21)
                                                  ├─ #23 portail/preuves (#19, #20)
                                                  └─ #24 dashboard/admin/audit (#11, #12, #16)
```

Chemin critique : **#5 → #7 → #8 → #10 → #11 → #13 → #16 → #19 → #20 → #25 → #26 → #27 → #28**.
- #16 (invitations) est **sur** le chemin critique : prérequis de #19 (portail client, membership client) et de #25 (seed). Ses propres prérequis **#12 (tenants) et #15 (reset/mail) sont des convergences obligatoires avant #16**, donc avant #19 : ils doivent être livrés au plus tard en même temps que #13, et non traités comme du travail « en parallèle sans échéance ».
- #14 → #21 est une branche parallèle de longueur comparable (convergence en #25).

Parallélisables (hors chemin critique) dès que leurs dépendances sont mergées : #6, #9, #17/#18 (front), #21, #22–#24.

## 4. Tableau issue → rôle → dépendances → priorité

| # | Titre court | Jalon | Rôle principal | Reviewers | Dépend de | Prio | Tests F |
|---|---|---|---|---|---|---|---|
| 1 | Plan, backlog, décisions | J1 | tech-lead | QA | — | P0 | — |
| 2 | Design system, DESIGN.md | J1 | designer | tech-lead, QA | #1 | P0 | — |
| 3 | Threat model | J1 | cyber | tech-lead, QA | #1 | P0 | mapping F01–F20 |
| 4 | Stratégie de test, QA_REPORT | J1 | qa | tech-lead | #1 | P0 | matrice F01–F20 |
| 5 | Scaffold, Compose, socle API | J2 | developer (Codex) | QA | #1 | P0 | F19, F20 (base) |
| 6 | CI GitHub Actions | J2 | developer (Codex) | QA | #5 | P0 | — |
| 7 | Modèles + migration Alembic | J2 | developer (Codex) | QA, Cyber | #5 | P0 | F11 (base) |
| 8 | Auth sessions/CSRF/Argon2id/rate limit | J2 | developer (Codex) | QA, Cyber | #7 | P0 | F01, F16 |
| 9 | CLI bootstrap admin | J2 | developer (Codex) | QA, Cyber | #8 | P0 | — |
| 10 | Autorisation par ressource | J2 | developer (Codex) | QA, Cyber | #8 | P0 | F17 |
| 11 | Audit append-only + endpoint | J2 | developer (Codex) | QA, Cyber | #7, #10 | P0 | F18 |
| 12 | API plateforme tenants | J2 | developer (Codex) | QA | #10, #11 | P0 | — |
| 13 | API clients + engagements | J2 | developer (Codex) | QA | #10, #11 | P0 | F03, F17 |
| 14 | API assets + findings | J2 | developer (Codex) | QA | #13 | P0 | F04, F07, F15 |
| 15 | Mail + reset password | J2 | developer (Codex) | QA, Cyber | #8, #11 | P0 | — |
| 16 | Invitations + acceptation | J2 | developer (Codex) | QA, Cyber | #12, #13, #15 | P0 | F02, F17 |
| 17 | Front shell + auth | J2 | developer (Codex) | QA, designer | #2, #5, #8 | P0 | F01, F02, F16 |
| 18 | Front cabinet | J2 | developer (Codex) | QA, designer | #13, #14, #17 | P0 | F15 |
| 19 | Publication + API portail client | J3 | developer (Codex) | QA, Cyber | #14, #16 | P0 | F05, F06, F07 |
| 20 | Preuves upload/download | J3 | developer (Codex) | QA, Cyber | #14, #19 | P0 | F12, F13, F14 |
| 21 | Graphe edges + paths | J3 | developer (Codex) | QA | #14 | P0 | F08–F11 |
| 22 | Front graphe React Flow | J3 | developer (Codex) | QA, designer | #18, #21 | P0 | F08, F09 |
| 23 | Front publication/preuves/portail | J3 | developer (Codex) | QA, designer, Cyber | #18, #19, #20 | P0 | F05, F06, F15 |
| 24 | Front dashboard/admin/audit | J3 | developer (Codex) | QA, designer | #11, #12, #16, #18 | P0 | — |
| 25 | Seed fictif idempotent | J3 | developer (Codex) | QA | #16, #20, #21 | P0 | F08 |
| 26 | Isolation cross-tenant + durcissement prod | J4 | cyber + developer | QA | #19, #20, #21, #25 | P0 | F05, F06, F11, F13, F15–F17, F19 |
| 27 | E2E Playwright | J4 | qa + developer | tech-lead | #22, #23, #24, #25, #34 | P0 | F01–F04, F06, F08–F10, F12, F15, F19 |
| 28 | Documentation de livraison | J4 | tech-lead + qa | designer, cyber | #26, #27 | P0 | F20 |
| 34 | Smoke Playwright login → mission → constat | J2 | qa + developer | tech-lead | #9, #16, #18 | P0 | F01, F03, F04, F16 |
| 29 | AQ invitation premier TENANT_ADMIN | J2 | tech-lead → commanditaire | — | — | P1 | — |
| 30 | AQ mission CLOSED / transitions | J2 | tech-lead → commanditaire | — | — | P1 | — |
| 31 | AQ précision CVSS / arrondi | J3 | tech-lead → commanditaire | — | — | P2 | — |

**Règle de priorité :** P0 = exigence obligatoire (01 §3, §7, §9, §10 ; 02 §2, §4) ou prérequis direct ; P1 = confort non normatif ; P2 = bonus. Toutes les issues de livraison #1–#28 et #34 sont P0 : **aucune n'est coupable**. Pour les AQ (#29–#31), le label de priorité indique l'urgence de la réponse attendue, pas une possibilité de coupe. La colonne « Tests F » reprend les IDs cités dans le corps de chaque issue.

Les issues AQ n'attendent pas de réponse pour avancer : chaque issue concernée applique l'**hypothèse de travail conservatrice** indiquée dans l'AQ. Une réponse du commanditaire qui diverge donnera lieu à une issue de correction dédiée.

## 5. Stratégie de branches, PR et review

- Branches depuis `main` à jour : `feature/<n>-slug`, `fix/<n>-slug`, `security/<n>-slug`, `test/<n>-slug` (04_GIT).
- Commits conventionnels (`feat:`, `fix:`, `test:`, `docs:`, `security:`, `chore:`), ciblés.
- **Une issue = une PR** (gabarit `.github/PULL_REQUEST_TEMPLATE.md`, `Closes #n`, commandes de tests réellement exécutées avec résultats).
- Implémentation par le rôle developer **via Codex CLI** (ADR-005) ; aucun remplacement silencieux par un autre agent.
- Review :
  - **QA systématique** sur toute PR (critères d'acceptation, tests exécutés, non-régression).
  - **Cyber obligatoire** pour toute PR labellisée `security` ou touchant auth, sessions, autorisation, invitations/reset, uploads/téléchargements, portail client, configuration prod (#7, #8, #9, #10, #11, #15, #16, #19, #20, #23, #26).
  - **Designer** sur les PR frontend (cohérence avec `docs/DESIGN.md`).
  - Le reviewer est toujours un rôle distinct de l'auteur ; review consignée dans la PR (commentaire ou review GitHub).
- Merge : uniquement après CI verte + reviews requises approuvées, décidé par le coordinateur ; merge en squash référencant l'issue. Pas de push direct sur `main`.
- Une PR rouge ou incomplète reste ouverte avec ses limites documentées ; tout écart hors périmètre est suivi dans une issue.

## 6. Definition of Done (par PR)

1. Tous les critères d'acceptation cochés ou explicitement reportés dans une issue de suivi (jamais pour une exigence obligatoire sans accord du Tech Lead consigné dans DECISIONS).
2. Tests ajoutés pour le comportement livré (dont cas négatifs d'autorisation pour toute route métier) ; IDs F concernés cités.
3. **Preuve d'exécution** : la PR contient le lien vers le run CI vert **ou** la sortie de commande conservée (bloc de log joint), et les F-IDs touchés sont consignés dans `docs/QA_REPORT.md` (commande, commit, date, résultat). Un test sans preuve est considéré comme non exécuté (02 §4).
4. **Règle de transition avant CI (#5, #6)** : tant que `ci.yml` (#6) n'est pas mergé, la PR joint la sortie **locale réellement exécutée** en environnement de référence Python 3.12 (Docker ou `uv` avec 3.12, ADR-002) : `pytest`, lint, build frontend, `docker compose config`/`up` selon le cas. #6 doit lui-même montrer un run CI vert sur sa propre PR. Dès #6 mergé, la CI verte est obligatoire.
5. **Refus des régressions de sécurité** : toute PR qui rend rouge, supprime, désactive (`skip`/`xfail`) ou affaiblit un test d'autorisation, d'isolation, de session/CSRF, d'upload ou d'échappement est **refusée**, quelle que soit la justification fonctionnelle. Une modification légitime d'un tel test exige une review Cyber explicite.
6. Migrations fournies pour tout changement de schéma ; `alembic upgrade head` rejouable.
7. Aucune donnée réelle, secret, token, chemin machine ou valeur magique non nommée dans le diff.
8. Contrats §6 respectés (chemins, codes HTTP, format d'erreur) ; aucune simplification silencieuse.
9. Documentation mise à jour si commandes, config ou architecture changent ; décisions nouvelles ajoutées à `docs/DECISIONS.md`.
10. Reviews requises (QA, + Cyber/Designer selon §5) approuvées par un rôle distinct.
11. Fichiers ≤ 300 lignes visés (500 max), fonctions ≤ 40 lignes visées (règles de code du dépôt).

## 7. Risques principaux

| Risque | Mitigation |
|---|---|
| Relais Codex CLI indisponible ou en échec | Arrêt et signalement au commanditaire (ADR-005), pas de substitution silencieuse |
| Fuite cross-tenant via une route oubliée | Couche #10 obligatoire + suite paramétrée #26 + review Cyber |
| Dérive de l'algorithme contractuel | Fonction pure testée unitairement sur tous les cas de 02 §3 (#21) |
| Ambiguïtés normatives | AQ #29–#31 avec hypothèses conservatrices ; aucune invention |
| Environnement local (Python 3.14) différent de la cible | Exécution de référence en Docker / CI Python 3.12 (ADR-002) |
| Dépassement du temps | Seuls les bonus (P2) et le confort non normatif (P1) sont coupables ; tout item obligatoire (P0) reste dû. En cas de retard : réduire le polish UI et les bonus, jamais une exigence de 01/02 ; signaler au commanditaire tout risque de non-livraison d'un P0 |
| Intégration proxy/cookies/CSRF découverte tard | Smoke Playwright #34 dès la sortie de J2 (ADR-019) |
| Persistance F19 non prouvée | E2E #27 avec `restart` **et** `down`/`up` sans `-v` (ADR-020) |
