"""
Module Mix-Play pour composer de nouvelles phrases à partir des transcriptions existantes.

Ce module permet de :
- Charger et indexer tous les mots des transcriptions avec leurs timecodes
- Rechercher des mots spécifiques dans différents enregistrements
- Composer de nouvelles phrases en utilisant les extraits audio originaux
- Générer un fichier audio final mixé avec les différentes voix
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import unicodedata
from pydub import AudioSegment
from collections import defaultdict
import difflib


@dataclass
class WordMatch:
    """Représente un mot trouvé dans les transcriptions avec toutes ses métadonnées."""
    word: str
    cleaned_word: str
    start: float
    end: float
    duration: float
    confidence: float
    speaker: str
    file_path: str
    file_name: str
    segment_id: int
    audio_path: str


@dataclass
class ComposedSentence:
    """Représente une phrase composée avec les mots sélectionnés."""
    text: str
    words: List[WordMatch]
    total_duration: float
    speakers_used: List[str]
    files_used: List[str]


class MixPlayer:
    """
    Classe principale pour le système Mix-Play.
    
    Permet de charger les transcriptions, d'indexer les mots, 
    et de composer de nouvelles phrases à partir des extraits audio.
    """
    
    def __init__(self, transcription_dir: str = "output_transcription", audio_dir: str = "audio"):
        """
        Initialise le MixPlayer.
        
        Args:
            transcription_dir: Répertoire contenant les fichiers de transcription JSON
            audio_dir: Répertoire contenant les fichiers audio originaux
        """
        self.transcription_dir = Path(transcription_dir)
        self.audio_dir = Path(audio_dir)
        self.word_index: Dict[str, List[WordMatch]] = defaultdict(list)
        self.transcriptions_loaded = False
        self.audio_cache: Dict[str, AudioSegment] = {}
    
    def clean_word(self, word: str) -> str:
        """
        Nettoie un mot pour la recherche (supprime ponctuation, normalise les accents).
        
        Args:
            word: Le mot à nettoyer
            
        Returns:
            Le mot nettoyé et normalisé
        """
        # Supprimer les espaces en début/fin
        word = word.strip()
        
        # Supprimer la ponctuation commune
        word = re.sub(r'[.,;:!?"\'\-\(\)\[\]{}]', '', word)
        
        # Normaliser les accents et convertir en minuscules
        word = unicodedata.normalize('NFD', word.lower())
        word = ''.join(c for c in word if not unicodedata.combining(c))
        
        return word
    
    def load_transcriptions(self) -> None:
        """
        Charge toutes les transcriptions et indexe les mots.
        """
        print("🎵 Chargement des transcriptions...")
        
        # Réinitialiser l'index
        self.word_index.clear()
        
        # Parcourir tous les fichiers JSON de transcription
        json_files = list(self.transcription_dir.glob("*_complete.json"))
        
        if not json_files:
            raise FileNotFoundError(f"Aucun fichier de transcription trouvé dans {self.transcription_dir}")
        
        for json_file in json_files:
            self._load_single_transcription(json_file)
        
        total_words = sum(len(matches) for matches in self.word_index.values())
        unique_words = len(self.word_index)
        
        print(f"✅ {len(json_files)} transcriptions chargées")
        print(f"📚 {total_words} mots indexés ({unique_words} mots uniques)")
        
        self.transcriptions_loaded = True
    
    def _load_single_transcription(self, json_path: Path) -> None:
        """
        Charge une transcription unique et indexe ses mots.
        
        Args:
            json_path: Chemin vers le fichier JSON de transcription
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraire le nom du fichier audio original
            file_name = data['metadata']['file']
            audio_path = data['metadata']['path']
            
            # Parcourir tous les segments
            for segment in data['transcription']['segments']:
                segment_id = segment['id']
                speaker = segment['speaker']
                
                # Parcourir tous les mots du segment
                for word_data in segment.get('words', []):
                    word = word_data['word']
                    cleaned = self.clean_word(word)
                    
                    # Ignorer les mots vides après nettoyage
                    if not cleaned:
                        continue
                    
                    # Créer l'objet WordMatch
                    word_match = WordMatch(
                        word=word,
                        cleaned_word=cleaned,
                        start=word_data['start'],
                        end=word_data['end'],
                        duration=word_data['duration'],
                        confidence=word_data['confidence'],
                        speaker=speaker,
                        file_path=str(json_path),
                        file_name=file_name,
                        segment_id=segment_id,
                        audio_path=audio_path
                    )
                    
                    # Ajouter à l'index
                    self.word_index[cleaned].append(word_match)
        
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de {json_path}: {e}")
    
    def search_word(self, search_term: str, max_results: int = 10) -> List[WordMatch]:
        """
        Recherche un mot dans l'index avec algorithme strict.
        
        Args:
            search_term: Le terme à rechercher
            max_results: Nombre maximum de résultats à retourner
            
        Returns:
            Liste des correspondances trouvées, triées par pertinence
        """
        if not self.transcriptions_loaded:
            self.load_transcriptions()
        
        cleaned_search = self.clean_word(search_term)
        
        # 1. Recherche exacte d'abord (priorité absolue)
        exact_matches = self.word_index.get(cleaned_search, [])
        if exact_matches:
            exact_matches.sort(key=lambda x: x.confidence, reverse=True)
            return exact_matches[:max_results]
        
        # 2. Recherche par préfixe/suffixe pour conjugaisons/déclinaisons
        prefix_matches = []
        suffix_matches = []
        
        for word_key in self.word_index.keys():
            # Correspondances par préfixe (pour conjugaisons)
            if len(cleaned_search) >= 3 and word_key.startswith(cleaned_search):
                prefix_matches.extend(self.word_index[word_key])
            # Correspondances par suffixe (pour les mots composés)
            elif len(cleaned_search) >= 3 and word_key.endswith(cleaned_search):
                suffix_matches.extend(self.word_index[word_key])
        
        # Combiner préfixe et suffixe, trier par confiance
        morphological_matches = prefix_matches + suffix_matches
        if morphological_matches:
            morphological_matches.sort(key=lambda x: x.confidence, reverse=True)
            return morphological_matches[:max_results]
        
        # 3. Recherche floue très stricte (seuil élevé)
        similar_words = difflib.get_close_matches(
            cleaned_search, 
            self.word_index.keys(), 
            n=3,  # Moins de candidats
            cutoff=0.9  # Seuil très élevé pour éviter les fausses correspondances
        )
        
        if similar_words:
            matches = []
            for similar_word in similar_words:
                # Double vérification : calculer la similarité réelle
                similarity = difflib.SequenceMatcher(None, cleaned_search, similar_word).ratio()
                if similarity >= 0.85:  # Seuil encore plus strict
                    matches.extend(self.word_index[similar_word])
            
            if matches:
                matches.sort(key=lambda x: x.confidence, reverse=True)
                return matches[:max_results]
        
        # 4. En dernier recours, recherche phonétique simple
        # Pour les mots très courts ou avec variantes d'orthographe courantes
        if len(cleaned_search) <= 3:
            phonetic_matches = []
            for word_key in self.word_index.keys():
                if abs(len(word_key) - len(cleaned_search)) <= 1:
                    # Différence de Hamming pour mots courts
                    differences = sum(1 for a, b in zip(cleaned_search, word_key) if a != b)
                    if differences <= 1:  # Maximum 1 caractère différent
                        phonetic_matches.extend(self.word_index[word_key])
            
            if phonetic_matches:
                phonetic_matches.sort(key=lambda x: x.confidence, reverse=True)
                return phonetic_matches[:max_results]
        
        # Aucune correspondance trouvée
        return []
    
    def find_best_word_match(self, search_term: str, 
                           preferred_speakers: Optional[List[str]] = None,
                           min_confidence: float = 0.5,
                           used_sources: Optional[Dict[str, int]] = None,
                           prioritize_diversity: bool = True) -> Optional[WordMatch]:
        """
        Trouve la meilleure correspondance pour un mot donné en privilégiant la diversité des sources.
        
        Args:
            search_term: Le terme à rechercher
            preferred_speakers: Liste des intervenants préférés (optionnel)
            min_confidence: Confiance minimum requise
            used_sources: Dictionnaire des sources déjà utilisées {"file_speaker": count}
            prioritize_diversity: Si True, privilégie les sources moins utilisées
            
        Returns:
            La meilleure correspondance trouvée ou None
        """
        matches = self.search_word(search_term, max_results=50)
        
        # Filtrer par confiance minimum
        matches = [m for m in matches if m.confidence >= min_confidence]
        
        if not matches:
            return None
        
        # Si des intervenants préférés sont spécifiés, les prioriser
        if preferred_speakers:
            preferred_matches = [m for m in matches if m.speaker in preferred_speakers]
            if preferred_matches:
                matches = preferred_matches
        
        # Si on privilégie la diversité et qu'on a l'historique des sources
        if prioritize_diversity and used_sources:
            # Calculer un score pour chaque match basé sur confiance + diversité
            scored_matches = []
            
            for match in matches:
                source_key = f"{Path(match.file_name).stem}_{match.speaker}"
                usage_count = used_sources.get(source_key, 0)
                
                # Score de diversité : plus une source est utilisée, moins elle est prioritaire
                diversity_bonus = 1.0 / (1 + usage_count * 0.3)  # Diminue graduellement
                
                # Score combiné : confiance * bonus de diversité
                combined_score = match.confidence * diversity_bonus
                
                scored_matches.append((combined_score, match))
            
            # Trier par score combiné décroissant
            scored_matches.sort(key=lambda x: x[0], reverse=True)
            
            # Retourner le match avec le meilleur score
            return scored_matches[0][1]
        
        # Sinon, retourner simplement le match avec la meilleure confiance
        return matches[0]
    
    def compose_sentence(self, words: List[str], 
                        preferred_speakers: Optional[List[str]] = None,
                        min_confidence: float = 0.5,
                        max_gap_duration: float = 0.5,
                        prioritize_diversity: bool = True) -> ComposedSentence:
        """
        Compose une phrase en recherchant les meilleurs mots disponibles avec diversité des sources.
        
        Args:
            words: Liste des mots à composer
            preferred_speakers: Intervenants préférés (optionnel)
            min_confidence: Confiance minimum pour chaque mot
            max_gap_duration: Durée maximum de silence entre les mots (secondes)
            prioritize_diversity: Si True, privilégie la variété des sources
            
        Returns:
            La phrase composée
        """
        if not self.transcriptions_loaded:
            self.load_transcriptions()
        
        selected_words = []
        missing_words = []
        used_sources = {}  # Tracker des sources utilisées: {"file_speaker": count}
        
        print(f"🎭 COMPOSITION AVEC DIVERSITÉ DES SOURCES" if prioritize_diversity else "🎭 COMPOSITION STANDARD")
        print("-" * 40)
        
        for i, word in enumerate(words, 1):
            match = self.find_best_word_match(
                word, 
                preferred_speakers=preferred_speakers,
                min_confidence=min_confidence,
                used_sources=used_sources,
                prioritize_diversity=prioritize_diversity
            )
            
            if match:
                selected_words.append(match)
                
                # Mettre à jour le compteur des sources utilisées
                source_key = f"{Path(match.file_name).stem}_{match.speaker}"
                used_sources[source_key] = used_sources.get(source_key, 0) + 1
                
                # Afficher le détail de sélection
                usage_count = used_sources[source_key]
                source_indicator = "🔄" if usage_count > 1 else "✨"
                print(f"{i:2d}. '{word}' → '{match.word}' {source_indicator}")
                print(f"     📁 {Path(match.file_name).stem} | 🎭 {match.speaker} | ⏱️ {match.start:.1f}s")
                if usage_count > 1:
                    print(f"     🔄 Source utilisée {usage_count} fois")
                print()
            else:
                missing_words.append(word)
                print(f"{i:2d}. '{word}' → ❌ NON TROUVÉ")
        
        if missing_words:
            print(f"⚠️  Mots non trouvés: {', '.join(missing_words)}")
            
        # Statistiques de diversité
        print(f"📊 STATISTIQUES DE DIVERSITÉ:")
        print(f"   🎯 {len(selected_words)} mots sélectionnés")
        print(f"   📁 {len(set(Path(w.file_name).stem for w in selected_words))} fichiers utilisés")
        print(f"   🎭 {len(set(w.speaker for w in selected_words))} intervenants utilisés")
        print(f"   🔄 {len([s for s in used_sources.values() if s > 1])} sources réutilisées")
        print()
        
        # Calculer la durée totale (mots + silences entre les mots)
        total_duration = sum(word.duration for word in selected_words)
        if len(selected_words) > 1:
            total_duration += max_gap_duration * (len(selected_words) - 1)
        
        # Statistiques
        speakers_used = list(set(word.speaker for word in selected_words))
        files_used = list(set(word.file_name for word in selected_words))
        
        # Créer le texte composé
        composed_text = " ".join(word.word.strip() for word in selected_words)
        
        return ComposedSentence(
            text=composed_text,
            words=selected_words,
            total_duration=total_duration,
            speakers_used=speakers_used,
            files_used=files_used
        )
    
    def _load_audio_file(self, audio_path: str) -> AudioSegment:
        """
        Charge un fichier audio en cache.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            L'objet AudioSegment
        """
        if audio_path not in self.audio_cache:
            print(f"🎵 Chargement de {Path(audio_path).name}...")
            self.audio_cache[audio_path] = AudioSegment.from_file(audio_path)
        
        return self.audio_cache[audio_path]
    
    def generate_mixed_audio(self, composed_sentence: ComposedSentence,
                           output_path: str,
                           gap_duration: float = 0.3,
                           crossfade_duration: int = 50,
                           word_padding: float = 0.1,
                           normalize_volume: bool = True,
                           fade_mode: str = "standard",
                           tempo_factor: float = 1.0,
                           preserve_pitch: bool = True) -> str:
        """
        Génère un fichier audio mixé à partir d'une phrase composée.
        
        Args:
            composed_sentence: La phrase composée
            output_path: Chemin de sortie pour le fichier audio
            gap_duration: Durée du silence entre les mots (secondes)
            crossfade_duration: Durée du crossfade entre segments (ms)
            word_padding: Padding autour de chaque mot (secondes)
            normalize_volume: Normaliser le volume de chaque segment
            fade_mode: Mode de fondu ("standard", "artistic", "seamless")
            tempo_factor: Facteur de vitesse (0.5 = plus lent, 2.0 = plus rapide)
            preserve_pitch: Préserver le pitch lors du changement de tempo
            
        Returns:
            Le chemin du fichier généré
        """
        if not composed_sentence.words:
            raise ValueError("Aucun mot à mixer")
        
        print(f"🎬 Génération audio mixé - Mode: {fade_mode}, Tempo: {tempo_factor}x")
        
        # Créer le silence entre les mots
        gap_silence = AudioSegment.silent(duration=int(gap_duration * 1000))
        
        segments = []
        
        # Traiter chaque mot avec les nouveaux paramètres
        for i, word in enumerate(composed_sentence.words):
            segment = self._process_word_segment(
                word, word_padding, normalize_volume, fade_mode, tempo_factor, preserve_pitch
            )
            segments.append(segment)
            print(f"  • Mot {i+1}/{len(composed_sentence.words)}: '{word.word.strip()}' ({len(segment)/1000:.2f}s)")
        
        # Assembler selon le mode de fondu
        print("🔗 Assemblage des segments...")
        if fade_mode == "seamless":
            mixed_audio = self._seamless_assembly(segments, gap_duration, crossfade_duration)
        elif fade_mode == "artistic":
            mixed_audio = self._artistic_assembly(segments, gap_duration, crossfade_duration)
        else:
            mixed_audio = self._standard_assembly(segments, gap_duration, crossfade_duration)
        
        # Normalisation finale du volume
        if normalize_volume:
            mixed_audio = mixed_audio.normalize(headroom=10.0)
        
        # Exporter le fichier final
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        mixed_audio.export(output_path, format="mp3", bitrate="192k")
        
        print(f"✅ Audio mixé généré: {output_path}")
        print(f"📊 Durée finale: {len(mixed_audio) / 1000:.2f}s")
        print(f"🎭 Intervenants: {', '.join(composed_sentence.speakers_used)}")
        print(f"🎵 Fichiers source: {', '.join(composed_sentence.files_used)}")
        print(f"⚙️  Paramètres: mode={fade_mode}, tempo={tempo_factor}x, padding={word_padding}s")
        
        return str(output_path)
    
    def _process_word_segment(self, word: WordMatch, padding: float, normalize: bool,
                            fade_mode: str, tempo_factor: float, preserve_pitch: bool) -> AudioSegment:
        """Traite un segment de mot avec tous les effets."""
        # Charger l'audio source
        audio = self._load_audio_file(word.audio_path)
        
        # Calculer les limites avec padding
        padding_ms = int(padding * 1000)
        start_ms = max(0, int(word.start * 1000) - padding_ms)
        end_ms = min(len(audio), int(word.end * 1000) + padding_ms)
        
        # Extraire le segment
        segment = audio[start_ms:end_ms]
        
        # Ajuster le tempo si nécessaire
        if tempo_factor != 1.0:
            segment = self._change_tempo(segment, tempo_factor, preserve_pitch)
        
        # Normalisation
        if normalize:
            segment = segment.normalize(headroom=20.0)
        
        # Appliquer le fade selon le mode
        if fade_mode == "artistic":
            # Fade beaucoup plus long et progressif
            fade_duration = min(300, len(segment) // 2)  # Jusqu'à 300ms, ou la moitié du segment
            if len(segment) > fade_duration * 2:
                segment = segment.fade_in(fade_duration).fade_out(fade_duration)
        elif fade_mode == "seamless":
            # Fade très court pour préserver la parole
            fade_duration = min(15, len(segment) // 10)
            if len(segment) > fade_duration * 2:
                segment = segment.fade_in(fade_duration).fade_out(fade_duration)
        else:  # standard
            fade_duration = min(50, len(segment) // 4)
            if len(segment) > fade_duration * 2:
                segment = segment.fade_in(fade_duration).fade_out(fade_duration)
        
        return segment
    
    def _change_tempo(self, segment: AudioSegment, factor: float, preserve_pitch: bool) -> AudioSegment:
        """Change le tempo d'un segment audio."""
        try:
            import librosa
            import numpy as np
            import soundfile as sf
            import tempfile
            import os
            
            # Méthode alternative plus robuste avec fichiers temporaires
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                    try:
                        # Exporter le segment vers un fichier temporaire
                        segment.export(temp_input.name, format="wav")
                        temp_input.flush()
                        
                        # Charger avec librosa
                        y, sr = librosa.load(temp_input.name, sr=None)
                        
                        if preserve_pitch:
                            # Changer seulement le tempo, préserver le pitch
                            y_stretched = librosa.effects.time_stretch(y, rate=factor)
                        else:
                            # Changer tempo et pitch ensemble (simple resample)
                            y_stretched = librosa.effects.time_stretch(y, rate=factor)
                        
                        # Sauvegarder le résultat
                        sf.write(temp_output.name, y_stretched, sr)
                        
                        # Recharger en AudioSegment
                        new_segment = AudioSegment.from_wav(temp_output.name)
                        
                        return new_segment
                        
                    finally:
                        # Nettoyer les fichiers temporaires
                        try:
                            os.unlink(temp_input.name)
                            os.unlink(temp_output.name)
                        except:
                            pass
            
        except ImportError:
            print("⚠️ librosa/soundfile non disponible, tempo inchangé")
            print("📦 Installation: pip install librosa soundfile")
            return segment
        except Exception as e:
            print(f"⚠️ Erreur changement tempo: {e}, tempo inchangé")
            return segment
    
    def _standard_assembly(self, segments: List[AudioSegment], gap_duration: float, 
                         crossfade_duration: int) -> AudioSegment:
        """Assemblage standard avec silences et crossfade simple."""
        gap_silence = AudioSegment.silent(duration=int(gap_duration * 1000))
        mixed_audio = segments[0]
        
        for segment in segments[1:]:
            mixed_audio = mixed_audio + gap_silence
            
            if crossfade_duration > 0 and len(mixed_audio) > crossfade_duration and len(segment) > crossfade_duration:
                mixed_audio = mixed_audio.append(segment, crossfade=crossfade_duration)
            else:
                mixed_audio = mixed_audio + segment
        
        return mixed_audio
    
    def _artistic_assembly(self, segments: List[AudioSegment], gap_duration: float,
                         crossfade_duration: int) -> AudioSegment:
        """Assemblage artistique avec fondus longs et chevauchements."""
        mixed_audio = segments[0]
        
        for segment in segments[1:]:
            # Fondu artistique beaucoup plus long
            artistic_crossfade = max(crossfade_duration, 400)  # Au moins 400ms
            gap_silence = AudioSegment.silent(duration=max(0, int(gap_duration * 1000) - artistic_crossfade))
            
            if len(gap_silence) > 0:
                mixed_audio = mixed_audio + gap_silence
            
            # Chevauchement artistique long
            if len(mixed_audio) > artistic_crossfade and len(segment) > artistic_crossfade:
                mixed_audio = mixed_audio.append(segment, crossfade=artistic_crossfade)
            else:
                mixed_audio = mixed_audio + segment
        
        return mixed_audio
    
    def _seamless_assembly(self, segments: List[AudioSegment], gap_duration: float,
                         crossfade_duration: int) -> AudioSegment:
        """Assemblage seamless avec fondus courts et gaps minimaux."""
        mixed_audio = segments[0]
        
        for segment in segments[1:]:
            # Gap minimal pour le mode seamless
            minimal_gap = max(50, int(gap_duration * 1000) // 3)
            gap_silence = AudioSegment.silent(duration=minimal_gap)
            
            mixed_audio = mixed_audio + gap_silence
            
            # Crossfade court mais présent
            seamless_crossfade = min(crossfade_duration, 30)
            if len(mixed_audio) > seamless_crossfade and len(segment) > seamless_crossfade:
                mixed_audio = mixed_audio.append(segment, crossfade=seamless_crossfade)
            else:
                mixed_audio = mixed_audio + segment
        
        return mixed_audio
    
    def get_word_statistics(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les mots indexés.
        
        Returns:
            Dictionnaire contenant les statistiques
        """
        if not self.transcriptions_loaded:
            self.load_transcriptions()
        
        # Compter les mots par intervenant
        speaker_counts = defaultdict(int)
        file_counts = defaultdict(int)
        confidence_scores = []
        
        for word_list in self.word_index.values():
            for word in word_list:
                speaker_counts[word.speaker] += 1
                file_counts[word.file_name] += 1
                confidence_scores.append(word.confidence)
        
        # Calculer les statistiques
        total_words = sum(len(matches) for matches in self.word_index.values())
        unique_words = len(self.word_index)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            "total_words": total_words,
            "unique_words": unique_words,
            "average_confidence": avg_confidence,
            "speakers": dict(speaker_counts),
            "files": dict(file_counts),
            "most_common_words": sorted(
                [(word, len(matches)) for word, matches in self.word_index.items()],
                key=lambda x: x[1],
                reverse=True
            )[:20]
        }
    
    def export_composed_sentence_info(self, composed_sentence: ComposedSentence, 
                                    output_path: str) -> str:
        """
        Exporte les informations détaillées d'une phrase composée en JSON.
        
        Args:
            composed_sentence: La phrase composée
            output_path: Chemin de sortie pour le fichier JSON
            
        Returns:
            Le chemin du fichier généré
        """
        # Convertir en dictionnaire sérialisable
        export_data = {
            "metadata": {
                "text": composed_sentence.text,
                "total_duration": composed_sentence.total_duration,
                "speakers_used": composed_sentence.speakers_used,
                "files_used": composed_sentence.files_used,
                "words_count": len(composed_sentence.words),
                "generation_date": None  # Sera ajouté par l'appelant si nécessaire
            },
            "words": [asdict(word) for word in composed_sentence.words]
        }
        
        # Exporter vers JSON
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Informations exportées: {output_path}")
        
        return str(output_path)