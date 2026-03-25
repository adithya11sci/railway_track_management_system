"""
Data Ingestion Agent - Reads and parses timetable files, track data, and train metadata.
Uses the chennai_central_real_dataset.csv as the primary source of truth.
"""
import pandas as pd
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionAgent:
    """
    Responsible for:
    - Loading train data from CSV.
    - Normalizing train types and priorities.
    - Filtering data for specific scenarios if needed.
    """

    def __init__(self, dataset_path: str = "chennai_central_real_dataset.csv"):
        self.dataset_path = dataset_path
        # Map train types to scores as per requirement
        # Premium trains (4), Peak passenger (3), Regular passenger (2), Goods (1)
        self.priority_map = {
            "Premium Express": 4,
            "Rajdhani Express": 4,
            "Duronto Express": 4,
            "Shatabdi Exp": 4,
            "Vande Bharat": 4,
            "Superfast Express": 3,
            "Mail Express": 3,
            "Express": 2,
            "Double Decker": 2,
            "Garib Rath": 2,
            "Passenger": 2,
            "Goods": 1,
            "Freight": 1
        }

    def load_data(self) -> List[Dict[str, Any]]:
        """Reads the CSV and returns a list of train dictionaries."""
        if not os.path.exists(self.dataset_path):
            logger.error(f"Dataset not found at {self.dataset_path}")
            return []

        try:
            df = pd.read_csv(self.dataset_path)
            # Basic cleaning
            df = df.fillna("")
            
            trains = []
            for _, row in df.iterrows():
                train_id = str(row['train_id'])
                if not train_id: continue
                
                train_type = row.get('train_type', 'Express')
                priority_score = self._get_priority_score(train_type)
                
                train_data = {
                    "train_id": train_id,
                    "train_name": row.get('train_name', ''),
                    "train_type": train_type,
                    "priority_score": priority_score,
                    "source": row.get('source_station', ''),
                    "destination": row.get('destination_station', ''),
                    "scheduled_arrival": row.get('scheduled_arrival', '--'),
                    "scheduled_departure": row.get('scheduled_departure', '--'),
                    "platform": row.get('platform', ''),
                    "track_number": row.get('track_number', 1),
                    "direction": row.get('direction', 'Arrival'),
                    "intermediate_stops": row.get('intermediate_stops', '')
                }
                trains.append(train_data)
            
            logger.info(f"Successfully ingested {len(trains)} trains from dataset.")
            return trains
        except Exception as e:
            logger.error(f"Error ingesting data: {e}")
            return []

    def _get_priority_score(self, train_type: str) -> int:
        """Determines priority score based on train type string."""
        for key, score in self.priority_map.items():
            if key.lower() in train_type.lower():
                return score
        return 2  # Default to Regular Passenger
