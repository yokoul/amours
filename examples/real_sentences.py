#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de montage de VRAIES phrases (reconstructions grammaticales)
Reconstruit les phrases à partir des mots individuels dans les JSONs
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

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

@dataclass
class Word:
    """Représente un mot avec ses timecodes"""
    word: str
    start: float
    end: float
    confidence: float

@dataclass
class ReconstructedSentence:
    """Représente une phrase reconstruite"""
    text: str
    words: List[Word]
    file_name: str
    audio_path: str
    speaker: str
    start: float
    end: float
    duration: float
    keywords_found: List[str]
    match_score: float

class SentenceReconstructor:
    """Reconstruit et monte des phrases grammaticales réelles"""
    
    def __init__(self, transcription_dir: str = "output_transcription", audio_dir: str = "audio"):
        self.transcription_dir = Path(transcription_dir)
        self.audio_dir = Path(audio_dir)
        self.sentences: List[ReconstructedSentence] = []
        self.audio_cache: Dict[str, AudioSegment] = {}
        
    def load_sentences(self):
        """Charge et reconstruit toutes les phrases grammaticales"""
        print("📖 Reconstruction des phrases grammaticales...")
        
        json_files = list(self.transcription_dir.glob("*.json"))
        
        for json_file in json_files:
            self._reconstruct_sentences_from_file(json_file)
        
        print(f"✅ {len(self.sentences)} phrases reconstruites depuis {len(json_files)} fichiers")
        
    def _reconstruct_sentences_from_file(self, json_path: Path):
        """Reconstruit les phrases d'un fichier de transcription"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_name = data['metadata']['file']
            audio_path = self.audio_dir / file_name
            
            for segment in data['transcription']['segments']:
                speaker = segment['speaker']
                
                # Récupérer tous les mots du segment avec leurs timecodes
                words = []
                for word_data in segment.get('words', []):
                    word = Word(
                        word=word_data['word'],
                        start=word_data['start'],
                        end=word_data['end'],
                        confidence=word_data.get('confidence', 1.0)
                    )
                    words.append(word)
                
                if not words:
                    continue
                
                # Reconstruire les phrases grammaticales
                sentences = self._split_into_sentences(words)
                
                for sentence_words in sentences:
                    if len(sentence_words) < 3:  # Au moins 3 mots pour une phrase
                        continue
                    
                    # Construire le texte de la phrase
                    text = " ".join(w.word.strip() for w in sentence_words)
                    
                    # Calculer les timecodes
                    start_time = sentence_words[0].start
                    end_time = sentence_words[-1].end
                    duration = end_time - start_time
                    
                    # Filtrer les phrases trop longues
                    if duration > 20.0:  # Maximum 20 secondes pour une phrase
                        continue
                    
                    sentence = ReconstructedSentence(
                        text=text,
                        words=sentence_words,
                        file_name=file_name,
                        audio_path=str(audio_path),
                        speaker=speaker,
                        start=start_time,
                        end=end_time,
                        duration=duration,
                        keywords_found=[],
                        match_score=0.0
                    )
                    
                    self.sentences.append(sentence)
                
        except Exception as e:
            print(f"⚠️ Erreur reconstruction {json_path}: {e}")
    
    def _split_into_sentences(self, words: List[Word]) -> List[List[Word]]:
        """
        Découpe une liste de mots en phrases grammaticales
        Basé sur la ponctuation et les pauses
        """
        sentences = []
        current_sentence = []
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # Fin de phrase si :
            # 1. Ponctuation forte (. ! ? ...)
            # 2. Pause longue après le mot (>1 seconde)
            # 3. Phrase déjà assez longue (>15 mots) + virgule ou pause
            
            is_end_punctuation = re.search(r'[.!?…]', word.word)
            
            next_word_pause = False
            if i < len(words) - 1:
                next_word = words[i + 1]
                pause_duration = next_word.start - word.end
                next_word_pause = pause_duration > 1.0  # Pause > 1 seconde
            
            long_sentence_break = (
                len(current_sentence) > 15 and 
                (re.search(r'[,;:]', word.word) or next_word_pause)
            )
            
            # Fin de phrase détectée
            if is_end_punctuation or next_word_pause or long_sentence_break or i == len(words) - 1:
                if len(current_sentence) >= 3:  # Au moins 3 mots
                    sentences.append(current_sentence.copy())
                current_sentence = []
        
        # Ajouter la dernière phrase si elle existe
        if current_sentence and len(current_sentence) >= 3:
            sentences.append(current_sentence)
        
        return sentences
    
    def search_sentences(self, keywords: List[str], max_results: int = 10, 
                        max_duration: float = 15.0, diversify_sources: bool = True) -> List[ReconstructedSentence]:
        """
        Recherche des phrases contenant les mots-clés
        """
        if not self.sentences:
            self.load_sentences()
        
        # Nettoyer les mots-clés
        clean_keywords = [self._clean_word(kw) for kw in keywords if kw.strip()]
        
        matches = []
        
        for sentence in self.sentences:
            # Filtrer par durée
            if sentence.duration > max_duration:
                continue
                
            # Nettoyer le texte de la phrase
            clean_text = self._clean_word(sentence.text)
            clean_words = clean_text.split()
            
            # Chercher les correspondances
            found_keywords = []
            total_score = 0
            
            for keyword in clean_keywords:
                # Recherche exacte d'abord
                if keyword in clean_words:
                    found_keywords.append(keyword)
                    total_score += 2.0
                else:
                    # Recherche floue
                    similar = difflib.get_close_matches(
                        keyword, clean_words, n=1, cutoff=0.8
                    )
                    if similar:
                        found_keywords.append(f"{keyword}≈{similar[0]}")
                        total_score += 1.0
            
            # Si au moins un mot-clé trouvé
            if found_keywords:
                # Score avec bonus pour phrases courtes
                match_score = (len(found_keywords) / len(clean_keywords)) * total_score
                
                if sentence.duration <= 8.0:
                    match_score *= 1.3
                elif sentence.duration <= 5.0:
                    match_score *= 1.5
                
                sentence_copy = ReconstructedSentence(
                    text=sentence.text,
                    words=sentence.words,
                    file_name=sentence.file_name,
                    audio_path=sentence.audio_path,
                    speaker=sentence.speaker,
                    start=sentence.start,
                    end=sentence.end,
                    duration=sentence.duration,
                    keywords_found=found_keywords,
                    match_score=match_score
                )
                
                matches.append(sentence_copy)
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Diversifier les sources si demandé
        if diversify_sources and len(matches) > max_results:
            matches = self._diversify_sources(matches, max_results)
        else:
            matches = matches[:max_results]
        
        return matches
    
    def _diversify_sources(self, matches: List[ReconstructedSentence], max_results: int) -> List[ReconstructedSentence]:
        """Diversifie les sources dans la sélection finale"""
        selected = []
        used_sources = set()
        
        # Première passe : prendre les meilleurs de chaque source
        for match in matches:
            source_key = f"{Path(match.file_name).stem}_{match.speaker}"
            
            if source_key not in used_sources:
                selected.append(match)
                used_sources.add(source_key)
                
                if len(selected) >= max_results:
                    break
        
        # Deuxième passe : compléter si besoin
        if len(selected) < max_results:
            for match in matches:
                if match not in selected:
                    selected.append(match)
                    if len(selected) >= max_results:
                        break
        
        return selected
    
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
    
    def generate_sentence_montage(self, sentences: List[ReconstructedSentence], 
                                 output_file: str,
                                 gap_duration: float = 1.0,
                                 fade_in_duration: float = 0.1,
                                 fade_out_duration: float = 0.1) -> str:
        """Génère un montage audio des phrases sélectionnées"""
        
        if not sentences:
            raise ValueError("Aucune phrase à assembler")
        
        print(f"🎬 Génération montage de {len(sentences)} phrases grammaticales...")
        
        # Créer le montage
        final_audio = None
        gap_silence = AudioSegment.silent(duration=int(gap_duration * 1000))
        
        for i, sentence in enumerate(sentences, 1):
            print(f"  📝 {i}/{len(sentences)}: {sentence.text}")
            print(f"      ⏱️ {sentence.duration:.1f}s - {len(sentence.words)} mots")
            
            # Charger l'audio source
            source_audio = self._load_audio(sentence.audio_path)
            
            # Extraire la phrase avec un petit padding
            start_ms = max(0, int((sentence.start - 0.1) * 1000))
            end_ms = min(len(source_audio), int((sentence.end + 0.1) * 1000))
            
            sentence_audio = source_audio[start_ms:end_ms]
            
            # Appliquer les fondus
            if fade_in_duration > 0:
                fade_in_ms = int(fade_in_duration * 1000)
                sentence_audio = sentence_audio.fade_in(min(fade_in_ms, len(sentence_audio) // 4))
            
            if fade_out_duration > 0:
                fade_out_ms = int(fade_out_duration * 1000)
                sentence_audio = sentence_audio.fade_out(min(fade_out_ms, len(sentence_audio) // 4))
            
            # Ajouter au montage
            if final_audio is None:
                final_audio = sentence_audio
            else:
                final_audio = final_audio + gap_silence + sentence_audio
        
        # Sauvegarder
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        final_audio.export(str(output_path), format="mp3", bitrate="192k")
        
        duration = len(final_audio) / 1000.0
        print(f"✅ Montage généré: {output_path.name}")
        print(f"⏱️ Durée totale: {duration:.1f}s")
        print(f"🎭 Intervenants: {', '.join(set(s.speaker for s in sentences))}")
        print(f"📁 Fichiers source: {', '.join(set(Path(s.file_name).stem for s in sentences))}")
        
        return str(output_path)
    
    def _load_audio(self, audio_path: str) -> AudioSegment:
        """Charge un fichier audio avec cache"""
        if audio_path not in self.audio_cache:
            print(f"🎵 Chargement {Path(audio_path).name}...")
            self.audio_cache[audio_path] = AudioSegment.from_file(audio_path)
        
        return self.audio_cache[audio_path]

def main():
    """Interface en ligne de commande"""
    
    if len(sys.argv) < 3:
        print("Usage: python real_sentences.py <nombre_phrases> <mot-clé1> [mot-clé2] ...")
        print()
        print("Exemples:")
        print("  python real_sentences.py 3 amour")
        print("  python real_sentences.py 5 amour vie bonheur")
        print("  python real_sentences.py 2 bonjour")
        sys.exit(1)
    
    try:
        num_sentences = int(sys.argv[1])
        keywords = sys.argv[2:]
    except ValueError:
        print("❌ Le nombre de phrases doit être un entier")
        sys.exit(1)
    
    print(f"🎯 Recherche de {num_sentences} phrases grammaticales avec mots-clés: {', '.join(keywords)}")
    print()
    
    # Initialiser le reconstructeur
    reconstructor = SentenceReconstructor()
    reconstructor.load_sentences()
    
    # Rechercher les phrases
    matches = reconstructor.search_sentences(
        keywords, 
        max_results=num_sentences * 2,  # Plus de candidats
        max_duration=15.0,
        diversify_sources=True
    )
    
    if not matches:
        print("❌ Aucune phrase trouvée avec ces mots-clés")
        sys.exit(1)
    
    print(f"🔍 {len(matches)} phrases trouvées:")
    print("-" * 60)
    
    # Sélectionner le nombre demandé
    selected_sentences = matches[:num_sentences]
    
    for i, sentence in enumerate(selected_sentences, 1):
        print(f"{i:2d}. 📝 {sentence.text}")
        print(f"     🎯 Mots trouvés: {', '.join(sentence.keywords_found)}")
        print(f"     📁 {Path(sentence.file_name).stem} | 🎭 {sentence.speaker} | ⭐ {sentence.match_score:.1f}")
        print(f"     ⏱️ {sentence.start:.1f}s - {sentence.end:.1f}s ({sentence.duration:.1f}s) | 🔤 {len(sentence.words)} mots")
        print()
    
    # Générer le montage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3])
    output_file = f"output_mix_play/sentences_{keywords_str}_{num_sentences}phrases_{timestamp}.mp3"
    
    try:
        audio_file = reconstructor.generate_sentence_montage(
            selected_sentences,
            output_file,
            gap_duration=1.0,
            fade_in_duration=0.1,
            fade_out_duration=0.1
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