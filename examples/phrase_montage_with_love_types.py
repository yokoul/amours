#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de montage de phrases complètes avec filtrage par types d'amour
Sélectionne et lit des phrases entières avec mots-clés et types d'amour
"""

import sys
from pathlib import Path
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pydub import AudioSegment
import difflib
import random
import math

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("⚠️ mutagen non disponible - métadonnées MP3 désactivées")

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

@dataclass
class PhraseMatch:
    """Représente une phrase trouvée"""
    text: str
    file_name: str
    audio_path: str
    speaker: str
    start: float
    end: float
    segment_id: int
    keywords_found: List[str]
    match_score: float
    love_type: Optional[str] = None  # Type d'amour dominant

class PhraseSelector:
    """Sélecteur et monteur de phrases complètes avec support des types d'amour"""
    
    def __init__(self, transcription_dir: str = "output_transcription", 
                 semantic_dir: str = "output_semantic", 
                 audio_dir: str = "audio"):
        self.transcription_dir = Path(transcription_dir)
        self.semantic_dir = Path(semantic_dir)
        self.audio_dir = Path(audio_dir)
        self.phrases: List[PhraseMatch] = []
        self.audio_cache: Dict[str, AudioSegment] = {}
        self.semantic_data: Dict[str, Dict] = {}  # Cache pour les données sémantiques
        
    def load_phrases(self):
        """Charge toutes les phrases des transcriptions"""
        print("📖 Chargement des phrases...")
        
        json_files = list(self.transcription_dir.glob("*.json"))
        
        for json_file in json_files:
            self._load_phrases_from_file(json_file)
        
        print(f"✅ {len(self.phrases)} phrases chargées depuis {len(json_files)} fichiers")
        self._load_semantic_data()
        
    def _load_semantic_data(self):
        """Charge les analyses sémantiques correspondantes"""
        semantic_files = list(self.semantic_dir.glob("*_love_analysis.json"))
        
        for semantic_file in semantic_files:
            # Extraire le nom de base du fichier
            base_name = semantic_file.name.replace("_with_speakers_love_analysis_love_analysis.json", "")
            
            try:
                with open(semantic_file, 'r', encoding='utf-8') as f:
                    semantic_data = json.load(f)
                self.semantic_data[base_name] = semantic_data
            except Exception as e:
                print(f"⚠️ Erreur chargement sémantique {semantic_file.name}: {e}")
        
        print(f"📊 {len(self.semantic_data)} analyses sémantiques chargées")
        self._enrich_phrases_with_love_types()
    
    def _enrich_phrases_with_love_types(self):
        """Enrichit les phrases avec leurs types d'amour dominant"""
        enriched_count = 0
        
        for phrase in self.phrases:
            # Extraire le nom de base du fichier (sans extension)
            base_name = phrase.file_name.replace(".mp3", "")
            
            if base_name in self.semantic_data:
                semantic_data = self.semantic_data[base_name]
                
                # Chercher le segment correspondant dans l'analyse sémantique
                if 'semantic_analysis' in semantic_data and 'segments' in semantic_data['semantic_analysis']:
                    for sem_segment in semantic_data['semantic_analysis']['segments']:
                        if sem_segment['segment_id'] == phrase.segment_id:
                            phrase.love_type = sem_segment.get('dominant_love_type')
                            enriched_count += 1
                            break
        
        print(f"💝 {enriched_count} phrases enrichies avec types d'amour")
        
    def _load_phrases_from_file(self, json_path: Path):
        """Charge les phrases d'un fichier de transcription"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_name = data['metadata']['file']
            # Utiliser le chemin réel du fichier audio du JSON au lieu de construire manuellement
            audio_path = data['metadata'].get('path', self.audio_dir / file_name)

            # Utiliser directement les segments qui sont déjà des phrases
            for segment in data['transcription']['segments']:
                text = segment['text'].strip()
                duration = segment.get('duration', segment['end'] - segment['start'])

                # Filtres de qualité
                if len(text) < 10:  # Ignorer phrases très courtes
                    continue
                if duration > 20.0:  # Ignorer phrases très longues 
                    continue
                if len(text.split()) < 3:  # Au moins 3 mots
                    continue

                phrase = PhraseMatch(
                    text=text,
                    file_name=file_name,
                    audio_path=str(audio_path),
                    speaker=segment['speaker'],
                    start=segment['start'],
                    end=segment['end'],
                    segment_id=segment['id'],
                    keywords_found=[],
                    match_score=0.0,
                    love_type=None  # Sera enrichi plus tard
                )

                self.phrases.append(phrase)

        except Exception as e:
            print(f"❌ Erreur chargement {json_path}: {e}")

    def search_phrases(self, keywords: List[str], 
                      min_score: float = 0.3,
                      love_types: Optional[List[str]] = None) -> List[PhraseMatch]:
        """Recherche des phrases contenant les mots-clés avec filtre optionnel par types d'amour
        
        Args:
            keywords: Liste de mots-clés à rechercher
            min_score: Score minimum pour considérer une phrase
            love_types: Liste optionnelle de types d'amour à filtrer
        """
        matches = []
        
        # Types d'amour disponibles pour référence
        available_love_types = {"romantique", "familial", "amical", "spirituel", 
                              "erotique", "narcissique", "platonique", "compassionnel"}
        
        if love_types:
            print(f"💝 Filtrage par types d'amour: {', '.join(love_types)}")
        
        for phrase in self.phrases:
            # Filtre par type d'amour si spécifié
            if love_types and phrase.love_type:
                if phrase.love_type not in love_types:
                    continue
            
            # Recherche par mots-clés
            phrase_lower = phrase.text.lower()
            found_keywords = []
            score = 0.0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Correspondance exacte
                if keyword_lower in phrase_lower:
                    found_keywords.append(keyword)
                    score += 2.0
                else:
                    # Recherche floue avec difflib
                    words_in_phrase = phrase_lower.split()
                    best_match = difflib.get_close_matches(keyword_lower, words_in_phrase, 
                                                         n=1, cutoff=0.7)
                    if best_match:
                        found_keywords.append(f"{keyword}≈{best_match[0]}")
                        score += 1.5
            
            if found_keywords and score >= min_score:
                phrase.keywords_found = found_keywords
                phrase.match_score = score
                matches.append(phrase)
        
        # Trier par score décroissant avec randomisation
        matches.sort(key=lambda x: x.match_score + random.uniform(-0.2, 0.2), reverse=True)
        
        return matches

    def _diversify_sources(self, matches: List[PhraseMatch], target_count: int) -> List[PhraseMatch]:
        """Sélectionne les phrases en diversifiant les sources avec randomisation renforcée"""
        if len(matches) <= target_count:
            return matches
        
        # Ajouter plus de randomisation aux scores avant sélection
        for match in matches:
            # Variation plus importante du score (±15%)
            variation = random.uniform(-0.15, 0.15) * match.match_score
            match.match_score += variation
        
        # Mélanger les candidats au sein de chaque niveau de qualité
        # Diviser en 3 tiers : excellent (60%), bon (30%), acceptable (10%)
        excellent_threshold = len(matches) * 0.6
        good_threshold = len(matches) * 0.9
        
        excellent_candidates = matches[:int(excellent_threshold)]
        good_candidates = matches[int(excellent_threshold):int(good_threshold)]
        acceptable_candidates = matches[int(good_threshold):]
        
        # Mélanger chaque groupe
        random.shuffle(excellent_candidates)
        random.shuffle(good_candidates)
        random.shuffle(acceptable_candidates)
        
        # Sélection stratifiée avec plus de variation
        selected = []
        file_speaker_count = {}
        
        # Pool combiné avec pondération
        candidate_pool = (excellent_candidates * 3 +  # 3x plus de chances
                         good_candidates * 2 +        # 2x plus de chances  
                         acceptable_candidates)       # 1x chances
        
        random.shuffle(candidate_pool)  # Mélange final
        
        for phrase in candidate_pool:
            if len(selected) >= target_count:
                break
                
            file_speaker_key = f"{phrase.file_name}_{phrase.speaker}"
            current_count = file_speaker_count.get(file_speaker_key, 0)
            
            # Limiter à 2 phrases par combinaison fichier+intervenant (au lieu de 1)
            if current_count < 2:
                selected.append(phrase)
                file_speaker_count[file_speaker_key] = current_count + 1
        
        # Si pas assez trouvé, compléter sans restriction
        if len(selected) < target_count:
            remaining_pool = [p for p in matches if p not in selected]
            random.shuffle(remaining_pool)
            selected.extend(remaining_pool[:target_count - len(selected)])
        
        return selected[:target_count]

    def display_search_results(self, matches: List[PhraseMatch]):
        """Affiche les résultats de recherche avec types d'amour"""
        if not matches:
            print("❌ Aucune phrase trouvée")
            return
        
        print(f"🔍 {len(matches)} phrases trouvées:")
        print("-" * 50)
        
        for i, phrase in enumerate(matches[:20], 1):  # Limiter à 20 pour l'affichage
            duration = phrase.end - phrase.start
            love_emoji = self._get_love_emoji(phrase.love_type)
            love_display = f" {love_emoji} {phrase.love_type}" if phrase.love_type else ""
            
            print(f" {i:2d}. 📝 {phrase.text}")
            print(f"     🎯 Mots trouvés: {', '.join(phrase.keywords_found)}")
            print(f"     📁 {phrase.file_name} | 🎭 {phrase.speaker} | ⭐ {phrase.match_score:.1f}{love_display}")
            print(f"     ⏱️ {phrase.start:.1f}s - {phrase.end:.1f}s ({duration:.1f}s)")
            print()

    def _get_love_emoji(self, love_type: str) -> str:
        """Retourne l'emoji correspondant au type d'amour"""
        love_emojis = {
            "romantique": "💕",
            "familial": "👨‍👩‍👧‍👦", 
            "amical": "🤝",
            "spirituel": "🙏",
            "erotique": "🔥",
            "narcissique": "🪞",
            "platonique": "📚",
            "compassionnel": "🤗"
        }
        return love_emojis.get(love_type, "💖")

    def generate_phrase_montage(self, phrases: List[PhraseMatch], 
                              output_file: str,
                              gap_duration: float = 1.5,
                              fade_in_duration: float = 0.3,
                              fade_out_duration: float = 0.3,
                              normalize: str = "rms",
                              keywords: List[str] = None,
                              love_type: str = None) -> str:
        """
        Génère un montage audio des phrases sélectionnées
        
        Args:
            phrases: Liste des phrases à assembler
            output_file: Fichier de sortie
            gap_duration: Silence entre phrases (secondes)
            fade_in_duration: Durée du fade in (secondes)
            fade_out_duration: Durée du fade out (secondes)
            normalize: Méthode de normalisation ("peak", "rms", "loudness", "none")
            
        Returns:
            Chemin du fichier audio généré
        """
        print(f"🎬 Génération montage de {len(phrases)} phrases...")
        
        # Créer le montage
        final_audio = None
        gap_silence = AudioSegment.silent(duration=int(gap_duration * 1000))  # ms
        
        for i, phrase in enumerate(phrases, 1):
            print(f"  📝 {i}/{len(phrases)}: {phrase.text[:60]}...")
            
            # Charger l'audio source
            source_audio = self._load_audio(phrase.audio_path)
            
            # Extraire la phrase (en millisecondes)
            start_ms = int(phrase.start * 1000)
            end_ms = int(phrase.end * 1000)
            
            # Ajouter un peu de contexte (padding)
            padding_ms = 100  # 0.1s de contexte
            start_ms = max(0, start_ms - padding_ms)
            end_ms = min(len(source_audio), end_ms + padding_ms)
            
            phrase_audio = source_audio[start_ms:end_ms]
            
            # Normaliser l'audio pour équilibrer les volumes
            if normalize and normalize != "none":
                phrase_audio = self.normalize_audio(phrase_audio, normalize)
            
            # Appliquer les fondus
            if fade_in_duration > 0:
                fade_in_ms = int(fade_in_duration * 1000)
                phrase_audio = phrase_audio.fade_in(min(fade_in_ms, len(phrase_audio) // 4))
            
            if fade_out_duration > 0:
                fade_out_ms = int(fade_out_duration * 1000)
                phrase_audio = phrase_audio.fade_out(min(fade_out_ms, len(phrase_audio) // 4))
            
            # Ajouter au montage final
            if final_audio is None:
                final_audio = phrase_audio
            else:
                final_audio = final_audio + gap_silence + phrase_audio
        
        # Créer le dossier de sortie s'il n'existe pas
        output_path = Path("output_mix_play")
        output_path.mkdir(exist_ok=True)
        
        # Chemin complet du fichier de sortie
        output_file_path = output_path / output_file
        
        # Exporter en MP3
        final_audio.export(str(output_file_path), format="mp3", bitrate="192k")
        
        # Ajouter les métadonnées détaillées
        self._add_mp3_metadata(str(output_file_path), phrases, keywords or [], 
                             love_type, len(final_audio) / 1000.0)
        
        # Statistiques finales
        total_duration = len(final_audio) / 1000.0  # Convertir en secondes
        unique_speakers = len(set(phrase.speaker for phrase in phrases))
        unique_files = len(set(phrase.file_name for phrase in phrases))
        
        print(f"✅ Montage généré: {output_file}")
        print(f"⏱️ Durée totale: {total_duration:.1f}s")
        print(f"🎭 Intervenants: {', '.join(set(phrase.speaker for phrase in phrases))}")
        print(f"📁 Fichiers source: {', '.join(set(phrase.file_name.replace('.mp3', '') for phrase in phrases))}")
        
        return str(output_file_path)
    
    def _load_audio(self, audio_path: str) -> AudioSegment:
        """Charge un fichier audio avec cache"""
        if audio_path not in self.audio_cache:
            print(f"🎵 Chargement {Path(audio_path).name}...")
            self.audio_cache[audio_path] = AudioSegment.from_file(audio_path)
        
        return self.audio_cache[audio_path]
    
    def normalize_audio(self, audio: AudioSegment, method: str = "peak") -> AudioSegment:
        """Normalise l'audio selon différentes méthodes
        
        Args:
            audio: Segment audio à normaliser
            method: "peak", "rms" ou "loudness"
        """
        if method == "peak":
            # Normalisation par pic (plus simple et rapide)
            return audio.normalize()
        
        elif method == "rms":
            # Normalisation par RMS (Root Mean Square) - plus équilibré
            target_dBFS = -20.0  # Volume cible
            change_in_dBFS = target_dBFS - audio.dBFS
            return audio.apply_gain(change_in_dBFS)
        
        elif method == "loudness":
            # Normalisation par loudness perçue (EBU R128-like)
            # Approximation simple basée sur RMS pondéré
            target_dBFS = -23.0  # Standard broadcast
            current_rms = audio.rms
            if current_rms > 0:
                # Calcul simplifié du gain nécessaire
                target_rms = 10 ** (target_dBFS / 20) * audio.max_possible_amplitude
                gain_ratio = target_rms / current_rms
                gain_db = 20 * math.log10(gain_ratio) if gain_ratio > 0 else 0
                return audio.apply_gain(min(max(gain_db, -30), 30))  # Limiter le gain
            return audio
        
        return audio  # Méthode inconnue, retourner tel quel
    
    def _add_mp3_metadata(self, mp3_path: str, phrases: List[PhraseMatch], 
                         keywords: List[str], love_type: str, duration: float):
        """Ajoute les métadonnées complètes au fichier MP3 avec types d'amour"""
        if not MUTAGEN_AVAILABLE:
            return
            
        try:
            audio_file = MP3(mp3_path, ID3=ID3)
            
            # Créer les tags ID3 si inexistants
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # Informations de base avec type d'amour
            title = f"Montage: {', '.join(keywords)}"
            if love_type:
                title += f" | Type: {love_type}"
            
            audio_file.tags.add(TIT2(encoding=3, text=title))
            audio_file.tags.add(TPE1(encoding=3, text="Amours Mix-Play"))
            audio_file.tags.add(TALB(encoding=3, text=f"Love Analysis - {love_type}" if love_type else "Generated Montages"))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            audio_file.tags.add(TCON(encoding=3, text="Speech/Love Analysis"))
            
            # Statistiques générales avec des tags personnalisés
            intervenants = list(set(p.speaker for p in phrases))
            fichiers = list(set(Path(p.file_name).stem for p in phrases))
            love_types = list(set(getattr(p, 'love_type', None) for p in phrases if hasattr(p, 'love_type') and p.love_type))
            
            # Métadonnées globales structurées
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_search', text=', '.join(keywords)))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_filter_type', text=love_type or 'none'))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_detected_types', text=', '.join(love_types)))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_duration', text=f"{duration:.1f}s"))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_speakers', text=', '.join(intervenants)))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_sources', text=', '.join(fichiers)))
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_count', text=str(len(phrases))))
            
            # Métadonnées détaillées pour chaque phrase
            for i, phrase in enumerate(phrases, 1):
                prefix = f"amour_phrase{i}"
                
                # Texte de la phrase
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_text', 
                                       text=phrase.text))
                
                # Mots-clés trouvés
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_keywords', 
                                       text=', '.join(phrase.keywords_found)))
                
                # Source et intervenant
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_source', 
                                       text=Path(phrase.file_name).stem))
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_speaker', 
                                       text=phrase.speaker))
                
                # Type d'amour détecté
                phrase_love_type = getattr(phrase, 'love_type', None)
                if phrase_love_type:
                    audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_love_type', 
                                           text=phrase_love_type))
                
                # Score et timecodes
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_score', 
                                       text=f"{phrase.match_score:.1f}"))
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_start', 
                                       text=f"{phrase.start:.1f}s"))
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_end', 
                                       text=f"{phrase.end:.1f}s"))
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_duration', 
                                       text=f"{phrase.end-phrase.start:.1f}s"))
                audio_file.tags.add(COMM(encoding=3, lang='fra', desc=f'{prefix}_segment_id', 
                                       text=str(phrase.segment_id)))
            
            audio_file.save()
            print(f"📋 Métadonnées structurées ajoutées au MP3 ({len(phrases)} phrases, type: {love_type or 'tous'})")
            
        except Exception as e:
            print(f"⚠️ Erreur métadonnées MP3: {e}")

