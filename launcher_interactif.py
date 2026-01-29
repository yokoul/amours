#!/usr/bin/env python3
"""
Lanceur interactif pour les outils de transcription et d'analyse.
Interface utilisateur simplifiée pour tous les scripts du projet.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class InteractiveLauncher:
    """Interface interactive pour lancer les différents outils."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / '.venv' / 'bin'
        
    def show_banner(self):
        """Affiche le banner de l'application."""
        print("=" * 70)
        print("🎵 TRANSCRIPTION AUDIO & ANALYSE SÉMANTIQUE")
        print("=" * 70)
        print("Interface interactive pour les outils de transcription")
        print()
    
    def show_main_menu(self) -> int:
        """Affiche le menu principal et retourne le choix."""
        print("📋 MENU PRINCIPAL")
        print("-" * 40)
        print("1. 🎵 Transcription audio avec intervenants")
        print("2. 🔧 Reconstruction de phrases (sur JSON existant)")
        print("3. ❤️  Analyse sémantique d'amour")
        print("4. 🔄 Workflow complet (Transcription → Reconstruction → Analyse)")
        print("5. � Traitement BATCH de tous les audios (avec Whisper large)")
        print("6. 📁 Lister les fichiers disponibles")
        print("7. ❌ Quitter")
        print()
        
        while True:
            try:
                choice = int(input("Votre choix (1-7): ").strip())
                if 1 <= choice <= 7:
                    return choice
                else:
                    print("❌ Choix invalide. Entrez un numéro entre 1 et 7.")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide.")
    
    def list_audio_files(self) -> List[Path]:
        """Liste les fichiers audio disponibles."""
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
        audio_files = []
        
        # Chercher dans le dossier audio
        audio_dir = self.project_root / 'audio'
        if audio_dir.exists():
            for file in audio_dir.rglob('*'):
                if file.is_file() and file.suffix.lower() in audio_extensions:
                    audio_files.append(file)
        
        return sorted(audio_files)
    
    def list_json_files(self, directory: str = "output*") -> List[Path]:
        """Liste les fichiers JSON de transcription disponibles."""
        json_files = []
        
        # Chercher dans tous les dossiers output*
        for output_dir in self.project_root.glob(directory):
            if output_dir.is_dir():
                for file in output_dir.glob('*.json'):
                    if 'complete' in file.name:
                        json_files.append(file)
        
        return sorted(json_files)
    
    def select_file(self, files: List[Path], file_type: str = "fichier") -> Path:
        """Interface de sélection de fichier."""
        if not files:
            print(f"❌ Aucun {file_type} trouvé.")
            return None
        
        print(f"\n📂 {file_type.title()}s disponibles:")
        print("-" * 50)
        
        for i, file in enumerate(files, 1):
            # Afficher le chemin relatif pour plus de lisibilité
            rel_path = file.relative_to(self.project_root)
            size = ""
            if file.exists():
                size_mb = file.stat().st_size / (1024 * 1024)
                if size_mb > 1:
                    size = f" ({size_mb:.1f} MB)"
                else:
                    size_kb = file.stat().st_size / 1024
                    size = f" ({size_kb:.0f} KB)"
            
            print(f"{i:2d}. {rel_path}{size}")
        
        print(f"{len(files)+1:2d}. ← Retour au menu principal")
        print()
        
        while True:
            try:
                choice = int(input(f"Sélectionnez un {file_type} (1-{len(files)+1}): ").strip())
                if 1 <= choice <= len(files):
                    return files[choice-1]
                elif choice == len(files) + 1:
                    return None
                else:
                    print(f"❌ Choix invalide. Entrez un numéro entre 1 et {len(files)+1}.")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide.")
    
    def get_whisper_model_choice(self) -> str:
        """Interface pour choisir le modèle Whisper."""
        print("\nModèles Whisper disponibles:")
        print("1. medium (recommandé, équilibré)")
        print("2. large (plus précis, plus lent)")
        print("3. small (plus rapide, moins précis)")
        print("4. base (très rapide)")
        
        model_choice = input("Modèle Whisper (1-4, défaut: 1): ").strip()
        models = ['medium', 'large', 'small', 'base']
        return models[int(model_choice)-1] if model_choice.isdigit() and 1 <= int(model_choice) <= 4 else 'medium'
    
    def get_output_directory(self, default: str = "output_transcription") -> str:
        """Interface pour choisir le dossier de sortie."""
        output_dir = input(f"Dossier de sortie ({default}): ").strip()
        return output_dir if output_dir else default
    
    def get_output_settings(self) -> Dict[str, Any]:
        """Interface pour choisir les paramètres de sortie."""
        print("\n⚙️  PARAMÈTRES DE SORTIE")
        print("-" * 30)
        
        # Dossier de sortie
        output_dir = self.get_output_directory()
        
        # Formats d'export
        print("\nFormats d'export disponibles:")
        formats_available = ['json', 'csv', 'srt', 'words']
        print("1. json (données complètes)")
        print("2. csv (tableau)")
        print("3. srt (sous-titres)")
        print("4. words (mots avec timestamps)")
        print("5. Tous les formats")
        
        format_choice = input("Formats à générer (1-5, défaut: 1): ").strip()
        if format_choice == '5':
            formats = formats_available
        elif format_choice == '2':
            formats = ['csv']
        elif format_choice == '3':
            formats = ['srt']
        elif format_choice == '4':
            formats = ['words']
        else:
            formats = ['json']
        
        # Modèle Whisper
        model = self.get_whisper_model_choice()
        
        # Reconstruction de phrases
        reconstruct = input("Reconstruire les phrases automatiquement ? (O/n): ").strip().lower()
        reconstruct_sentences = reconstruct not in ['n', 'non', 'no']
        
        # Analyse sémantique
        semantic = input("Inclure l'analyse sémantique des types d'amour ? (O/n): ").strip().lower()
        with_semantic = semantic not in ['n', 'non', 'no']
        
        return {
            'output_dir': output_dir,
            'formats': formats,
            'model': model,
            'reconstruct_sentences': reconstruct_sentences,
            'with_semantic': with_semantic
        }
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """Interface pour les paramètres d'analyse sémantique."""
        print("\n⚙️  PARAMÈTRES D'ANALYSE")
        print("-" * 30)
        
        # Dossier de sortie
        output_dir = self.get_output_directory("output_semantic")
        
        # Formats de sortie
        print("\nFormats d'analyse:")
        print("1. summary (résumé texte)")
        print("2. json (données détaillées)")
        print("3. Les deux")
        
        format_choice = input("Format de sortie (1-3, défaut: 3): ").strip()
        if format_choice == '1':
            formats = ['summary']
        elif format_choice == '2':
            formats = ['json']
        else:
            formats = ['json', 'summary']
        
        # Seuil de détection
        threshold = input("Seuil de détection (0.0-1.0, défaut: 0.15): ").strip()
        try:
            threshold = float(threshold) if threshold else 0.15
            threshold = max(0.0, min(1.0, threshold))
        except ValueError:
            threshold = 0.15
        
        return {
            'output_dir': output_dir,
            'formats': formats,
            'threshold': threshold
        }
    
    def run_command(self, cmd: List[str], description: str = "Commande") -> bool:
        """Exécute une commande et affiche le résultat."""
        print(f"\n🚀 {description}")
        print("=" * 60)
        print(f"💻 Commande: {' '.join(cmd)}")
        print()
        
        try:
            # Utiliser l'environnement virtuel
            env = os.environ.copy()
            if (self.venv_path / 'activate').exists():
                env['VIRTUAL_ENV'] = str(self.venv_path.parent)
                env['PATH'] = f"{self.venv_path}:{env.get('PATH', '')}"
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env=env,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ {description} terminée avec succès!")
                return True
            else:
                print(f"\n❌ Erreur lors de {description.lower()}")
                return False
                
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution: {str(e)}")
            return False
    
    def transcribe_audio(self):
        """Lance la transcription audio."""
        audio_files = self.list_audio_files()
        selected_file = self.select_file(audio_files, "fichier audio")
        
        if not selected_file:
            return
        
        settings = self.get_output_settings()
        
        cmd = [
            'python', 'transcribe_audio.py',
            '--input', str(selected_file),
            '--output', settings['output_dir'],
            '--formats'] + settings['formats'] + [
            '--whisper-model', settings['model']
        ]
        
        if settings['reconstruct_sentences']:
            cmd.append('--reconstruct-sentences')
        
        if settings['with_semantic']:
            cmd.append('--with-semantic-analysis')
        
        self.run_command(cmd, "Transcription audio")
    
    def reconstruct_sentences(self):
        """Lance la reconstruction de phrases."""
        json_files = self.list_json_files()
        selected_file = self.select_file(json_files, "fichier JSON")
        
        if not selected_file:
            return
        
        output_dir = input("Dossier de sortie (output_sentences): ").strip()
        if not output_dir:
            output_dir = "output_sentences"
        
        cmd = [
            'python', 'reconstruct_sentences.py',
            '--input', str(selected_file),
            '--output', output_dir
        ]
        
        self.run_command(cmd, "Reconstruction de phrases")
    
    def analyze_love(self):
        """Lance l'analyse sémantique."""
        json_files = self.list_json_files("output*")
        selected_file = self.select_file(json_files, "fichier JSON")
        
        if not selected_file:
            return
        
        settings = self.get_analysis_settings()
        
        cmd = [
            'python', 'analyze_love.py',
            '--input', str(selected_file),
            '--output', settings['output_dir'],
            '--formats'] + settings['formats'] + [
            '--threshold', str(settings['threshold'])
        ]
        
        self.run_command(cmd, "Analyse sémantique")
    
    def complete_workflow(self):
        """Lance le workflow complet."""
        print("\n🔄 WORKFLOW COMPLET")
        print("=" * 50)
        print("Ce workflow va:")
        print("1. Transcrire un fichier audio")
        print("2. Reconstruire les phrases")
        print("3. Analyser sémantiquement")
        print()
        
        # Étape 1: Transcription
        print("ÉTAPE 1/3: Transcription audio")
        print("-" * 30)
        
        audio_files = self.list_audio_files()
        selected_audio = self.select_file(audio_files, "fichier audio")
        
        if not selected_audio:
            return
        
        # Pour le workflow complet, on utilise des paramètres optimisés
        print("Configuration automatique :")
        print("• Reconstruction de phrases : OUI")
        print("• Analyse sémantique : OUI")  
        print("• Format : JSON uniquement")
        
        # Demander seulement le modèle et le dossier de sortie
        output_dir = self.get_output_directory()
        model = self.get_whisper_model_choice()
        
        transcription_settings = {
            'output_dir': output_dir,
            'model': model,
            'reconstruct_sentences': True,
            'with_semantic': True,
            'formats': ['json']
        }
        
        transcribe_cmd = [
            'python', 'transcribe_audio.py',
            '--input', str(selected_audio),
            '--output', transcription_settings['output_dir'],
            '--formats', 'json',
            '--whisper-model', transcription_settings['model'],
            '--reconstruct-sentences',
            '--with-semantic-analysis'
        ]
        
        if not self.run_command(transcribe_cmd, "WORKFLOW COMPLET: Transcription + Reconstruction + Analyse sémantique"):
            print("❌ Échec du workflow complet")
            return
        
        print("\n🎉 Workflow complet terminé avec succès!")
        print(f"📂 Résultats dans : {transcription_settings['output_dir']}")
        print("📄 Le fichier JSON contient :")
        print("   • Transcription complète avec intervenants")
        print("   • Phrases reconstruites")
        print("   • Analyse sémantique des types d'amour")
    
    def batch_process_all_audio(self):
        """Traite tous les fichiers audio en batch avec Whisper large."""
        print("\n🔥 TRAITEMENT BATCH DE TOUS LES AUDIOS")
        print("=" * 60)
        
        audio_files = self.list_audio_files()
        
        if not audio_files:
            print("❌ Aucun fichier audio trouvé.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print(f"\n📊 {len(audio_files)} fichiers audio trouvés")
        
        # Afficher la liste complète des fichiers
        print("\n📋 LISTE DES FICHIERS (ordre alphabétique):")
        print("-" * 60)
        for i, audio_file in enumerate(audio_files, 1):
            rel_path = audio_file.relative_to(self.project_root)
            print(f"{i:3d}. {rel_path}")
        
        print("\n⚙️  CONFIGURATION DU BATCH:")
        print("   • Modèle Whisper: LARGE (haute qualité)")
        print("   • Reconstruction de phrases: OUI")
        print("   • Analyse sémantique: OUI")
        print("   • Écrasement des JSON existants: OUI")
        print()
        
        # Demander le point de départ
        start_from = input(f"\n🔢 Commencer à partir du fichier n° (1-{len(audio_files)}, défaut: 1): ").strip()
        try:
            start_index = int(start_from) - 1 if start_from else 0
            start_index = max(0, min(start_index, len(audio_files) - 1))
        except ValueError:
            start_index = 0
        
        if start_index > 0:
            print(f"▶️  Reprise à partir du fichier n°{start_index + 1}: {audio_files[start_index].name}")
            files_to_process = audio_files[start_index:]
        else:
            files_to_process = audio_files
        
        # Demander confirmation
        confirm = input(f"\n⚠️  Voulez-vous traiter {len(files_to_process)} fichiers (n°{start_index + 1} à {len(audio_files)}) ? (O/n): ").strip().lower()
        if confirm in ['n', 'non', 'no']:
            print("❌ Traitement batch annulé.")
            return
        
        # Dossiers de sortie
        output_dir = self.get_output_directory()
        output_semantic = "output_semantic"
        
        # Traiter chaque fichier
        success_count = 0
        fail_count = 0
        
        for idx, audio_file in enumerate(files_to_process, start_index + 1):
            print("\n" + "=" * 60)
            print(f"🎵 Traitement {idx}/{len(audio_files)}: {audio_file.name}")
            print(f"   (Fichier n°{idx} sur {len(audio_files)} au total)")
            print("=" * 60)
            
            # Étape 1: Transcription avec reconstruction et analyse intégrée
            transcribe_cmd = [
                'python', 'transcribe_audio.py',
                '--input', str(audio_file),
                '--output', output_dir,
                '--formats', 'json',
                '--whisper-model', 'large',
                '--reconstruct-sentences',
                '--with-semantic-analysis'
            ]
            
            if not self.run_command(transcribe_cmd, f"Transcription de {audio_file.name}"):
                fail_count += 1
                continue
            
            # Étape 2: Générer les fichiers d'analyse sémantique séparés dans output_semantic/
            # Construire le nom du fichier JSON de transcription
            json_name = audio_file.stem + "_with_speakers_complete.json"
            json_path = self.project_root / output_dir / json_name
            
            if json_path.exists():
                print(f"\n📊 Génération des fichiers d'analyse sémantique...")
                analyze_cmd = [
                    'python', 'analyze_love.py',
                    '--input', str(json_path),
                    '--output', output_semantic,
                    '--formats', 'json', 'summary',
                    '--threshold', '0.15'
                ]
                
                if self.run_command(analyze_cmd, f"Analyse sémantique de {audio_file.name}"):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                print(f"⚠️  Fichier JSON non trouvé: {json_path}")
                fail_count += 1
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU TRAITEMENT BATCH")
        print("=" * 60)
        print(f"✅ Fichiers traités avec succès: {success_count}")
        if fail_count > 0:
            print(f"❌ Fichiers en erreur: {fail_count}")
        print(f"📂 Transcriptions dans: {output_dir}")
        print(f"📂 Analyses sémantiques dans: {output_semantic}")
        
        # Indiquer le prochain fichier en cas d'interruption
        if start_index + len(files_to_process) < len(audio_files):
            next_file_num = start_index + len(files_to_process) + 1
            print(f"\n💡 Pour continuer plus tard, relancer avec le fichier n°{next_file_num}")
        elif success_count + fail_count < len(files_to_process):
            next_file_num = start_index + success_count + fail_count + 1
            print(f"\n💡 En cas d'interruption, reprendre au fichier n°{next_file_num}")
        
        print("\n🎉 Traitement batch terminé!")
    
    def list_files(self):
        """Affiche les fichiers disponibles."""
        print("\n📁 FICHIERS DISPONIBLES")
        print("=" * 50)
        
        # Fichiers audio
        audio_files = self.list_audio_files()
        if audio_files:
            print(f"\n🎵 Fichiers audio ({len(audio_files)}):")
            for file in audio_files[:10]:  # Limiter à 10
                rel_path = file.relative_to(self.project_root)
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   • {rel_path} ({size_mb:.1f} MB)")
            if len(audio_files) > 10:
                print(f"   ... et {len(audio_files) - 10} autres fichiers")
        else:
            print("\n🎵 Aucun fichier audio trouvé")
        
        # Fichiers JSON
        json_files = self.list_json_files()
        if json_files:
            print(f"\n📄 Fichiers JSON de transcription ({len(json_files)}):")
            for file in json_files[:10]:  # Limiter à 10
                rel_path = file.relative_to(self.project_root)
                size_kb = file.stat().st_size / 1024
                print(f"   • {rel_path} ({size_kb:.0f} KB)")
            if len(json_files) > 10:
                print(f"   ... et {len(json_files) - 10} autres fichiers")
        else:
            print("\n📄 Aucun fichier JSON de transcription trouvé")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def run(self):
        """Lance l'interface interactive."""
        self.show_banner()
        
        while True:
            choice = self.show_main_menu()
            
            if choice == 1:
                self.transcribe_audio()
            elif choice == 2:
                self.reconstruct_sentences()
            elif choice == 3:
                self.analyze_love()
            elif choice == 4:
                self.complete_workflow()
            elif choice == 5:
                self.batch_process_all_audio()
            elif choice == 6:
                self.list_files()
            elif choice == 7:
                print("\n👋 Au revoir!")
                break
            
            if choice != 7:
                input("\nAppuyez sur Entrée pour continuer...")
                print("\n" + "=" * 70)


def main():
    """Point d'entrée principal."""
    try:
        launcher = InteractiveLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()