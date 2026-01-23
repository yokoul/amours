#!/usr/bin/env python3
"""
Interface interactive pour la transcription et l'analyse d'amour.
Menu principal pour naviguer facilement entre tous les outils.
"""

import os
import sys
from pathlib import Path
import subprocess
from typing import List, Dict, Any

# Couleurs pour l'interface
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Affiche l'en-tête du programme."""
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎙️  SYSTÈME DE TRANSCRIPTION ET ANALYSE D'AMOUR 💕{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print()


def print_menu():
    """Affiche le menu principal."""
    print(f"{Colors.BOLD}{Colors.BLUE}📋 MENU PRINCIPAL{Colors.ENDC}")
    print()
    print(f"{Colors.GREEN}1.{Colors.ENDC} 🎙️  Transcrire un fichier audio (avec intervenants)")
    print(f"{Colors.GREEN}2.{Colors.ENDC} 🔧 Reconstruire des phrases à partir d'une transcription")
    print(f"{Colors.GREEN}3.{Colors.ENDC} 💕 Analyser les types d'amour")
    print(f"{Colors.GREEN}4.{Colors.ENDC} 🚀 Pipeline complet (Transcription → Phrases → Analyse)")
    print()
    print(f"{Colors.YELLOW}5.{Colors.ENDC} 📂 Lister les fichiers audio disponibles")
    print(f"{Colors.YELLOW}6.{Colors.ENDC} 📋 Lister les transcriptions existantes")
    print(f"{Colors.YELLOW}7.{Colors.ENDC} 📊 Comparer les analyses (segments vs phrases)")
    print()
    print(f"{Colors.RED}0.{Colors.ENDC} ❌ Quitter")
    print()


def get_audio_files() -> List[Path]:
    """Retourne la liste des fichiers audio disponibles."""
    audio_dirs = [Path("audio"), Path("audio/audio_bank")]
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma'}
    
    audio_files = []
    for audio_dir in audio_dirs:
        if audio_dir.exists():
            for file in audio_dir.iterdir():
                if file.is_file() and file.suffix.lower() in audio_extensions:
                    audio_files.append(file)
    
    return sorted(audio_files)


def get_transcription_files() -> List[Path]:
    """Retourne la liste des fichiers de transcription disponibles."""
    output_dirs = [
        Path("output"), Path("output_v1"), Path("output_v2"), 
        Path("output_new"), Path("output_sentences")
    ]
    
    transcription_files = []
    for output_dir in output_dirs:
        if output_dir.exists():
            for file in output_dir.glob("*_complete.json"):
                transcription_files.append(file)
            for file in output_dir.glob("*_sentences.json"):
                transcription_files.append(file)
    
    return sorted(transcription_files)


def choose_file(files: List[Path], file_type: str) -> Path:
    """Interface de sélection de fichier."""
    if not files:
        print(f"{Colors.RED}❌ Aucun fichier {file_type} trouvé{Colors.ENDC}")
        return None
    
    print(f"{Colors.BOLD}{Colors.BLUE}📂 Sélectionnez un fichier {file_type} :{Colors.ENDC}")
    print()
    
    for i, file in enumerate(files, 1):
        size = ""
        if file.exists():
            size_mb = file.stat().st_size / (1024 * 1024)
            size = f" ({size_mb:.1f} MB)"
        
        print(f"{Colors.GREEN}{i:2}.{Colors.ENDC} {file.name}{size}")
        print(f"     📁 {file.parent}")
    
    print(f"{Colors.RED} 0.{Colors.ENDC} ← Retour au menu")
    print()
    
    while True:
        try:
            choice = input(f"{Colors.CYAN}Votre choix (0-{len(files)}) : {Colors.ENDC}")
            choice = int(choice)
            
            if choice == 0:
                return None
            elif 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                print(f"{Colors.RED}❌ Choix invalide{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}❌ Veuillez entrer un numéro{Colors.ENDC}")


def get_output_directory(default_name: str) -> str:
    """Demande le dossier de sortie."""
    print(f"{Colors.BOLD}{Colors.BLUE}📂 Dossier de sortie :{Colors.ENDC}")
    output_dir = input(f"{Colors.CYAN}Dossier (défaut: {default_name}) : {Colors.ENDC}").strip()
    return output_dir if output_dir else default_name


