"""
Exemple d'utilisation du système Mix-Play.

Cet exemple montre comment utiliser le MixPlayer pour composer
la phrase demandée: "Avec tous l'amour du monde le bonheur nous rempli de la vie elle-même"
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def main():
    """Exemple d'utilisation du Mix-Play."""
    
    print("🎵 Exemple Mix-Play - Composition de phrase")
    print("=" * 50)
    
    # Phrase à composer (comme demandée dans la description)
    target_sentence = "Avec tous l'amour du monde le bonheur nous rempli de la vie elle-même"
    
    print(f"📝 Phrase à composer: {target_sentence}")
    print()
    
    # Initialiser le MixPlayer
    print("🚀 Initialisation du Mix-Player...")
    mix_player = MixPlayer()
    
    try:
        # Charger les transcriptions
        mix_player.load_transcriptions()
        
        # Afficher quelques statistiques
        stats = mix_player.get_word_statistics()
        print(f"📊 {stats['total_words']:,} mots chargés depuis {len(stats['files'])} fichiers")
        print()
        
        # Découper la phrase en mots
        words = target_sentence.split()
        print(f"🔤 Mots à rechercher ({len(words)}): {words}")
        print()
        
        # Analyser la disponibilité de chaque mot
        print("🔍 ANALYSE DE DISPONIBILITÉ:")
        print("-" * 30)
        
        available_words = []
        missing_words = []
        
        for word in words:
            matches = mix_player.search_word(word, max_results=3)
            if matches:
                available_words.append(word)
                best_match = matches[0]
                print(f"✅ '{word}' -> '{best_match.word}' ({best_match.speaker}, confiance: {best_match.confidence:.2%})")
            else:
                missing_words.append(word)
                print(f"❌ '{word}' -> Aucune correspondance trouvée")
        
        print(f"\n📈 Résultat: {len(available_words)}/{len(words)} mots disponibles")
        
        if missing_words:
            print(f"⚠️  Mots manquants: {', '.join(missing_words)}")
        
        print()
        
        # Composer la phrase avec différentes stratégies
        print("🎭 COMPOSITION AVEC DIFFÉRENTES STRATÉGIES:")
        print("-" * 45)
        
        # Stratégie 1: Meilleure qualité (confiance élevée)
        print("1️⃣  Stratégie 'Haute qualité' (confiance > 70%)")
        composed_hq = mix_player.compose_sentence(
            words=words,
            min_confidence=0.7
        )
        print(f"   📝 Résultat: {composed_hq.text}")
        print(f"   ⏱️  Durée: {composed_hq.total_duration:.2f}s")
        print(f"   🎭 Intervenants: {', '.join(composed_hq.speakers_used)}")
        print(f"   🔤 Mots trouvés: {len(composed_hq.words)}/{len(words)}")
        print()
        
        # Stratégie 2: Maximiser les mots trouvés (confiance plus basse)
        print("2️⃣  Stratégie 'Maximum de mots' (confiance > 40%)")
        composed_max = mix_player.compose_sentence(
            words=words,
            min_confidence=0.4
        )
        print(f"   📝 Résultat: {composed_max.text}")
        print(f"   ⏱️  Durée: {composed_max.total_duration:.2f}s")
        print(f"   🎭 Intervenants: {', '.join(composed_max.speakers_used)}")
        print(f"   🔤 Mots trouvés: {len(composed_max.words)}/{len(words)}")
        print()
        
        # Générer l'audio pour la meilleure composition
        best_composition = composed_max if len(composed_max.words) > len(composed_hq.words) else composed_hq
        
        print(f"🎬 GÉNÉRATION DE L'AUDIO (stratégie sélectionnée: {'Maximum' if best_composition == composed_max else 'Haute qualité'})")
        print("-" * 40)
        
        # Créer le nom de fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output_mix_play")
        audio_file = output_dir / f"exemple_phrase_{timestamp}.mp3"
        info_file = output_dir / f"exemple_phrase_{timestamp}_info.json"
        
        # Générer l'audio
        generated_audio = mix_player.generate_mixed_audio(
            best_composition,
            str(audio_file),
            gap_duration=0.2,  # Silence plus court pour un rendu plus naturel
            crossfade_duration=30  # Crossfade léger
        )
        
        # Exporter les informations
        info_exported = mix_player.export_composed_sentence_info(
            best_composition, 
            str(info_file)
        )
        
        print()
        print("🎉 EXEMPLE TERMINÉ AVEC SUCCÈS !")
        print("=" * 30)
        print(f"🎵 Fichier audio généré: {generated_audio}")
        print(f"📄 Informations détaillées: {info_exported}")
        print(f"📊 Phrase finale: {best_composition.text}")
        print()
        print("💡 Conseils pour améliorer les résultats:")
        print("   • Utilisez des mots plus courts et courants")
        print("   • Essayez des variantes (singulier/pluriel, masculin/féminin)")
        print("   • Préférez les mots avec une haute fréquence d'apparition")
        
        if missing_words:
            print(f"\n🔍 Mots à rechercher manuellement: {', '.join(missing_words)}")
            print("   • Vérifiez les variations orthographiques")
            print("   • Essayez des synonymes")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()