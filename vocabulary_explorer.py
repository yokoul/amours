"""
Utilitaire d'exploration du vocabulaire Mix-Play.

Cet outil permet d'explorer les mots disponibles dans les transcriptions,
de rechercher des alternatives, et de préparer des phrases optimisées.
"""

import sys
from pathlib import Path
from collections import Counter
import difflib

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def explore_similar_words(mix_player: MixPlayer, target_word: str, max_suggestions: int = 10):
    """Explore les mots similaires disponibles."""
    cleaned_target = mix_player.clean_word(target_word)
    
    # Recherche de mots similaires
    all_words = list(mix_player.word_index.keys())
    similar = difflib.get_close_matches(
        cleaned_target, 
        all_words, 
        n=max_suggestions,
        cutoff=0.4
    )
    
    print(f"🔍 MOTS SIMILAIRES À '{target_word}':")
    print("-" * 40)
    
    if not similar:
        print("❌ Aucun mot similaire trouvé")
        return
    
    for word in similar:
        matches = mix_player.word_index[word]
        best_match = max(matches, key=lambda x: x.confidence)
        speakers = set(m.speaker for m in matches)
        
        print(f"• '{best_match.word}' ({len(matches)} occurrences)")
        print(f"  🎭 Intervenants: {', '.join(sorted(speakers))}")
        print(f"  🎯 Meilleure confiance: {best_match.confidence:.2%}")
        print(f"  📁 Exemple: {Path(best_match.file_name).stem}")
        print()


def analyze_sentence_feasibility(mix_player: MixPlayer, sentence: str):
    """Analyse la faisabilité d'une phrase et propose des alternatives."""
    words = sentence.split()
    
    print(f"📝 ANALYSE DE FAISABILITÉ: {sentence}")
    print("=" * 60)
    
    available = []
    missing = []
    alternatives = {}
    
    for word in words:
        matches = mix_player.search_word(word, max_results=1)
        
        if matches:
            available.append(word)
            print(f"✅ '{word}' -> '{matches[0].word}' ({matches[0].confidence:.1%})")
        else:
            missing.append(word)
            print(f"❌ '{word}' -> Non trouvé")
            
            # Chercher des alternatives
            cleaned = mix_player.clean_word(word)
            similar = difflib.get_close_matches(
                cleaned, 
                mix_player.word_index.keys(), 
                n=3, 
                cutoff=0.5
            )
            
            if similar:
                alternatives[word] = []
                for sim_word in similar:
                    best_match = max(mix_player.word_index[sim_word], key=lambda x: x.confidence)
                    alternatives[word].append((best_match.word.strip(), best_match.confidence))
    
    print(f"\n📊 RÉSUMÉ: {len(available)}/{len(words)} mots disponibles")
    
    if missing:
        print(f"\n🔍 ALTERNATIVES POSSIBLES:")
        print("-" * 30)
        
        for word in missing:
            if word in alternatives:
                print(f"'{word}' pourrait être remplacé par:")
                for alt_word, confidence in alternatives[word]:
                    print(f"  • '{alt_word}' (confiance: {confidence:.1%})")
            else:
                print(f"'{word}': Aucune alternative trouvée")
            print()


def suggest_optimized_phrases():
    """Propose des phrases optimisées basées sur le vocabulaire disponible."""
    
    suggestions = [
        "avec tout mon amour du monde",
        "le bonheur de la vie nous donne",
        "amour et bonheur dans la vie",
        "tous les moments de bonheur",
        "la vie nous donne de la joie",
        "avec amour nous vivons ensemble",
        "le monde est plein de bonheur",
        "dans la vie il y a l'amour"
    ]
    
    print("💡 PHRASES SUGGÉRÉES (optimisées pour le vocabulaire disponible):")
    print("=" * 65)
    
    for i, phrase in enumerate(suggestions, 1):
        print(f"{i}. {phrase}")
    
    return suggestions


def main():
    """Fonction principale d'exploration."""
    
    print("🔍 Mix-Play - Explorateur de Vocabulaire")
    print("=" * 45)
    
    # Initialiser le MixPlayer
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Menu interactif
    while True:
        print("\n🎛️  MENU D'EXPLORATION")
        print("-" * 25)
        print("1. Analyser une phrase")
        print("2. Rechercher des mots similaires")
        print("3. Phrases suggérées")
        print("4. Statistiques détaillées")
        print("5. Quitter")
        
        choice = input("\nVotre choix (1-5): ").strip()
        
        if choice == '1':
            sentence = input("\nEntrez une phrase à analyser: ").strip()
            if sentence:
                print()
                analyze_sentence_feasibility(mix_player, sentence)
        
        elif choice == '2':
            word = input("\nMot à explorer: ").strip()
            if word:
                print()
                explore_similar_words(mix_player, word)
        
        elif choice == '3':
            print()
            suggestions = suggest_optimized_phrases()
            print("\n💡 Vous pouvez tester ces phrases avec l'interface Mix-Play principale !")
        
        elif choice == '4':
            print()
            stats = mix_player.get_word_statistics()
            
            print("📊 STATISTIQUES DÉTAILLÉES")
            print("-" * 30)
            print(f"• Total de mots: {stats['total_words']:,}")
            print(f"• Mots uniques: {stats['unique_words']:,}")
            print(f"• Confiance moyenne: {stats['average_confidence']:.2%}")
            
            print(f"\n🎭 Distribution par intervenant:")
            for speaker, count in sorted(stats['speakers'].items()):
                percentage = (count / stats['total_words']) * 100
                print(f"  • {speaker}: {count:,} mots ({percentage:.1f}%)")
            
            print(f"\n🔤 Top 15 mots les plus fréquents:")
            for word, count in stats['most_common_words'][:15]:
                print(f"  • '{word}': {count} occurrences")
        
        elif choice == '5':
            print("\n👋 Exploration terminée !")
            break
        
        else:
            print("\n❌ Choix invalide")


if __name__ == "__main__":
    main()