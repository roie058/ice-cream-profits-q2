import os
import sys
import numpy as np 

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
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
        self.slope = None
        self.intercept = None
        self.prediction_artists = []
        self.hover_annotation = None
        self.hover_temps = []

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

        unit_label = QLabel("Unit:", self)
        unit_label.setProperty("class", "stat-label")
        top_bar.addWidget(unit_label)

        self.unit_combo = QComboBox(self)
        self.unit_combo.setObjectName("unit_combo")
        self.unit_combo.addItems(["°C", "°F"])
        self.unit_combo.setCursor(Qt.PointingHandCursor)
        self.unit_combo.currentIndexChanged.connect(self.on_unit_changed)
        top_bar.addWidget(self.unit_combo)

        self.about_btn = QPushButton("About", self)
        self.about_btn.setObjectName("about_btn")
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.clicked.connect(self.open_about)
        top_bar.addWidget(self.about_btn)

        main_layout.addLayout(top_bar)

        # Live Summary Statistics & R² Bar
        stats_bar = QFrame(self)
        stats_bar.setObjectName("stats_bar")
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(14, 8, 14, 8)
        stats_layout.setSpacing(16)

        self.count_label = QLabel("Days: --", self)
        self.avg_temp_label = QLabel("Avg Temp: --", self)
        self.avg_rev_label = QLabel("Avg Profit: --", self)
        self.peak_rev_label = QLabel("Peak Profit: --", self)
        self.r2_label = QLabel("R²: --", self)

        for lbl in (
            self.count_label,
            self.avg_temp_label,
            self.avg_rev_label,
            self.peak_rev_label,
            self.r2_label,
        ):
            lbl.setProperty("class", "stat-label")
            stats_layout.addWidget(lbl)

        stats_layout.addStretch()
        main_layout.addWidget(stats_bar)

        # Embedded matplotlib graph card (with zoom & save toolbar)
        graph_card = QFrame(self)
        graph_card.setObjectName("graph_card")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(12, 10, 12, 12)
        graph_layout.setSpacing(6)

        self.figure = Figure(figsize=(8, 5), facecolor="#ffffff")
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas, stretch=1)

        main_layout.addWidget(graph_card, stretch=1)

        #Interactive Profit Predictor Bar
        predict_bar = QFrame(self)
        predict_bar.setObjectName("predict_bar")
        predict_layout = QHBoxLayout(predict_bar)
        predict_layout.setContentsMargins(14, 8, 14, 8)
        predict_layout.setSpacing(10)

        predict_prompt = QLabel("Predict Profit for Temp:", self)
        predict_prompt.setProperty("class", "stat-label")
        predict_layout.addWidget(predict_prompt)

        self.predict_temp_input = QDoubleSpinBox(self)
        self.predict_temp_input.setObjectName("predict_temp_input")
        self.predict_temp_input.setRange(-20.0, 120.0)
        self.predict_temp_input.setDecimals(1)
        self.predict_temp_input.setSingleStep(0.5)
        self.predict_temp_input.setValue(25.0)
        self.predict_temp_input.setSuffix(" °C")
        self.predict_temp_input.lineEdit().returnPressed.connect(self._handle_predict_trigger)
        predict_layout.addWidget(self.predict_temp_input)

        self.predict_btn = QPushButton("Predict", self)
        self.predict_btn.setObjectName("predict_btn")
        self.predict_btn.setCursor(Qt.PointingHandCursor)
        self.predict_btn.clicked.connect(self._handle_predict_trigger)
        predict_layout.addWidget(self.predict_btn)

        self.predict_result_label = QLabel("Predicted Profit: --", self)
        self.predict_result_label.setObjectName("predict_result_label")
        predict_layout.addWidget(self.predict_result_label)

        predict_layout.addStretch()
        main_layout.addWidget(predict_bar)

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

                    self.temperatures.append(float(temp))
                    self.revenues.append(float(revenue))
                self.plot_data()    
        except Exception:
            print(f"Error reading file: {file_path}")
                    
                    

                
        

    def plot_data(self):
        self.ax.clear()
        self.prediction_artists = []
        self.slope = None
        self.intercept = None
        temps = self.get_display_temperatures()
        self.hover_temps = temps
        self.ax.scatter(temps, self.revenues, color="#0284c7", s=1)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_title("Ice Cream Sales Profits vs. Outside Temperature")
        self.ax.set_xlabel(f"Outside Temperature {self.unit_combo.currentText()}")
        self.ax.set_ylabel("Revenue ($)")

        if len(temps) >= 2:
            m, b = np.polyfit(temps, self.revenues, 1)
            self.slope, self.intercept = m, b
            x_line = np.array([min(temps), max(temps)])
            y_line = m * x_line + b
            self.ax.plot(x_line, y_line, color="#ef4444", linewidth=2, label="Trendline")

            sign = "+" if b >= 0 else "-"
            equation = f"y = {m:.2f}x {sign} {abs(b):.2f}"
            self.ax.text(
                0.05,
                0.92,
                equation,
                transform=self.ax.transAxes,
                fontsize=11,
                fontweight="bold",
                color="#b91c1c",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#fef2f2", edgecolor="#fecaca"),
            )

        self.hover_annotation = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            fontsize=9,
            color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#ffffff", edgecolor="#94a3b8", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="#64748b", lw=1),
            zorder=10,
        )
        self.hover_annotation.set_visible(False)

        self.canvas.draw()
        self.update_stats()

    def update_stats(self):
        temps = self.get_display_temperatures()
        if len(temps)==0:
            return
        days = len(temps)
        avg_temp = sum(temps)/days
        peak_rev = max(self.revenues)
        avg_rev = sum(self.revenues)/days
        if days>=2:
            r= np.corrcoef(temps, self.revenues)[0,1]
            r2 = r**2
            self.r2_label.setText(f"R²: {r2:.4f}")
       
        self.count_label.setText(f"Days: {days}")
        self.avg_temp_label.setText(f"Avg Temp: {avg_temp:.2f} {self.unit_combo.currentText()}")
        self.avg_rev_label.setText(f"Avg Profit: {avg_rev:.2f}")
        self.peak_rev_label.setText(f"Peak Profit: {peak_rev:.2f}")

    def _handle_predict_trigger(self):
        self.predict_temp_input.interpretText()
        self.on_predict_profit()

    def highlight_prediction(self, temp: float, predicted_profit: float):    
        for artist in self.prediction_artists:
            artist.remove()
        self.prediction_artists.clear()

        vline = self.ax.axvline(temp, color="#16a34a", linestyle="--", linewidth=1, alpha=0.7)
        hline = self.ax.axhline(predicted_profit, color="#16a34a", linestyle="--", linewidth=1, alpha=0.7)
        point = self.ax.scatter([temp], [predicted_profit], color="#16a34a", s=70, zorder=5, edgecolors="#ffffff", linewidths=1.5)
        ann = self.ax.annotate(
            f"({temp:.1f}, ${predicted_profit:.2f})",
            xy=(temp, predicted_profit),
            xytext=(10, -18),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color="#15803d",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0fdf4", edgecolor="#86efac"),
        )
        self.prediction_artists.extend([vline, hline, point, ann])
        self.canvas.draw()

    def on_predict_profit(self):
        if self.slope is None or self.intercept is None:
            self.predict_result_label.setText("Load a file first")
            return
        temp = self.predict_temp_input.value()
        predicted_profit = self.slope * temp + self.intercept
        self.predict_result_label.setText(f"Predicted Profit: ${predicted_profit:.2f}")
        self.highlight_prediction(temp, predicted_profit)

    def get_display_temperatures(self):
        unit = self.unit_combo.currentText()
        if unit == "°F":
            new_temp_list = []
            for t in self.temperatures:
                new_temp_list.append(float(t)*9/5+32)
            return new_temp_list
        return self.temperatures

    def on_unit_changed(self):
        unit = self.unit_combo.currentText()
        self.predict_temp_input.setSuffix(f" {unit}")
        self.predict_result_label.setText("Predicted Profit: --")
        self.plot_data()

    def _on_mouse_move(self, event):
        if self.hover_annotation is None:
            return
        if event.inaxes != self.ax or len(self.hover_temps) == 0:
            if self.hover_annotation.get_visible():
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        points = np.column_stack((self.hover_temps, self.revenues))
        pixel_coords = self.ax.transData.transform(points)
        dists = np.hypot(pixel_coords[:, 0] - event.x, pixel_coords[:, 1] - event.y)
        nearest_idx = int(np.argmin(dists))

        if dists[nearest_idx] <= 12:
            temp = self.hover_temps[nearest_idx]
            rev = self.revenues[nearest_idx]
            text = self.format_hover_tooltip(temp, rev)
            if text:
                self.hover_annotation.xy = (temp, rev)
                self.hover_annotation.set_text(text)
                # Flip tooltip left if near the right edge of the plot
                xlim = self.ax.get_xlim()
                offset_x = -220 if temp > (xlim[0] + xlim[1]) * 0.65 else 12
                self.hover_annotation.set_position((offset_x, 12))
                self.hover_annotation.set_visible(True)
                self.canvas.draw_idle()
                return

        if self.hover_annotation.get_visible():
            self.hover_annotation.set_visible(False)
            self.canvas.draw_idle()

    def format_hover_tooltip(self, temp: float, rev: float) -> str:
        unit = self.unit_combo.currentText()
        if self.slope is not None and self.intercept is not None:
            expected = self.slope * temp + self.intercept
            diff = rev - expected
            sign = "+"
            if diff<0:
                sign = '-'
            return f"Temp: {temp:.1f} {unit}\nProfit: ${rev:.2f} ({sign}${abs(diff):.2f} distance from trend)" 
       
        return f"Temp: {temp:.1f} {unit}\nProfit: ${rev:.2f}"      
            
        
        
        


def main():
    app = QApplication(sys.argv)
    window = IceCreamWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
