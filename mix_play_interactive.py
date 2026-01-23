"""
Interface interactive pour composer des phrases avec le système Mix-Play.

Cette interface permet de :
- Charger les transcriptions et afficher les statistiques
- Composer des phrases interactivement
- Prévisualiser les mots trouvés
- Générer l'audio final
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer, ComposedSentence


def print_banner():
    """Affiche la bannière du Mix-Play."""
    print("=" * 60)
    print("🎵 MIX-PLAY - Compositeur de phrases audio")
    print("=" * 60)
    print()


def print_statistics(mix_player: MixPlayer):
    """Affiche les statistiques des transcriptions chargées."""
    stats = mix_player.get_word_statistics()
    
    print("📊 STATISTIQUES DES TRANSCRIPTIONS")
    print("-" * 40)
    print(f"• Mots totaux indexés: {stats['total_words']:,}")
    print(f"• Mots uniques: {stats['unique_words']:,}")
    print(f"• Confiance moyenne: {stats['average_confidence']:.2%}")
    print()
    
    print("🎭 INTERVENANTS:")
    for speaker, count in sorted(stats['speakers'].items()):
        print(f"  • {speaker}: {count:,} mots")
    print()
    
    print("📁 FICHIERS:")
    for file_name, count in sorted(stats['files'].items()):
        print(f"  • {Path(file_name).stem}: {count:,} mots")
    print()
    
    print("🔤 MOTS LES PLUS FRÉQUENTS:")
    for word, count in stats['most_common_words'][:10]:
        print(f"  • '{word}': {count} occurrences")
    print()


def preview_word_matches(mix_player: MixPlayer, word: str, max_results: int = 5):
    """Prévisualise les correspondances trouvées pour un mot."""
    matches = mix_player.search_word(word, max_results=max_results)
    
    if not matches:
        print(f"❌ Aucune correspondance trouvée pour '{word}'")
        return
    
    print(f"🔍 CORRESPONDANCES POUR '{word}' ({len(matches)} trouvées):")
    print("-" * 50)
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. '{match.word}' [{match.speaker}]")
        print(f"   📁 {Path(match.file_name).stem}")
        print(f"   ⏱️  {match.start:.2f}s - {match.end:.2f}s ({match.duration:.2f}s)")
        print(f"   🎯 Confiance: {match.confidence:.2%}")
        print()


def compose_sentence_interactive(mix_player: MixPlayer) -> Optional[ComposedSentence]:
    """Interface interactive pour composer une phrase."""
    print("✍️  COMPOSITION DE PHRASE")
    print("-" * 30)
    
    # Demander la phrase à composer
    while True:
        sentence_text = input("Entrez la phrase à composer (ou 'quit' pour annuler): ").strip()
        
        if sentence_text.lower() == 'quit':
            return None
        
        if sentence_text:
            break
        
        print("⚠️  Veuillez entrer une phrase non vide.")
    
    # Découper en mots
    words = sentence_text.split()
    print(f"🔤 Mots à rechercher: {words}")
    print()
    
    # Options avancées
    print("⚙️  OPTIONS AVANCÉES (appuyez sur Entrée pour les valeurs par défaut)")
    
    # Intervenants préférés
    speakers_input = input("Intervenants préférés (séparés par des virgules, optionnel): ").strip()
    preferred_speakers = [s.strip() for s in speakers_input.split(',')] if speakers_input else None
    
    # Confiance minimum
    confidence_input = input("Confiance minimum (0.0-1.0, défaut: 0.5): ").strip()
    try:
        min_confidence = float(confidence_input) if confidence_input else 0.5
        min_confidence = max(0.0, min(1.0, min_confidence))
    except ValueError:
        min_confidence = 0.5
    
    print(f"🎯 Configuration: confiance min = {min_confidence:.2f}")
    if preferred_speakers:
        print(f"🎭 Intervenants préférés: {', '.join(preferred_speakers)}")
    print()
    
    # Prévisualiser les correspondances
    preview = input("Prévisualiser les correspondances pour chaque mot ? (o/N): ").strip().lower()
    
    if preview in ['o', 'oui', 'y', 'yes']:
        for word in words:
            preview_word_matches(mix_player, word)
            input("Appuyez sur Entrée pour continuer...")
            print()
    
    # Composer la phrase
    print("🎵 Composition en cours...")
    composed = mix_player.compose_sentence(
        words=words,
        preferred_speakers=preferred_speakers,
        min_confidence=min_confidence
    )
    
    # Afficher le résultat
    print("✅ PHRASE COMPOSÉE")
    print("-" * 20)
    print(f"📝 Texte: {composed.text}")
    print(f"⏱️  Durée totale: {composed.total_duration:.2f}s")
    print(f"🎭 Intervenants utilisés: {', '.join(composed.speakers_used)}")
    print(f"📁 Fichiers utilisés: {', '.join(Path(f).stem for f in composed.files_used)}")
    print(f"🔤 Mots trouvés: {len(composed.words)}/{len(words)}")
    print()
    
    if len(composed.words) < len(words):
        missing = len(words) - len(composed.words)
        print(f"⚠️  {missing} mot(s) non trouvé(s) avec les critères spécifiés.")
        print()
    
    return composed


def generate_audio_interactive(mix_player: MixPlayer, composed: ComposedSentence) -> Optional[str]:
    """Interface interactive pour générer l'audio final."""
    print("🎬 GÉNÉRATION DE L'AUDIO")
    print("-" * 25)
    
    # Nom de fichier par défaut
    safe_text = "".join(c if c.isalnum() or c.isspace() else "" for c in composed.text)
    safe_text = "_".join(safe_text.split()[:5])  # Premiers 5 mots
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"mix_play_{safe_text}_{timestamp}"
    
    # Demander le nom de fichier
    filename = input(f"Nom du fichier (sans extension, défaut: {default_name}): ").strip()
    if not filename:
        filename = default_name
    
    # Options audio
    print("\n⚙️  OPTIONS AUDIO")
    gap_input = input("Durée du silence entre mots en secondes (défaut: 0.3): ").strip()
    try:
        gap_duration = float(gap_input) if gap_input else 0.3
        gap_duration = max(0.0, min(2.0, gap_duration))
    except ValueError:
        gap_duration = 0.3
    
    crossfade_input = input("Durée du crossfade en ms (défaut: 50): ").strip()
    try:
        crossfade = int(crossfade_input) if crossfade_input else 50
        crossfade = max(0, min(500, crossfade))
    except ValueError:
        crossfade = 50
    
    # Chemins de sortie
    output_dir = Path("output_mix_play")
    audio_path = output_dir / f"{filename}.mp3"
    info_path = output_dir / f"{filename}_info.json"
    
    print(f"\n🎵 Génération de l'audio avec les paramètres:")
    print(f"  • Silence entre mots: {gap_duration}s")
    print(f"  • Crossfade: {crossfade}ms")
    print(f"  • Fichier de sortie: {audio_path}")
    
    try:
        # Générer l'audio
        audio_file = mix_player.generate_mixed_audio(
            composed,
            str(audio_path),
            gap_duration=gap_duration,
            crossfade_duration=crossfade
        )
        
        # Exporter les informations détaillées
        info_file = mix_player.export_composed_sentence_info(composed, str(info_path))
        
        print(f"\n🎉 GÉNÉRATION TERMINÉE !")
        print(f"🎵 Audio: {audio_file}")
        print(f"📄 Informations: {info_file}")
        
        return audio_file
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")
        return None


