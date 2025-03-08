from flask import Flask, render_template, request, jsonify
import subprocess
import os
import tempfile
import requests
import re
import logging
import json
from pocketsphinx import Config, Decoder, get_model_path, Pocketsphinx

app = Flask(__name__)

# Configuration Azure
SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'francecentral')

# Configuration de PocketSphinx
SPHINX_CONFIG = {
    'hmm': os.path.join(get_model_path(), 'fr-fr'),  # Modèle acoustique français
    'dict': os.path.join(get_model_path(), 'fr-fr.dict'),  # Dictionnaire de prononciation
    'allphone': os.path.join(get_model_path(), 'fr-fr.phone'),  # Liste des phonèmes
    'beam': 1e-20,  # Paramètre de recherche
    'pbeam': 1e-20,  # Paramètre de recherche phonétique
    'lw': 2.0,  # Poids du modèle de langage
}

# Dictionnaire de correspondances phonétiques amélioré
PHONEMES = {
    # Cas spéciaux (à traiter en premier)
    "aujourd'hui": 'oʒuʁdɥi',
    "aujourd hui": 'oʒuʁdɥi',
    "aujourdhui": 'oʒuʁdɥi',
    "université": 'ynivɛʁsite',
    
    # Voyelles composées (à traiter ensuite)
    'eau': 'o',
    'eaux': 'o',
    'au': 'o',
    'aux': 'o',
    'ai': 'ɛ',
    'aient': 'ɛ',
    'aie': 'ɛ',
    'aies': 'ɛ',
    'ais': 'ɛ',
    'ait': 'ɛ',
    'ei': 'ɛ',
    'oi': 'wa',
    'oie': 'wa',
    'oient': 'wa',
    'oin': 'wɛ̃',
    'ou': 'u',
    
    # Nasales
    'ein': 'ɛ̃',
    'ain': 'ɛ̃',
    'aim': 'ɛ̃',
    'in': 'ɛ̃',
    'im': 'ɛ̃',
    'un': 'œ̃',
    'um': 'œ̃',
    'an': 'ɑ̃',
    'am': 'ɑ̃',
    'en': 'ɑ̃',
    'em': 'ɑ̃',
    'on': 'ɔ̃',
    'om': 'ɔ̃',
    
    # Voyelles simples
    'é': 'e',
    'è': 'ɛ',
    'ê': 'ɛ',
    'ë': 'ɛ',
    'â': 'ɑ',
    'à': 'a',
    'ô': 'o',
    'î': 'i',
    'ï': 'i',
    'û': 'y',
    'ù': 'y',
    'ü': 'y',
    'œu': 'œ',
    'eu': 'ø',
    
    # Terminaisons spéciales
    'er$': 'e',
    'ez$': 'e',
    'et$': 'ɛ',
    'ent$': 'ɑ̃',
    'es$': 'ə',
    'e$': 'ə',
    
    # Consonnes composées
    'ch': 'ʃ',
    'ph': 'f',
    'th': 't',
    'gn': 'ɲ',
    'ng': 'ŋ',
    'qu': 'k',
    'gu(?=[ei])': 'g',
    'ç': 's',
    
    # Règles contextuelles
    'c(?=[eiyéèêë])': 's',  # c suivi de e, i, y et leurs variantes
    'c(?=[aouàâôù])': 'k',  # c suivi de a, o, u et leurs variantes
    'g(?=[eiyéèêë])': 'ʒ',  # g suivi de e, i, y et leurs variantes
    'g(?=[aouàâôù])': 'g',  # g suivi de a, o, u et leurs variantes
    's(?=[aeiouéèêëàâîïôûù])(?<=[aeiouéèêëàâîïôûù])': 'z',  # s entre voyelles
    'ss': 's',
    
    # Consonnes simples finales à traiter
    'b$': 'b',
    'd$': 'd',
    'f$': 'f',
    'g$': 'g',
    'k$': 'k',
    'l$': 'l',
    'm$': 'm',
    'n$': 'n',
    'p$': 'p',
    'r$': 'ʁ',
    's$': '',  # s final muet
    't$': '',  # t final muet
    'x$': '',  # x final muet
    'z$': '',  # z final muet
}

