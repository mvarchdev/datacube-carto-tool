import threading
from pathlib import Path
import main

class MapGenerationManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = {}  # Dictionary to hold the status of each district

    def generate_map_for_district(self, district_code):
        with self.lock:
            if district_code in self.status and self.status[district_code] == 'Processing':
                return False  # Already processing

            self.status[district_code] = 'Processing'
            thread = threading.Thread(target=self._generate_map, args=(district_code,))
            thread.start()
            return True

    def _generate_map(self, district_code):
        try:
            main.process_district(district_code)
            self.status[district_code] = 'Completed'
        except Exception as e:
            self.status[district_code] = f'Error: {e}'

    def get_status(self, district_code):
        return self.status.get(district_code, 'Not started')

map_generation_manager = MapGenerationManager()
