#!/usr/bin/env python3
"""
Extrait tous les mots uniques des transcriptions audio
pour construire une liste de mots disponibles.
"""

import json
import re
from pathlib import Path
from collections import Counter

def extract_words_from_transcriptions():
    """Extrait tous les mots des fichiers de transcription."""
    transcription_dir = Path("output_transcription")
    all_words = []
    
    # Parcourir tous les fichiers JSON
    for json_file in transcription_dir.glob("*_complete.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extraire les segments de transcription
            transcription = data.get('transcription', {})
            segments = transcription.get('segments', [])
            
            for segment in segments:
                # Extraire les mots individuels avec leurs timestamps
                words_list = segment.get('words', [])
                for word_obj in words_list:
                    word = word_obj.get('word', '').strip().lower()
                    # Nettoyer et valider
                    word = re.sub(r'[^\w\sàâäéèêëïîôùûüÿæœç-]', '', word)
                    if word and len(word) > 1:
                        all_words.append(word)
                
        except Exception as e:
            print(f"Erreur avec {json_file.name}: {e}")
            continue
    
    return all_words

def filter_love_themed_words(words, min_length=4, min_frequency=3):
    """Filtre les mots par thème d'amour et fréquence."""
    
    # Mots-clés liés à l'amour (pour filtrage thématique)
    love_themes = {
        'émotions': ['amour', 'passion', 'désir', 'tendresse', 'émotion', 'sentiment', 
                     'joie', 'bonheur', 'tristesse', 'mélancolie', 'nostalgie', 'espoir',
                     'peur', 'angoisse', 'jalousie', 'colère', 'rage', 'haine'],
        'physique': ['cœur', 'corps', 'main', 'regard', 'yeux', 'voix', 'sourire',
                     'baiser', 'caresse', 'étreinte', 'toucher', 'peau', 'lèvre',
                     'visage', 'cheveux', 'sang', 'larme', 'soupir', 'frisson'],
        'relations': ['amant', 'amante', 'couple', 'famille', 'enfant', 'mère', 'père',
                      'frère', 'sœur', 'ami', 'amitié', 'rencontre', 'séparation',
                      'union', 'mariage', 'divorce', 'trahison', 'fidélité'],
        'temporalité': ['instant', 'moment', 'temps', 'éternité', 'toujours', 'jamais',
                        'hier', 'demain', 'attente', 'souvenir', 'mémoire', 'passé',
                        'présent', 'avenir', 'futur'],
        'spatialité': ['lieu', 'maison', 'chambre', 'lit', 'jardin', 'rue', 'ville',
                       'mer', 'ciel', 'terre', 'horizon', 'distance', 'absence', 'présence'],
        'abstractions': ['âme', 'esprit', 'pensée', 'rêve', 'songe', 'désir', 'envie',
                         'besoin', 'manque', 'vide', 'plein', 'vie', 'mort', 'destin'],
        'intensité': ['fort', 'faible', 'grand', 'petit', 'profond', 'léger', 'lourd',
                      'doux', 'dur', 'chaud', 'froid', 'brûlant', 'glacé'],
        'mouvement': ['venir', 'partir', 'rester', 'fuir', 'suivre', 'tomber', 'lever',
                      'courir', 'marcher', 'danser', 'voler', 'glisser'],
        'parole': ['dire', 'parler', 'mots', 'silence', 'cri', 'chant', 'voix',
                   'murmure', 'aveu', 'secret', 'promesse', 'serment', 'mensonge'],
        'sens': ['voir', 'regarder', 'entendre', 'écouter', 'sentir', 'toucher',
                 'goûter', 'parfum', 'odeur', 'saveur', 'lumière', 'ombre', 'couleur']
    }
    
    # Rassembler tous les mots thématiques
    all_love_words = set()
    for category in love_themes.values():
        all_love_words.update(category)
    
    # Compter les fréquences
    word_counts = Counter(words)
    
    # Filtrer : mots assez longs, fréquents, et thématiquement pertinents
    filtered = []
    for word, count in word_counts.items():
        if (len(word) >= min_length and 
            count >= min_frequency and
            (word in all_love_words or any(theme in word for theme in ['amour', 'aimer', 'cœur', 'vie', 'mort']))):
            filtered.append((word, count))
    
    # Trier par fréquence décroissante
    filtered.sort(key=lambda x: x[1], reverse=True)
    
    return filtered

def main():
    print("🔍 Extraction des mots depuis les transcriptions...")
    all_words = extract_words_from_transcriptions()
    print(f"✅ {len(all_words)} mots totaux extraits")
    
    print("\n🎯 Filtrage par thème d'amour...")
    love_words = filter_love_themed_words(all_words)
    print(f"✅ {len(love_words)} mots pertinents trouvés")
    
    print("\n📊 Top 150 mots les plus fréquents :")
    print("-" * 60)
    for word, count in love_words[:150]:
        print(f"{word:20} ({count:4} occurrences)")
    
    # Sauvegarder dans un fichier
    output_file = Path("vocabulary_extracted.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Vocabulaire extrait des transcriptions audio\n")
        f.write(f"# {len(love_words)} mots au total\n\n")
        for word, count in love_words:
            f.write(f"{word}\n")
    
    print(f"\n💾 Liste sauvegardée dans: {output_file}")
    
    # Générer le code JavaScript
    js_words = [word for word, _ in love_words[:150]]
    print("\n📝 Code JavaScript pour poetic-server.js :")
    print("-" * 60)
    print("const loveWords = [")
    for i in range(0, len(js_words), 6):
        batch = js_words[i:i+6]
        print(f"    {', '.join(repr(w) for w in batch)},")
    print("];")

if __name__ == '__main__':
    main()