# Cache pour les transcriptions
CACHE_TRANSCRIPTIONS = {}

def transcrire(texte):
    """Transcrit le texte en phonèmes avec une logique améliorée"""
    texte = texte.lower()
    
    # Vérifier d'abord les cas spéciaux
    if texte in ["aujourd'hui", "aujourd hui", "aujourdhui", "université"]:
        return PHONEMES[texte]
    
    # Prétraitement
    texte = texte.replace('œ', 'oe')  # Normalisation des ligatures
    texte = re.sub(r'h', '', texte)   # Suppression des h muets
    
    # Application des règles de transcription
    for pattern, phoneme in sorted(PHONEMES.items(), key=lambda x: len(x[0]), reverse=True):
        if pattern.startswith('(?') or pattern.endswith('$'):
            # Utilisation de regex pour les patterns complexes
            texte = re.sub(pattern, phoneme, texte)
        else:
            # Remplacement simple pour les patterns littéraux
            texte = texte.replace(pattern, phoneme)
    
    # Post-traitement
    # Gestion des consonnes finales muettes
    texte = re.sub(r'([tdspx])s?$', '', texte)
    
    # Gestion des voyelles
    texte = re.sub(r'e(?=[aeiouéèêëàâîïôûù])', '', texte)  # e suivi d'une voyelle devient muet
    
    # Gestion des doubles consonnes
    texte = re.sub(r'([bcdfgklmnprstv])\1', r'\1', texte)
    
    # Ajout des liaisons
    texte = re.sub(r'([aeiouéèêëàâîïôûù])n(?=[aeiouéèêëàâîïôûù])', r'\1n‿', texte)
    
    # Nettoyage
    texte = re.sub(r'\s+', ' ', texte)  # Normalise les espaces
    texte = texte.strip()
    
    return texte

def transcrire_avec_phonetisaurus(texte):
    """Transcrit le texte en utilisant Phonetisaurus"""
    # Créer un fichier temporaire pour le texte d'entrée
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(texte + '\n')
        input_file = f.name

    try:
        # Exécuter Phonetisaurus
        cmd = [
            "phonetisaurus-apply",
            "--model", "models/fr.fst",  # Modèle français
            "--word_list", input_file,
            "--nbest", "1"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Traiter la sortie
        if result.returncode == 0:
            # La sortie de Phonetisaurus est au format : mot TAB transcription
            transcription = result.stdout.strip().split('\t')[-1]
            return transcription
        else:
            return "Erreur de transcription"
            
    except Exception as e:
        print(f"Erreur : {str(e)}")
        return "Erreur de transcription"
        
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(input_file):
            os.unlink(input_file)

def obtenir_prononciation_wiktionary(mot):
    """Obtient la prononciation depuis Wiktionnaire sans modifier le mot"""
    print(f"\n[WIKTIONNAIRE] Recherche de la prononciation pour '{mot}'")
    try:
        S = requests.Session()
        URL = "https://fr.wiktionary.org/w/api.php"
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": mot,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "redirects": True
        }
        
        print(f"[WIKTIONNAIRE] URL: {URL}")
        print(f"[WIKTIONNAIRE] Paramètres: {PARAMS}")
        
        R = S.get(url=URL, params=PARAMS)
        print(f"[WIKTIONNAIRE] Status code: {R.status_code}")
        
        if R.status_code != 200:
            print(f"[WIKTIONNAIRE] Erreur HTTP: {R.text}")
            return None
            
        DATA = R.json()
        
        if 'query' in DATA and 'pages' in DATA['query']:
            pages = DATA['query']['pages']
            for page_id in pages:
                if str(page_id).startswith('-'):  # Page n'existe pas
                    print(f"[WIKTIONNAIRE] Page non trouvée pour '{mot}'")
                    return None
                    
                page = pages[page_id]
                if 'revisions' in page and page['revisions']:
                    revision = page['revisions'][0]
                    if '*' in revision['slots']['main']:
                        contenu = revision['slots']['main']['*']
                        print(f"\n[WIKTIONNAIRE] Contenu reçu (premiers 500 caractères):")
                        print("=" * 80)
                        print(contenu[:500])
                        print("=" * 80)
                        
                        # Chercher la prononciation dans le contenu
                        # Format typique : {{pron|fr|sɛ}}
                        match = re.search(r'\{\{pron\|fr\|([^}|]+)}}', contenu)
                        if match:
                            prononciation = match.group(1)
                            print(f"[WIKTIONNAIRE] ✓ Prononciation trouvée: {prononciation}")
                            return prononciation
                            
        print(f"[WIKTIONNAIRE] ✗ Aucune prononciation trouvée pour '{mot}'")
        return None
    except Exception as e:
        print(f"[WIKTIONNAIRE] Erreur: {str(e)}")
        return None

