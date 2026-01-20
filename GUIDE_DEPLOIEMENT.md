# Guide de Déploiement du Bot Discord

Ce guide vous explique comment héberger votre bot gratuitement (ou à faible coût) pour qu'il tourne 24h/24 et 7j/7, même quand votre ordinateur est éteint.

> [!NOTE]
> Pour que le bot fonctionne tout le temps, il doit être hébergé sur un **serveur**. Il existe des services "Cloud" qui proposent des offres gratuites suffisantes pour un petit bot.

## Prérequis

1.  Avoir votre code sur **GitHub** (c'est le plus simple pour connecter les hébergeurs).
2.  Avoir les fichiers `Dockerfile` et/ou `Procfile` (déjà créés dans votre projet).
3.  Connaître vos variables d'environnement (Token Discord, Email MyGES, etc.).

---

## Option 1 : Render (Recommandé - Facile)

**Render** propose une offre gratuite pour les services Web et Workers.

1.  Créez un compte sur [dashboard.render.com](https://dashboard.render.com/).
2.  Cliquez sur **"New +"** et sélectionnez **"Web Service"**.
3.  Connectez votre compte GitHub et sélectionnez le dépôt de votre bot.
4.  Configurez le service :
    *   **Name:** `myges-bot` (ou ce que vous voulez)
    *   **Region:** Choisissez `Frankfurt (Germany)` (le plus proche).
    *   **Branch:** `main` (ou master).
    *   **Runtime:** `Docker`.
5.  **Variables d'environnement (Environment Variables) :**
    C'est *crucial*. Ajoutez les clés-valeurs suivantes (les mêmes que dans votre `.env`) :
    *   `DISCORD_TOKEN`: `votre_token_ici`
    *   `DISCORD_CHANNEL_ID`: `votre_id_channel`
    *   `MYGES_EMAIL`: `votre_email`
    *   `MYGES_PASSWORD`: `votre_mot_de_passe`
6.  Cliquez sur **"Create Web Service"**.

> [!WARNING]
> L'offre gratuite de Render met le service en veille s'il n'est pas utilisé pendant 15 mins. Cependant, comme c'est un bot connecté en WebSocket à Discord, il *devrait* rester actif, ou se réveiller rapidement. Si vous avez des problèmes de veille, il faudra peut-être regarder du côté de **Fly.io**.

---

## Option 2 : Fly.io (Ligne de commande)

**Fly.io** demande d'installer un petit outil en ligne de commande, mais c'est très performant.

1.  Installez `flyctl` (L'outil en ligne de commande de Fly.io).
    *   Mac: `brew install flyctl`
2.  Connectez-vous : `fly auth login`
3.  Dans le dossier de votre bot, lancez : `fly launch`
4.  Répondez aux questions (non pour la base de données Postgres/Redis).
5.  Définissez les secrets (variables) :
    ```bash
    fly secrets set DISCORD_TOKEN=votre_token MYGES_EMAIL=votre_email MYGES_PASSWORD=votre_pwd DISCORD_CHANNEL_ID=votre_id
    ```
6.  Déployez : `fly deploy`

---

## Option 3 : AlwaysData (Hébergeur Français)

**AlwaysData** offre 100Mo gratuits, ce qui est suffisant pour un petit script Python.

1.  Créez un compte sur [alwaysdata.com](https://www.alwaysdata.com/).
2.  Allez dans l'interface d'administration.
3.  Téléversez vos fichiers via FTP ou WebFTP.
4.  Dans **Environnement > Python**, configurez votre script.
5.  Ajoutez vos variables d'environnement dans la configuration.

---

## Résumé

Pour débuter sans prise sa tête :
1.  Mettez votre code sur **GitHub**.
2.  Utilisez **Render.com** en connectant votre repo.
3.  N'oubliez surtout pas de copier vos **Environment Variables** dans le tableau de bord de l'hébergeur !
