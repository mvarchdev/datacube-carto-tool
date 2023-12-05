import threading
from pathlib import Path
import main


def get_file_code(district_code, num_classes, color_palette_name):
    return str(district_code) + str(num_classes) + str(color_palette_name)

class MapGenerationManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = {}  # Dictionary to hold the status of each district

    def generate_map_for_district(self, district_code, num_classes, color_palette_name):
        with self.lock:
            if get_file_code(district_code, num_classes, color_palette_name) in self.status and self.status[get_file_code(district_code, num_classes, color_palette_name)] == 'Processing':
                return False  # Already processing

            self.status[get_file_code(district_code, num_classes, color_palette_name)] = 'Processing'
            thread = threading.Thread(target=self._generate_map, args=(district_code, num_classes, color_palette_name,))
            thread.start()
            return True

    def _generate_map(self, district_code, num_classes, color_palette_name):
        try:
            main.process_district(district_code, num_classes, color_palette_name)
            self.status[get_file_code(district_code, num_classes, color_palette_name)] = 'Completed'
        except Exception as e:
            self.status[get_file_code(district_code, num_classes, color_palette_name)] = f'Error: {e}'

    def get_status(self, district_code, num_classes, color_palette_name):
        return self.status.get(get_file_code(district_code, num_classes, color_palette_name), 'Not started')


map_generation_manager = MapGenerationManager()