def obtenir_prononciation_sphinx(mot):
    """
    Obtient la prononciation d'un mot en utilisant PocketSphinx
    """
    try:
        # Initialiser PocketSphinx avec le modèle français
        ps = Pocketsphinx(
            lang="fr-FR",
            verbose=False,
            logfn=None
        )
        
        # Obtenir la transcription phonétique
        result = ps.phonemes(mot)
        
        # Nettoyer et formater la sortie
        if result:
            # Supprimer les espaces superflus et convertir en format IPA
            phones = result.strip().split()
            # Conversion basique des phonèmes CMU en IPA
            cmu_to_ipa = {
                'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ',
                'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð',
                'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'F': 'f', 'G': 'ɡ',
                'HH': 'h', 'IH': 'ɪ', 'IY': 'i', 'JH': 'dʒ', 'K': 'k',
                'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'OW': 'oʊ',
                'OY': 'ɔɪ', 'P': 'p', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ',
                'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'u', 'V': 'v',
                'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'
            }
            
            ipa = []
            for phone in phones:
                # Supprimer les chiffres de stress (0,1,2) s'ils existent
                base_phone = ''.join([c for c in phone if not c.isdigit()])
                if base_phone in cmu_to_ipa:
                    ipa.append(cmu_to_ipa[base_phone])
                else:
                    ipa.append(base_phone)
            
            return ''.join(ipa)
        return None
    except Exception as e:
        print(f"Erreur lors de la transcription avec PocketSphinx : {str(e)}")
        return None

def transcrire_texte(texte):
    """
    Transcrit un texte en phonétique
    """
    # Nettoyer et préparer le texte
    texte = texte.lower().strip()
    mots = texte.split()
    resultat = []
    
    for mot in mots:
        # D'abord essayer avec PocketSphinx
        prononciation = obtenir_prononciation_sphinx(mot)
        
        # Si PocketSphinx échoue, utiliser le système local
        if not prononciation:
            prononciation = transcrire(mot)
            
        resultat.append(prononciation if prononciation else mot)
    
    return ' '.join(resultat)

def est_consonne(phoneme):
    """Détermine si un phonème est une consonne"""
    consonnes = {'b', 'd', 'f', 'g', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'z', 'ʃ', 'ʒ', 'ŋ', 'ɲ', 'ʁ'}
    return phoneme in consonnes

def est_voyelle(phoneme):
    """Détermine si un phonème est une voyelle"""
    voyelles = {'a', 'e', 'i', 'o', 'u', 'y', 'ø', 'œ', 'ə', 'ɛ', 'ɔ', 'ɑ', 
                'ɛ̃', 'ɑ̃', 'ɔ̃', 'œ̃', 'ɥ', 'w', 'j'}
    # Gérer les voyelles nasales qui peuvent avoir un tilde
    return phoneme in voyelles or phoneme.rstrip('̃') in voyelles

def extraire_phonemes(transcription):
    """Extrait les phonèmes individuels en tenant compte des caractères spéciaux"""
    phonemes = []
    i = 0
    while i < len(transcription):
        # Gérer les voyelles nasales (comme ɑ̃)
        if i + 1 < len(transcription) and transcription[i+1] == '̃':
            phonemes.append(transcription[i:i+2])
            i += 2
        else:
            if transcription[i] != ' ':
                phonemes.append(transcription[i])
            i += 1
    return phonemes

