# Demo Atlas – Gestion des migrations avec Atlas

Ce projet illustre comment gérer les migrations de base de données MySQL avec [Atlas](https://atlasgo.io), en suivant le même parcours que le [getting started officiel](https://atlasgo.io/getting-started) : workflow déclaratif, puis workflow versionné.

---

## Prérequis

| Outil | Installation |
|---|---|
| Docker | https://docs.docker.com/get-docker/ |
| mise | `brew install mise` ou https://mise.jdx.dev/getting-started.html |

> Atlas est lancé via Docker — aucune installation locale nécessaire.

```bash
mise trust -qa && mise install
```

### Alias utile

```bash
alias atlas='docker compose run --rm atlas'
```

---

## Structure du projet

```
demo-atlas/
├── src/
│   ├── main.py              # API Flask (users + tasks + UI)
│   └── templates/
│       └── index.html       # Interface web (Tailwind CSS)
├── migrations/              # Fichiers SQL versionnés (générés par Atlas)
├── initdb/                  # Scripts d'init MySQL
├── atlas.hcl                # Configuration Atlas (env docker)
├── schema.hcl               # Schéma cible déclaratif (source de vérité)
├── Dockerfile               # Image Python/uv pour l'application
├── compose.yml              # MySQL 8 + application + service Atlas
└── pyproject.toml           # Dépendances Python (Flask, mysql-connector)
```

---

## Étape 1 – Démarrer l'environnement

```bash
docker compose up -d
docker compose ps   # STATUS doit être "healthy" (~15 s)
```

Deux services démarrent :
- **mysql** – MySQL 8 sur le port `3306`
- **myapp** – API Flask sur le port `5001`

---

## Étape 2 – Définir le schéma cible

Le fichier `schema.hcl` décrit l'état **désiré** de la base. Atlas calcule toujours le diff entre l'état actuel et ce fichier — c'est la source de vérité.

```bash
cat schema.hcl
```

---

## Étape 3 – Workflow déclaratif : schema apply

Le workflow déclaratif applique le schéma **directement**, sans fichier de migration. Idéal pour le dev/test.

```bash
atlas schema apply --env docker --auto-approve
```

Atlas détecte que la base est vide et applique le diff :

```
-- Applying changes:
-- CREATE TABLE `users` ...
-- CREATE TABLE `tasks` ...
```

Vérifier le résultat :

```bash
atlas schema inspect --env docker
```

Atlas détecte que `users` et `tasks` existent déjà si on relance — **il n'applique que ce qui change**.

---

## Étape 4 – Utiliser l'application

L'application Flask tourne dans Docker. Une fois les tables créées (étape 3), ouvrir http://localhost:5001 pour accéder à l'interface web.

### Interface web

L'UI permet de créer des utilisateurs et des tâches, et de les marquer comme terminées. Elle se rafraîchit automatiquement toutes les 10 secondes.

### API REST

```bash
# Créer un utilisateur
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Créer une tâche
curl -X POST http://localhost:5001/tasks \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "title": "Préparer la démo Atlas"}'

# Lister les tâches
curl http://localhost:5001/tasks

# Marquer une tâche comme terminée
curl -X PATCH http://localhost:5001/tasks/1
```

### Développement avec hot-reload

```bash
docker compose watch
```

Les modifications dans `src/` sont synchronisées automatiquement dans le conteneur.

---

## Étape 5 – Workflow versionné : migrate diff → lint → apply

Le workflow versionné génère des fichiers SQL dans `migrations/`, committables dans git et révisables en PR. C'est le workflow recommandé pour la **production**.

### 5a. Remettre la base à zéro

```bash
atlas schema clean \
  --url "mysql://root:password@demo-atlas-mysql:3306/demo" \
  --auto-approve
```

### 5b. Générer la migration initiale

Atlas compare `schema.hcl` (état cible) avec la base vide et génère le SQL :

```bash
atlas migrate diff initial --env docker
```

Deux fichiers sont créés dans `migrations/` :
- `<timestamp>_initial.sql` — le SQL de migration
- `atlas.sum` — checksum d'intégrité

```bash
cat migrations/*_initial.sql
```

### 5c. Lint

Atlas analyse la migration pour détecter des problèmes (changement destructif, lock de table, etc.) :

```bash
atlas migrate lint --env docker --latest 1
```

### 5d. Appliquer

```bash
atlas migrate apply --env docker
```

Résultat attendu :

```
Migrating to version <timestamp> (1 migration in total):
  -- migrating version <timestamp>_initial
    -> CREATE TABLE `users` ...
    -> CREATE TABLE `tasks` ...
  -- ok (Xs)
```

```bash
atlas migrate status --env docker
```

---

## Étape 6 – Modifier le schéma

On veut ajouter une colonne `bio` aux utilisateurs et `due_date` aux tâches.

### 6a. Modifier schema.hcl

Dans `table "users"`, ajouter avant `primary_key` :

```hcl
column "bio" {
  type = text
  null = true
}
```

Dans `table "tasks"`, ajouter avant `primary_key` :

```hcl
column "due_date" {
  type = date
  null = true
}
```

### 6b. Générer la migration

```bash
atlas migrate diff add_bio_and_due_date --env docker
```

Résultat attendu dans le nouveau fichier :

```sql
-- Modify "users" table
ALTER TABLE `users` ADD COLUMN `bio` text NULL;
-- Modify "tasks" table
ALTER TABLE `tasks` ADD COLUMN `due_date` date NULL;
```

### 6c. Lint

```bash
atlas migrate lint --env docker --latest 1
```

### 6d. Appliquer

```bash
atlas migrate apply --env docker
```

### 6e. Vérifier l'état final

```bash
atlas schema inspect --env docker
```

---

## Commandes Atlas de référence

| Commande | Description |
|---|---|
| `atlas schema apply` | Applique le schéma déclaratif directement |
| `atlas schema inspect` | Inspecte la base et exporte en HCL |
| `atlas schema clean` | Vide la base (⚠️ destructif) |
| `atlas migrate diff <name>` | Génère une migration depuis le diff schéma |
| `atlas migrate apply` | Applique les migrations en attente |
| `atlas migrate status` | État des migrations appliquées |
| `atlas migrate lint` | Analyse et lint des migrations |
| `atlas migrate hash` | Recalcule atlas.sum |

Préfixer chaque commande avec `docker compose run --rm atlas` (ou utiliser l'alias `atlas`).

---

## Nettoyer l'environnement

```bash
docker compose down -v   # Supprime les conteneurs et le volume MySQL
```
