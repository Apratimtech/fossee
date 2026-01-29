"""
Chemical Equipment Parameter Visualizer – Desktop (PyQt5 + Matplotlib).
"""
import sys
import os

os.environ["QT_API"] = "qt5"
import matplotlib
matplotlib.use("Qt5Agg")

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSplitter,
    QScrollArea,
    QFrame,
    QHeaderView,
    QAbstractItemView,
    QProgressBar,
    QDialog,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from api_client import (
    login,
    upload_file,
    get_summary,
    get_data,
    get_history,
    download_pdf,
)

# Project root (parent of frontend-desktop); sample CSV lives here.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


DEMO_USER, DEMO_PASS = "admin", "admin"


def _default_api_base():
    return os.environ.get("API_BASE", "http://localhost:8000")


# ----- Login -----


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in")
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Chemical Equipment Parameter Visualizer"))
        layout.addWidget(QLabel("Sign in to continue"))

        form = QFormLayout()
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Username")
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Username", self.user_edit)
        form.addRow("Password", self.pass_edit)
        layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #f85149;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        demo = QPushButton("Use demo (admin / admin)")
        demo.clicked.connect(self._on_demo)
        layout.addWidget(demo)

        self.credentials = None

    def _on_demo(self):
        self.user_edit.setText(DEMO_USER)
        self.pass_edit.setText(DEMO_PASS)
        self._on_ok()

    def _on_ok(self):
        u = self.user_edit.text().strip()
        p = self.pass_edit.text()
        self.error_label.setText("")
        if not u or not p:
            self.error_label.setText("Username and password required.")
            return
        try:
            if login(u, p):
                self.credentials = (u, p)
                self.accept()
            else:
                self.error_label.setText("Invalid username or password.")
        except Exception as e:
            self.error_label.setText(str(e))

    def get_credentials(self):
        return self.credentials


# ----- Workers (avoid blocking UI) -----


class Worker(QThread):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            out = self.fn(*self.args, **self.kwargs)
            self.result.emit(out)
        except Exception as e:
            self.error.emit(str(e))


# ----- Matplotlib canvas -----


class MplCanvas(FigureCanvas):
    def __init__(self, fig: Figure, parent=None):
        super().__init__(fig)
        self.setParent(parent)
        self.setMinimumSize(320, 220)


