from app import transcrire_texte

mots_test = [
    "aujourd'hui",
    "bonjour",
    "c'est",
    "ordinateur",
    "université",
    "français"
]

print("Test des transcriptions :")
print("-" * 40)
for mot in mots_test:
    transcription = transcrire_texte(mot)
    print(f"{mot:15} : {transcription}")
print("-" * 40) 