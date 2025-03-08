from flask import Flask, render_template, request, jsonify
import subprocess
import os
import tempfile
import requests
import re

app = Flask(__name__)

# Dictionnaire de correspondances phonétiques amélioré
PHONEMES = {
    # Voyelles composées (à traiter en premier)
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

def transcrire(texte):
    """Transcrit le texte en phonèmes avec une logique améliorée"""
    texte = texte.lower()
    
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
    """Obtient la prononciation depuis l'API de Wiktionary"""
    try:
        print(f"Tentative d'obtention de la prononciation pour le mot : {mot}")
        # Utiliser l'API MediaWiki de Wiktionary
        url = "https://fr.wiktionary.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts',
            'titles': mot,
            'explaintext': True,
            'formatversion': 2
        }
        print(f"Appel API avec paramètres : {params}")
        
        response = requests.get(url, params=params, timeout=30)
        print(f"Code de réponse : {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Données reçues : {data}")
            
            # Extraire la prononciation du contenu
            if 'query' in data and 'pages' in data['query']:
                for page in data['query']['pages']:
                    if 'extract' in page:
                        extract = page['extract']
                        # Chercher la prononciation IPA
                        match = re.search(r'\\(.*?\\)', extract)
                        if match:
                            prononciation = match.group(1)
                            print(f"Prononciation trouvée : {prononciation}")
                            return prononciation
            
            print("Aucune prononciation trouvée dans les données")
        return None
    except Exception as e:
        print(f"Erreur détaillée lors de l'appel API : {str(e)}")
        return None

def transcrire_texte(texte):
    """Transcrit le texte en utilisant Wiktionary ou le système de fallback"""
    print(f"Transcription du texte : {texte}")
    mots = texte.split()
    resultat = []
    
    for mot in mots:
        print(f"Traitement du mot : {mot}")
        # Essayer d'abord avec Wiktionary
        prononciation = obtenir_prononciation_wiktionary(mot.lower())
        if prononciation:
            print(f"Prononciation Wiktionary trouvée : {prononciation}")
            resultat.append(prononciation)
        else:
            print(f"Utilisation du système local pour : {mot}")
            transcription_locale = transcrire(mot)
            print(f"Transcription locale : {transcription_locale}")
            resultat.append(transcription_locale)
    
    resultat_final = ' '.join(resultat)
    print(f"Résultat final de la transcription : {resultat_final}")
    return resultat_final

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

@app.route('/api/transcrire', methods=['POST'])
def api_transcrire():
    print("\n=== Nouvelle requête de transcription ===")
    try:
        data = request.get_json()
        print(f"Données reçues : {data}")
        
        if not data or 'texte' not in data:
            print("Erreur: Aucun texte fourni")
            return jsonify({'error': 'Aucun texte fourni'}), 400
            
        texte = data['texte']
        print(f"Texte à transcrire : {texte}")
        
        # Transcription directe
        transcription = transcrire_texte(texte)
        print(f"Transcription obtenue : {transcription}")
        
        # Groupement des phonèmes
        paires = grouper_phonemes(transcription)
        print(f"Paires obtenues : {paires}")
        
        # Préparation de la réponse
        reponse = {
            'transcription': transcription,
            'paires': paires
        }
        print(f"Réponse complète : {reponse}")
        
        return jsonify(reponse)
        
    except Exception as e:
        print(f"Erreur lors de la transcription : {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 