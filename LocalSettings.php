<?php
# Configuration de base de MediaWiki
$wgSitename = "Wiki Phonétique";
$wgMetaNamespace = "Wiki_Phonétique";

# Base de données
$wgDBtype = "mysql";
$wgDBserver = "localhost";
$wgDBname = "wikidb";
$wgDBuser = "wikiuser";
$wgDBpassword = "votre_mot_de_passe";

# Chemin vers l'extension
$wgExtensionDirectory = __DIR__ . "/extensions";

# Charger l'extension de transcription phonétique
wfLoadExtension('PhoneticTranscription');

# Configuration de l'extension
$wgPhoneticTranscriptionSettings = [
    'language' => 'fr',
    'defaultEngine' => 'espeak',
    'preservePunctuation' => true,
    'useIPA' => true
];

# Paramètres de sécurité
$wgSecretKey = "votre_clé_secrète";
$wgUpgradeKey = "votre_clé_upgrade";

# Droits d'accès
$wgGroupPermissions['*']['phonetic'] = true;
$wgGroupPermissions['sysop']['phonetic-admin'] = true;

# Cache
$wgMainCacheType = CACHE_NONE;
$wgMemCachedServers = [];

# Debug (à désactiver en production)
$wgShowExceptionDetails = true;
$wgShowDBErrorBacktrace = true;
$wgDebugLogFile = __DIR__ . "/debug.log"; 