# Auth Migration & Alignment Notes

Objectif: documenter les changements à mener pour aligner l’authentification entre `auth` (base avancée) et `prediction_skills`, et préparer une implémentation commune (email-first, rôles unifiés, sécurité renforcée, conventions de réponse).

## 1) Modèle utilisateur (source commune)
- Référence: `auth/accounts/models.py` (User email-only, rôles enum EMPLOYEE/MANAGER/HR/ADMIN, is_email_verified, LoginAttempt, LoginActivity).
- État `prediction_skills`: User Django par défaut (username requis), rôles via groupes DRH/RESPONSABLE_RH/MANAGER.
- Décision cible: email = identifiant unique. Converger vers `accounts.User` (ou alias `username=email` si étape intermédiaire). Garder `role` enum comme source d’autorité.
- À prévoir: migration des données (copier username→email si vide, forcer unicité email, recréer utilisateurs de service/test).
- Statut (auth): compat `username` ajouté, normalisation email + contrainte unique case-insensitive, `email_verified_at`, index sur `role`.

## 2) Rôles / groupes / permissions
- Rôles `auth`: EMPLOYEE, MANAGER, HR, ADMIN (ADMIN = admin général/technique).
- Groupes (auth): HR, HR_ADMIN, MANAGER, MANAGER_ADMIN, EMPLOYEE, EMPLOYEE_ADMIN, AUDITOR, SECURITY_ADMIN, SUPPORT.
- Stratégie: role = source de vérité, groupes synchronisés (base) pour compatibilité. Les groupes “*_ADMIN” sont gérés manuellement.
- Sync base (auth): HR → HR, MANAGER → MANAGER, EMPLOYEE → EMPLOYEE. ADMIN bypass toutes permissions.
- Permissions dédiées: `IsAuditorReadOnly`, `IsSecurityAdmin`, `IsSupport` + helpers d’accès (roles + groupes).
- Statut (auth): HR a accès aux endpoints manager via `IsManagerOrAbove`.

## 3) Flux d’authentification
- Couverture `auth` (à conserver): register, login, refresh, logout (blacklist), me, reset mot de passe, vérification email, suivi des login, lockout custom.
- Couverture `prediction_skills` (à intégrer si besoin): monitoring APM/logs, éventuelle personnalisation middleware.
- Actions prévues: exposer le login par email, conserver refresh/blacklist, garder `ApiResponseMixin` pour les enveloppes de réponse, ajouter endpoints reset/vérif email si absents côté consommateur.
- Statut (auth): login accepte email ou username; username requis à l’inscription.

## 4) Sécurité / verrouillage
- `auth`: `LoginAttempt` (lock après N échecs), email d’alerte, `LoginActivity` (audit).
- `prediction_skills`: django-axes (lock username/IP, configurable), middleware de sécurité/logging.
- Recommandation: activer django-axes dans `auth` (middleware + settings) pour bénéficier du lock IP/user robuste, tout en gardant `LoginActivity` pour l’audit. Harmoniser les paramètres de lock (seuils, durée). Si login email-only, basculer Axes sur le champ email.

## 5) JWT / sessions
- Les deux projets utilisent SimpleJWT; différence: login username (prediction_skills) vs email (auth).
- Cible: login email. Conserver rotation/blacklist. Harmoniser `SIMPLE_JWT` (durées, headers) et `AXES_LOCK_OUT_PARAMETERS` (email plutôt que username).

## 6) Structure des réponses API
- `auth`: enveloppe standard `{"data": ..., "meta": {"success": true}}` via `ApiResponseMixin`.
- `prediction_skills`: réponses brutes DRF.
- Décision: adopter l’enveloppe standard pour tous les endpoints (auth et métier) ou documenter une exception. Mettre à jour les clients/tests si enveloppe généralisée.

## 7) Étapes techniques proposées
1) Activer/porter django-axes dans `auth` (settings, middleware, config lock sur email). Garder `LoginActivity`.
2) Unifier le modèle user: utiliser `accounts.User` comme référence; ajouter un script de migration des users existants (username→email, création des rôles/groupes). Si transition douce: alias `username=email` temporaire.
3) Synchroniser rôle ↔ groupes: migration de bootstrap (groupes HR/HR_ADMIN/MANAGER/MANAGER_ADMIN/EMPLOYEE/EMPLOYEE_ADMIN/AUDITOR/SECURITY_ADMIN/SUPPORT) et signal pour tenir à jour. Mettre à jour permissions DRF pour lire le rôle ou les groupes mappés.
4) Standardiser les endpoints et contrats: login/register/reset/verify email, `/me`, logout blacklist; choisir l’enveloppe de réponse unique. Mettre à jour Postman/tests.
5) Sécurité applicative: aligner lockout (seuil/durée), CSRF/CORS/headers, logs de sécurité (APM si souhaité), monitoring (prometheus si requis).
6) Tests: ajouter/adapter les tests d’auth (login email, lockout, reset, verify email, logout blacklist, permissions par rôle/groupe), et les tests d’intégration avec future_skills.

## 8) Points de migration / data
- S’assurer que tous les utilisateurs ont un email unique (sinon dédoublonner). Remplir username = email pendant la transition si nécessaire.
- Recréer les superusers/admin techniques avec le nouveau modèle.
- Nettoyer les tokens/mots de passe de test avant prod.

## 9) Rollout conseillé
- Phase 1 (dev): activer django-axes + enveloppe standard dans `auth`; tests end-to-end email login; mapping rôles↔groupes.
- Phase 2 (intégration): basculer `prediction_skills` pour consommer l’auth unifiée (login email, permissions mappées), mettre à jour clients/tests/Postman.
- Phase 3 (prod): migrer les comptes existants, surveiller les lockouts et les journaux d’activité, valider le monitoring.

## 10) Questions en suspens
- ADMIN réservé au staff technique ou équivalent DRH ?
- Enveloppe de réponse: généralisation à toutes les APIs ou seulement auth ?
- Tolérance rétro-compat (accepter username en plus d’email) et durée de la période de grâce.
