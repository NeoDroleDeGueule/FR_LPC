import tkinter as tk
from tkinter import ttk, scrolledtext
from wiki_api import WikiAPI

class WikiInterface:
    def __init__(self):
        self.wiki = WikiAPI()
        
        # Dictionnaire de correspondances phonétiques simples
        self.phonemes = {
            'a': 'a', 'à': 'a', 'â': 'a',
            'e': 'ə', 'é': 'e', 'è': 'ɛ', 'ê': 'ɛ',
            'i': 'i', 'î': 'i',
            'o': 'ɔ', 'ô': 'o',
            'u': 'y', 'û': 'y',
            'ou': 'u',
            'an': 'ɑ̃', 'en': 'ɑ̃',
            'in': 'ɛ̃', 'ain': 'ɛ̃', 'ein': 'ɛ̃',
            'on': 'ɔ̃',
            'ch': 'ʃ',
            'gn': 'ɲ',
            'ng': 'ŋ',
            'ph': 'f',
            'th': 't',
            'qu': 'k',
            'gu': 'g'
        }
        
        self.fenetre = tk.Tk()
        self.fenetre.title("MediaWiki - Transcription Phonétique")
        self.fenetre.geometry("1000x800")
        
        # Style
        self.fenetre.configure(bg='#f0f0f0')
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0')
        
        # Frame principal
        main_frame = ttk.Frame(self.fenetre, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Zone de recherche MediaWiki
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Titre de la page MediaWiki :").pack(anchor=tk.W)
        self.page_entry = ttk.Entry(search_frame, width=50)
        self.page_entry.pack(side=tk.LEFT, padx=(0, 10), pady=(5, 5))
        self.page_entry.bind('<Return>', lambda e: self.charger_et_transcrire())
        
        charger_button = ttk.Button(search_frame, text="Charger et Transcrire", command=self.charger_et_transcrire)
        charger_button.pack(side=tk.LEFT)
        
        # Zone de contenu MediaWiki
        ttk.Label(main_frame, text="Contenu de la page :").pack(anchor=tk.W)
        self.contenu_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.contenu_text.pack(fill=tk.X, pady=(5, 10))
        
        # Zone de transcription phonétique
        ttk.Label(main_frame, text="Transcription phonétique :").pack(anchor=tk.W)
        self.phonemes_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.phonemes_text.pack(fill=tk.BOTH, expand=True)
    
    def charger_et_transcrire(self):
        titre = self.page_entry.get()
        if titre:
            try:
                # Charger le contenu
                contenu = self.wiki.obtenir_contenu_brut(titre)
                if contenu:
                    # Afficher le contenu original
                    self.contenu_text.delete("1.0", tk.END)
                    self.contenu_text.insert(tk.END, contenu)
                    
                    # Transcrire le contenu
                    transcription = contenu.lower()
                    for pattern, phoneme in sorted(self.phonemes.items(), key=lambda x: len(x[0]), reverse=True):
                        transcription = transcription.replace(pattern, phoneme)
                    
                    # Afficher la transcription
                    self.phonemes_text.delete("1.0", tk.END)
                    self.phonemes_text.insert(tk.END, f"[{transcription}]")
                else:
                    self.contenu_text.delete("1.0", tk.END)
                    self.contenu_text.insert(tk.END, "Page non trouvée")
                    self.phonemes_text.delete("1.0", tk.END)
            except Exception as e:
                self.contenu_text.delete("1.0", tk.END)
                self.contenu_text.insert(tk.END, f"Erreur lors du chargement : {str(e)}")
                self.phonemes_text.delete("1.0", tk.END)
    
    def lancer(self):
        self.fenetre.mainloop()

if __name__ == "__main__":
    app = WikiInterface()
    app.lancer() 