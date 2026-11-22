import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

try:
    from About import AboutWindow
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from About import AboutWindow


class IceCreamWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("IceCreamWindow")
        self.setWindowTitle("Ice Cream Sales Profits")
        self.resize(900, 620)

        self.temperatures = []
        self.revenues = []

        self.about_window = None
        self.init_ui()
        self.load_stylesheet()
        self.plot_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Top control bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.load_btn = QPushButton("Load File", self)
        self.load_btn.setObjectName("load_btn")
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.clicked.connect(self.open_file_dialog)
        top_bar.addWidget(self.load_btn)

        self.file_label = QLabel("No file loaded", self)
        self.file_label.setObjectName("file_label")
        top_bar.addWidget(self.file_label)

        top_bar.addStretch()

        self.about_btn = QPushButton("About", self)
        self.about_btn.setObjectName("about_btn")
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.clicked.connect(self.open_about)
        top_bar.addWidget(self.about_btn)

        main_layout.addLayout(top_bar)

        # Embedded matplotlib graph card (with zoom & save toolbar)
        graph_card = QFrame(self)
        graph_card.setObjectName("graph_card")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(12, 10, 12, 12)
        graph_layout.setSpacing(6)

        self.figure = Figure(figsize=(8, 5), facecolor="#ffffff")
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas, stretch=1)

        main_layout.addWidget(graph_card, stretch=1)

    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Ice Cream CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path:
            self.file_label.setText(os.path.basename(file_path))
            self.on_load_file(file_path)

    def open_about(self):
        if self.about_window is None:
            self.about_window = AboutWindow()
        self.about_window.show()
        self.about_window.raise_()
        self.about_window.activateWindow()

    def on_load_file(self, file_path: str):
        if file_path == '':
            return

        self.temperatures = []
        self.revenues = []
        try:
            with open(file_path, "r") as rows:
                graph_lines = rows.readlines()
                for i in range(1, len(graph_lines)):
                    temp, revenue = graph_lines[i].strip().split(",")
                    print(f"temp: {temp}, revenue: {revenue}")
                    self.temperatures.append(float(temp))
                    self.revenues.append(float(revenue))
                self.plot_data()    
        except Exception:
            print(f"Error reading file: {file_path}")
                    
                    

                
        

    def plot_data(self):
        self.ax.clear()
        self.ax.scatter(self.temperatures, self.revenues, color="#0284c7",s=1)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_title("Ice Cream Sales Profits vs. Outside Temperature")
        self.ax.set_xlabel("Outside Temperature (C°)")
        self.ax.set_ylabel("Revenue (NIS)")
        self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    window = IceCreamWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
