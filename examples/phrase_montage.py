#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de montage de phrases complètes
Sélectionne et lit des phrases entières avec mots-clés
"""

import sys
from pathlib import Path
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pydub import AudioSegment
import difflib
import random
import math
import time

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
    love_analysis: Optional[Dict[str, float]] = None  # Scores détaillés par type

class PhraseSelector:
    """Sélecteur et monteur de phrases complètes"""
    
    def __init__(self, transcription_dir: str = "output_transcription", 
                 semantic_dir: str = "output_semantic", 
                 audio_dir: str = "audio"):
        self.transcription_dir = Path(transcription_dir)
        self.semantic_dir = Path(semantic_dir)
        self.audio_dir = Path(audio_dir)
        self.phrases: List[PhraseMatch] = []
        self.audio_cache: Dict[str, AudioSegment] = {}
        self.semantic_data: Dict[str, Dict] = {}  # Cache pour les données sémantiques
        self.transcription_data: Dict[str, Dict] = {}  # Cache des transcriptions complètes
        
    def load_phrases(self):
        """Charge toutes les phrases des transcriptions"""
        print("📖 Chargement des phrases...")
        
        json_files = list(self.transcription_dir.glob("*.json"))
        
        for json_file in json_files:
            self._load_phrases_from_file(json_file)
        
        print(f"✅ {len(self.phrases)} phrases chargées depuis {len(json_files)} fichiers")
        self._load_semantic_data()
        
    def _load_semantic_data(self):
        """Charge les analyses sémantiques correspondantes et enrichit les phrases"""
        semantic_files = list(self.semantic_dir.glob("*_love_analysis.json"))
        
        print(f"🔍 Chargement de {len(semantic_files)} fichiers sémantiques...")
        
        for semantic_file in semantic_files:
            # Extraire le nom de base du fichier
            base_name = semantic_file.name.replace("_with_speakers_love_analysis_love_analysis.json", "")
            
            try:
                with open(semantic_file, 'r', encoding='utf-8') as f:
                    semantic_data = json.load(f)
                self.semantic_data[base_name] = semantic_data
                
                # Enrichir les phrases correspondantes
                if 'transcription' in semantic_data and 'segments' in semantic_data['transcription']:
                    # Le nom du fichier est dans metadata
                    file_name = semantic_data['metadata']['file']
                    
                    matched_count = 0
                    for segment in semantic_data['transcription']['segments']:
                        segment_id = segment.get('id')
                        
                        # Trouver la phrase correspondante
                        for phrase in self.phrases:
                            if phrase.file_name == file_name and phrase.segment_id == segment_id:
                                # Enrichir avec les données sémantiques
                                phrase.love_type = segment.get('dominant_love_type')
                                phrase.love_analysis = segment.get('love_analysis')
                                matched_count += 1
                                break
                    
                    if matched_count > 0:
                        print(f"  ✓ {base_name}: {matched_count} phrases enrichies")
                
            except Exception as e:
                print(f"⚠️ Erreur chargement sémantique {semantic_file.name}: {e}")
        
        # Compter combien de phrases ont été enrichies
        enriched_count = sum(1 for p in self.phrases if p.love_analysis is not None)
        print(f"📊 {len(self.semantic_data)} analyses sémantiques chargées, {enriched_count}/{len(self.phrases)} phrases enrichies")
        
    def _load_phrases_from_file(self, json_path: Path):
        """Charge les phrases d'un fichier de transcription"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_name = data['metadata']['file']
            # Stocker les données complètes pour pouvoir accéder aux phrases suivantes
            self.transcription_data[file_name] = data
            
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
                    love_type=None,  # Sera enrichi par _load_semantic_data()
                    love_analysis=None  # Sera enrichi par _load_semantic_data()
                )
                
                self.phrases.append(phrase)
                
        except Exception as e:
            print(f"⚠️ Erreur chargement {json_path}: {e}")
    
    def search_phrases(self, keywords: List[str], max_results: int = 10, 
                      max_duration: float = 15.0, diversify_sources: bool = True) -> List[PhraseMatch]:
        """
        Recherche des phrases contenant les mots-clés
        
        Args:
            keywords: Liste des mots-clés à rechercher
            max_results: Nombre maximum de résultats
            max_duration: Durée maximum d'une phrase (secondes)
            diversify_sources: Si True, privilégie la diversité des sources
            
        Returns:
            Liste des phrases correspondantes, triées par score
        """
        if not self.phrases:
            self.load_phrases()
        
        # Nettoyer les mots-clés
        clean_keywords = [self._clean_word(kw) for kw in keywords if kw.strip()]
        
        matches = []
        
        for phrase in self.phrases:
            # Filtrer par durée d'abord
            duration = phrase.end - phrase.start
            if duration > max_duration:
                continue
                
            # Nettoyer le texte de la phrase
            clean_text = self._clean_word(phrase.text)
            clean_words = clean_text.split()
            
            # Chercher les correspondances
            found_keywords = []
            total_score = 0
            
            for keyword in clean_keywords:
                # Recherche exacte d'abord
                if keyword in clean_words:
                    found_keywords.append(keyword)
                    total_score += 2.0  # Bonus pour correspondance exacte
                else:
                    # Recherche floue
                    similar = difflib.get_close_matches(
                        keyword, clean_words, n=1, cutoff=0.8
                    )
                    if similar:
                        found_keywords.append(f"{keyword}≈{similar[0]}")
                        total_score += 1.0  # Moins de points pour correspondance floue
            
            # Si au moins un mot-clé trouvé
            if found_keywords:
                # Score final : (mots trouvés / mots cherchés) * bonus qualité
                match_score = (len(found_keywords) / len(clean_keywords)) * total_score
                
                # Bonus pour durée raisonnable (phrases courtes privilégiées)
                if duration <= 10.0:
                    match_score *= 1.2
                elif duration <= 5.0:
                    match_score *= 1.5
                
                phrase_copy = PhraseMatch(
                    text=phrase.text,
                    file_name=phrase.file_name,
                    audio_path=phrase.audio_path,
                    speaker=phrase.speaker,
                    start=phrase.start,
                    end=phrase.end,
                    segment_id=phrase.segment_id,
                    keywords_found=found_keywords,
                    match_score=match_score,
                    love_type=phrase.love_type,  # Préserver les données sémantiques
                    love_analysis=phrase.love_analysis  # Préserver les scores d'amour
                )
                
                matches.append(phrase_copy)
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Ajouter une variation aléatoire plus importante pour forcer la diversité
        # même sur des requêtes identiques répétées
        if len(matches) > max_results:
            for match in matches:
                # Variation aléatoire plus forte (±15% au lieu de ±5%) pour plus de variation
                variation = random.uniform(-0.15, 0.15) * match.match_score
                match.match_score += variation
            
            # Re-trier avec les scores légèrement variés
            matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Diversifier les sources si demandé
        if diversify_sources and len(matches) > max_results:
            matches = self._diversify_sources(matches, max_results)
        else:
            # Même sans diversification, ajouter un peu d'aléatoire
            if len(matches) > max_results:
                # Prendre les meilleurs mais avec un peu de variation
                top_candidates = matches[:max_results * 2]
                random.shuffle(top_candidates)
                matches = top_candidates[:max_results]
            else:
                matches = matches[:max_results]
        
        return matches
    
    def _diversify_sources(self, matches: List[PhraseMatch], max_results: int) -> List[PhraseMatch]:
        """
        Diversifie les sources dans la sélection finale avec aléatoire
        
        Args:
            matches: Liste des correspondances triées par score
            max_results: Nombre de résultats souhaités
            
        Returns:
            Liste diversifiée avec variation aléatoire
        """
        if len(matches) <= max_results:
            # Mélanger l'ordre si on a juste assez de résultats
            random.shuffle(matches)
            return matches
        
        # Séparer par tranches de qualité pour garder un minimum de pertinence
        top_tier = matches[:max_results * 2]  # Les meilleurs
        good_tier = matches[max_results * 2:max_results * 4] if len(matches) > max_results * 2 else []
        
        selected = []
        used_sources = set()
        
        # Mélanger les tranches
        random.shuffle(top_tier)
        random.shuffle(good_tier)
        
        # Pool de candidats (70% top, 30% good si disponible)
        candidate_pool = top_tier + good_tier[:len(good_tier)//3] if good_tier else top_tier
        
        # Première passe : diversification des sources
        for match in candidate_pool:
            source_key = f"{Path(match.file_name).stem}_{match.speaker}"
            
            if source_key not in used_sources:
                selected.append(match)
                used_sources.add(source_key)
                
                if len(selected) >= max_results:
                    break
        
        # Deuxième passe : compléter aléatoirement si besoin
        if len(selected) < max_results:
            remaining = [m for m in candidate_pool if m not in selected]
            random.shuffle(remaining)
            
            for match in remaining:
                selected.append(match)
                if len(selected) >= max_results:
                    break
        
        return selected[:max_results]
    
    def _clean_word(self, text: str) -> str:
        """Nettoie le texte pour la recherche"""
        import unicodedata
        
        # Minuscules et suppression ponctuation
        text = re.sub(r'[.,;:!?"\'\-\(\)\[\]{}]', ' ', text.lower())
        
        # Normaliser accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Espaces multiples → simple
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_next_phrase_same_speaker(self, phrase: PhraseMatch, num_next: int = 1) -> Optional[float]:
        """
        Trouve la fin de la Nième phrase suivante si elle est du même intervenant.
        
        Args:
            phrase: La phrase actuelle
            num_next: Nombre de phrases suivantes à inclure
            
        Returns:
            Le timestamp de fin étendu, ou None si pas de phrase suivante du même intervenant
        """
        # Récupérer les données de transcription
        if phrase.file_name not in self.transcription_data:
            return None
        
        data = self.transcription_data[phrase.file_name]
        segments = data['transcription']['segments']
        
        # Trouver le segment actuel
        current_idx = None
        for idx, seg in enumerate(segments):
            if seg['id'] == phrase.segment_id:
                current_idx = idx
                break
        
        if current_idx is None:
            return None
        
        # Vérifier les N phrases suivantes
        extended_end = phrase.end
        phrases_added = 0
        
        for i in range(1, num_next + 1):
            next_idx = current_idx + i
            if next_idx >= len(segments):
                break
            
            next_segment = segments[next_idx]
            
            # Vérifier que c'est le même intervenant
            if next_segment['speaker'] != phrase.speaker:
                break
            
            # Étendre jusqu'à la fin de cette phrase
            extended_end = next_segment['end']
            phrases_added += 1
        
        return extended_end if phrases_added > 0 else None
    
    def generate_phrase_montage(self, phrases: List[PhraseMatch], 
                              output_file: str,
                              gap_duration: float = 1.5,
                              fade_in_duration: float = 0.3,
                              fade_out_duration: float = 0.3,
                              normalize: str = "rms",
                              keywords: List[str] = None,
                              include_next_phrases: int = 0) -> str:
        """
        Génère un montage audio des phrases sélectionnées
        
        Args:
            phrases: Liste des phrases à assembler
            output_file: Fichier de sortie
            gap_duration: Silence entre phrases (secondes)
            fade_in_duration: Durée du fondu d'entrée (secondes)
            fade_out_duration: Durée du fondu de sortie (secondes)
            include_next_phrases: Nombre de phrases suivantes du même intervenant à inclure (0 = désactivé)
            
        Returns:
            Chemin du fichier audio généré
        """
        if not phrases:
            raise ValueError("Aucune phrase à assembler")
        
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
            
            # Ajouter un peu de contexte au début (padding)
            padding_ms = 100  # 0.1s de contexte
            start_ms = max(0, start_ms - padding_ms)
            
            # Étendre jusqu'à la fin des phrases suivantes si demandé
            if include_next_phrases > 0:
                extended_end = self._get_next_phrase_same_speaker(phrase, include_next_phrases)
                if extended_end:
                    end_ms = int(extended_end * 1000)
                    duration_added = extended_end - phrase.end
                    print(f"      ↪️  +{include_next_phrases} phrase(s) suivante(s) du même intervenant (+{duration_added:.1f}s)")
                else:
                    end_ms = min(len(source_audio), end_ms + padding_ms)
            else:
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
            
            # Ajouter au montage
            if final_audio is None:
                final_audio = phrase_audio
            else:
                final_audio = final_audio + gap_silence + phrase_audio
        
        # Sauvegarder
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        final_audio.export(str(output_path), format="mp3", bitrate="192k")
        
        # Ajouter les métadonnées détaillées
        self._add_mp3_metadata(str(output_path), phrases, keywords or [], 
                             len(final_audio) / 1000.0)
        
        duration = len(final_audio) / 1000.0
        print(f"✅ Montage généré: {output_path.name}")
        print(f"⏱️ Durée totale: {duration:.1f}s")
        print(f"🎭 Intervenants: {', '.join(set(p.speaker for p in phrases))}")
        print(f"📁 Fichiers source: {', '.join(set(Path(p.file_name).stem for p in phrases))}")
        
        return str(output_path)
    
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
                         keywords: List[str], duration: float):
        """Ajoute les métadonnées complètes au fichier MP3"""
        if not MUTAGEN_AVAILABLE:
            return
            
        try:
            audio_file = MP3(mp3_path, ID3=ID3)
            
            # Créer les tags ID3 si inexistants
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # Informations de base
            audio_file.tags.add(TIT2(encoding=3, text=f"Montage: {', '.join(keywords)}"))
            audio_file.tags.add(TPE1(encoding=3, text="Amours Mix-Play"))
            audio_file.tags.add(TALB(encoding=3, text="Generated Montages"))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            audio_file.tags.add(TCON(encoding=3, text="Speech/Podcast"))
            
            # Statistiques générales avec des tags personnalisés
            intervenants = list(set(p.speaker for p in phrases))
            fichiers = list(set(Path(p.file_name).stem for p in phrases))
            
            # Métadonnées globales structurées
            audio_file.tags.add(COMM(encoding=3, lang='fra', desc='amour_search', text=', '.join(keywords)))
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
            print(f"📋 Métadonnées structurées ajoutées au MP3 ({len(phrases)} phrases)")
            
        except Exception as e:
            print(f"⚠️ Erreur métadonnées MP3: {e}")
    
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

