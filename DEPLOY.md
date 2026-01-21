# 🚀 Déploiement sur Fly.io

C'est parti ! Voici comment mettre ton bot en ligne gratuitement.

## 1. Installation de l'outil Fly (Terminal)

Copie-colle cette commande dans ton terminal (hors de vs code si besoin, ou dans un nouveau terminal) :
```bash
brew install flyctl
```

## 2. Connexion

Authentifie-toi :
```bash
fly auth login
```
(Ça va ouvrir une page web, connecte-toi avec ton compte GitHub ou email).

## 3. Lancement du projet

Initialise l'application :
```bash
fly launch
```
- **App Name** : Laisse vide (généré auto) ou mets un nom unique (ex: `mon-bot-gez`).
- **Region** : Choisis `cdg` (Paris) pour que ce soit rapide.
- **Configuration** : Réponds "Yes" pour copier la config, ou "Tweak settings" si tu veux changer. En général les défauts sont bons.
- **Deploy now?** : Réponds **No** pour l'instant (on doit mettre les secrets avant !).

## 4. Configuration des Secrets (Important !)

On ne met JAMAIS le fichier `.env` sur le serveur. On injecte les variables directement via Fly :

Remplace les valeurs par les tiennes (celles de ton fichier `.env`) :

```bash
fly secrets set DISCORD_TOKEN="TonTokenIci"
fly secrets set DISCORD_CHANNEL_ID="TonIDChannel"
fly secrets set MYGES_EMAIL="TonEmail"
fly secrets set MYGES_PASSWORD="TonMotDePasse"
```

## 5. Déploiement

Une fois les secrets configurés, lance le bot :
```bash
fly deploy
```

## 6. Vérification

Pour voir si tout va bien :
```bash
fly logs
```

---
**Note sur la sauvegarde** :
Sur la version gratuite de base, le fichier `schedule_state.json` sera remis à zéro si le bot redémarre (mise à jour, crash). Pour un bot simple, ce n'est pas grave (il refera juste une vérification). Si tu veux une persistance absolue, on pourra ajouter un "Volume" plus tard.
