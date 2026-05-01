import sys
from pathlib import Path
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QComboBox, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSize

#ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg", "ffmpeg")

def get_ffmpeg_path():
    
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        
        base_path = os.path.dirname(os.path.abspath(__file__))
    

    ext = ".exe"
    return os.path.join(base_path, "ffmpeg", f"ffmpeg{ext}")

ffmpeg_path = get_ffmpeg_path()
class Worker(QThread):
    finished = Signal()
    def __init__(self, file, mode):
        super().__init__()
        self.file = file
        self.mode = mode

    def run(self):
        output_file = str(Path(self.file).parent / f"(compressed){Path(self.file).stem}.mp3")
        modes = {
            "smallest": [ffmpeg_path, "-i", self.file, "-ac", "1", "-ar", "22050", "-b:a", "32k", "-y", output_file],
            "medium": [ffmpeg_path, "-i", self.file, "-ac", "1", "-ar", "22050", "-b:a", "64k", "-y", output_file],
            "large": [ffmpeg_path, "-i", self.file, "-ac", "1", "-ar", "44100", "-b:a", "96k", "-y", output_file]
        }
        cmd = modes.get(self.mode, modes["smallest"])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.finished.emit()

class DropLabel(QFrame):
    file_dropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Drag & Drop Audio File Here\n(or click Select File)")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        
        self.setObjectName("DropArea")
        self.label.setObjectName("DropLabelText")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.label.setText(Path(file_path).name)
        self.file_dropped.emit(file_path)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Audio Compressor")
        self.resize(900, 840)
        # Base dimensions for scaling calculations
        self.base_width = 450
        self.base_height = 500
        self.setMinimumSize(self.base_width, self.base_height)
        
        self.file_path = None
        
        # 1. Main Layout Setup
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # 2. Initialize Widgets as Instance Variables
        self.header = QLabel("Audio Compressor")
        self.header.setObjectName("Header")

        self.drop_area = DropLabel()
        
        self.mode_label = QLabel("Compression Quality")
        self.mode_label.setObjectName("ModeLabel")

        self.mode_select = QComboBox()
        self.mode_select.addItems(["smallest", "medium", "large"])
        self.mode_select.setEditable(True)
        self.mode_select.lineEdit().setReadOnly(True)
        self.mode_select.lineEdit().setAlignment(Qt.AlignCenter)
        
        self.select_btn = QPushButton("Select File Manually")
        
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setValue(0)

        self.compress_btn = QPushButton("Compress Now")
        self.compress_btn.setObjectName("CompressBtn")
        self.compress_btn.setCursor(Qt.PointingHandCursor)

        # 3. Assemble Layout with Stretch Factors
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.drop_area, stretch=4) 
        self.main_layout.addWidget(self.mode_label)
        self.main_layout.addWidget(self.mode_select, stretch=1)
        self.main_layout.addWidget(self.select_btn, stretch=1)
        self.main_layout.addWidget(self.progress, stretch=1)
        self.main_layout.addWidget(self.compress_btn, stretch=1)

        # 4. Connections
        self.drop_area.file_dropped.connect(self.set_file)
        self.select_btn.clicked.connect(self.select_file)
        self.compress_btn.clicked.connect(self.start_compression)

        # Initial style application
        self.apply_styles()

    def resizeEvent(self, event):
        """ Handles dynamic scaling of fonts and padding on resize """
        multiplier = self.width() / self.base_width * 0.8
        
        # Calculate dynamic sizes
        header_font = 22 * multiplier
        button_font = 11 * multiplier
        label_font = 14 * multiplier
        padding_val = 5 * multiplier
        radius_val = 8 * multiplier

        dynamic_css = f"""
            QLabel#Header {{ font-size: {header_font}px; font-weight: bold; margin-bottom: {10 * multiplier}px; }}
            QLabel#ModeLabel {{ font-size: {12 * multiplier}px; color: #717D8A; font-weight: bold; }}
            
            QPushButton {{ 
                font-size: {button_font}px; 
                padding: {padding_val}px; 
                border-radius: {radius_val}px; 
            }}
            
            QComboBox {{ 
                font-size: {button_font}px; 
                padding: {8 * multiplier}px; 
                border-radius: {radius_val}px; 
            }}
            
            QProgressBar {{ 
                font-size: {button_font}px; 
                min-height: {20 * multiplier}px; 
                border-radius: {radius_val}px; 
            }}
            
            #DropLabelText {{ font-size: {label_font}px; font-weight: bold; color: #A0AAB4; }}
            #DropArea {{ border: {2 * multiplier}px dashed #4A5C66; border-radius: {12 * multiplier}px; }}
        """
        self.apply_styles(dynamic_css)
        super().resizeEvent(event)

    def apply_styles(self, dynamic_extra=""):
        base_style = """
            QWidget { background-color: #0F1419; }
            QLabel { color: white; }
            
            #DropArea { background-color: #1E262C; }
            
            QPushButton { background-color: #35434C; color: white; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #455561; }
            QPushButton:pressed { background-color: #2A353C; }
            
            #CompressBtn { background-color: #0078D4; }
            #CompressBtn:hover { background-color: #1084DE; }
            
            QComboBox { background-color: #1E262C; color: white; font-weight: bold; border: 1px solid #35434C; }
            QComboBox QAbstractItemView { background-color: #1E262C; color: white; selection-background-color: #35434C; }
            
            QProgressBar { background-color: #1E262C; color: white; border: none; text-align: center; }
            QProgressBar::chunk { background-color: #0078D4; border-radius: 4px; }
        """
        self.setStyleSheet(base_style + dynamic_extra)

    def set_file(self, file):
        self.file_path = file

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Audio")
        if file:
            self.set_file(file)
            self.drop_area.label.setText(Path(file).name)

    def start_compression(self):
        if not self.file_path:
            self.drop_area.label.setText("Please select a file first")
            return

        self.compress_btn.setEnabled(False)
        self.progress.setRange(0, 0)
        self.worker = Worker(self.file_path, self.mode_select.currentText())
        self.worker.finished.connect(self.finish_compression)
        self.worker.start()

    def finish_compression(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.compress_btn.setEnabled(True)
        self.drop_area.label.setText("Success! File Compressed.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