def main():
    """Interface en ligne de commande"""
    
    # Initialiser seed aléatoire basé sur l'horodatage pour garantir la variation
    seed = int(time.time() * 1000000) % 2147483647  # Utiliser les microsecondes
    random.seed(seed)
    print(f"🎲 Seed aléatoire: {seed}")
    
    if len(sys.argv) < 3:
        print("Usage: python phrase_montage.py <nombre_phrases> <mot-clé1> [mot-clé2] [--love-type type1,type2]")
        print()
        print("Exemples:")
        print("  python phrase_montage.py 3 amour")
        print("  python phrase_montage.py 5 amour vie bonheur")
        print("  python phrase_montage.py 3 relation --love-type romantique,familial")
        print("  python phrase_montage.py 4 passion --love-type erotique")
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
    
    print(f"🎯 Recherche de {num_phrases} phrases avec mots-clés: {', '.join(keywords)}")
    print()
    
    # Initialiser le sélecteur
    selector = PhraseSelector()
    selector.load_phrases()
    
    # Rechercher les phrases avec plus de variation
    matches = selector.search_phrases(
        keywords, 
        max_results=num_phrases * 5,  # Encore plus de candidats pour plus de variation
        max_duration=15.0,  # Maximum 15 secondes par phrase
        diversify_sources=True  # Diversifier les sources
    )
    
    if not matches:
        print("❌ Aucune phrase trouvée avec ces mots-clés")
        print()
        print("💡 Essayez avec des mots plus courants ou moins spécifiques")
        sys.exit(1)
    
    print(f"🔍 {len(matches)} phrases trouvées:")
    print("-" * 50)
    
    # Afficher les candidats
    selected_phrases = matches[:num_phrases]
    
    for i, phrase in enumerate(selected_phrases, 1):
        print(f"{i:2d}. 📝 {phrase.text}")
        print(f"     🎯 Mots trouvés: {', '.join(phrase.keywords_found)}")
        print(f"     📁 {Path(phrase.file_name).stem} | 🎭 {phrase.speaker} | ⭐ {phrase.match_score:.1f}")
        print(f"     ⏱️ {phrase.start:.1f}s - {phrase.end:.1f}s ({phrase.end - phrase.start:.1f}s)")
        print()
    
    # Générer le montage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3])  # Max 3 mots dans le nom
    output_file = f"output_mix_play/montage_{keywords_str}_{num_phrases}phrases_{timestamp}.mp3"
    
    try:
        audio_file = selector.generate_phrase_montage(
            selected_phrases,
            output_file,
            gap_duration=1.5,  # 1.5s de silence entre phrases
            fade_in_duration=0.2,
            fade_out_duration=0.2,
            normalize="rms",  # Normalisation RMS pour équilibrer les volumes
            keywords=keywords  # Passer les mots-clés pour métadonnées
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
                print(f"📂 Fichier: {audio_file}")
        else:
            print(f"📂 Fichier généré: {audio_file}")
    
    except Exception as e:
        print(f"❌ Erreur génération: {e}")

if __name__ == "__main__":
    main()