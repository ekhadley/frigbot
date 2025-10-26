import logging
import os
import json
from pathlib import Path
from datetime import datetime

MAX_LOG_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'data'):
            log_data['data'] = record.data
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

class SizedRotatingFileHandler(logging.FileHandler):
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.index = 0
        
        # Find the most recent log file and continue using it if under size limit
        existing_logs = sorted(self.log_dir.glob('frigbot_*.jsonl'))
        if existing_logs:
            latest_log = existing_logs[-1]
            if os.path.getsize(latest_log) < MAX_LOG_FILE_SIZE:
                self.current_file = latest_log
            else:
                self.current_file = self._get_new_filename()
        else:
            self.current_file = self._get_new_filename()
        
        super().__init__(self.current_file, mode='a', encoding='utf-8')
    
    def _get_new_filename(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'frigbot_{timestamp}_{self.index:03d}.jsonl'
        self.index += 1
        return self.log_dir / filename
    
    def emit(self, record):
        if os.path.exists(self.baseFilename) and os.path.getsize(self.baseFilename) >= MAX_LOG_FILE_SIZE:
            self.close()
            self.baseFilename = str(self._get_new_filename())
            self.stream = self._open()
        super().emit(record)

def setup_logging():
    file_handler = SizedRotatingFileHandler('logs')
    console_handler = logging.StreamHandler()
    
    file_handler.setFormatter(JsonFormatter())
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
    ))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger('frigbot')