def main():
    """Fonction principale de l'interface interactive."""
    print_banner()
    
    # Initialiser le MixPlayer
    print("🚀 Initialisation du Mix-Player...")
    try:
        mix_player = MixPlayer()
        mix_player.load_transcriptions()
    except Exception as e:
        print(f"❌ Erreur lors du chargement des transcriptions: {e}")
        return
    
    print()
    print_statistics(mix_player)
    
    # Boucle principale
    while True:
        print("🎛️  MENU PRINCIPAL")
        print("-" * 20)
        print("1. Composer une nouvelle phrase")
        print("2. Rechercher un mot spécifique")
        print("3. Afficher les statistiques")
        print("4. Quitter")
        print()
        
        choice = input("Votre choix (1-4): ").strip()
        print()
        
        if choice == '1':
            # Composer une phrase
            composed = compose_sentence_interactive(mix_player)
            if composed:
                generate_audio = input("Générer l'audio maintenant ? (O/n): ").strip().lower()
                if generate_audio not in ['n', 'non', 'no']:
                    audio_file = generate_audio_interactive(mix_player, composed)
                    if audio_file:
                        print(f"💡 Vous pouvez maintenant écouter: {audio_file}")
        
        elif choice == '2':
            # Rechercher un mot
            word = input("Mot à rechercher: ").strip()
            if word:
                preview_word_matches(mix_player, word, max_results=10)
        
        elif choice == '3':
            # Afficher les statistiques
            print_statistics(mix_player)
        
        elif choice == '4':
            # Quitter
            print("👋 À bientôt !")
            break
        
        else:
            print("❌ Choix invalide, veuillez réessayer.")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()