def extraire_syllabes(transcription):
    """Extrait les syllabes d'une transcription phonétique"""
    # Séparer en mots
    mots = transcription.split()
    syllabes = []
    
    for mot in mots:
        phonemes = extraire_phonemes(mot)
        syllabe_courante = []
        
        i = 0
        while i < len(phonemes):
            # Si c'est une voyelle
            if est_voyelle(phonemes[i]):
                # Ajouter la voyelle à la syllabe courante
                syllabe_courante.append(phonemes[i])
                i += 1
                
                # Vérifier si une consonne suit
                if i < len(phonemes) and est_consonne(phonemes[i]):
                    # Si c'est la dernière consonne du mot, l'ajouter à la syllabe courante
                    if i == len(phonemes) - 1:
                        syllabe_courante.append(phonemes[i])
                        i += 1
                    # Sinon, vérifier si une voyelle suit
                    elif i + 1 < len(phonemes) and est_voyelle(phonemes[i + 1]):
                        # La consonne appartient à la syllabe suivante
                        break
                    else:
                        # La consonne appartient à la syllabe courante
                        syllabe_courante.append(phonemes[i])
                        i += 1
                
                # Ajouter la syllabe complète à la liste
                if syllabe_courante:
                    syllabes.append(''.join(syllabe_courante))
                    syllabe_courante = []
            
            # Si c'est une consonne
            elif est_consonne(phonemes[i]):
                # Si c'est la première consonne d'une syllabe
                if not syllabe_courante:
                    syllabe_courante.append(phonemes[i])
                i += 1
    
    return syllabes

def grouper_phonemes(transcription):
    """Groupe les phonèmes selon les règles CV avec _ pour les phonèmes isolés"""
    # Séparer en mots
    mots = transcription.split()
    resultat = []
    
    for mot in mots:
        phonemes = extraire_phonemes(mot)
        i = 0
        while i < len(phonemes):
            # Si c'est une consonne
            if est_consonne(phonemes[i]):
                # Vérifier si une voyelle suit
                if i + 1 < len(phonemes) and est_voyelle(phonemes[i+1]):
                    # Cas CV
                    resultat.append(phonemes[i] + phonemes[i+1])
                    i += 2
                else:
                    # Consonne seule
                    resultat.append(phonemes[i] + "_")
                    i += 1
            # Si c'est une voyelle
            elif est_voyelle(phonemes[i]):
                # Si c'est une voyelle seule (pas de consonne avant)
                if i == 0 or not est_consonne(phonemes[i-1]):
                    resultat.append("_" + phonemes[i])
                i += 1
    
    return resultat

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/transcrire', methods=['POST'])
def transcrire_route():
    try:
        # Vérifier le Content-Type
        if not request.is_json:
            print("[ERREUR] Content-Type incorrect")
            return jsonify({'error': 'Content-Type doit être application/json'}), 415
            
        data = request.get_json()
        if not data:
            print("[ERREUR] Corps de requête vide")
            return jsonify({'error': 'Corps de requête vide'}), 400
            
        if 'texte' not in data:
            print("[ERREUR] Champ 'texte' manquant")
            return jsonify({'error': "Le champ 'texte' est requis"}), 400
            
        texte = data['texte']
        if not isinstance(texte, str):
            print("[ERREUR] Le champ 'texte' doit être une chaîne")
            return jsonify({'error': "Le champ 'texte' doit être une chaîne de caractères"}), 400
            
        if not texte.strip():
            print("[ERREUR] Texte vide")
            return jsonify({'error': 'Le texte ne peut pas être vide'}), 400
            
        print(f"\n[REQUÊTE] Nouvelle requête de transcription reçue: '{texte}'")
        
        transcription = transcrire_texte(texte)
        if not transcription:
            print("[ERREUR] Échec de la transcription")
            return jsonify({'error': 'Échec de la transcription'}), 500
            
        reponse = {
            'transcription': transcription,
            'texte_original': texte
        }
        print(f"[RÉPONSE] Envoi de la réponse: {reponse}")
        return jsonify(reponse)
        
    except json.JSONDecodeError:
        print("[ERREUR] JSON invalide")
        return jsonify({'error': 'JSON invalide'}), 400
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors du traitement: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configuration du serveur
    port = int(os.environ.get("PORT", 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port) 