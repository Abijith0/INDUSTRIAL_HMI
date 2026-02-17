from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtCharts import *
from PySide6.QtPrintSupport import QPrinter
import sys, csv, os, sqlite3, json, logging, random
from datetime import datetime

# ===== 0. EXE RESOURCE HELPER =====
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ===== 1. LOGGING SETUP =====
logging.basicConfig(filename='machine_log.txt', level=logging.ERROR, format='%(asctime)s - %(message)s')

# ===== THEME =====
BG = "#F2F4F7"
HEADER = "#0D47A1"
SIDEBAR = "#E0E0E0"
BTN_SEL = "#0D47A1"
GREEN = "#4CAF50"
RED = "#D32F2F"
GREY = "#BDBDBD"

# UPDATED STYLE: FIXES DROPDOWNS, CALENDARS & POPUPS FOR ALL PCs
GLOBAL_STYLE = """
    * { font-family: 'Arial'; color: black; }
    
    /* Main Structure */
    QLabel#ScreenTitle { font-size: 28px; font-weight: bold; color: white; border: none; }
    QLabel#SectionHeading { font-size: 20px; font-weight: bold; color: #1A237E; }
    
    /* === NEW FIX: Persistent Style for Input Labels === */
    QLabel#InputLabel { font-size: 20px; font-weight: bold; color: black; border: none; }
    
    QFrame#MainPanel { background: white; border: 2px solid #CFD8DC; border-radius: 5px; }
    
    /* Buttons */
    QPushButton#ControlBox {
        background-color: white; color: black; font-size: 16px; font-weight: bold;
        border: 2px solid #90A4AE; border-radius: 4px; min-height: 60px; 
    }
    QPushButton#ControlBox:hover { background-color: #D1D9DB; }
    QPushButton#ControlBox:pressed { background-color: #4CAF50; border: 2px solid #2E7D32; color: black; }
    
    QPushButton#MenuBtn {
        background-color: transparent; border: none; color: white; font-size: 24px; font-weight: bold;
    }
    QPushButton#MenuBtn:hover { background-color: #1565C0; border-radius: 4px; }

    /* === FIX: Force White Backgrounds/Black Text on Popups === */
    QComboBox { background-color: white; color: black; border: 1px solid #90A4AE; padding: 5px; }
    QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #0D47A1; selection-color: white; }
    
    QDateEdit { background-color: white; color: black; border: 1px solid #90A4AE; }
    
    /* Calendar Fixes */
    QCalendarWidget QWidget { background-color: white; color: black; alternate-background-color: #E0E0E0; }
    QCalendarWidget QToolButton { color: black; background-color: white; }
    QCalendarWidget QMenu { background-color: white; color: black; }
    
    /* Dialogs & Messages */
    QMessageBox { background-color: white; color: black; }
    QDialog { background-color: white; color: black; }
    QLineEdit { color: black; background-color: white; }
"""

class AutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Leak Test")
        self.setStyleSheet(GLOBAL_STYLE)
        
        # --- AUTO SCREEN SIZE DETECTION ---
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(screen.width(), screen.height())
        self.showMaximized()
        
        # --- SYSTEM INITIALIZATION ---
        self.load_config()      
        self.init_database()    
        self.current_report_date = QDate.currentDate()

        # --- UI LAYOUT ---
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG};")
        self.setCentralWidget(central)
        
        # ROOT LAYOUT
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. HEADER (Compact Height: 60px)
        header = QFrame(); header.setFixedHeight(60); header.setStyleSheet(f"background:{HEADER}; border: none;") 
        h_layout = QHBoxLayout(header); h_layout.setContentsMargins(10, 0, 20, 0)

        self.menu_btn = QPushButton("☰"); self.menu_btn.setObjectName("MenuBtn"); self.menu_btn.setFixedSize(40, 40); self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        h_layout.addWidget(self.menu_btn)
        
        self.screen_title = QLabel("HOME"); self.screen_title.setObjectName("ScreenTitle")
        h_layout.addWidget(self.screen_title); h_layout.addStretch()
        
        self.comm_status = QLabel("PLC: OFFLINE")
        self.comm_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFCDD2; margin-right: 20px;")
        h_layout.addWidget(self.comm_status)

        self.clock = QLabel(); self.clock.setStyleSheet("font-size: 18px; color: white; border: none;") 
        h_layout.addWidget(self.clock); root.addWidget(header)

        # 2. BODY
        body = QHBoxLayout(); body.setSpacing(0); root.addLayout(body)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.sidebar.setStyleSheet(f"background:{SIDEBAR}; border-right: 2px solid #B0BEC5;")
        self.sl = QVBoxLayout(self.sidebar); self.sl.setContentsMargins(5, 10, 5, 10); self.sl.setSpacing(5)
        body.addWidget(self.sidebar)

        # Navigation Buttons
        nav_items = [("HOME", 0), ("AUTO", 1), ("MANUAL", 2), ("INPUT STATUS", 3), ("OUTPUT STATUS", 4), 
                     ("DATALOG", 5), ("CHARTS", 8), ("ALARMS", 9), ("REPORT", 6)]
        
        for text, idx in nav_items: self.nav_btn(text, idx)
        self.sl.addStretch()
        self.nav_btn("EXPORT", export=True)
        self.nav_btn("SETTINGS", settings=True)

        # Main Content Stack (NO SCROLL AREA - Direct Layout)
        self.stack = QStackedWidget()
        body.addWidget(self.stack)

        # Add Screens
        self.stack.addWidget(self.build_home())     # 0
        self.stack.addWidget(self.build_auto())     # 1 
        self.stack.addWidget(self.build_manual())   # 2
        self.stack.addWidget(self.build_io_screen("INPUT"))   # 3
        self.stack.addWidget(self.build_io_screen("OUTPUT"))  # 4
        self.stack.addWidget(self.build_datalog())  # 5
        self.stack.addWidget(self.build_report())   # 6
        self.stack.addWidget(self.build_settings()) # 7 
        self.stack.addWidget(self.build_charts())   # 8 
        self.stack.addWidget(self.build_alarms())   # 9 

        # Timers
        self.timer_clock = QTimer(self); self.timer_clock.timeout.connect(self.update_clock); self.timer_clock.start(1000)
        self.update_clock()
        self.timer_plc = QTimer(self); self.timer_plc.timeout.connect(self.update_plc_data); self.timer_plc.start(200)
        self.calculate_yield()

    # ================= SYSTEM BACKEND =================
    def init_database(self):
        try:
            self.conn = sqlite3.connect("scada.db")
            self.cursor = self.conn.cursor()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS cycles_v2 (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    date TEXT, time TEXT, serial TEXT, result TEXT,
                                    c1 REAL, c2 REAL, c3 REAL, c4 REAL, c5 REAL, c6 REAL, c7 REAL)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS alarms (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    date TEXT, time TEXT, message TEXT, type TEXT)''')
            self.conn.commit()
        except Exception as e: logging.error(f"DB Init Error: {e}")

    def load_config(self):
        self.config_file = "config.json"
        defaults = {"leak_limit": 0.8, "bypass": False, "plc_ip": "192.168.0.1", "plc_port": 502}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f: self.config = json.load(f)
            except: self.config = defaults
        else: self.config = defaults; self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f: json.dump(self.config, f)
        except: pass

    # ================= LOGIC & ANIMATION =================
    def toggle_sidebar(self):
        width = self.sidebar.width(); new_width = 0 if width == 240 else 240
        self.anim_group = QParallelAnimationGroup()
        anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        anim_max.setDuration(300); anim_max.setStartValue(width); anim_max.setEndValue(new_width); anim_max.setEasingCurve(QEasingCurve.InOutQuart)
        anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        anim_min.setDuration(300); anim_min.setStartValue(width); anim_min.setEndValue(new_width); anim_min.setEasingCurve(QEasingCurve.InOutQuart)
        self.anim_group.addAnimation(anim_max); self.anim_group.addAnimation(anim_min)
        self.anim_group.finished.connect(self.force_layout_refresh); self.anim_group.start()

    def force_layout_refresh(self):
        self.centralWidget().layout().update()
        # Wiggle to force repaint
        self.resize(self.width() + 1, self.height())
        self.resize(self.width() - 1, self.height())

    def calculate_yield(self):
        try:
            self.cursor.execute("SELECT count(*) FROM cycles_v2"); total = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT count(*) FROM cycles_v2 WHERE result='OK'"); ok_count = self.cursor.fetchone()[0]
            yield_pct = (ok_count / total) * 100 if total > 0 else 100.0
            if hasattr(self, 'yield_val_lbl'):
                self.yield_val_lbl.setText(f"{yield_pct:.1f}%")
                color = "#4CAF50" if yield_pct >= 90 else ("#FFC107" if yield_pct >= 80 else "#D32F2F")
                self.yield_val_lbl.setStyleSheet(f"font-size: 40px; font-weight: bold; color: {color};")
            if hasattr(self, 'cnt_ok_lbl'): self.cnt_ok_lbl.setText(str(ok_count))
            if hasattr(self, 'cnt_ng_lbl'): self.cnt_ng_lbl.setText(str(total - ok_count))
        except: pass

    def update_plc_data(self):
        if random.random() < 0.05: self.simulate_cycle_data()

    def simulate_cycle_data(self):
        vals = [round(random.uniform(0.1, 1.2), 3) for _ in range(7)]
        limit = self.config["leak_limit"]
        result = "OK" if all(v < limit for v in vals) else "NG"
        sn = f"SN-{random.randint(1000,9999)}"
        dt = datetime.now()
        self.cursor.execute("""
            INSERT INTO cycles_v2 (date, time, serial, result, c1, c2, c3, c4, c5, c6, c7) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (dt.strftime("%d-%m-%Y"), dt.strftime("%H:%M:%S"), sn, result, *vals))
        self.conn.commit()
        self.calculate_yield()
        if hasattr(self, 'datalog_table'): self.refresh_datalog()

    def closeEvent(self, event):
        if hasattr(self, 'conn'): self.conn.close()
        event.accept()

    # ================= UI BUILDERS =================
    def nav_btn(self, text, index=None, settings=False, export=False):
        b = QPushButton(text); b.setMinimumHeight(55); b.setCursor(Qt.PointingHandCursor) # Reduced height
        b.setStyleSheet(f"QPushButton {{ background:white; font-size:16px; font-weight:bold; border:1px solid #CFD8DC; border-radius:4px; }} QPushButton:pressed {{ background:{BTN_SEL}; color:white; }}")
        if settings: b.clicked.connect(self.open_settings)
        elif export: b.clicked.connect(self.open_export_dialog)
        else: b.clicked.connect(lambda: self.goto(index, text))
        self.sl.addWidget(b)

    def build_home(self):
        home = QWidget(); main = QVBoxLayout(home); main.setContentsMargins(30, 30, 30, 30)
        title = QLabel("LEAK TEST MACHINE"); title.setAlignment(Qt.AlignCenter); title.setStyleSheet("font-size:36px; font-weight:bold; color:black;"); main.addWidget(title)
        
        self.machine_img = QLabel(); self.machine_img.setAlignment(Qt.AlignCenter); self.machine_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.machine_img.setStyleSheet("background:white; border:3px solid #B0BEC5;"); self.machine_img.setScaledContents(True)
        img_path_1 = resource_path("1.jpg")
        if os.path.exists(img_path_1): self.machine_img.setPixmap(QPixmap(img_path_1))
        else: self.machine_img.setText(f"IMAGE NOT FOUND:\n{img_path_1}")
        main.addWidget(self.machine_img, 1)
        
        bottom = QHBoxLayout()
        def create_logo(image_name):
            lbl = QLabel(); lbl.setFixedSize(200, 80); lbl.setStyleSheet("background:white; border:2px solid #90A4AE;"); lbl.setScaledContents(True)
            path = resource_path(image_name)
            if os.path.exists(path): lbl.setPixmap(QPixmap(path))
            else: lbl.setText("IMG NOT FOUND")
            return lbl
        l1 = create_logo("2.jpg"); bottom.addWidget(l1); bottom.addStretch(); l2 = create_logo("3.jpg"); bottom.addWidget(l2)
        main.addLayout(bottom); return home

    def build_auto(self):
        auto = QWidget(); root = QVBoxLayout(auto); root.setContentsMargins(15, 15, 15, 15); root.setSpacing(10)
        self.bypass_banner = QLabel("⚠ WARNING: SCANNER BYPASS ACTIVE ⚠")
        self.bypass_banner.setAlignment(Qt.AlignCenter); self.bypass_banner.setStyleSheet("background: #FFEB3B; color: black; font-weight: bold; font-size: 18px; padding: 8px; border: 2px solid #FBC02D; border-radius: 4px;")
        self.bypass_banner.setVisible(self.config.get("bypass", False)); root.addWidget(self.bypass_banner)
        
        top = QHBoxLayout(); root.addLayout(top); cond = QFrame(); cond.setObjectName("MainPanel"); cond.setFixedWidth(400); cl = QVBoxLayout(cond)
        cl.addWidget(QLabel("HOME CONDITIONS", objectName="SectionHeading"))
        for s in ["Auto Mode", "Hydraulic", "Emergency", "Inlet Air Pressure", "Shuttle Rev Sensor", "Top Rev Sensor", "Component Sensor"]:
            row = QHBoxLayout(); row.addWidget(QLabel(s, styleSheet="font-size: 16px;")); row.addStretch(); row.addWidget(self.lamp(False)); cl.addLayout(row)
        cl.addStretch(); top.addWidget(cond)
        
        cav = QFrame(); cav.setObjectName("MainPanel"); cav_layout = QGridLayout(cav)
        cav_layout.addWidget(QLabel("LEAK TEST VALUES", objectName="SectionHeading"), 0, 0, 1, 2)
        for i in range(7):
            v = QLabel("0.000"); v.setStyleSheet("background: #000; color: #00FF00; font-family: 'Courier New'; font-size: 22px; padding: 5px; font-weight: bold; border-radius: 4px;")
            cav_layout.addWidget(QLabel(f"Cav {i+1}", styleSheet="font-size: 18px; font-weight: bold;"), i+1, 0); cav_layout.addWidget(v, i+1, 1)
        top.addWidget(cav, 1)
        
        mid = QHBoxLayout(); root.addLayout(mid)
        def cb(t, obj_name=None): 
            f = QFrame(); f.setObjectName("MainPanel"); v = QVBoxLayout(f)
            v.addWidget(QLabel(t, styleSheet="font-weight: bold; font-size: 16px;")); lbl = QLabel("0", styleSheet="font-size: 36px; font-weight: bold; color: #0D47A1;"); v.addWidget(lbl)
            if obj_name: setattr(self, obj_name, lbl) 
            return f
        mid.addWidget(cb("JOB OK", "cnt_ok_lbl")); mid.addWidget(cb("JOB NG", "cnt_ng_lbl")); mid.addWidget(cb("YIELD %", "yield_val_lbl"))
        
        scan_f = QFrame(); scan_f.setObjectName("MainPanel"); scan_f.setStyleSheet("background: #FFF9C4;")
        sv = QVBoxLayout(scan_f); sv.addWidget(QLabel("SCAN DATA", styleSheet="font-weight: bold;")); sv.addWidget(QLabel("WAITING...", styleSheet="font-size: 28px; font-weight: bold;")); mid.addWidget(scan_f, 1)
        
        r_msg = QLabel("SYSTEM READY"); r_msg.setAlignment(Qt.AlignCenter); r_msg.setFixedHeight(50); r_msg.setStyleSheet("background: #263238; color: white; font-size: 24px; font-weight: bold; border-radius: 4px;"); root.addWidget(r_msg); return auto

    def build_manual(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20)
        sections = [("Shuttle Control", ["Shuttle FWD", "Shuttle REV"]), ("Top Clamp", ["Clamp FWD", "Clamp REV"]), 
                    ("ATEQ Tester", ["ATEQ Start", "ATEQ Stop"]), ("Utility", ["Air Blow", "Reset Alarm"])]
        for title, btns in sections:
            f = QFrame(); f.setObjectName("MainPanel"); sl = QVBoxLayout(f); sl.addWidget(QLabel(title, objectName="SectionHeading"))
            hb = QHBoxLayout(); [hb.addWidget(QPushButton(b, objectName="ControlBox")) for b in btns]; sl.addLayout(hb); l.addWidget(f)
        return page

    def build_io_screen(self, io_type):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(30, 30, 30, 30)
        l.addWidget(QLabel(f"PLC {io_type} STATUS", objectName="SectionHeading"))
        table = QTableWidget(20, 3); table.setHorizontalHeaderLabels(["Address", "Description", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        prefix = "X" if io_type == "INPUT" else "Y"; label_text = "Input" if io_type == "INPUT" else "Output"
        for i in range(20):
            num = i + 1; table.setItem(i, 0, QTableWidgetItem(f"{prefix}{num}")); table.setItem(i, 1, QTableWidgetItem(f"{label_text} {num}"))
            lw = QWidget(); lh = QHBoxLayout(lw); lh.setContentsMargins(0,0,0,0); lh.setAlignment(Qt.AlignCenter); lh.addWidget(self.lamp(False)); table.setCellWidget(i, 2, lw)
        l.addWidget(table); return page

    def build_datalog(self):
        p = QWidget(); l = QVBoxLayout(p); l.setContentsMargins(20,20,20,20)
        l.addWidget(QLabel("DATALOG", objectName="SectionHeading"))
        search_layout = QHBoxLayout(); search_lbl = QLabel("Search Serial:"); search_lbl.setStyleSheet("font-weight:bold; font-size:16px;")
        self.search_bar = QLineEdit(); self.search_bar.setPlaceholderText("Filter..."); self.search_bar.setStyleSheet("font-size: 16px; padding: 6px; border: 1px solid #B0BEC5; border-radius: 4px;")
        self.search_bar.textChanged.connect(self.filter_datalog); search_layout.addWidget(search_lbl); search_layout.addWidget(self.search_bar); l.addLayout(search_layout)
        
        self.datalog_table = QTableWidget(0, 11) 
        cols = ["Date", "Time", "Serial", "Result", "C1 Leak", "C2 Leak", "C3 Leak", "C4 Leak", "C5 Leak", "C6 Leak", "C7 Leak"]
        self.datalog_table.setHorizontalHeaderLabels(cols)
        self.datalog_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.datalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive); self.datalog_table.horizontalHeader().setDefaultSectionSize(100)
        self.refresh_datalog(); l.addWidget(self.datalog_table); return p

    def refresh_datalog(self):
        try:
            self.cursor.execute("SELECT date, time, serial, result, c1, c2, c3, c4, c5, c6, c7 FROM cycles_v2 ORDER BY id DESC LIMIT 100")
            rows = self.cursor.fetchall()
            self.datalog_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.datalog_table.setItem(i, j, QTableWidgetItem(str(val)))
                    if j == 3: color = QColor("#C8E6C9") if val == "OK" else QColor("#FFCDD2"); self.datalog_table.item(i, j).setBackground(color)
        except: pass

    def filter_datalog(self, text):
        for row in range(self.datalog_table.rowCount()):
            item = self.datalog_table.item(row, 2)
            match = (text.lower() in item.text().lower()) if item else False
            self.datalog_table.setRowHidden(row, not match and text != "")

    def build_report(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(20, 20, 20, 20)
        nav = QFrame(); nav.setObjectName("MainPanel"); nav.setFixedHeight(60); nh = QHBoxLayout(nav)
        self.report_date_lbl = QLabel(self.current_report_date.toString("dd-MM-yyyy")); self.report_date_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0D47A1;")
        prev_b = QPushButton("< PREV"); next_b = QPushButton("NEXT >"); today_b = QPushButton("TODAY")
        prev_b.clicked.connect(lambda: self.update_rep(-1)); next_b.clicked.connect(lambda: self.update_rep(1)); today_b.clicked.connect(lambda: self.update_rep(0))
        nh.addWidget(prev_b); nh.addStretch(); nh.addWidget(self.report_date_lbl); nh.addStretch(); nh.addWidget(today_b); nh.addWidget(next_b); layout.addWidget(nav)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); container = QWidget(); ch = QHBoxLayout(container)
        shifts = [("SHIFT 1 (07:30-15:30)", ["07:30-08:30", "08:30-09:30", "09:30-10:30", "10:30-11:30", "11:30-12:30", "12:30-13:30", "13:30-14:30", "14:30-15:30"]),
                  ("SHIFT 2 (15:30-23:30)", ["15:30-16:30", "16:30-17:30", "17:30-18:30", "18:30-19:30", "19:30-20:30", "20:30-21:30", "21:30-22:30", "22:30-23:30"]),
                  ("SHIFT 3 (23:30-07:30)", ["23:30-00:30", "00:30-01:30", "01:30-02:30", "02:30-03:30","03:30-04:30", "04:30-05:30", "05:30-06:30", "06:30-07:30"])]
        for title, times in shifts:
            v = QVBoxLayout(); v.addWidget(QLabel(title, styleSheet="font-weight:bold; color:#0D47A1;")); t = QTableWidget(len(times), 3); t.setHorizontalHeaderLabels(["Time", "OK", "NG"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for i, time_range in enumerate(times): t.setItem(i, 0, QTableWidgetItem(time_range))
            v.addWidget(t); ch.addLayout(v)
        scroll.setWidget(container); layout.addWidget(scroll); return page

    def build_settings(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(20)
        cl.addWidget(QLabel("MACHINE SETTINGS", objectName="SectionHeading"))
        panel = QFrame(); panel.setObjectName("MainPanel"); panel.setStyleSheet("background:white; border:2px solid #90A4AE; padding:20px;")
        pl = QVBoxLayout(panel); pl.setSpacing(20)
        grid = QGridLayout(); pl.addLayout(grid)
        
        # 1. Leak Limit
        lbl_limit = QLabel("Leak Limit (cm3/min):")
        lbl_limit.setObjectName("InputLabel") 
        self.limit_input = QLineEdit(str(self.config.get("leak_limit", 0.8)))
        self.limit_input.setStyleSheet("font-size: 20px; padding: 5px; color: black;") 
        grid.addWidget(lbl_limit, 0, 0); grid.addWidget(self.limit_input, 0, 1)

        # 2. IP Address
        lbl_ip = QLabel("PLC IP Address:")
        lbl_ip.setObjectName("InputLabel")
        self.ip_input = QLineEdit(str(self.config.get("plc_ip", "192.168.0.1")))
        self.ip_input.setStyleSheet("font-size: 20px; padding: 5px; color: black;")
        grid.addWidget(lbl_ip, 1, 0); grid.addWidget(self.ip_input, 1, 1)

        # 3. Port
        lbl_port = QLabel("PLC Port:")
        lbl_port.setObjectName("InputLabel") 
        self.port_input = QLineEdit(str(self.config.get("plc_port", 502)))
        self.port_input.setStyleSheet("font-size: 20px; padding: 5px; color: black;")
        grid.addWidget(lbl_port, 2, 0); grid.addWidget(self.port_input, 2, 1)

        self.bypass_btn = QPushButton("SCANNER BYPASS"); self.bypass_btn.setCheckable(True); self.bypass_btn.setChecked(self.config.get("bypass", False))
        self.bypass_btn.setMinimumHeight(60); self.bypass_btn.clicked.connect(self.update_bypass_visuals); self.update_bypass_visuals(); pl.addWidget(self.bypass_btn)
        save_cfg_btn = QPushButton("UPDATE CONFIG"); save_cfg_btn.setStyleSheet("background:#1976D2; color:white; font-weight:bold; padding:10px;")
        save_cfg_btn.clicked.connect(self.update_config_file); pl.addWidget(save_cfg_btn)
        pl.addWidget(QLabel("--------------------------------------------------"))
        reset_group = QHBoxLayout()
        def setting_btn(text, color): b = QPushButton(text); b.setStyleSheet(f"background:{color}; color:white; font-size:18px; font-weight:bold; border-radius:5px; min-height:60px;"); return b
        btn_ok = setting_btn("RESET OK COUNT", GREEN); btn_ng = setting_btn("RESET NG COUNT", RED)
        btn_ok.clicked.connect(lambda: QMessageBox.information(self,"Info","OK Count Reset")); btn_ng.clicked.connect(lambda: QMessageBox.information(self,"Info","NG Count Reset"))
        reset_group.addWidget(btn_ok); reset_group.addWidget(btn_ng); pl.addLayout(reset_group); cl.addWidget(panel); cl.addStretch(); scroll.setWidget(container); l.addWidget(scroll); return page

    def update_bypass_visuals(self):
        if self.bypass_btn.isChecked(): self.bypass_btn.setText("SCANNER BYPASS: ENABLED (UNSAFE)"); self.bypass_btn.setStyleSheet("background-color: #D32F2F; color: white; font-size: 18px; font-weight: bold; border-radius: 5px; border: 2px solid #B71C1C;")
        else: self.bypass_btn.setText("SCANNER BYPASS: DISABLED (SAFE)"); self.bypass_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px; font-weight: bold; border-radius: 5px; border: 2px solid #388E3C;")

    def update_config_file(self):
        try:
            self.config["leak_limit"] = float(self.limit_input.text()); self.config["plc_ip"] = self.ip_input.text(); self.config["plc_port"] = int(self.port_input.text()); self.config["bypass"] = self.bypass_btn.isChecked(); self.save_config()
            if hasattr(self, 'bypass_banner'): self.bypass_banner.setVisible(self.config["bypass"])
            QMessageBox.information(self, "Saved", "Configuration Updated!"); self.refresh_charts()
        except: QMessageBox.warning(self, "Error", "Invalid Input")

    def build_charts(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20)
        self.chart_spc = QChart(); self.chart_spc.setTitle("SPC Trend (Last 20 Cycles)")
        self.series_spc = QLineSeries(); self.series_spc.setName("Leak Rate")
        self.limit_series = QLineSeries(); self.limit_series.setName("Limit")
        pen = QPen(QColor(0,0,255)); pen.setWidth(3); self.series_spc.setPen(pen)
        lpen = QPen(QColor(255,0,0)); lpen.setWidth(2); lpen.setStyle(Qt.DashLine); self.limit_series.setPen(lpen)
        self.chart_spc.addSeries(self.series_spc); self.chart_spc.addSeries(self.limit_series)
        self.chart_spc.createDefaultAxes()
        axes = self.chart_spc.axes(Qt.Vertical)
        if axes: self.axis_y_spc = axes[0]; self.axis_y_spc.setRange(0, 1.5)
        cv1 = QChartView(self.chart_spc); cv1.setRenderHint(QPainter.Antialiasing)
        f1 = QFrame(); f1.setObjectName("MainPanel"); v1 = QVBoxLayout(f1); v1.addWidget(cv1); l.addWidget(f1)
        self.chart_bar = QChart(); self.chart_bar.setTitle("Avg Leak Rate per Cavity")
        self.bar_set = QBarSet("Avg Leak"); self.bar_set.setColor(QColor("#0D47A1"))
        self.bar_series = QBarSeries(); self.bar_series.append(self.bar_set)
        self.chart_bar.addSeries(self.bar_series)
        axis_x = QBarCategoryAxis(); axis_x.append([f"C{i}" for i in range(1,8)])
        self.chart_bar.addAxis(axis_x, Qt.AlignBottom); self.bar_series.attachAxis(axis_x)
        axis_y = QValueAxis(); axis_y.setRange(0, 1.0)
        self.chart_bar.addAxis(axis_y, Qt.AlignLeft); self.bar_series.attachAxis(axis_y)
        cv2 = QChartView(self.chart_bar); cv2.setRenderHint(QPainter.Antialiasing)
        f2 = QFrame(); f2.setObjectName("MainPanel"); v2 = QVBoxLayout(f2); v2.addWidget(cv2); l.addWidget(f2)
        self.refresh_charts(); return page

    def refresh_charts(self):
        try:
            self.series_spc.clear(); self.limit_series.clear()
            self.cursor.execute("SELECT c1 FROM cycles_v2 ORDER BY id DESC LIMIT 20")
            data = self.cursor.fetchall()[::-1]
            limit = self.config.get("leak_limit", 0.8)
            for i, (val,) in enumerate(data): self.series_spc.append(i, val); self.limit_series.append(i, limit)
            self.bar_series.clear()
            new_set = QBarSet("Avg Leak"); new_set.setColor(QColor("#0D47A1"))
            self.cursor.execute("SELECT avg(c1), avg(c2), avg(c3), avg(c4), avg(c5), avg(c6), avg(c7) FROM cycles_v2")
            avgs = self.cursor.fetchone()
            if avgs and avgs[0]: 
                for v in avgs: new_set.append(v)
            else:
                for _ in range(7): new_set.append(0)
            self.bar_series.append(new_set)
        except: pass

    def build_alarms(self):
        p = QWidget(); l = QVBoxLayout(p); l.setContentsMargins(20,20,20,20)
        l.addWidget(QLabel("ALARM HISTORY", objectName="SectionHeading"))
        self.alarm_table = QTableWidget(0, 4)
        self.alarm_table.setHorizontalHeaderLabels(["Date", "Time", "Message", "Type"])
        self.alarm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.refresh_alarms(); l.addWidget(self.alarm_table); return p

    def refresh_alarms(self):
        self.cursor.execute("SELECT date, time, message, type FROM alarms ORDER BY id DESC")
        rows = self.cursor.fetchall()
        self.alarm_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.alarm_table.setItem(i, j, QTableWidgetItem(str(val)))
                if row[3] == "CRITICAL": self.alarm_table.item(i, j).setBackground(QColor("#FFCDD2"))

    def open_export_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Export Data"); dlg.setFixedWidth(500); v = QVBoxLayout(dlg)
        self.exp_type = QComboBox(); self.exp_type.addItems(["PRODUCTION REPORT", "DATALOG"]); v.addWidget(self.exp_type)
        grid = QGridLayout(); self.start_cal = QDateEdit(calendarPopup=True); self.end_cal = QDateEdit(calendarPopup=True)
        self.start_cal.setDate(QDate.currentDate()); self.end_cal.setDate(QDate.currentDate())
        grid.addWidget(QLabel("Start:"), 0, 0); grid.addWidget(self.start_cal, 0, 1); grid.addWidget(QLabel("End:"), 1, 0); grid.addWidget(self.end_cal, 1, 1); v.addLayout(grid)
        btn_base = "QPushButton { height: 50px; background: white; font-weight: bold; border: 1px solid #CFD8DC; border-radius: 4px; } "
        csv_b = QPushButton("EXPORT TO EXCEL (CSV)"); csv_b.setStyleSheet(btn_base + f"QPushButton:pressed {{ background: {GREEN}; color: black; }}")
        pdf_b = QPushButton("EXPORT TO PDF"); pdf_b.setStyleSheet(btn_base + f"QPushButton:pressed {{ background: {RED}; color: white; }}")
        csv_b.clicked.connect(lambda: self.do_exp("csv")); pdf_b.clicked.connect(lambda: self.do_exp("pdf"))
        v.addWidget(csv_b); v.addWidget(pdf_b); dlg.exec()

    def do_exp(self, f_type):
        prefix = "ProductionReport" if self.exp_type.currentText() == "PRODUCTION REPORT" else "Datalog"
        date_str = self.start_cal.date().toString("dd-MM-yyyy")
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", f"{prefix}_{date_str}.{f_type}", f"{f_type.upper()} Files (*.{f_type})")
        if not filename: return
        try:
            self.cursor.execute("SELECT date, time, serial, result, c1, c2, c3, c4, c5, c6, c7 FROM cycles_v2") 
            data = self.cursor.fetchall()
            if f_type == "csv":
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Date", "Time", "Serial", "Result", "C1", "C2", "C3", "C4", "C5", "C6", "C7"])
                    writer.writerows(data)
                QMessageBox.information(self, "Success", f"Exported {len(data)} rows.")
            elif f_type == "pdf":
                printer = QPrinter(QPrinter.HighResolution); printer.setOutputFormat(QPrinter.PdfFormat); printer.setOutputFileName(filename)
                html = f"<h1>{prefix}</h1><h3>Date: {date_str}</h3><table border='1' cellspacing='0' cellpadding='5' width='100%'>"
                html += "<tr style='background:#ccc'><th>Date</th><th>Time</th><th>Serial</th><th>Result</th><th>C1</th><th>C2</th><th>C3</th><th>C4</th><th>C5</th><th>C6</th><th>C7</th></tr>"
                for row in data: color = "#e6ffe6" if row[3] == "OK" else "#ffe6e6"; html += f"<tr style='background:{color}'><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td><td>{row[8]}</td><td>{row[9]}</td><td>{row[10]}</td></tr>"
                html += "</table>"; doc = QTextDocument(); doc.setHtml(html); doc.print_(printer); QMessageBox.information(self, "Success", "Exported PDF.")
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def open_settings(self):
        pwd, ok = QInputDialog.getText(self, "Security", "Enter Password:", QLineEdit.Password)
        if ok and pwd == "2025": self.goto(7, "SETTINGS")
        elif ok: QMessageBox.warning(self, "Error", "Incorrect Password")

    def goto(self, i, name): self.stack.setCurrentIndex(i); self.screen_title.setText(name)
    def update_clock(self): self.clock.setText(datetime.now().strftime("%d-%m-%Y  %H:%M:%S"))
    def update_rep(self, d): self.current_report_date = QDate.currentDate() if d == 0 else self.current_report_date.addDays(d); self.report_date_lbl.setText(self.current_report_date.toString("dd-MM-yyyy"))
    def lamp(self, on=False): l = QLabel(); l.setFixedSize(30, 30); color = "#4CAF50" if on else GREY; l.setStyleSheet(f"background:{color}; border-radius:15px; border: 2px solid #757575;"); return l

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    win = AutomationApp()
    win.show()
    sys.exit(app.exec())