# ----- Main window -----


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Parameter Visualizer (Desktop)")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self.credentials = None  # (user, pass)
        self.history = []
        self.selected = None
        self.summary = None
        self.data = []
        self._workers = []

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        # Toolbar
        tb = QHBoxLayout()
        self.upload_btn = QPushButton("Upload CSV")
        self.upload_btn.clicked.connect(self._upload)
        self.refresh_btn = QPushButton("Refresh history")
        self.refresh_btn.clicked.connect(self._fetch_history)
        self.pdf_btn = QPushButton("Download PDF report")
        self.pdf_btn.clicked.connect(self._download_pdf)
        self.pdf_btn.setEnabled(False)
        self.logout_btn = QPushButton("Sign out")
        self.logout_btn.clicked.connect(self._logout)
        self.user_label = QLabel("")
        tb.addWidget(self.upload_btn)
        tb.addWidget(self.refresh_btn)
        tb.addWidget(self.pdf_btn)
        tb.addStretch()
        tb.addWidget(self.user_label)
        tb.addWidget(self.logout_btn)
        layout.addLayout(tb)

        # Main content
        split = QSplitter(Qt.Horizontal)
        self.history_list = QListWidget()
        self.history_list.setMaximumWidth(280)
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.currentItemChanged.connect(self._on_history_select)
        split.addWidget(self._wrap_group("History (last 5)", self.history_list))

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.summary_label = QLabel("Select an upload or upload a new CSV.")
        self.summary_label.setWordWrap(True)
        self.scroll_layout.addWidget(self.summary_label)

        self.charts_widget = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_widget)
        self.charts_layout.setContentsMargins(0, 8, 0, 8)
        self.scroll_layout.addWidget(self.charts_widget)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scroll_layout.addWidget(self.table)

        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        split.addWidget(right)

        split.setSizes([280, 700])
        layout.addWidget(split)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _wrap_group(self, title, w):
        g = QGroupBox(title)
        g_layout = QVBoxLayout(g)
        g_layout.setContentsMargins(6, 12, 6, 6)
        g_layout.addWidget(w)
        return g

    def _run(self, fn, *args, on_result=None, on_error=None, **kwargs):
        def _on_result(x):
            if on_result:
                on_result(x)
            self.progress.setVisible(False)

        def _on_error(msg):
            QMessageBox.warning(self, "Error", msg)
            self.progress.setVisible(False)
            if on_error:
                on_error(msg)

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        w = Worker(fn, *args, **kwargs)
        w.result.connect(_on_result)
        w.error.connect(_on_error)
        self._workers.append(w)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        w.start()

    def _upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV", _PROJECT_ROOT, "CSV (*.csv)"
        )
        if not path:
            return
        u, p = self.credentials

        def do():
            return upload_file(path, u, p)

        def ok(res):
            self.history = [res] + [h for h in self.history if h.get("id") != res.get("id")]
            self.history = self.history[:5]
            self._refresh_history_list()
            self._select_by_id(res.get("id"))
            self._fetch_summary_and_data(res["id"])

        self._run(do, on_result=ok)

    def _fetch_history(self):
        u, p = self.credentials

        def do():
            return get_history(u, p)

        def ok(h):
            self.history = h
            self._refresh_history_list()
            if self.history and not self.selected:
                self._select_by_id(self.history[0]["id"])
                self._fetch_summary_and_data(self.history[0]["id"])
            elif self.selected:
                bid = self.selected.get("id")
                if not any(x.get("id") == bid for x in self.history):
                    self.selected = self.history[0] if self.history else None
                    if self.selected:
                        self._fetch_summary_and_data(self.selected["id"])

        self._run(do, on_result=ok)

    def _refresh_history_list(self):
        self.history_list.blockSignals(True)
        self.history_list.clear()
        for h in self.history:
            item = QListWidgetItem(h.get("filename", "?"))
            item.setData(Qt.UserRole, h)
            self.history_list.addItem(item)
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            d = item.data(Qt.UserRole)
            if d.get("id") == (self.selected or {}).get("id"):
                self.history_list.setCurrentItem(item)
                break
        self.history_list.blockSignals(False)

    def _on_history_select(self, current, _prev):
        if not current:
            return
        d = current.data(Qt.UserRole)
        self._select_by_id(d.get("id"))
        self._fetch_summary_and_data(d["id"])

    def _select_by_id(self, id_):
        for h in self.history:
            if h.get("id") == id_:
                self.selected = h
                self.pdf_btn.setEnabled(True)
                return
        self.selected = None
        self.pdf_btn.setEnabled(False)

    def _fetch_summary_and_data(self, upload_id):
        u, p = self.credentials

        def do():
            s = get_summary(upload_id, u, p)
            d = get_data(upload_id, u, p)
            return s, d

        def ok(pair):
            s, d = pair
            self.summary = s
            self.data = d.get("data") or []
            self._render_summary()
            self._render_charts()
            self._render_table()

        self._run(do, on_result=ok)

    def _render_summary(self):
        s = self.summary or {}
        sm = s.get("summary") or s
        tot = sm.get("total_count", 0)
        av = sm.get("averages") or {}
        self.summary_label.setText(
            f"<b>{s.get('filename', '')}</b><br><br>"
            f"Total count: <b>{tot}</b><br>"
            f"Averages — Flowrate: <b>{av.get('flowrate', '—')}</b>, "
            f"Pressure: <b>{av.get('pressure', '—')}</b>, "
            f"Temperature: <b>{av.get('temperature', '—')}</b>"
        )

    def _render_charts(self):
        while self.charts_layout.count():
            child = self.charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        sm = (self.summary or {}).get("summary") or self.summary or {}
        dist = sm.get("type_distribution") or {}
        av = sm.get("averages") or {}
        if not dist and not av:
            return

        row = QHBoxLayout()
        if dist:
            fig = Figure(figsize=(5, 3), facecolor="#161b22")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#161b22")
            ax.tick_params(colors="#8b949e")
            ax.spines["bottom"].set_color("#30363d")
            ax.spines["left"].set_color("#30363d")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            labels = list(dist.keys())
            vals = list(dist.values())
            ax.bar(labels, vals, color="#58a6ff", edgecolor="#58a6ff")
            ax.set_ylabel("Count", color="#e6edf3")
            ax.set_title("Equipment type distribution", color="#e6edf3")
            fig.tight_layout()
            canvas = MplCanvas(fig)
            row.addWidget(canvas, 1)
        if av:
            fig2 = Figure(figsize=(4, 3), facecolor="#161b22")
            ax2 = fig2.add_subplot(111)
            ax2.set_facecolor("#161b22")
            ax2.tick_params(colors="#8b949e")
            ax2.spines["bottom"].set_color("#30363d")
            ax2.spines["left"].set_color("#30363d")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            keys = ["Flowrate", "Pressure", "Temperature"]
            vals = [av.get("flowrate", 0), av.get("pressure", 0), av.get("temperature", 0)]
            ax2.bar(keys, vals, color=["#3fb950", "#d29922", "#f85149"], edgecolor="#30363d")
            ax2.set_ylabel("Average", color="#e6edf3")
            ax2.set_title("Averages", color="#e6edf3")
            fig2.tight_layout()
            canvas2 = MplCanvas(fig2)
            row.addWidget(canvas2, 1)
        self.charts_layout.addLayout(row)

    def _render_table(self):
        self.table.clear()
        rows = self.data or []
        if not rows:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        cols = list(rows[0].keys())
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([str(c).replace("_", " ").title() for c in cols])
        for i, r in enumerate(rows):
            for j, c in enumerate(cols):
                v = r.get(c)
                self.table.setItem(i, j, QTableWidgetItem(str(v) if v is not None else "—"))

    def _download_pdf(self):
        if not self.selected:
            return
        u, p = self.credentials
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", f"report_{self.selected.get('filename', '')}.pdf", "PDF (*.pdf)"
        )
        if not path:
            return

        def do():
            download_pdf(self.selected["id"], path, u, p)

        def ok():
            QMessageBox.information(self, "Done", f"Saved to {path}")

        self._run(do, on_result=ok)

    def _logout(self):
        self.credentials = None
        self.history = []
        self.selected = None
        self.summary = None
        self.data = []
        self.history_list.clear()
        self.summary_label.setText("Select an upload or upload a new CSV.")
        self._render_charts()
        self._render_table()
        self.pdf_btn.setEnabled(False)
        self.user_label.setText("")
        self.hide()
        app = QApplication.instance()
        if app:
            d = LoginDialog(self)
            if d.exec_() == QDialog.Accepted:
                self.credentials = d.get_credentials()
                self.user_label.setText(self.credentials[0])
                self._fetch_history()
                self.show()
            else:
                app.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    d = LoginDialog()
    if d.exec_() != QDialog.Accepted:
        return
    creds = d.get_credentials()
    w = MainWindow()
    w.credentials = creds
    w.user_label.setText(creds[0])
    w._fetch_history()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
