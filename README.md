## 🧠 **Concept de la solution IntelliOLT – Supervision intelligente de réseau FTTH (ISP)**

IntelliOLT est une plateforme **unifiée, modulaire et intelligente** conçue pour les opérateurs télécoms (ISP) qui déploient des réseaux FTTH (Fibre To The Home) basés sur des équipements OLT/ONT. Elle intègre la collecte SNMP, la détection rapide de défaillances (BFD), l’alerte avancée, l’intelligence artificielle (détection d’anomalies, prédictions), l’analyse de données (KPIs, rapports) et la simulation réseau (EVE‑NG). L’objectif est de fournir une **visibilité complète, automatisée et prédictive** de l’infrastructure.

---

## 🏗️ **Architecture globale**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Clients / Frontend                          │
│   (React / API REST / Admin Django Jazzmin / Tableaux de bord)      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      API Gateway (Django REST)                      │
│  Permissions JWT / Throttling / Documentation (Swagger/ReDoc)       │
└───────────────┬───────────────────────────────┬─────────────────────┘
                │                               │
┌───────────────▼───────────────┐ ┌─────────────▼─────────────────────┐
│      Applications métier      │ │        Tâches asynchrones         │
│  • users / core / equipements │ │            Celery                 │
│  • snmp_collector / bfd       │ │  • Collecte SNMP                  │
│  • alerting / ai_engine       │ │  • Polling BFD                    │
│  • analytics / eve_ng         │ │  • Détection anomalies / IA       │
│                               │ │  • Agrégation KPIs / rapports     │
│                               │ │  • Notifications                  │
└───────────────┬───────────────┘ └─────────────┬─────────────────────┘
                │                               │
┌───────────────▼───────────────────────────────▼─────────────────────┐
│                     Bases de données & caches                       │
│  • PostgreSQL (avec TimescaleDB pour métriques temporelles)         │
│  • Redis (cache, verrouillage, files d’attente Celery)              │
└───────────────┬───────────────────────────────┬─────────────────────┘
                │                               │
