from pathlib import Path
import traceback
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QLineEdit, QSpinBox, QDoubleSpinBox, QProgressBar, QVBoxLayout, QHBoxLayout,
    QFormLayout, QMessageBox, QGroupBox)
from src.video_engine import analyze_video
from src.clip_splitter import split_video_timeline
from src.clip_exporter import export_clips

class ProcessingWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    def __init__(self, video, output, minimum, maximum, overlap):
        super().__init__()
        self.video, self.output = Path(video), Path(output)
        self.minimum, self.maximum, self.overlap = minimum, maximum, overlap
    @Slot()
    def run(self):
        try:
            self.status.emit("Lecture de la durée de la vidéo…")
            info = analyze_video(self.video)
            segments = split_video_timeline(info["duration"], self.minimum, self.maximum, self.overlap)
            self.status.emit(f"Découpage en {len(segments)} clip(s)…")
            def update(done, total, filename):
                self.progress.emit(round(done * 100 / total))
                self.status.emit(f"Clip {done}/{total} créé : {filename}")
            outputs = export_clips(self.video, self.output, segments, self.video.stem, update)
            self.progress.emit(100)
            self.finished.emit(f"{len(outputs)} clip(s) créé(s) dans :\\n{self.output}")
        except Exception as exc:
            self.error.emit(f"{exc}\\n\\n{traceback.format_exc()}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Clip Maker — Découpage uniquement")
        self.resize(680, 430)
        self.video = QLineEdit(); self.video.setReadOnly(True)
        pick_video = QPushButton("Choisir…"); pick_video.clicked.connect(self.choose_video)
        row_video = QHBoxLayout(); row_video.addWidget(self.video); row_video.addWidget(pick_video)
        self.output = QLineEdit(); self.output.setReadOnly(True)
        pick_output = QPushButton("Choisir…"); pick_output.clicked.connect(self.choose_output)
        row_output = QHBoxLayout(); row_output.addWidget(self.output); row_output.addWidget(pick_output)
        self.minimum = QSpinBox(); self.minimum.setRange(1, 3600); self.minimum.setValue(30); self.minimum.setSuffix(" s")
        self.maximum = QSpinBox(); self.maximum.setRange(1, 3600); self.maximum.setValue(34); self.maximum.setSuffix(" s")
        self.overlap = QDoubleSpinBox(); self.overlap.setRange(0, 3599); self.overlap.setDecimals(1); self.overlap.setValue(2); self.overlap.setSuffix(" s")
        group = QGroupBox("Paramètres")
        form = QFormLayout(); form.addRow("Durée minimale :", self.minimum); form.addRow("Durée maximale :", self.maximum); form.addRow("Chevauchement :", self.overlap); group.setLayout(form)
        self.start = QPushButton("Découper la vidéo"); self.start.clicked.connect(self.start_cut)
        self.progress = QProgressBar(); self.progress.setRange(0, 100)
        self.status = QLabel("Choisis une vidéo et un dossier de destination."); self.status.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Vidéo à découper :")); layout.addLayout(row_video)
        layout.addWidget(QLabel("Dossier de destination :")); layout.addLayout(row_output)
        layout.addWidget(group); layout.addWidget(self.start); layout.addWidget(self.progress); layout.addWidget(self.status)
        central = QWidget(); central.setLayout(layout); self.setCentralWidget(central)
        self.thread = None; self.worker = None
    def choose_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une vidéo", "", "Vidéos (*.mp4 *.mov *.mkv *.avi *.webm)")
        if path:
            self.video.setText(path)
            if not self.output.text(): self.output.setText(str(Path(path).parent))
    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination")
        if path: self.output.setText(path)
    def start_cut(self):
        video, output = self.video.text().strip(), self.output.text().strip()
        if not video or not Path(video).is_file():
            QMessageBox.warning(self, "Vidéo manquante", "Choisis une vidéo valide."); return
        if not output or not Path(output).is_dir():
            QMessageBox.warning(self, "Dossier manquant", "Choisis un dossier de destination valide."); return
        if self.maximum.value() < self.minimum.value():
            QMessageBox.warning(self, "Paramètres invalides", "La durée maximale doit être >= à la durée minimale."); return
        if self.overlap.value() >= self.minimum.value():
            QMessageBox.warning(self, "Paramètres invalides", "Le chevauchement doit être inférieur à la durée minimale."); return
        self.start.setEnabled(False); self.progress.setValue(0); self.status.setText("Préparation…")
        self.thread = QThread(self)
        self.worker = ProcessingWorker(video, output, self.minimum.value(), self.maximum.value(), self.overlap.value())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue); self.worker.status.connect(self.status.setText)
        self.worker.finished.connect(self.done); self.worker.error.connect(self.failed)
        self.worker.finished.connect(self.thread.quit); self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup); self.thread.start()
    @Slot(str)
    def done(self, message):
        self.status.setText("Découpage terminé.")
        QMessageBox.information(self, "Terminé", message)
    @Slot(str)
    def failed(self, message):
        self.status.setText("Erreur pendant le découpage.")
        QMessageBox.critical(self, "Erreur", message.split("\\n\\n", 1)[0])
    @Slot()
    def cleanup(self):
        self.start.setEnabled(True)
        if self.worker: self.worker.deleteLater()
        self.worker = None
        if self.thread: self.thread.deleteLater()
        self.thread = None