def get_formats() -> List[str]:
    """Interface de sélection des formats."""
    available_formats = {
        '1': 'json',
        '2': 'csv', 
        '3': 'srt',
        '4': 'summary',
        '5': 'artistic'
    }
    
    print(f"{Colors.BOLD}{Colors.BLUE}📋 Formats d'export :{Colors.ENDC}")
    print(f"{Colors.GREEN}1.{Colors.ENDC} JSON (données complètes)")
    print(f"{Colors.GREEN}2.{Colors.ENDC} CSV (données tabulaires)")
    print(f"{Colors.GREEN}3.{Colors.ENDC} SRT (sous-titres)")
    print(f"{Colors.GREEN}4.{Colors.ENDC} Summary (résumé textuel)")
    print(f"{Colors.GREEN}5.{Colors.ENDC} Artistic (format créatif)")
    print(f"{Colors.YELLOW}A.{Colors.ENDC} Tous les formats")
    print()
    
    choice = input(f"{Colors.CYAN}Sélection (ex: 1,4 ou A) [défaut: json,summary] : {Colors.ENDC}").strip()
    
    if not choice:
        return ['json', 'summary']
    
    if choice.upper() == 'A':
        return list(available_formats.values())
    
    formats = []
    for c in choice.replace(',', ' ').split():
        if c in available_formats:
            formats.append(available_formats[c])
    
    return formats if formats else ['json', 'summary']


