"""
Mix-Play par Groupes de Mots (Chunks) - Version améliorée.

Cette version extrait des groupes de 2-4 mots consécutifs des transcriptions
pour créer des compositions plus naturelles et fluides.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer, WordMatch, ComposedSentence


@dataclass
class WordChunk:
    """Représente un groupe de mots consécutifs."""
    words: List[WordMatch]
    text: str
    start: float
    end: float
    duration: float
    speaker: str
    file_name: str
    file_path: str
    audio_path: str
    average_confidence: float
    
    @property
    def word_count(self) -> int:
        return len(self.words)


class ChunkMixPlayer(MixPlayer):
    """Version du MixPlayer qui travaille avec des groupes de mots."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chunks_index: Dict[str, List[WordChunk]] = {}
        self.chunks_loaded = False
    
    def extract_chunks(self, min_chunk_size: int = 2, max_chunk_size: int = 4,
                      min_confidence: float = 0.7) -> None:
        """
        Extrait tous les groupes de mots possibles des transcriptions.
        
        Args:
            min_chunk_size: Taille minimum d'un chunk (mots)
            max_chunk_size: Taille maximum d'un chunk (mots)
            min_confidence: Confiance minimum pour inclure un chunk
        """
        if not self.transcriptions_loaded:
            self.load_transcriptions()
        
        print(f"🧩 Extraction des chunks ({min_chunk_size}-{max_chunk_size} mots, confiance > {min_confidence:.0%})...")
        
        self.chunks_index.clear()
        total_chunks = 0
        
        # Parcourir tous les fichiers JSON
        for json_file in self.transcription_dir.glob("*_complete.json"):
            chunks_from_file = self._extract_chunks_from_file(
                json_file, min_chunk_size, max_chunk_size, min_confidence
            )
            total_chunks += len(chunks_from_file)
            
            # Indexer les chunks par leur contenu nettoyé
            for chunk in chunks_from_file:
                # Nettoyer le texte pour l'indexation
                clean_text = self._clean_chunk_text(chunk.text)
                if clean_text:  # Ignorer les chunks vides après nettoyage
                    self.chunks_index.setdefault(clean_text, []).append(chunk)
        
        unique_chunks = len(self.chunks_index)
        
        print(f"✅ {total_chunks} chunks extraits ({unique_chunks} uniques)")
        print(f"📊 Taille moyenne: {total_chunks / unique_chunks:.1f} chunks par texte")
        
        self.chunks_loaded = True
    
    def _extract_chunks_from_file(self, json_path: Path, 
                                min_chunk_size: int, max_chunk_size: int,
                                min_confidence: float) -> List[WordChunk]:
        """Extrait les chunks d'un fichier de transcription."""
        import json
        
        chunks = []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_name = data['metadata']['file']
            audio_path = data['metadata']['path']
            
            # Parcourir tous les segments
            for segment in data['transcription']['segments']:
                segment_words = segment.get('words', [])
                
                if len(segment_words) < min_chunk_size:
                    continue
                
                # Extraire tous les chunks possibles de ce segment
                for chunk_size in range(min_chunk_size, min(max_chunk_size + 1, len(segment_words) + 1)):
                    for start_idx in range(len(segment_words) - chunk_size + 1):
                        chunk_words = segment_words[start_idx:start_idx + chunk_size]
                        
                        # Vérifier la confiance moyenne
                        avg_confidence = sum(w['confidence'] for w in chunk_words) / len(chunk_words)
                        if avg_confidence < min_confidence:
                            continue
                        
                        # Créer le WordChunk
                        word_matches = []
                        for word_data in chunk_words:
                            word_match = WordMatch(
                                word=word_data['word'],
                                cleaned_word=self.clean_word(word_data['word']),
                                start=word_data['start'],
                                end=word_data['end'],
                                duration=word_data['duration'],
                                confidence=word_data['confidence'],
                                speaker=word_data['speaker'],
                                file_path=str(json_path),
                                file_name=file_name,
                                segment_id=segment['id'],
                                audio_path=audio_path
                            )
                            word_matches.append(word_match)
                        
                        # Créer le chunk
                        chunk_text = "".join(w['word'] for w in chunk_words)
                        chunk_start = chunk_words[0]['start']
                        chunk_end = chunk_words[-1]['end']
                        
                        chunk = WordChunk(
                            words=word_matches,
                            text=chunk_text,
                            start=chunk_start,
                            end=chunk_end,
                            duration=chunk_end - chunk_start,
                            speaker=chunk_words[0]['speaker'],
                            file_name=file_name,
                            file_path=str(json_path),
                            audio_path=audio_path,
                            average_confidence=avg_confidence
                        )
                        
                        chunks.append(chunk)
        
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des chunks de {json_path}: {e}")
        
        return chunks
    
    def _clean_chunk_text(self, text: str) -> str:
        """Nettoie le texte d'un chunk pour l'indexation."""
        # Supprimer les espaces en début/fin
        text = text.strip()
        
        # Supprimer la ponctuation
        text = re.sub(r'[.,;:!?"\'\-\(\)\[\]{}]', '', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Convertir en minuscules
        text = text.lower()
        
        return text
    
    def search_chunks(self, search_text: str, max_results: int = 10) -> List[WordChunk]:
        """
        Recherche des chunks contenant le texte spécifié.
        
        Args:
            search_text: Texte à rechercher (peut être plusieurs mots)
            max_results: Nombre maximum de résultats
        """
        if not self.chunks_loaded:
            self.extract_chunks()
        
        search_clean = self._clean_chunk_text(search_text)
        
        matches = []
        
        # Recherche exacte d'abord
        if search_clean in self.chunks_index:
            matches.extend(self.chunks_index[search_clean])
        
        # Recherche par inclusion
        for chunk_text, chunk_list in self.chunks_index.items():
            if search_clean in chunk_text or chunk_text in search_clean:
                for chunk in chunk_list:
                    if chunk not in matches:
                        matches.append(chunk)
        
        # Trier par confiance puis par durée (préférer les chunks plus courts)
        matches.sort(key=lambda c: (-c.average_confidence, c.duration))
        
        return matches[:max_results]
    
    def compose_from_chunks(self, target_text: str, 
                          max_chunk_results: int = 5) -> ComposedSentence:
        """
        Compose une phrase en utilisant des chunks de mots.
        
        Args:
            target_text: Texte cible à composer
            max_chunk_results: Nombre maximum de chunks à considérer par recherche
        """
        if not self.chunks_loaded:
            self.extract_chunks()
        
        words = target_text.split()
        selected_chunks = []
        used_words = set()
        
        print(f"🧩 Composition par chunks: {target_text}")
        
        # Essayer de couvrir le texte avec des chunks
        i = 0
        while i < len(words):
            best_chunk = None
            best_coverage = 0
            
            # Essayer des groupes de différentes tailles
            for chunk_size in range(min(4, len(words) - i), 0, -1):
                search_phrase = " ".join(words[i:i + chunk_size])
                chunks = self.search_chunks(search_phrase, max_chunk_results)
                
                for chunk in chunks:
                    # Vérifier si ce chunk couvre bien les mots recherchés
                    coverage = self._calculate_coverage(search_phrase, chunk.text)
                    
                    if coverage > best_coverage:
                        best_coverage = coverage
                        best_chunk = chunk
            
            if best_chunk and best_coverage > 0.5:  # Au moins 50% de correspondance
                selected_chunks.append(best_chunk)
                # Avancer selon la taille du chunk
                chunk_words = len(best_chunk.text.split())
                i += min(chunk_words, len(words) - i)
                print(f"  ✅ Chunk trouvé: '{best_chunk.text.strip()}' (confiance: {best_chunk.average_confidence:.1%})")
            else:
                # Passer au mot suivant si aucun chunk approprié
                print(f"  ❌ Aucun chunk pour: '{words[i]}'")
                i += 1
        
        if not selected_chunks:
            print("⚠️ Aucun chunk trouvé, utilisation de la méthode par mots individuels")
            return self.compose_sentence(words)
        
        # Créer la phrase composée
        all_words = []
        for chunk in selected_chunks:
            all_words.extend(chunk.words)
        
        total_duration = sum(chunk.duration for chunk in selected_chunks) + 0.3 * (len(selected_chunks) - 1)
        speakers_used = list(set(chunk.speaker for chunk in selected_chunks))
        files_used = list(set(chunk.file_name for chunk in selected_chunks))
        composed_text = " ".join(chunk.text.strip() for chunk in selected_chunks)
        
        return ComposedSentence(
            text=composed_text,
            words=all_words,
            total_duration=total_duration,
            speakers_used=speakers_used,
            files_used=files_used
        )
    
    def _calculate_coverage(self, target: str, chunk_text: str) -> float:
        """Calcule le pourcentage de couverture d'un chunk par rapport au target."""
        target_clean = self._clean_chunk_text(target)
        chunk_clean = self._clean_chunk_text(chunk_text)
        
        target_words = set(target_clean.split())
        chunk_words = set(chunk_clean.split())
        
        if not target_words:
            return 0
        
        intersection = target_words.intersection(chunk_words)
        return len(intersection) / len(target_words)
    
    def generate_chunk_audio(self, composed: ComposedSentence, output_path: str,
                           gap_duration: float = 0.2,
                           chunk_padding: float = 0.1) -> str:
        """
        Génère l'audio en traitant chunk par chunk plutôt que mot par mot.
        
        Args:
            composed: La phrase composée
            output_path: Chemin de sortie
            gap_duration: Silence entre chunks
            chunk_padding: Padding autour de chaque chunk
        """
        from pydub import AudioSegment
        
        if not composed.words:
            raise ValueError("Aucun mot à mixer")
        
        print(f"🎵 Génération audio par chunks (padding: {chunk_padding}s)...")
        
        # Regrouper les mots consécutifs du même fichier/speaker
        chunks = self._group_consecutive_words(composed.words)
        
        segments = []
        gap_silence = AudioSegment.silent(duration=int(gap_duration * 1000))
        
        for i, chunk_words in enumerate(chunks):
            # Prendre le premier et dernier mot pour définir les limites
            first_word = chunk_words[0]
            last_word = chunk_words[-1]
            
            # Charger l'audio source
            audio = self._load_audio_file(first_word.audio_path)
            
            # Calculer les limites avec padding
            padding_ms = int(chunk_padding * 1000)
            start_ms = max(0, int(first_word.start * 1000) - padding_ms)
            end_ms = min(len(audio), int(last_word.end * 1000) + padding_ms)
            
            # Extraire le segment complet du chunk
            segment = audio[start_ms:end_ms]
            
            # Normalisation et fade
            segment = segment.normalize(headroom=15.0)
            fade_duration = min(30, len(segment) // 6)
            if len(segment) > fade_duration * 2:
                segment = segment.fade_in(fade_duration).fade_out(fade_duration)
            
            segments.append(segment)
            
            chunk_text = " ".join(w.word.strip() for w in chunk_words)
            print(f"  • Chunk {i+1}: '{chunk_text}' ({len(segment)/1000:.2f}s)")
        
        # Assembler avec des transitions plus douces
        print("🔗 Assemblage des chunks...")
        mixed_audio = segments[0]
        
        for segment in segments[1:]:
            mixed_audio = mixed_audio + gap_silence + segment
        
        # Normalisation finale
        mixed_audio = mixed_audio.normalize(headroom=8.0)
        
        # Export
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mixed_audio.export(output_path, format="mp3", bitrate="192k")
        
        print(f"✅ Audio par chunks généré: {output_path}")
        print(f"📊 {len(chunks)} chunks, durée totale: {len(mixed_audio)/1000:.2f}s")
        
        return str(output_path)
    
    def _group_consecutive_words(self, words: List[WordMatch]) -> List[List[WordMatch]]:
        """Groupe les mots consécutifs du même fichier/segment."""
        if not words:
            return []
        
        groups = []
        current_group = [words[0]]
        
        for i in range(1, len(words)):
            current = words[i]
            previous = words[i-1]
            
            # Même fichier et temps consécutifs (< 2 secondes d'écart)
            if (current.file_name == previous.file_name and 
                current.speaker == previous.speaker and
                (current.start - previous.end) < 2.0):
                current_group.append(current)
            else:
                groups.append(current_group)
                current_group = [current]
        
        groups.append(current_group)
        return groups


def demo_chunk_mixing():
    """Démonstration du système par chunks."""
    
    print("🧩 Démo Mix-Play par Chunks de Mots")
    print("=" * 40)
    
    chunk_player = ChunkMixPlayer()
    chunk_player.extract_chunks(min_chunk_size=2, max_chunk_size=4, min_confidence=0.7)
    
    # Phrases de test
    test_phrases = [
        "bonjour et merci beaucoup",
        "la vie est vraiment belle",
        "avec tout mon amour sincère",
        "dans ce monde merveilleux"
    ]
    
    for phrase in test_phrases:
        print(f"\n🎯 Test: {phrase}")
        print("-" * 30)
        
        # Composition par chunks
        composed = chunk_player.compose_from_chunks(phrase)
        
        if composed.words:
            print(f"✅ Résultat: {composed.text}")
            print(f"📊 {len(composed.words)} mots, {len(composed.speakers_used)} locuteurs")
            
            # Générer l'audio
            timestamp = datetime.now().strftime("%H%M%S")
            safe_name = phrase.replace(" ", "_").replace("'", "")
            output_file = f"output_mix_play/chunk_{safe_name}_{timestamp}.mp3"
            
            try:
                audio_file = chunk_player.generate_chunk_audio(composed, output_file)
                print(f"🎵 Audio généré: {Path(audio_file).name}")
            except Exception as e:
                print(f"❌ Erreur audio: {e}")
        else:
            print("❌ Aucune composition possible")
    
    print(f"\n💡 Les fichiers audio ont été générés dans output_mix_play/")
    print("🎧 Testez-les pour comparer avec la méthode par mots individuels !")


if __name__ == "__main__":
    demo_chunk_mixing()