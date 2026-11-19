# ChainScope — Design system « Relevé »

- **Auteur :** rôle UX/UI Designer (issue #2) — 2026-11-19
- **Sources normatives :** `01_SPECIFICATIONS_ET_ARCHITECTURE.md` §3, §4, §6, §7, §8 ; `10_UX_CREATIVITE.md` ; `docs/PLAN.md` ; ADR-008, ADR-012 à ADR-015, ADR-021 à ADR-025.
- **Tokens :** `docs/design-tokens.json` (bloc `tailwind` → `theme.extend`, bloc `semantic` → mapping métier).
- **Vérification contraste :** `python3 docs/tools/check_contrast.py` (bibliothèque standard, code retour 1 si une paire échoue). Résultat consigné en annexe A.
- **Portée :** ce document décrit l'interface ; il ne change aucun contrat. Les points non couverts par la spec ont été remontés au Tech Lead et tranchés par ADR-021 à ADR-024 (§12), jamais ici.

---

## 1. Identité

### Nom de code : « Relevé »

ChainScope reste le nom du produit (spec). Le design system s'appelle **Relevé**, au sens du relevé topographique : on arpente un terrain, on note ce qui existe, on trace des chemins. Un audit, c'est la même chose : constater, cartographier, puis montrer au client la carte de ce qui reste ouvert.

Ce que ça donne visuellement :

- **Papier et encre.** Fonds clairs, texte encre bleu-ardoise (`ink-900`), une couleur d'accent : **sarcelle** (`accent-600`), pour l'action et le chemin sélectionné. La couleur sert à signaler, pas à décorer.
- **Courbes de niveau.** Motif original de lignes concentriques fines (SVG inline, `ink-200`) réservé à l'écran de connexion et aux états vides. Jamais derrière une donnée.
- **Glyphe.** Trois points reliés par un trait qui se termine en crochet fermant : un chemin qui aboutit à une cible. Dessiné pour le projet (SVG inline, une seule couleur `currentColor`), sans reprise de logo existant. Les inspirations (Linear, Sentry, DefectDojo, React Flow) ne servent qu'à la densité et au triage ; aucun asset, aucune palette ni aucune icône ne vient de chez eux.

### Ton

Factuel, calme, en français, avec vouvoiement. Pas d'alarmisme (« Critique » est une sévérité, pas un cri), pas de jargon gratuit. Les boutons disent ce qu'ils font : « Publier au client », « Retirer la publication », « Supprimer la relation ». Les messages d'erreur disent ce qui s'est passé et quoi faire ensuite.

## 2. Principes

1. **Vérité serveur.** L'écran montre ce que l'API renvoie, rien de plus. Chemins, scores, visibilité client et permissions viennent du backend. Le front ne calcule pas, ne déduit pas, n'anticipe pas (10_UX).
2. **Jamais la couleur seule.** Sévérité, statut, publication et état d'edge combinent toujours libellé texte, forme ou icône, et couleur.
3. **Densité lisible.** Tables compactes (ligne 40 px desktop, 48 px tablette), filtres toujours visibles, détails dans un panneau latéral plutôt que dans une nouvelle page quand c'est possible.
4. **Actions sensibles explicites.** Publication, retrait et suppression passent par une confirmation qui dit précisément ce qui va changer et pour qui.
5. **Clavier d'abord.** Tout ce qui se fait à la souris se fait au clavier, y compris dans le graphe (§8.5).
6. **Trois espaces étanches.** Cabinet, portail client et plateforme ont chacun leur coquille, leur navigation et leurs routes d'API. Aucun composant ne mélange deux espaces.

## 3. Architecture de navigation

### 3.1 Espaces et coquilles

| Espace | Rôles | Coquille | Routes API consommées |
|---|---|---|---|
| **Public** | non connecté | Carte centrée sur fond « courbes de niveau » | `/auth/*` |
| **Cabinet** | `TENANT_ADMIN`, `PENTESTER` | Barre latérale `ink-900`, en-tête blanc, bandeau nom du cabinet | `/tenants/{id}/*`, `/engagements/{id}/*` |
| **Portail client** | `CLIENT_VIEWER` | Pas de barre latérale ; en-tête `accent-800` avec la mention « Portail client » | `/client/*` uniquement |
| **Plateforme** | `PLATFORM_ADMIN` | Barre latérale `ink-700` et mention « Administration plateforme » | `/platform/*` uniquement |

Les trois coquilles ont des couleurs d'en-tête différentes : on sait toujours dans quel espace on se trouve.

### 3.2 Routage front (React Router)

```
/login  /forgot-password  /reset-password  /accept-invitation        (public)
/spaces                                                              (sélecteur, si plusieurs espaces)
/t/:tenantId/dashboard
/t/:tenantId/clients                 /t/:tenantId/clients/:clientId
/t/:tenantId/engagements             /t/:tenantId/engagements/:engagementId[/assets|/findings|/graph]
/t/:tenantId/engagements/:engagementId/findings/:findingId
/t/:tenantId/members                 (TENANT_ADMIN)
/t/:tenantId/audit                   (TENANT_ADMIN)
/portal                              /portal/engagements/:engagementId
/portal/engagements/:engagementId/findings/:findingId
/platform/tenants
```

- Le `tenantId` dans l'URL sert seulement au contexte de navigation. L'autorisation reste côté serveur. Un `tenantId` falsifié produit l'état 404 ou 403 renvoyé par l'API (§7).
- Les gardes de route par rôle servent à l'affichage : elles évitent de montrer un lien inutile, elles ne protègent rien (ADR-014). Une route gardée n'est pas pré-chargée (pas de `prefetch` de données d'un espace non autorisé).
- Après connexion : un seul espace, redirection directe ; plusieurs espaces, `/spaces` (cartes « Cabinet X », « Portail client Y », « Administration plateforme »). Le paramètre `returnTo` n'accepte qu'un chemin relatif interne commençant par un seul `/` : rejet de `//`, `/\`, de tout antislash et de tout schéma (anti open redirect, test Vitest dans #17).
- Les espaces proposés viennent exclusivement de `GET /auth/me` (ADR-021 : `is_platform_admin`, `tenant_memberships`, `client_memberships`). Après un rechargement de page (F19), la coquille rappelle `GET /auth/me` ; aucun état d'autorisation n'est persisté côté navigateur. Un tenant suspendu n'apparaît plus dans `me`.

### 3.3 Navigation cabinet (barre latérale)

`Tableau de bord` · `Missions` · `Clients` · `Équipe` (admin) · `Journal d'audit` (admin). En bas : sélecteur d'espace, menu utilisateur (e-mail, « Se déconnecter »).
Dans une mission, des onglets secondaires : `Vue d'ensemble` · `Actifs` · `Constats` · `Graphe`. Le fil d'Ariane suit la forme `Missions / Audit Web 2026 / Constats / F1`.

## 4. Parcours obligatoires page par page (§3 et §7)

Légende des wireframes : `[Bouton]`, `(badge)`, `▤` table, `▦` panneau, `…` contenu.

### P1 — Authentification (§7.1, flux §3.3 et §3.4)

```
┌──────────── courbes de niveau ────────────┐
│        ◦—◦—◦]  ChainScope                  │
│   E-mail     [______________]              │
│   Mot de passe [____________] [Afficher]   │
│   [Se connecter]                           │
│   Mot de passe oublié ?                    │
└────────────────────────────────────────────┘
```
- **Connexion :** 401 donne « E-mail ou mot de passe incorrect », sans préciser lequel. 429 donne « Trop de tentatives. Réessayez dans quelques minutes. » Le bouton est désactivé pendant l'envoi et affiche un spinner avec le texte « Connexion… ».
- **Mot de passe oublié :** on affiche toujours le même message après envoi : « Si un compte existe pour cette adresse, un e-mail a été envoyé. » Aucune différence visible entre compte existant et inexistant (§8).
- **Réinitialisation et acceptation d'invitation :** le jeton est lu dans le **fragment** d'URL (`#token=…`, ADR-025, avec `Referrer-Policy: no-referrer`) puis retiré de l'historique (`replace`). Le formulaire contient le nouveau mot de passe, sa confirmation et les règles affichées sous le champ. Si le jeton est expiré ou déjà utilisé, une page d'erreur dédiée l'explique (« Ce lien n'est plus valide. Demandez-en un nouveau. »), sans formulaire.
- **Déconnexion :** depuis le menu utilisateur. Le cache TanStack Query est vidé, l'utilisateur arrive sur `/login` avec un toast « Vous êtes déconnecté ».

### P2 — Tableau de bord cabinet (§7.2)

```
┌ Missions en cours (n) ─────────┬ Constats par gravité ─────────┐
│ ▤ nom · client · statut · MAJ  │ ▮▮▮▮ Critique 3                │
│                                │ ▮▮▮  Élevée   5   (barres +    │
│ [Voir toutes les missions]     │ ▮▮   Moyenne  8    libellé +   │
│                                │ ▮    Faible   2    nombre)     │
├ Activité récente ──────────────┴───────────────────────────────┤
│ ▤ horodatage · acteur · action · ressource                     │
└ Filtres : client ▾  statut mission ▾  gravité ▾ ───────────────┘
```
- Compteurs (ADR-022) : un seul appel `GET /tenants/{id}/engagements?status=IN_PROGRESS&limit=100`. Le front **additionne** les champs calculés serveur `findings_count_by_severity` et `findings_count_by_status` des missions renvoyées, sans autre logique. Pas d'endpoint d'agrégat, pas de requête par mission. Les filtres client et gravité restreignent ces mêmes missions et compteurs (filtres serveur ADR-023 quand ils existent).
- « Activité récente » est présente pour les deux rôles cabinet (01 §7.2), avec une source différente :
  - `TENANT_ADMIN` : flux `GET /tenants/{id}/audit-events` (horodatage, acteur, action, ressource) ;
  - `PENTESTER` : constats récemment modifiés des missions en cours, via `GET /engagements/{id}/findings?sort=-updated_at&limit=…` (constante nommée). Le pentester n'appelle jamais `audit-events`.

  Le titre de section reste « Activité récente » ; le sous-titre précise la source (« Journal du cabinet » ou « Constats récemment modifiés »).
- Le graphique « constats par gravité » est une liste de barres horizontales, avec le nombre en texte. On peut le lire sans la couleur.

### P3 — Clients (§7.3, flux §3.3 et §3.5)
- **Liste :** table filtrable (nom), pagination serveur, bouton `[Nouveau client]` visible si l'API l'autorise pour le rôle (affichage). Un 403 éventuel reste géré.
- **Création :** dialog avec un champ `Nom`. En cas de succès, toast et ouverture du détail.
- **Détail :** nom (modifiable via PATCH), missions du client, onglet `Invitations` (liste des invitations renvoyées par l'API, filtre `state` = en attente, utilisée ou expirée selon ADR-023 ; formulaire e-mail ; `[Inviter]`).

### P4 — Missions (§7.4, flux §3.5)
- **Liste :** filtres client, statut, recherche par nom ; colonnes nom, client, statut (badge), constats par gravité (mini-jauge + nombres, depuis `findings_count_by_severity`, ADR-022), constats non résolus (`findings_count_by_status.OPEN` + `IN_PROGRESS`, simple somme d'affichage), dernière mise à jour. Tri par défaut serveur `-updated_at` (ADR-023).
- **Création :** dialog avec nom, client (select alimenté par l'API), périmètre (`scope`, textarea en texte brut), statut initial `DRAFT`.
- **Vue d'ensemble :** périmètre, statut avec sélecteur des transitions autorisées par l'API, compteurs.
- **Mission `CLOSED` :** bandeau `warning` en haut de la mission, « Mission clôturée : les modifications techniques sont désactivées. » Les boutons de mutation sont masqués. Si un 409 `ENGAGEMENT_CLOSED` arrive malgré tout, il est affiché tel quel (vérité serveur). Seul `TENANT_ADMIN` voit `[Rouvrir]` (hypothèse AQ #30).
- **Actifs :** table avec nom, type, criticité (pastilles 1–5 + chiffre), entrée et cible critique (icônes + texte). Création et édition dans un panneau latéral. La suppression passe par une confirmation. Un 409 `ASSET_IN_USE` donne « Cet actif est utilisé par n relation(s) du graphe. Supprimez-les d'abord. »
- **Constats :** table avec titre, sévérité, CVSS (mono, une décimale), statut, publication, auteur et date. Filtres sévérité, statut et publication, synchronisés dans l'URL.

### P5 — Détail d'un constat (§7.5, flux §3.5 et §3.8)

```
┌ F1 — Injection SQL sur /search ─── (▮▮▮▮ Critique) (○ Ouvert) (◌ Interne) ┐
│ CVSS 8.8   Auteur · créé le · modifié le                                   │
├ Description │ Impact │ Recommandation   (texte brut, retours ligne conservés)│
├ Statut  [Ouvert ▾]                    Publication  [Publier au client]       │
├ Preuves ▤ nom · type · taille · SHA-256 (tronqué + copier) · [Visible client]│
│         [Ajouter une preuve]  PDF, PNG, JPEG, TXT — 10 Mio max               │
└ Relations du graphe utilisant ce constat (liste) ───────────────────────────┘
```
- Tout contenu utilisateur est rendu en texte, sans HTML ni Markdown (ADR-014, F15).
- Le changement de statut vers `REMEDIATED` affiche une note : « Les relations de graphe appuyées sur ce constat seront neutralisées. » Après succès, les requêtes `paths` et `edges` sont invalidées.
- Le bouton `Visible client` est un interrupteur étiqueté. Quand le constat n'est pas publié, une aide l'indique : « Visible côté client uniquement après publication du constat. »
- Upload : la vérification de taille et de type côté client sert uniquement le confort. Le serveur décide, et ses réponses 413 `PAYLOAD_TOO_LARGE` et 400 `UNSUPPORTED_MEDIA_TYPE` sont affichées (§7). Une barre de progression apparaît pendant l'envoi.
- Téléchargement : lien vers la route autorisée. Pas d'aperçu inline dans le socle.

### P6 — Graphe interactif (§7.6, flux §3.6 et §3.7)

```
┌ Mission › Graphe ────────────────────────────────────────────────────────┐
│ ┌ Canvas React Flow ──────────────────────────┐ ┌ ▦ Chemins actifs (n) ─┐ │
│ │  [→ Web]━━F1━━▶[API]━━F2━━▶[◆ DB]          │ │ ▸ 75.0 · 2 sauts      │ │
│ │                  ┆                          │ │   Web → API → DB      │ │
│ │               ┄┄F3┄┄▷[Poste]  (neutralisé)  │ │ ▸ …                   │ │
│ │ [+][−][Ajuster] [Liste]                     │ ├ ▦ Relations ──────────┤ │
│ └─────────────────────────────────────────────┘ │ ▤ source→cible·constat│ │
│                                                  │ [Nouvelle relation]   │ │
└──────────────────────────────────────────────────┴───────────────────────┘
```
Les conventions détaillées sont au §8. Le panneau droit est l'équivalent textuel complet du canvas.

### P7 — Portail client (§7.7, flux §3.8)
- `/portal` : cartes des missions renvoyées par `GET /client/engagements` (nom, statut, `published_findings_count` d'ADR-022 : constats publiés uniquement ; si le champ est absent, rien n'est affiché à sa place).
- Mission : table des constats publiés (sévérité, titre, statut, date de publication), avec filtres sévérité et statut.
- Constat : lecture seule. Aucun bouton de mutation, aucun champ éditable, aucun emplacement réservé à des notes internes. Preuves listées uniquement si l'API les renvoie, avec un téléchargement via `/client/evidences/{id}/download`.
- Ton plus pédagogique : courte légende « Que signifie cette sévérité ? » sous le badge (texte statique, sans donnée).

### P8 — Administration plateforme (§7.8, flux §3.1 et §3.2)
- Table des tenants : nom, slug, état (badge `Actif` ou `Suspendu`). `[Nouveau tenant]` ouvre un dialog avec nom et slug, et une validation du format du slug affichée.
- Suspension et réactivation passent par une confirmation qui explique la conséquence : « Les membres de ce cabinet n'auront plus accès à ses données. Leurs autres accès éventuels ne changent pas. » (ADR-025 : 403 `TENANT_SUSPENDED` sur les routes du tenant, missions retirées du portail client).
- Invitation du premier `TENANT_ADMIN` : selon la réponse à l'AQ #29, sans parcours inventé avant.
- Aucun lien vers missions, constats ou preuves. Le bootstrap admin (§3.1) se fait par CLI, sans écran.

### P9 — Journal d'audit (§7.9)
- Table paginée : horodatage (local, UTC en infobulle), acteur, action, type de ressource, identifiant (mono, tronqué + copier), `request_id`. Filtres action et type si l'API les supporte.
- Les métadonnées s'affichent telles que renvoyées, en texte. L'écran n'enrichit rien.

### Équipe (gestion des membres, §6 `members`)
- Table des membres renvoyés par l'API (e-mail, rôle) et formulaire d'invitation (e-mail, rôle `PENTESTER` ou `TENANT_ADMIN` selon ce que l'API accepte).

## 5. Design tokens

La source unique est `docs/design-tokens.json`. Intégration prévue :

```ts
// frontend/tailwind.config.ts (à réaliser par le rôle developer)
import tokens from '../docs/design-tokens.json';
export default { content: ['./index.html', './src/**/*.{ts,tsx}'], theme: { extend: tokens.tailwind } };
```
Si le build Docker du frontend n'a pas accès à `docs/`, le developer copie le fichier dans `frontend/src/design/` et le test de contraste pointe vers cette copie : `check_contrast.py <chemin>`.

### 5.1 Couleurs

| Rôle | Token | Hex | Usage |
|---|---|---|---|
| Texte principal | `ink-900` | `#14202B` | corps, titres |
| Texte secondaire | `ink-700` | `#34485A` | libellés, edges actifs |
| Texte atténué | `ink-500` | `#56687A` | métadonnées, aides |
| Bordure de champ | `ink-400` | `#7D8C9A` | inputs, edges neutralisés |
| Séparateurs | `ink-200` / `ink-300` | `#D6DEE5` / `#B7C3CE` | décoratif uniquement |
| Fond application | `ink-50` | `#F5F7F9` | arrière-plan |
| Surface | `paper` | `#FFFFFF` | cartes, tables, dialogs |
| Canvas graphe | `canvas` | `#F1F4F6` | fond React Flow |
| Accent | `accent-600` / `700` / `800` | `#0E7069` / `#0B5F59` / `#084A45` | action primaire, chemin sélectionné, nav active |
| Focus | `focus` | `#2349C8` | anneau de focus uniquement |
| Danger / Succès / Avertissement / Info | `*-700` sur `*-50` | voir JSON | alertes, toasts |

### 5.2 Sévérités (badge rectangulaire, coins `rounded-sm`)

| Valeur | Libellé | Glyphe (barres) | Badge fg / bg | Couleur pleine (graphe, barres) |
|---|---|---|---|---|
| `LOW` | Faible | ▮▯▯▯ | `#2F5A7A` / `#E3EEF6` | `#4A7FA8` |
| `MEDIUM` | Moyenne | ▮▮▯▯ | `#7A4D00` / `#FFF1D6` | `#B7791F` |
| `HIGH` | Élevée | ▮▮▮▯ | `#9A3412` / `#FDE7DA` | `#D9622B` |
| `CRITICAL` | Critique | ▮▮▮▮ | `#FFFFFF` / `#A3172E` (plein, inversé) | `#A3172E` |

Le glyphe « jauge à 4 barres » encode l'ordre sans couleur. Le badge `CRITICAL` est le seul plein, ce qui le distingue aussi en niveaux de gris. Le libellé est toujours affiché, et `aria-label="Sévérité : Critique"`.

### 5.3 Statuts

Les statuts de constat utilisent une **pastille arrondie (`rounded-full`) à contour**, pour qu'on ne les confonde pas avec les sévérités rectangulaires.

| Valeur | Libellé | Icône | Couleur | Effet sur les chemins (affiché, pas calculé) |
|---|---|---|---|---|
| `OPEN` | Ouvert | cercle vide | `ink-900`, contour `ink-500` | actif |
| `IN_PROGRESS` | En cours | demi-cercle | `#1F5AA6` | actif |
| `REMEDIATED` | Corrigé | coche | `#146C2E` | neutralise les relations |
| `ACCEPTED_RISK` | Risque accepté | drapeau | `#6B3FA0` | reste actif (acceptation ≠ correction) |

Missions : `DRAFT` Brouillon (contour pointillé, crayon) · `IN_PROGRESS` En cours (accent, lecture) · `CLOSED` Clôturée (cadenas).
Publication : `Publié au client` (œil, succès) · `Interne` (œil barré, neutre). Le fond seul ne porte jamais l'information.

### 5.4 Typographie

Polices système (`font-sans`) et monospace système (`font-mono`, pour CVSS, UUID, SHA-256 et `request_id`). Aucune police distante n'est chargée (CSP `default-src 'self'`, ADR-009).

| Token | Taille / interligne | Usage |
|---|---|---|
| `text-xs` | 12/16 | métadonnées, badges |
| `text-sm` | 14/20 | tables, formulaires (taille par défaut de l'app) |
| `text-base` | 16/24 | texte long (description, impact) |
| `text-lg` | 18/28 | titres de section |
| `text-xl` | 22/30 | titre de page |
| `text-2xl` | 28/36 | écran de connexion, titre de constat |

Graisses : 400, 500 (libellés, badges), 600 (titres). Les chiffres des tables utilisent `tabular-nums`.

### 5.5 Espacement, rayons, ombres, couches

- **Espacement :** échelle Tailwind par défaut (pas de 4 px). Usage conseillé : `1` (4), `2` (8), `3` (12), `4` (16), `6` (24), `8` (32). Gouttière de page `6` desktop, `4` tablette. Tokens de mise en page : `w-sidebar` 240 px, `w-sidebar-collapsed` 64 px, `h-topbar` 56 px, `w-drawer` 416 px.
- **Rayons :** `sm` 4 (badges sévérité, inputs), `DEFAULT` 6 (boutons), `md` 8 (cartes, nœuds du graphe), `lg` 12 (dialogs), `full` (statuts, pastilles).
- **Ombres :** `shadow-card`, `shadow-popover`, `shadow-dialog`. Sobres, teintées encre.
- **Couches :** `z-sticky` 20 < `z-drawer` 30 < `z-dialog` 40 < `z-toast` 50.
- **Mouvement :** `duration-fast` 120 ms, `duration-base` 200 ms. Avec `prefers-reduced-motion: reduce`, les transitions et les animations de recentrage du graphe sont coupées.

## 6. Composants

| Composant | Comportement clé | Accessibilité |
|---|---|---|
| **AppShell** (×3) | coquille par espace (§3.1) | lien d'évitement « Aller au contenu », `<nav aria-label>`, `<main>` |
| **PageHeader** | fil d'Ariane, titre, actions principales à droite | `<h1>` unique par page |
| **DataTable** | tri, filtres, pagination **serveur** (`limit`/`offset`, ADR-012), filtres reflétés dans l'URL, ligne cliquable + lien explicite sur le titre, colonnes prioritaires sur tablette | `<table>` natif, `<th scope>`, `aria-sort`, résumé « 1–20 sur 57 » en `aria-live=polite` |
| **FilterBar** | selects et recherche (debounce, constante nommée), bouton « Réinitialiser » | chaque contrôle a un `<label>` |
| **SeverityBadge / StatusBadge / PublicationBadge / EngagementStatusBadge** | §5.2–5.3 | texte visible, icône `aria-hidden` |
| **CriticalityPips** | 5 pastilles + chiffre | `aria-label="Criticité 4 sur 5"` |
| **Button** | `primary` (accent), `secondary` (contour), `danger`, `ghost` ; état `loading` désactive et garde la largeur | cible ≥ 40 px desktop, ≥ 44 px tablette |
| **FormField** | label au-dessus, aide, erreur inline (message serveur 400/422 mappé au champ si possible) | `aria-describedby`, `aria-invalid`, `required` |
| **ConfirmDialog** | voir §6.1 | `role="alertdialog"`, focus piégé, `Échap` = annuler, focus rendu au déclencheur |
| **Drawer** | création et édition latérales | `role="dialog"`, `aria-modal` |
| **Toast** | voir §6.2 | région `aria-live` |
| **FileUpload** | zone de dépôt + bouton « Choisir un fichier », types et limite affichés, progression | le bouton est l'interaction principale, le glisser-déposer est un plus |
| **CopyField** | identifiant tronqué + bouton copier (SHA-256, UUID, request_id) | `aria-label="Copier l'identifiant"`, toast « Copié » |
| **States** | `Skeleton`, `EmptyState`, `ErrorState`, `ForbiddenState`, `NotFoundState`, `ClosedBanner` | §7 |

### 6.1 Dialogs de confirmation

- **Publication :** titre « Publier ce constat au client ? ». Le corps nomme le client et le constat (titre et sévérité) et rappelle que « le client pourra lire le titre, la description, l'impact, la recommandation, la sévérité, le CVSS et le statut ». Il indique aussi le nombre de preuves marquées visibles. Boutons `[Annuler]` (focus initial) et `[Publier au client]` (primaire).
- **Retrait de publication :** « Le constat ne sera plus visible dans le portail client. L'action est journalisée. » `[Retirer la publication]`.
- **Suppression** (actif, relation) : nomme l'objet (« Supprimer la relation Web → API (F1) ? »), dit que l'action est définitive et en donne les conséquences connues. `[Supprimer]` en `danger`. Le focus initial va sur `[Annuler]` et `Entrée` ne déclenche jamais la suppression par défaut.
- **Suspension de tenant :** même gabarit que la suppression.
- Pendant la requête, les deux boutons sont désactivés. Une erreur s'affiche dans le dialog, qui reste ouvert.

### 6.2 Toasts non intrusifs

- En bas à droite, 3 au plus empilés, au-dessus du contenu sans rien masquer d'essentiel.
- Succès et info disparaissent après 5 s (constante nommée). La minuterie se met en pause au survol ou au focus. Les erreurs restent jusqu'à leur fermeture et affichent `request_id` (copiable).
- `aria-live="polite"` (succès) et `role="alert"` (erreur). Un toast ne vole jamais le focus.
- Les toasts ne contiennent aucune donnée confidentielle au-delà de ce que l'écran affiche déjà (pas de contenu de constat ni de nom de fichier de preuve dans un toast de portail).

## 7. États : chargement, vide, erreur, permissions

| Situation | Rendu |
|---|---|
| Chargement initial | squelettes aux dimensions du contenu final (pas de saut de mise en page) ; `aria-busy="true"` sur la région |
| Rechargement en arrière-plan | données conservées, petit indicateur dans l'en-tête de la table |
| Vide (aucune donnée) | illustration « courbes de niveau » + phrase + action adaptée au rôle (« Aucune mission. [Nouvelle mission] » pour un admin ; sans bouton pour un rôle qui ne peut pas créer) |
| Vide (filtres) | « Aucun résultat pour ces filtres. [Réinitialiser les filtres] » |
| 400 / 422 | erreurs mappées sur les champs, résumé en tête de formulaire avec liens vers les champs |
| 401 | session expirée : redirection vers `/login?returnTo=…` et message « Votre session a expiré » ; le cache est vidé |
| 403 | `ForbiddenState` : « Vous n'avez pas l'autorisation d'effectuer cette action. » Pour une page entière, lien vers l'accueil de l'espace |
| 403 `TENANT_SUSPENDED` | page dédiée : « Ce cabinet est suspendu. Ses données ne sont plus accessibles. » + lien vers `/spaces` si d'autres espaces existent ; les données de ce tenant sont retirées du cache |
| 404 | `NotFoundState` : « Cette ressource n'existe pas ou n'est pas accessible. » Formulation identique pour une ressource inexistante ou hors périmètre (ADR-008) |
| 409 `ENGAGEMENT_CLOSED` | `ClosedBanner` + message serveur |
| 409 `LIMIT_REACHED` | « Limite atteinte pour cette mission (actifs ou relations). » |
| 409 autre / `ASSET_IN_USE` | message métier explicite (§4 P4) |
| 413 `PAYLOAD_TOO_LARGE` / 400 `UNSUPPORTED_MEDIA_TYPE` | « Fichier trop volumineux (10 Mio max). » / « Type de fichier non autorisé (PDF, PNG, JPEG, TXT). » Le mapping se fait par `error.code`, jamais par le seul statut HTTP. |
| 429 | « Trop de requêtes. Réessayez dans quelques instants. » |
| 5xx / réseau | `ErrorState` : « Une erreur est survenue. » + `[Réessayer]` + `request_id` copiable ; jamais de trace technique |

Mapping : `error.code` (ADR-013) est traduit par une table front. Si le code est inconnu, on affiche `error.message` en texte brut.

## 8. Conventions du graphe (React Flow)

### 8.1 Nœuds (actifs)
- Carte `paper`, `rounded-md`, bordure `ink-300`, 180 × 64 px. Contenu : icône de type (WEB, SERVER, DATABASE, WORKSTATION, OTHER), nom tronqué (complet en infobulle et `aria-label`), `CriticalityPips`.
- **Point d'entrée :** bordure gauche épaisse 4 px `graph.entry` + icône « flèche entrant dans un cadre » + micro-libellé « Entrée ».
- **Joyau (crown jewel) :** double bordure `graph.crown` + icône losange + micro-libellé « Cible critique ».
- Un nœud peut cumuler les deux marquages.

### 8.2 Relations (edges)
- **Active** (constat `OPEN`, `IN_PROGRESS`, `ACCEPTED_RISK`) : trait plein 2 px `ink-700`, flèche pleine. L'étiquette porte le titre court du constat et le glyphe de sévérité. Pour `ACCEPTED_RISK`, un petit drapeau s'ajoute à l'étiquette.
- **Neutralisée** (constat `REMEDIATED`) : tirets `6 4`, 1,5 px `ink-400`, flèche creuse, étiquette barrée + « neutralisée ». Elle reste visible (on montre que la correction a coupé le chemin), sans être supprimée.
- L'état actif ou neutralisé est le booléen **`is_active` calculé serveur** de chaque edge (ADR-024). L'étiquette utilise l'objet `finding {id, title, severity, cvss, status}` embarqué dans l'edge. Pas de jointure avec la liste des findings, et la règle d'activité n'est jamais dupliquée côté client.

### 8.3 Chemins
- La liste « Chemins actifs » est **exactement** la réponse de `GET /graph/paths`, dans son ordre, avec le score affiché tel quel (une décimale). Elle n'est ni triée, ni filtrée, ni complétée côté client.
- Sélectionner un chemin (clic ou `Entrée` dans la liste) met en avant ses `edge_ids` et `asset_ids` : trait 4 px `accent-600` + halo `accent-100` 10 px. Le reste du graphe passe à 35 % d'opacité. Un `Échap` ou un second clic désélectionne.
- Une liste vide donne : « Aucun chemin actif renvoyé par le serveur. » Les aides contextuelles s'appuient uniquement sur la liste des actifs (« Aucun actif marqué comme point d'entrée », « Aucun actif marqué comme cible critique »).
- Après toute mutation (relation, statut de constat, actif), les requêtes `edges` et `paths` sont invalidées et rechargées. Pendant le rechargement, la liste reste affichée avec la mention « Recalcul… », et la sélection est conservée si le chemin existe encore (comparaison des `edge_ids`).

### 8.4 Édition
- **Création de relation :** formulaire dans le panneau (Source, Cible, Constat, chacun un select avec label). C'est le parcours principal, accessible au clavier. Le tracé par glisser entre poignées ouvre le même formulaire pré-rempli. Les erreurs 400 `INVALID_REFERENCE` et 409 s'affichent dans le formulaire.
- **Suppression :** depuis la ligne de la table « Relations » ou l'edge sélectionné, avec confirmation (§6.1).
- **Repositionnement :** au relâchement du glisser, `PATCH asset {x,y}` avec debounce (constante nommée). En cas d'échec, le nœud revient à sa position et un toast d'erreur apparaît. Au clavier : nœud focalisé, `Maj+flèches` déplace d'un pas de grille (constante nommée), avec la même persistance.
- En mission `CLOSED`, les poignées, le glisser et les formulaires sont désactivés. Une mention « lecture seule » s'affiche sur le canvas.

### 8.5 Accessibilité du graphe
- Canvas en `role="group"` avec `aria-label="Graphe d'attaque de la mission <nom>"` et `aria-describedby` vers une aide clavier.
- Nœuds focalisables (`Tab`). `aria-label` complet, par exemple « Actif DB, base de données, criticité 5 sur 5, cible critique ».
- Edges : `aria-label`, par exemple « Relation Web vers API via F1, sévérité Élevée, active ».
- Le **panneau textuel est l'équivalent complet** : tables « Chemins actifs » et « Relations » natives, navigables au clavier. Le bouton `[Liste]` masque le canvas pour ne garder que ces tables (utile aussi sur petits écrans).
- Contrôles de zoom : boutons labellisés. Pas d'animation si `prefers-reduced-motion`.

## 9. Responsive (desktop et tablette)

| Largeur | Mise en page |
|---|---|
| ≥ 1280 (`xl`) | barre latérale 240 px, tables complètes, graphe + panneau 416 px côte à côte |
| 1024–1279 (`lg`) | idem, panneau graphe 360 px |
| 768–1023 (`md`, tablette) | barre latérale en rail 64 px (icônes + `aria-label`, libellé en infobulle, bouton pour la déplier en surcouche), tables limitées aux colonnes prioritaires (titre, sévérité, statut, publication) avec le reste dans le détail, panneau graphe en tiroir basculant `[Chemins]`, cibles tactiles ≥ 44 px, glisser des nœuds au toucher |
| < 768 | hors cible de la spec, mais rien ne casse : une colonne, graphe en mode `[Liste]` par défaut |

## 10. Accessibilité (socle)

- Contraste AA vérifié numériquement (annexe A) : texte ≥ 4,5:1, composants non textuels et graphes ≥ 3:1.
- Focus visible partout : `outline: 2px solid focus; outline-offset: 2px` (Tailwind `focus-visible:outline-focus`). Il n'est jamais supprimé.
- Ordre de tabulation égal à l'ordre visuel. Lien d'évitement. Un `<h1>` par page. `document.title` suit la forme « Page · ChainScope ».
- Tous les champs ont un `<label>` visible. Les placeholders ne remplacent pas les labels.
- Dialogs : focus piégé et restitué au déclencheur. `Échap` ferme (= annuler).
- Langue `lang="fr"`. Dates au format local avec date ISO en `title`.
- Raccourcis : `/` met le focus sur la recherche de la table courante (désactivé dans les champs). Pas d'autre raccourci global dans le socle.

## 11. Règles de non-fuite (front)

1. Le front n'affiche que ce que l'API renvoie pour l'utilisateur courant. Aucun champ n'est masqué en CSS « parce que le rôle ne doit pas le voir » : s'il ne doit pas être vu, il ne doit pas être demandé.
2. Le portail client consomme **uniquement** `/client/*`. Ses composants sont distincts et n'importent aucun hook de requête cabinet (règle de lint d'import possible, à proposer par le developer).
3. Pas de pré-chargement ni de `prefetch` pour un espace ou une page que le rôle ne peut pas ouvrir.
4. À la déconnexion, au 401 et au changement d'espace ou d'utilisateur, `queryClient.clear()` est appelé (ADR-014). Rien de métier ne va dans `localStorage` ou `sessionStorage`, à part des préférences d'interface non sensibles (ex. rail replié).
5. Les messages d'erreur affichés sont le code mappé ou `error.message` serveur, plus `request_id`. Jamais de corps brut ni de trace.
6. Le rendu des contenus utilisateur se fait en texte (`{value}` React), sans `dangerouslySetInnerHTML` ni Markdown (F15).
7. Les jetons d'invitation et de réinitialisation (fragment `#token=`, ADR-025) sont retirés de l'URL après lecture. Ils n'apparaissent ni dans `document.title`, ni dans les toasts, ni dans les logs console.
8. Le 404 ne distingue pas « inexistant » de « hors périmètre ». Les vérifications de rôle côté front ne se substituent jamais au 403 serveur.

## 12. Questions de conception résolues (ADR du Tech Lead)

Les quatre questions ouvertes de la première version ont été tranchées par le Tech Lead dans `docs/DECISIONS.md`. Aucune ne modifie un contrat de 01 §6 : ce sont des champs de réponse ou des filtres ajoutés.

| Question | ADR | Effet sur ce document |
|---|---|---|
| Q1 — contenu de `GET /auth/me` | **ADR-021** | §3.2 : espaces dérivés de `is_platform_admin`, `tenant_memberships`, `client_memberships` ; tenants suspendus exclus |
| Q2 — agrégats du tableau de bord | **ADR-022** | P2 : somme front de `findings_count_by_severity` / `_by_status` ; activité récente admin (audit) et pentester (constats `-updated_at`) ; P4 et P7 : compteurs par mission et `published_findings_count` |
| Q3 — filtres serveur des listes | **ADR-023** | FilterBar et DataTable n'exposent que les filtres de la table ADR-023 (dont `published` sur les constats, `state` sur les invitations) ; une valeur hors enum donne 422, affiché comme erreur de filtre |
| Q4 — statut du constat dans `graph/edges` | **ADR-024** | §8.2 : affichage de `is_active` et de `finding` embarqué, sans jointure |

Les précisions 403/404 et le tenant suspendu (ADR-025) sont reportés en §7 et P8.

## 13. Bonus UX — après stabilisation du socle (fin J4 au plus tôt)

Ces deux propositions n'ajoutent aucun endpoint et ne déplacent aucun calcul vers le client.

### B1 — Vue « avant / après remédiation »
Quand un constat passe à `REMEDIATED` depuis son détail ou depuis le graphe, le front garde en mémoire la réponse `paths` **précédente** (déjà reçue du serveur) et la compare à la **nouvelle** réponse serveur, par identité des `edge_ids`. Un bandeau dit « 2 chemins neutralisés par cette correction ». Le graphe peut basculer entre « Avant » et « Maintenant » : les chemins disparus apparaissent en fantôme pointillé.
*Justification :* rend visible l'effet concret d'une correction (le message clé de ChainScope) et aide à prioriser. *Garde-fous :* on compare deux réponses du serveur, sans rien calculer. La comparaison est perdue au rechargement de la page (pas de stockage). Elle n'existe que côté cabinet.

### B2 — Raccourci constat → graphe, chemins regroupés par cible
Sur le détail d'un constat, `[Voir dans le graphe]` ouvre le graphe et met en avant les relations dont `finding_id` correspond à ce constat, ainsi que les chemins renvoyés par le serveur qui contiennent ces relations (filtrage d'une réponse serveur). Dans le panneau, une bascule « Grouper par cible » regroupe la liste `paths` par `target_asset_id`, en gardant l'ordre serveur dans chaque groupe.
*Justification :* répond à « que débloque ce constat ? » et « qu'est-ce qui menace la base de données ? » sans rien inventer. *Garde-fous :* aucun re-tri par score, aucune déduction de chemin.

Le mode sombre est hors périmètre (tokens clairs uniquement). On le reconsidérera après les bonus, avec ses propres vérifications de contraste.

## 14. Revue designer des PR frontend

Liste vérifiée par le designer sur #17, #18, #22, #23, #24 :
- tokens utilisés (pas de couleur hex en dur dans les composants) ;
- badges avec libellé et forme, pas seulement la couleur ;
- états chargement, vide, erreur, 403 et 404 présents sur chaque page de données ;
- dialogs de confirmation sur publication, retrait, suppression et suspension ;
- focus visible et parcours clavier testé à la main sur la page livrée ;
- aucun appel cabinet depuis le portail ; aucun `dangerouslySetInnerHTML` ;
- capture d'écran desktop et tablette jointe à la PR.

---

## Annexe A — Contrastes WCAG 2.x vérifiés

Commande : `python3 docs/tools/check_contrast.py` (exécutée le 2026-11-19, code retour 0). Formule WCAG 2.x de luminance relative, ratio `(L1 + 0.05) / (L2 + 0.05)`. Le script vérifie aussi que chaque couleur des paires existe dans les blocs `tailwind` ou `semantic` (0 orpheline), ce qui évite la dérive entre paires et tokens. À brancher en CI (#6) sur le fichier réellement importé par Tailwind.

| Paire | Avant-plan | Fond | Ratio | Seuil | Resultat |
|---|---|---|---|---|---|
| texte principal / paper | `#14202B` | `#FFFFFF` | 16.52:1 | 4.5:1 | OK |
| texte principal / ink-50 (fond app) | `#14202B` | `#F5F7F9` | 15.38:1 | 4.5:1 | OK |
| texte secondaire ink-700 / paper | `#34485A` | `#FFFFFF` | 9.46:1 | 4.5:1 | OK |
| texte attenue ink-500 / paper | `#56687A` | `#FFFFFF` | 5.74:1 | 4.5:1 | OK |
| texte attenue ink-500 / ink-50 | `#56687A` | `#F5F7F9` | 5.35:1 | 4.5:1 | OK |
| texte attenue ink-500 / ink-100 (ligne survolee) | `#56687A` | `#E9EEF2` | 4.92:1 | 4.5:1 | OK |
| bouton primaire paper / accent-600 | `#FFFFFF` | `#0E7069` | 5.93:1 | 4.5:1 | OK |
| bouton primaire survol paper / accent-700 | `#FFFFFF` | `#0B5F59` | 7.51:1 | 4.5:1 | OK |
| lien accent-700 / paper | `#0B5F59` | `#FFFFFF` | 7.51:1 | 4.5:1 | OK |
| nav active accent-800 / accent-50 | `#084A45` | `#EDF7F6` | 9.27:1 | 4.5:1 | OK |
| bouton danger paper / danger-600 | `#FFFFFF` | `#B42318` | 6.57:1 | 4.5:1 | OK |
| alerte erreur danger-700 / danger-50 | `#912018` | `#FDECEA` | 7.58:1 | 4.5:1 | OK |
| alerte succes success-700 / success-50 | `#146C2E` | `#E6F4EA` | 5.75:1 | 4.5:1 | OK |
| alerte avertissement warning-700 / warning-50 | `#7A4D00` | `#FFF3DC` | 6.61:1 | 4.5:1 | OK |
| alerte info info-700 / info-50 | `#1F5AA6` | `#E7EFFA` | 5.90:1 | 4.5:1 | OK |
| badge LOW | `#2F5A7A` | `#E3EEF6` | 6.22:1 | 4.5:1 | OK |
| badge MEDIUM | `#7A4D00` | `#FFF1D6` | 6.51:1 | 4.5:1 | OK |
| badge HIGH | `#9A3412` | `#FDE7DA` | 6.13:1 | 4.5:1 | OK |
| badge CRITICAL | `#FFFFFF` | `#A3172E` | 7.72:1 | 4.5:1 | OK |
| statut OPEN / paper | `#14202B` | `#FFFFFF` | 16.52:1 | 4.5:1 | OK |
| statut IN_PROGRESS / paper | `#1F5AA6` | `#FFFFFF` | 6.84:1 | 4.5:1 | OK |
| statut REMEDIATED / paper | `#146C2E` | `#FFFFFF` | 6.53:1 | 4.5:1 | OK |
| statut ACCEPTED_RISK / paper | `#6B3FA0` | `#FFFFFF` | 7.38:1 | 4.5:1 | OK |
| non-texte: anneau focus / paper | `#2349C8` | `#FFFFFF` | 7.35:1 | 3.0:1 | OK |
| non-texte: anneau focus / ink-50 (fond app) | `#2349C8` | `#F5F7F9` | 6.84:1 | 3.0:1 | OK |
| non-texte: anneau focus / canvas graphe | `#2349C8` | `#F1F4F6` | 6.65:1 | 3.0:1 | OK |
| non-texte: bordure champ ink-400 / paper | `#7D8C9A` | `#FFFFFF` | 3.45:1 | 3.0:1 | OK |
| non-texte: sev LOW solid / paper | `#4A7FA8` | `#FFFFFF` | 4.29:1 | 3.0:1 | OK |
| non-texte: sev MEDIUM solid / paper | `#B7791F` | `#FFFFFF` | 3.64:1 | 3.0:1 | OK |
| non-texte: sev HIGH solid / paper | `#D9622B` | `#FFFFFF` | 3.66:1 | 3.0:1 | OK |
| non-texte: sev CRITICAL solid / paper | `#A3172E` | `#FFFFFF` | 7.72:1 | 3.0:1 | OK |
| graphe: edge actif / canvas | `#34485A` | `#F1F4F6` | 8.56:1 | 3.0:1 | OK |
| graphe: edge neutralise / canvas | `#7D8C9A` | `#F1F4F6` | 3.12:1 | 3.0:1 | OK |
| graphe: chemin selectionne / canvas | `#0E7069` | `#F1F4F6` | 5.37:1 | 3.0:1 | OK |
| graphe: chemin selectionne / halo | `#0E7069` | `#D5EEEB` | 4.87:1 | 3.0:1 | OK |
| graphe: libelle entry point / paper | `#1F5AA6` | `#FFFFFF` | 6.84:1 | 4.5:1 | OK |
| graphe: libelle crown jewel / paper | `#7A4D00` | `#FFFFFF` | 7.27:1 | 4.5:1 | OK |
| graphe: texte attenue ink-500 / canvas | `#56687A` | `#F1F4F6` | 5.20:1 | 4.5:1 | OK |

38/38 paires conformes