def run_command(cmd: List[str], description: str) -> bool:
    """Exécute une commande avec affichage."""
    print(f"{Colors.BOLD}{Colors.CYAN}🔄 {description}...{Colors.ENDC}")
    print(f"{Colors.YELLOW}Commande : {' '.join(cmd)}{Colors.ENDC}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print()
        print(f"{Colors.GREEN}✅ {description} terminée avec succès !{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"{Colors.RED}❌ Erreur lors de {description.lower()}{Colors.ENDC}")
        return False


def transcribe_audio():
    """Interface pour la transcription audio."""
    print(f"{Colors.HEADER}🎙️  TRANSCRIPTION AUDIO{Colors.ENDC}")
    print()
    
    # Sélection du fichier audio
    audio_files = get_audio_files()
    audio_file = choose_file(audio_files, "audio")
    if not audio_file:
        return
    
    # Paramètres
    output_dir = get_output_directory("output_transcription")
    formats = get_formats()
    
    # Modèle Whisper
    print(f"{Colors.BOLD}{Colors.BLUE}🤖 Modèle Whisper :{Colors.ENDC}")
    print(f"{Colors.GREEN}1.{Colors.ENDC} tiny (rapide, moins précis)")
    print(f"{Colors.GREEN}2.{Colors.ENDC} base (équilibré)")
    print(f"{Colors.GREEN}3.{Colors.ENDC} small (bon compromis)")
    print(f"{Colors.GREEN}4.{Colors.ENDC} medium (recommandé)")
    print(f"{Colors.GREEN}5.{Colors.ENDC} large (le plus précis)")
    
    models = ['tiny', 'base', 'small', 'medium', 'large']
    choice = input(f"{Colors.CYAN}Modèle (1-5) [défaut: 4=medium] : {Colors.ENDC}").strip()
    
    try:
        model_idx = int(choice) - 1 if choice else 3
        model = models[model_idx] if 0 <= model_idx < len(models) else 'medium'
    except ValueError:
        model = 'medium'
    
    # Exécution
    cmd = [
        'python', 'transcribe_audio.py',
        '--input', str(audio_file),
        '--output', output_dir,
        '--formats'] + formats + [
        '--whisper-model', model
    ]
    
    return run_command(cmd, "Transcription audio")


def reconstruct_sentences():
    """Interface pour la reconstruction de phrases."""
    print(f"{Colors.HEADER}🔧 RECONSTRUCTION DE PHRASES{Colors.ENDC}")
    print()
    
    # Sélection du fichier de transcription
    transcription_files = get_transcription_files()
    transcription_file = choose_file(transcription_files, "de transcription")
    if not transcription_file:
        return
    
    # Nom de sortie
    default_output = transcription_file.with_name(transcription_file.stem + "_sentences.json")
    output_name = input(f"{Colors.CYAN}Fichier de sortie [défaut: {default_output.name}] : {Colors.ENDC}").strip()
    output_file = output_name if output_name else str(default_output)
    
    # Exécution
    cmd = [
        'python', 'reconstruct_sentences.py',
        '--input', str(transcription_file),
        '--output', output_file
    ]
    
    return run_command(cmd, "Reconstruction de phrases")


def analyze_love():
    """Interface pour l'analyse d'amour."""
    print(f"{Colors.HEADER}💕 ANALYSE DES TYPES D'AMOUR{Colors.ENDC}")
    print()
    
    # Sélection du fichier de transcription
    transcription_files = get_transcription_files()
    transcription_file = choose_file(transcription_files, "de transcription")
    if not transcription_file:
        return
    
    # Paramètres
    output_dir = get_output_directory("output_love_analysis")
    formats = get_formats()
    
    # Seuil d'analyse
    threshold = input(f"{Colors.CYAN}Seuil d'amour (0.0-1.0) [défaut: 0.15] : {Colors.ENDC}").strip()
    try:
        threshold = float(threshold) if threshold else 0.15
        threshold = max(0.0, min(1.0, threshold))
    except ValueError:
        threshold = 0.15
    
    # Options avancées
    print(f"{Colors.BOLD}{Colors.BLUE}⚙️ Options avancées :{Colors.ENDC}")
    semantic = input(f"{Colors.CYAN}Analyse sémantique (sentence-transformers) ? [O/n] : {Colors.ENDC}").strip().lower()
    use_semantic = semantic != 'n'
    
    # Vérifier si c'est déjà des phrases reconstruites
    is_sentences = "_sentences" in transcription_file.name
    if not is_sentences:
        reconstruct = input(f"{Colors.CYAN}Reconstruire les phrases ? [O/n] : {Colors.ENDC}").strip().lower()
        use_reconstruct = reconstruct != 'n'
    else:
        use_reconstruct = False
        print(f"{Colors.GREEN}ℹ️  Fichier de phrases détecté, reconstruction désactivée{Colors.ENDC}")
    
    # Exécution
    cmd = [
        'python', 'analyze_love.py',
        '--input', str(transcription_file),
        '--output', output_dir,
        '--formats'] + formats + [
        '--threshold', str(threshold)
    ]
    
    if not use_semantic:
        cmd.append('--no-semantic')
    
    if not use_reconstruct:
        cmd.append('--no-reconstruct')
    
    return run_command(cmd, "Analyse des types d'amour")


def full_pipeline():
    """Pipeline complet : transcription → reconstruction → analyse."""
    print(f"{Colors.HEADER}🚀 PIPELINE COMPLET{Colors.ENDC}")
    print()
    
    # Sélection du fichier audio
    audio_files = get_audio_files()
    audio_file = choose_file(audio_files, "audio")
    if not audio_file:
        return
    
    base_name = audio_file.stem
    
    print(f"{Colors.BOLD}{Colors.YELLOW}🔄 Pipeline en 3 étapes :{Colors.ENDC}")
    print(f"1. 🎙️  Transcription : {audio_file.name}")
    print(f"2. 🔧 Reconstruction des phrases")
    print(f"3. 💕 Analyse des types d'amour")
    print()
    
    confirm = input(f"{Colors.CYAN}Lancer le pipeline complet ? [O/n] : {Colors.ENDC}").strip().lower()
    if confirm == 'n':
        return
    
    # Étape 1: Transcription
    print(f"{Colors.HEADER}ÉTAPE 1/3 : TRANSCRIPTION{Colors.ENDC}")
    cmd1 = [
        'python', 'transcribe_audio.py',
        '--input', str(audio_file),
        '--output', 'output_pipeline',
        '--formats', 'json',
        '--whisper-model', 'medium'
    ]
    
    if not run_command(cmd1, "Transcription"):
        return
    
    # Étape 2: Reconstruction
    print(f"{Colors.HEADER}ÉTAPE 2/3 : RECONSTRUCTION{Colors.ENDC}")
    transcription_file = Path(f"output_pipeline/{base_name}_with_speakers_complete.json")
    sentences_file = Path(f"output_pipeline/{base_name}_sentences.json")
    
    cmd2 = [
        'python', 'reconstruct_sentences.py',
        '--input', str(transcription_file),
        '--output', str(sentences_file)
    ]
    
    if not run_command(cmd2, "Reconstruction des phrases"):
        return
    
    # Étape 3: Analyse d'amour
    print(f"{Colors.HEADER}ÉTAPE 3/3 : ANALYSE D'AMOUR{Colors.ENDC}")
    cmd3 = [
        'python', 'analyze_love.py',
        '--input', str(sentences_file),
        '--output', 'output_pipeline',
        '--formats', 'json', 'summary', 'artistic',
        '--threshold', '0.15',
        '--no-reconstruct'
    ]
    
    if run_command(cmd3, "Analyse des types d'amour"):
        print(f"{Colors.GREEN}🎉 Pipeline complet terminé avec succès !{Colors.ENDC}")
        print(f"{Colors.CYAN}📂 Résultats dans : output_pipeline/{Colors.ENDC}")


def list_files():
    """Liste les fichiers disponibles."""
    print(f"{Colors.HEADER}📂 FICHIERS DISPONIBLES{Colors.ENDC}")
    print()
    
    # Fichiers audio
    audio_files = get_audio_files()
    print(f"{Colors.BOLD}{Colors.GREEN}🎙️  FICHIERS AUDIO ({len(audio_files)}){Colors.ENDC}")
    if audio_files:
        for file in audio_files:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   📁 {file.relative_to(Path.cwd())} ({size_mb:.1f} MB)")
    else:
        print(f"   {Colors.YELLOW}Aucun fichier audio trouvé{Colors.ENDC}")
    
    print()
    
    # Fichiers de transcription
    transcription_files = get_transcription_files()
    print(f"{Colors.BOLD}{Colors.BLUE}📋 TRANSCRIPTIONS ({len(transcription_files)}){Colors.ENDC}")
    if transcription_files:
        for file in transcription_files:
            file_type = "phrases" if "_sentences" in file.name else "segments"
            print(f"   📄 {file.relative_to(Path.cwd())} ({file_type})")
    else:
        print(f"   {Colors.YELLOW}Aucune transcription trouvée{Colors.ENDC}")


def compare_analyses():
    """Compare les analyses segments vs phrases."""
    print(f"{Colors.HEADER}📊 COMPARAISON D'ANALYSES{Colors.ENDC}")
    print(f"{Colors.YELLOW}ℹ️  Cette fonctionnalité compare les résultats d'analyse entre segments et phrases{Colors.ENDC}")
    print(f"{Colors.YELLOW}   Recherche automatique des paires de fichiers...{Colors.ENDC}")
    print()
    
    # À implémenter : logique de comparaison
    print(f"{Colors.YELLOW}🚧 Fonctionnalité en développement{Colors.ENDC}")


def main():
    """Fonction principale."""
    os.chdir(Path(__file__).parent)  # S'assurer d'être dans le bon répertoire
    
    while True:
        print_header()
        print_menu()
        
        choice = input(f"{Colors.BOLD}{Colors.CYAN}Votre choix (0-7) : {Colors.ENDC}").strip()
        print()
        
        if choice == '0':
            print(f"{Colors.GREEN}👋 À bientôt !{Colors.ENDC}")
            break
        
        elif choice == '1':
            transcribe_audio()
        
        elif choice == '2':
            reconstruct_sentences()
        
        elif choice == '3':
            analyze_love()
        
        elif choice == '4':
            full_pipeline()
        
        elif choice == '5':
            list_files()
        
        elif choice == '6':
            list_files()  # Même fonction pour l'instant
        
        elif choice == '7':
            compare_analyses()
        
        else:
            print(f"{Colors.RED}❌ Choix invalide{Colors.ENDC}")
        
        if choice != '0':
            input(f"\\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.ENDC}")
            print("\\n" * 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\\n{Colors.YELLOW}👋 Arrêt demandé par l'utilisateur{Colors.ENDC}")
    except Exception as e:
        print(f"\\n{Colors.RED}❌ Erreur inattendue : {e}{Colors.ENDC}")
        sys.exit(1)