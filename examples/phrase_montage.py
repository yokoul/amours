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

class PhraseSelector:
    """Sélecteur et monteur de phrases complètes"""
    
    def __init__(self, transcription_dir: str = "output_transcription", audio_dir: str = "audio"):
        self.transcription_dir = Path(transcription_dir)
        self.audio_dir = Path(audio_dir)
        self.phrases: List[PhraseMatch] = []
        self.audio_cache: Dict[str, AudioSegment] = {}
        
    def load_phrases(self):
        """Charge toutes les phrases des transcriptions"""
        print("📖 Chargement des phrases...")
        
        json_files = list(self.transcription_dir.glob("*.json"))
        
        for json_file in json_files:
            self._load_phrases_from_file(json_file)
        
        print(f"✅ {len(self.phrases)} phrases chargées depuis {len(json_files)} fichiers")
        
    def _load_phrases_from_file(self, json_path: Path):
        """Charge les phrases d'un fichier de transcription"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_name = data['metadata']['file']
            audio_path = self.audio_dir / file_name
            
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
                    match_score=0.0
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
                    match_score=match_score
                )
                
                matches.append(phrase_copy)
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Ajouter une variation aléatoire légère aux scores similaires
        # pour éviter de toujours sélectionner les mêmes phrases
        if len(matches) > max_results:
            for match in matches:
                # Petite variation aléatoire (±5% du score)
                variation = random.uniform(-0.05, 0.05) * match.match_score
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
    
    def generate_phrase_montage(self, phrases: List[PhraseMatch], 
                              output_file: str,
                              gap_duration: float = 1.5,
                              fade_in_duration: float = 0.3,
                              fade_out_duration: float = 0.3) -> str:
        """
        Génère un montage audio des phrases sélectionnées
        
        Args:
            phrases: Liste des phrases à assembler
            output_file: Fichier de sortie
            gap_duration: Silence entre phrases (secondes)
            fade_in_duration: Durée du fondu d'entrée (secondes)
            fade_out_duration: Durée du fondu de sortie (secondes)
            
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
            
            # Ajouter un peu de contexte (padding)
            padding_ms = 100  # 0.1s de contexte
            start_ms = max(0, start_ms - padding_ms)
            end_ms = min(len(source_audio), end_ms + padding_ms)
            
            phrase_audio = source_audio[start_ms:end_ms]
            
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

def main():
    """Interface en ligne de commande"""
    
    if len(sys.argv) < 3:
        print("Usage: python phrase_montage.py <nombre_phrases> <mot-clé1> [mot-clé2] [mot-clé3] ...")
        print()
        print("Exemples:")
        print("  python phrase_montage.py 3 amour")
        print("  python phrase_montage.py 5 amour vie bonheur")
        print("  python phrase_montage.py 2 bonjour salut")
        sys.exit(1)
    
    try:
        num_phrases = int(sys.argv[1])
        keywords = sys.argv[2:]
    except ValueError:
        print("❌ Le nombre de phrases doit être un entier")
        sys.exit(1)
    
    print(f"🎯 Recherche de {num_phrases} phrases avec mots-clés: {', '.join(keywords)}")
    print()
    
    # Initialiser le sélecteur
    selector = PhraseSelector()
    selector.load_phrases()
    
    # Rechercher les phrases
    matches = selector.search_phrases(
        keywords, 
        max_results=num_phrases * 3,  # Plus de candidats
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
            fade_out_duration=0.2
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