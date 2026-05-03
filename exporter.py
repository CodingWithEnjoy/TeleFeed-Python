import json
import os

class Exporter:
    def __init__(self, export_dir="export"):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        
    def export_to_json(self, channel_name, data):
        """Export channel data to a JSON file, matching the Go output structure"""
        filename = f"{channel_name}.json"
        filepath = os.path.join(self.export_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return filepath