┌───────────────▼───────────────┐ ┌─────────────▼─────────────────────┐
│   Infrastructure réseau       │ │         Écosystème externe         │
│   • OLT (Huawei, Nokia, etc.) │ │  • EVE‑NG (simulation)            │
│   • ONT                        │ │  • Grok / xAI (explications)      │
│   • Sessions BFD               │ │  • Slack / Teams / webhooks       │
└───────────────────────────────┘ └───────────────────────────────────┘
```

---

## ⚙️ **Fonctionnement détaillé (cycle de vie)**

### 1. **Découverte et inventaire des équipements** (`apps.equipements`)
- L’administrateur ajoute les **OLT** (fabricant, modèle, IP, communautés SNMP, coordonnées géographiques, site, baie, etc.).
- Les **ONT** sont automatiquement détectés via SNMP ou renseignés manuellement, avec rattachement à un client, un port GPON et un chemin optique (splitter).
- Des **liens fibre** entre OLT (backbone/distribution) sont modélisés, avec interfaces réseau et métriques (bande passante, utilisation).
- Toutes les données sont historisées (soft‑delete, audit).

### 2. **Collecte SNMP** (`apps.snmp_collector`)
- Un **catalogue d’OIDs** définit les métriques à surveiller (CPU, mémoire, température, puissance optique RX/TX, débits, etc.).
- Des **profils de polling** personnalisent les timeouts, retries et fréquences.
- **Celery** déclenche périodiquement la collecte sur chaque OLT actif (tâche `snmp.poll_single_olt`).
- Les valeurs brutes sont stockées dans `MetricHistory` (avec TimescaleDB pour les séries temporelles).
- En cas d’erreur SNMP (timeout, authentification, OID inexistant), un log est créé et une alerte peut être levée.

### 3. **Surveillance BFD** (`apps.bfd_monitor`)
- Chaque session BFD (entre deux interfaces ou sur un lien fibre) est modélisée (discriminateurs, intervalles TX/RX, multiplicateur).
- Une tâche Celery (`bfd.poll_session`) interroge périodiquement l’état BFD (via SNMP ou simulation). Les changements d’état sont enregistrés dans `BFDStateHistory`.
- Des règles de seuil (`BFDThresholdRule`) surveillent le taux de perte, le temps de détection, le flapping, etc.
- Les alertes BFD sont automatiquement remontées dans le système d’alerte global.

### 4. **Moteur d’alertes** (`apps.alerting`)
- **Règles multi‑sources** : une alerte peut être déclenchée par un seuil SNMP, un événement BFD, ou une anomalie IA.
- **Déduplication et cooldown** : une même condition ne génère pas d’alertes en rafale.
- **Notifications** : canaux configurables (email, Slack, Teams, webhook) avec test intégré.
- **Cycle de vie** : alertes actives → acquittées par l’opérateur → résolues automatiquement lorsque la condition disparaît.
- Un historique des notifications est conservé.

### 5. **Intelligence Artificielle** (`apps.ai_engine`)
- **Modèles ML** (Isolation Forest, Prophet, LSTM) enregistrés et versionnés.
- **Entraînement** asynchrone à partir des métriques SNMP historiques (`TrainingJob`).
- **Détection d’anomalies** : chaque OLT est analysé périodiquement par le modèle actif. Le score d’anomalie (0‑1) génère une entrée dans `AnomalyDetection` avec sévérité.
- **Explications** : intégration avec l’API **Grok (xAI)** pour fournir un texte explicatif (exemple : « CPU anormalement élevé à 95% alors que la moyenne est 30% »).
- **Prédictions** : utilisation de Prophet (ou autre) pour prévoir l’évolution d’une métrique (ex. charge CPU dans 24h). Les prédictions sont stockées dans `Prediction`.

### 6. **Analytique et rapports** (`apps.analytics`)
- **Agrégation automatique** des KPIs (horaires, journaliers) : nombre d’OLT/ONT actifs, taux de succès SNMP, sessions BFD UP, anomalies, alertes, etc.
- **Cache Redis** pour les KPIs temps réel (accès instantané depuis le dashboard).
- **Rapports PDF/Excel** : génération à la demande (plage personnalisée, type de rapport) avec graphiques intégrés (matplotlib, reportlab, openpyxl).
- **Tableaux de bord personnalisables** : chaque utilisateur peut organiser ses widgets (courbes, jauges, métriques) via l’API.

### 7. **Simulation réseau (EVE‑NG)** (`apps.eve_ng`)
- Permet de modéliser des laboratoires virtuels : labs, nœuds (OLT, routeurs, switchs).
- Intégration avec l’API EVE‑NG Community pour démarrer/arrêter des topologies.
- Synchronisation possible entre équipements réels et virtuels (ex. pousser une configuration).
- Utile pour la formation, le pré‑déploiement ou la reproduction de pannes.

### 8. **Administration et sécurité**
- **Authentification** : email/username + mot de passe, JWT pour l’API.
- **Permissions fines** : rôles (admin, superviseur, opérateur, observateur) avec permissions granulaires (gérer OLT, voir alertes, exporter données, etc.).
- **Journalisation** : toutes les actions sensibles sont tracées (`UserActivity`).
- **Configuration centralisée** : table `Config` (JSON) pour stocker les paramètres système (SNMP, BFD, IA, notifications).
- **Interface d’administration** : Django Jazzmin, avec thème moderne (clair/sombre), liens rapides, tableau de bord personnalisé.

### 9. **Orchestration et tâches périodiques**
- **Celery** exécute les collectes SNMP, les polls BFD, les détections IA, les agrégations, les générations de rapports.
- **Celery Beat** planifie :
  - Collecte SNMP toutes les 60 secondes (ou selon profil).
  - Polling BFD toutes les 30 secondes.
  - Détection d’anomalies toutes les 5 minutes.
  - Agrégation KPIs horaire/journalière.
- **Verrouillage Redis** pour éviter les exécutions concurrentes sur un même OLT/session.

---

## 📊 **Flux de données types**

1. **SNMP** : OLT → (SNMPv2c/v3) → `fetch_snmp_value` → `MetricHistory` → seuils → `Alert` → notifications.
2. **BFD** : Session BFD → `poll_bfd_session` → `BFDStateHistory` → `BFDActiveAlert` → `Alert`.
3. **IA** : `MetricHistory` (historique) → `train_model` (Isolation Forest) → `detect_anomalies_for_olt` → `AnomalyDetection` → (optionnel) `Alert`.
4. **Analytics** : `MetricHistory` + `Alert` + `BFDSession` + `AnomalyDetection` → `aggregate_kpi` → `KPIHistory` → génération de rapport → fichier PDF/Excel.
5. **Notification** : `Alert` déclenchée → `evaluate_rules_for_olt` → pour chaque canal actif → `send_alert_notification` (email/Slack/Teams/webhook) → `NotificationHistory`.

---

## 🎯 **Bénéfices pour un ISP**

- **Supervision unifiée** : tous les équipements (OLT, ONT, liens fibre, sessions BFD) dans une seule interface.
- **Détection proactive** : seuils SNMP, BFD et IA pour anticiper les pannes (ex. perte de puissance optique, flapping, anomalies CPU).
- **Réduction du MTTR** : alertes en temps réel vers les bons canaux (Slack, email, etc.) avec contexte.
- **Optimisation des ressources** : KPIs et rapports pour piloter l’expansion du réseau, la maintenance.
- **Simulation sans risque** : EVE‑NG permet de tester des configurations ou scénarios de panne.
- **Explicabilité IA** : via Grok, l’opérateur comprend pourquoi une anomalie a été signalée.
- **Scalabilité** : architecture asynchrone (Celery) et base temporelle (TimescaleDB) supportent plusieurs milliers d’OLT.

---

## 🧩 **Résumé des interactions entre applications**

| Application      | Utilise                                                     | Est utilisé par                                      |
|------------------|-------------------------------------------------------------|------------------------------------------------------|
| `core`           | BaseModel, SoftDeleteModel, permissions, pagination, etc.  | Toutes les autres apps                              |
| `users`          | User, Team, Role, Permission, UserActivity                 | `equipements` (créateur), `alerting` (acquitteur)   |
| `equipements`    | OLT, ONT, FibreLink, NetworkInterface, Vendor, etc.        | `snmp_collector`, `bfd_monitor`, `ai_engine`        |
| `snmp_collector` | MetricHistory, SnmpOID, PollJob, SnmpAlert                 | `ai_engine`, `alerting`, `analytics`                |
| `bfd_monitor`    | BFDSession, BFDStateHistory, BFDActiveAlert                | `alerting`, `analytics`                             |
| `ai_engine`      | MLModel, AnomalyDetection, Prediction                      | `alerting`, `analytics`                             |
| `alerting`       | Alert, AlertRule, NotificationChannel                      | `analytics` (comptage)                              |
| `analytics`      | KPIHistory, Report, DashboardWidget                        | Interface frontend / admin                          |
| `eve_ng`         | (indépendant, mais peut utiliser `equipements`)            | Simulation                                          |

---

## 🚀 **Démarrage et utilisation**

Après déploiement des conteneurs (PostgreSQL, Redis, Celery, Django), l’opérateur se connecte à l’interface d’administration (Jazzmin) ou à l’API REST. Il peut :

- Ajouter des OLT (via l’admin ou API).
- Configurer les OIDs SNMP et les profils de collecte.
- Définir des règles d’alerte et des canaux de notification.
- Lancer l’entraînement d’un modèle IA.
- Visualiser les KPIs en temps réel et générer des rapports.
- Démarrer des laboratoires EVE‑NG pour tester des changements.

L’ensemble est conçu pour être **maintenable, extensible et performant** en environnement de production ISP.