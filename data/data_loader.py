from PySide6.QtCore import QThread, Signal
import pandas as pd
import logging
from time import perf_counter
from utils.helpers import validate_and_resolve_path, normalize_dataframe_columns

logger = logging.getLogger(__name__)

class DataLoaderThread(QThread):
    data_loaded = Signal(pd.DataFrame)
    error_occurred = Signal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        start_time = perf_counter()
        try:
            path = validate_and_resolve_path(self.file_path, fallback_subdir="")
            logger.info(f"Loading Excel file: {path}")
            data = pd.read_excel(path, engine="openpyxl")
            
            data = normalize_dataframe_columns(data)
            
            self.data_loaded.emit(data)
            logger.info(f"Data loading completed in {perf_counter() - start_time:.2f} seconds")
        except FileNotFoundError as e:
            msg = str(e)
            logger.error(msg, exc_info=True)
            self.error_occurred.emit(msg)
        except Exception as e:
            msg = f"Failed to load Excel file: {e}"
            logger.error(msg, exc_info=True)
            self.error_occurred.emit(msg)