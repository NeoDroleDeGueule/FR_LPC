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
        # Utiliser l'API de Wiktionary
        url = f"https://fr.wiktionary.org/api/rest_v1/page/definition/{mot}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Chercher la prononciation dans les données
            for entry in data.get('items', []):
                if 'pronunciations' in entry:
                    for pron in entry['pronunciations']:
                        if 'ipa' in pron:
                            return pron['ipa'].strip('/')
        return None
    except Exception as e:
        print(f"Erreur Wiktionary : {str(e)}")
        return None

def transcrire_texte(texte):
    """Transcrit le texte en utilisant Wiktionary ou le système de fallback"""
    mots = texte.split()
    resultat = []
    
    for mot in mots:
        # Essayer d'abord avec Wiktionary
        prononciation = obtenir_prononciation_wiktionary(mot.lower())
        if prononciation:
            resultat.append(prononciation)
        else:
            # Utiliser notre système de transcription comme fallback
            resultat.append(transcrire(mot))
    
    return ' '.join(resultat)

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/api/transcrire', methods=['POST'])
def api_transcrire():
    data = request.get_json()
    texte = data.get('texte', '')
    transcription = transcrire_texte(texte)
    return jsonify({'transcription': transcription})

if __name__ == '__main__':
    app.run(debug=True) 