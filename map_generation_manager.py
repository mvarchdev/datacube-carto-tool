import threading
from pathlib import Path
import processor

def get_file_code(district_code, num_classes, color_palette_name):
    """
    Generates a unique file code for each map generation task.
    """
    return f"{district_code}_{num_classes}_{color_palette_name}"

class MapGenerationManager:
    """
    Manages the generation of maps for different districts in separate threads.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.status = {}  # Dictionary to hold the status of each district

    def generate_map_for_district(self, district_code, num_classes, color_palette_name):
        """
        Initiates map generation for a specific district in a separate thread.
        """
        file_code = get_file_code(district_code, num_classes, color_palette_name)
        with self.lock:
            if self.status.get(file_code) == 'Processing':
                return False  # Already processing

            self.status[file_code] = 'Processing'
            thread = threading.Thread(target=self._generate_map, args=(district_code, num_classes, color_palette_name,))
            thread.start()
            return True

    def _generate_map(self, district_code, num_classes, color_palette_name):
        """
        Internal method to generate a map for a district.
        """
        file_code = get_file_code(district_code, num_classes, color_palette_name)
        try:
            processor.process_district(district_code, num_classes, color_palette_name)
            self.status[file_code] = 'Completed'
        except Exception as e:
            self.status[file_code] = f'Error: {e}'

    def get_status(self, district_code, num_classes, color_palette_name):
        """
        Retrieves the status of a map generation task.
        """
        return self.status.get(get_file_code(district_code, num_classes, color_palette_name), 'Not started')


map_generation_manager = MapGenerationManager()
