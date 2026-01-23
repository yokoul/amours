"""
Gestionnaire d'export des données de transcription.
Supporte les formats JSON et CSV avec structures optimisées pour l'exploitation artistique.
"""

import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class ExportManager:
    """Classe pour l'export des résultats de transcription."""
    
    def __init__(self):
        """Initialise le gestionnaire d'export."""
        pass
    
    def export_json(self, transcription_data: Dict[str, Any], output_path: str) -> None:
        """
        Exporte les données de transcription au format JSON.
        
        Args:
            transcription_data: Données de transcription structurées
            output_path: Chemin de sortie du fichier JSON
        """
        try:
            output_file = Path(output_path)
            
            # S'assurer que l'extension est .json
            if output_file.suffix.lower() != '.json':
                output_file = output_file.with_suffix('.json')
            
            # Créer le dossier parent si nécessaire
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le JSON avec formatage lisible
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(
                    transcription_data, 
                    f, 
                    ensure_ascii=False, 
                    indent=2, 
                    sort_keys=False
                )
            
            print(f"📄 JSON exporté : {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'export JSON : {str(e)}")
    
    def export_csv(self, transcription_data: Dict[str, Any], output_path: str) -> None:
        """
        Exporte les données de transcription au format CSV.
        
        Args:
            transcription_data: Données de transcription structurées
            output_path: Chemin de sortie du fichier CSV
        """
        try:
            output_file = Path(output_path)
            
            # S'assurer que l'extension est .csv
            if output_file.suffix.lower() != '.csv':
                output_file = output_file.with_suffix('.csv')
            
            # Créer le dossier parent si nécessaire
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Préparer les données pour CSV
            csv_data = self._prepare_csv_data(transcription_data)
            
            # Écrire le CSV
            csv_data.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"📊 CSV exporté : {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'export CSV : {str(e)}")
    
    def _prepare_csv_data(self, transcription_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prépare les données pour l'export CSV.
        
        Args:
            transcription_data: Données de transcription
            
        Returns:
            DataFrame pandas avec les données formatées
        """
        rows = []
        metadata = transcription_data["metadata"]
        
        # Parcourir tous les segments et mots
        for segment in transcription_data["transcription"]["segments"]:
            segment_id = segment["id"]
            segment_start = segment["start"]
            segment_end = segment["end"]
            segment_text = segment["text"]
            
            if segment["words"]:
                # Une ligne par mot
                for word_idx, word in enumerate(segment["words"]):
                    row = {
                        # Métadonnées du fichier
                        "file_name": metadata["file"],
                        "file_duration": metadata["duration"],
                        "transcription_date": metadata["transcription_date"],
                        "model_used": metadata["model"],
                        
                        # Informations du segment
                        "segment_id": segment_id,
                        "segment_start": segment_start,
                        "segment_end": segment_end,
                        "segment_duration": segment["duration"],
                        "segment_text": segment_text,
                        
                        # Informations du mot
                        "word_index": word_idx,
                        "word": word["word"],
                        "word_start": word["start"],
                        "word_end": word["end"],
                        "word_duration": word.get("duration", round(word["end"] - word["start"], 3)),
                        "word_confidence": word.get("confidence", 0.0),
                        
                        # Position relative dans le segment
                        "word_position_in_segment": word_idx + 1,
                        "words_in_segment": len(segment["words"])
                    }
                    rows.append(row)
            else:
                # Si pas de mots individuels, une ligne pour le segment
                row = {
                    "file_name": metadata["file"],
                    "file_duration": metadata["duration"],
                    "transcription_date": metadata["transcription_date"],
                    "model_used": metadata["model"],
                    
                    "segment_id": segment_id,
                    "segment_start": segment_start,
                    "segment_end": segment_end,
                    "segment_duration": segment["duration"],
                    "segment_text": segment_text,
                    
                    "word_index": 0,
                    "word": segment_text,
                    "word_start": segment_start,
                    "word_end": segment_end,
                    "word_duration": segment["duration"],
                    "word_confidence": 0.0,
                    
                    "word_position_in_segment": 1,
                    "words_in_segment": 1
                }
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_words_only(self, transcription_data: Dict[str, Any], output_path: str) -> None:
        """
        Exporte uniquement les mots avec leurs timecodes (format simplifié).
        
        Args:
            transcription_data: Données de transcription
            output_path: Chemin de sortie
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            words_data = []
            
            for segment in transcription_data["transcription"]["segments"]:
                for word in segment["words"]:
                    words_data.append({
                        "word": word["word"],
                        "start": word["start"],
                        "end": word["end"],
                        "duration": word["duration"]
                    })
            
            if output_file.suffix.lower() == '.json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(words_data, f, ensure_ascii=False, indent=2)
            else:
                # CSV
                df = pd.DataFrame(words_data)
                df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"📝 Mots exportés : {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'export des mots : {str(e)}")
    
    def export_artistic_format(self, transcription_data: Dict[str, Any], output_path: str) -> None:
        """
        Exporte dans un format optimisé pour l'exploitation artistique.
        
        Args:
            transcription_data: Données de transcription
            output_path: Chemin de sortie
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Format artistique avec timeline
            artistic_data = {
                "project_info": {
                    "source_file": transcription_data["metadata"]["file"],
                    "total_duration": transcription_data["metadata"]["duration"],
                    "created_at": datetime.now().isoformat(),
                    "full_text": transcription_data["transcription"]["text"]
                },
                "timeline": [],
                "vocabulary": {},
                "statistics": {}
            }
            
            # Construire la timeline
            all_words = []
            for segment in transcription_data["transcription"]["segments"]:
                for word in segment["words"]:
                    word_data = {
                        "text": word["word"].strip(),
                        "start": word["start"],
                        "end": word["end"],
                        "duration": word["duration"],
                        "segment_id": segment["id"]
                    }
                    artistic_data["timeline"].append(word_data)
                    all_words.append(word["word"].strip().lower())
            
            # Vocabulaire unique avec fréquences
            from collections import Counter
            word_counts = Counter(all_words)
            artistic_data["vocabulary"] = dict(word_counts.most_common())
            
            # Statistiques
            artistic_data["statistics"] = {
                "total_words": len(all_words),
                "unique_words": len(word_counts),
                "avg_word_duration": sum(w["duration"] for w in artistic_data["timeline"]) / len(artistic_data["timeline"]) if artistic_data["timeline"] else 0,
                "segments_count": len(transcription_data["transcription"]["segments"]),
                "words_per_minute": (len(all_words) / transcription_data["metadata"]["duration"]) * 60 if transcription_data["metadata"]["duration"] > 0 else 0
            }
            
            # Sauvegarder
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(artistic_data, f, ensure_ascii=False, indent=2)
            
            print(f"🎨 Format artistique exporté : {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'export artistique : {str(e)}")
    
    def export_srt_subtitles(self, transcription_data: Dict[str, Any], output_path: str) -> None:
        """
        Exporte au format SRT pour sous-titres.
        
        Args:
            transcription_data: Données de transcription
            output_path: Chemin de sortie (.srt)
        """
        try:
            output_file = Path(output_path)
            if output_file.suffix.lower() != '.srt':
                output_file = output_file.with_suffix('.srt')
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            def format_time(seconds):
                """Formate le temps au format SRT (HH:MM:SS,mmm)."""
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcription_data["transcription"]["segments"], 1):
                    start_time = format_time(segment["start"])
                    end_time = format_time(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
            
            print(f"📺 Sous-titres SRT exportés : {output_file}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'export SRT : {str(e)}")