def main():
    """Interface en ligne de commande"""
    
    # Initialiser seed aléatoire basé sur l'horodatage pour garantir la variation
    seed = int(time.time() * 1000000) % 2147483647  # Utiliser les microsecondes
    random.seed(seed)
    print(f"🎲 Seed aléatoire: {seed}")
    
    if len(sys.argv) < 3:
        print("Usage: python phrase_montage_with_love_types.py <nombre_phrases> <mot-clé1> [mot-clé2] [--love-type type1,type2]")
        print()
        print("Exemples:")
        print("  python phrase_montage_with_love_types.py 3 amour")
        print("  python phrase_montage_with_love_types.py 5 amour vie bonheur")
        print("  python phrase_montage_with_love_types.py 3 relation --love-type romantique,familial")
        print("  python phrase_montage_with_love_types.py 4 passion --love-type erotique")
        print()
        print("Types d'amour disponibles:")
        print("  romantique, familial, amical, spirituel, erotique, narcissique, platonique, compassionnel")
        sys.exit(1)
    
    try:
        # Séparer les arguments normaux des options
        args = sys.argv[1:]
        love_types = None
        
        # Chercher --love-type dans les arguments
        if '--love-type' in args:
            love_type_index = args.index('--love-type')
            if love_type_index + 1 < len(args):
                love_types_str = args[love_type_index + 1]
                love_types = [t.strip() for t in love_types_str.split(',')]
                # Retirer --love-type et sa valeur des arguments
                args = args[:love_type_index] + args[love_type_index + 2:]
        
        num_phrases = int(args[0])
        keywords = args[1:]
    except (ValueError, IndexError):
        print("❌ Le nombre de phrases doit être un entier")
        sys.exit(1)
    
    love_filter_display = f" (types: {', '.join(love_types)})" if love_types else ""
    print(f"🎯 Recherche de {num_phrases} phrases avec mots-clés: {', '.join(keywords)}{love_filter_display}")
    print()
    
    # Initialiser le sélecteur
    selector = PhraseSelector()
    selector.load_phrases()
    
    # Rechercher les phrases avec plus de variation
    matches = selector.search_phrases(
        keywords, 
        min_score=0.3,
        love_types=love_types
    )
    
    if not matches:
        print("❌ Aucune phrase trouvée avec ces critères")
        sys.exit(1)
    
    # Afficher les résultats
    selector.display_search_results(matches)
    
    # Sélectionner et diversifier
    selected_phrases = selector._diversify_sources(matches, num_phrases)
    
    print(f"🎬 Génération montage de {len(selected_phrases)} phrases...")
    
    # Créer le nom du fichier de sortie avec types d'amour
    keywords_str = "_".join(keywords)
    love_suffix = f"_{'-'.join(love_types)}" if love_types else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"montage_{keywords_str}{love_suffix}_{num_phrases}phrases_{timestamp}.mp3"
    
    try:
        audio_file = selector.generate_phrase_montage(
            selected_phrases,
            output_file,
            gap_duration=1.5,  # 1.5s de silence entre phrases
            fade_in_duration=0.2,
            fade_out_duration=0.2,
            normalize="rms",  # Normalisation RMS pour équilibrer les volumes
            keywords=keywords,  # Passer les mots-clés pour métadonnées
            love_type=love_type if 'love_type' in locals() else None  # Type d'amour sélectionné
        )
        
        print(f"🎧 Lecture automatique...")
        
        # Lecture automatique sur macOS
        import platform
        if platform.system() == "Darwin":
            try:
                import subprocess
                subprocess.run(["afplay", audio_file], check=True)
                print("✅ Lecture terminée")
            except Exception as e:
                print(f"⚠️ Erreur lecture: {e}")
        
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()