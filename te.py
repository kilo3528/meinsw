import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import Toplevel, Label, Button
import random
import sqlite3
from datetime import datetime
import os
import sys
import json
import time
os.environ['LANG'] = 'uk_UA.UTF-8'
import locale
locale.setlocale(locale.LC_ALL, 'uk_UA')



# Визначення шляху до папки з грою
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

folder = application_path
filename = "game_data.db"
db_path = os.path.join(folder, filename)

# Створення папки якщо вона не існує
os.makedirs(folder, exist_ok=True)

class Minesweeper:
    def __init__(self, root, size=10, mines=10):
        self.root = root
        self.settings_file = "settings.json"
        
        # Ініціалізація тимчасових значень
        self.dark_mode = False
        self.dialog_enabled = True
        self.last_difficulty = "Легкий"  # Значення за замовчуванням
        
        # 1. Завантажити налаштування ПЕРШИМ
        self.timer_window = None
        self.timer_label = None
        self.timer_id = None
        self.timer_pos = {"x": 100, "y": 100}
        self.timer_geometry = "150x80"
        self.load_settings()
        self.timer_enabled = False
        if self.timer_enabled:
            self.create_timer_window()
            if self.game_active:
                self.start_timer()
        # 2. Ініціалізація Tkinter змінних ПОСЛЯ завантаження налаштувань
        self.dialog_var = tk.BooleanVar(value=self.dialog_enabled)
        self.difficulty_var = tk.StringVar(value=self.last_difficulty)
        
        # 3. Встановити параметри гри
        difficulty_settings = {
            "Легкий": (10, 10),
            "Середній": (12, 20),
            "Важкий": (16, 40)
        }
        self.size, self.mines = difficulty_settings[self.last_difficulty]

        # 4. Решта ініціалізацій
        self.timer_window = None
        self.difficulty_menu = None
        self.difficulty_var.set(self.last_difficulty)
        self.game_active = False
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.buttons = []
        self.board = []
        self.game_over = False
        self.flagged = set()
        self.first_click = True
        self.history_window = None
        self.info_window = None
        self.init_colors()
        self.create_widgets()
        self.update_colors()
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._update_difficulty_menu()
        self.create_db()
        self.setup_initial_state()
        self.remaining_time = 0
        
        
        # 5. Зберегти налаштування лише після повної ініціалізації
        self.save_settings()

    def init_colors(self):
        """Ініціалізує кольорові змінні на основі теми."""
        if self.dark_mode:
            self.bg_color = "#2c2f33"
            self.button_bg_color = "#23272a"
            self.button_active_bg = "#404EED"
            self.text_color = "#ffffff"
            self.reveal_color = "#36393f"
            self.mine_color = "#000000"
            self.flag_color = "#f39c12"
            self.hover_color = "#404EED"
            self.style.configure("Vertical.TScrollbar",
                                background=self.button_bg_color,
                                troughcolor=self.bg_color,
                                arrowcolor=self.text_color)
            self._configure_scrollbar_style()
            self.style.configure("TCheckbutton", 
                           background=self.bg_color,
                           foreground=self.text_color,
                           fieldbackground=self.bg_color,
                           indicatordiameter=15,
                           indicatorbackground=self.button_bg_color,
                           relief="flat")
            self.style.configure('TCheckbutton', 
                    background=self.bg_color,
                    foreground=self.text_color,
                    indicatorbackground=self.button_bg_color)
            self.style.map("TMenubutton",
                      background=[('active', self.button_active_bg)]),
            self.style.map("TCheckbutton",
                          background=[("active", self.bg_color)],
                          indicatorcolor=[("selected", self.text_color)],
                          indicatorbackground=[("selected", "#404EED")])
            
            
        else:
            self.bg_color = "#ffffff"
            self.button_bg_color = "#e0e0e0"
            self.button_active_bg = "#E1F5FE"
            self.text_color = "#000000"
            self.reveal_color = "#d0d0d0"
            self.mine_color = "#000000"
            self.flag_color = "#0000ff"
            self.hover_color = "#E1F5FE"
            self.style.configure("Menu",
                        background=self.button_bg_color,
                        foreground=self.text_color,
                        activebackground=self.button_active_bg)
            self._configure_scrollbar_style()
            self.style.configure("TCheckbutton", 
                           background=self.bg_color,
                           foreground=self.text_color,
                           fieldbackground=self.bg_color,
                           indicatordiameter=15,
                           indicatorbackground=self.button_bg_color,
                           relief="flat")
            self.style.configure('TCheckbutton', 
                    background=self.bg_color,
                    foreground=self.text_color,
                    indicatorbackground=self.button_bg_color)
            self.style.map("TCheckbutton",
                          background=[("active", self.bg_color)],
                          indicatorcolor=[("selected", self.text_color)],
                          indicatorbackground=[("selected", "#E1F5FE")])
        self.style.configure("TButton", 
                        background=self.button_bg_color,
                        foreground=self.text_color)
        self.style.map("TButton",
                      background=[('active', self.hover_color)],
                      foreground=[('active', self.text_color)])


    def _configure_scrollbar_style(self):
        """Оновлює стилі скролбарів відповідно до теми."""
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.button_bg_color,
            troughcolor=self.bg_color,
            bordercolor=self.bg_color,
            arrowcolor=self.text_color,
            gripcount=0  # Видаляємо непотрібний елемент
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', self.button_active_bg)],
            arrowcolor=[('active', self.text_color)]
        )

    def _refresh_scrollbars(self):
        """Оновлює всі існуючі скролбари безпечно."""
        windows = [self.history_window, self.info_window]
        for window in windows:
            if window and window.winfo_exists():
                for child in window.winfo_children():
                    if isinstance(child, ttk.Scrollbar):
                        child.configure(style="Vertical.TScrollbar")
            
    def update_colors(self):
        """Оновлює кольори всіх основних елементів."""
        # Головне вікно
        self.root.configure(bg=self.bg_color)
        self.menu_frame.configure(bg=self.bg_color)
        self.game_frame.configure(bg=self.bg_color)
        
        # Стилізація ttk віджетів
        self.style.configure("TButton", 
                            background=self.button_bg_color,
                            foreground=self.text_color)
        self.style.configure("TMenubutton",
                            background=self.button_bg_color,
                            foreground=self.text_color)
        
        # Оновлення кнопок меню
        for btn in [self.start_button, self.toggle_theme_button, 
                   self.history_button, self.info_button]:
            btn.configure(style="TButton")
        
        # Чекбокс
        self.style.configure("TCheckbutton", 
                           background=self.bg_color,
                           foreground=self.text_color,
                           indicatorbackground=self.button_bg_color)
        
        # Оновлення тексту кнопки теми
        theme_text = "Світла тема" if self.dark_mode else "Темна тема"
        self.toggle_theme_button.config(text=theme_text)

        
    def confirm_action(self, action):
        """Створює діалогове вікно для підтвердження дії."""
        if not self.game_active:  # Якщо гра не активна - не викликаємо діалог
            return True
        if self.game_over:  # Якщо гра вже завершена, не викликаємо діалог
            return True
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Підтвердження")
        dialog.geometry("400x120")
        dialog.resizable(False, False)
        dialog.configure(bg=self.bg_color)
        
        # Центрування вікна
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        dialog_width = 400
        dialog_height = 120
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        
        dialog.geometry(f"+{x}+{y}")

        result = {"choice": False}

        label_text = "Ви впевнені, що хочете перезапустити гру?\nНезбережені дані буде втрачено!"
        if action == "theme":
            label_text = "Ви впевнені, що хочете змінити тему?\nПоточна гра буде перезапущена!"
        elif action == "difficulty":
            label_text = "Ви впевнені, що хочете змінити рівень складності?\nПоточна гра буде перезапущена!"

        label = tk.Label(dialog, text=label_text, bg=self.bg_color, fg=self.text_color)
        label.pack(pady=10)

        def on_confirm():
            result["choice"] = True
            dialog.destroy()

        def on_cancel():
            result["choice"] = False
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=self.bg_color)
        btn_frame.pack(pady=10)

        confirm_btn = ttk.Button(btn_frame, text="Продовжити", command=on_confirm, style="TButton")
        confirm_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = ttk.Button(btn_frame, text="Скасувати", command=on_cancel, style="TButton")
        cancel_btn.pack(side=tk.LEFT, padx=10)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return result["choice"]


    def show_custom_dialog(self, title, message):
        """Створює кастомне діалогове вікно у стилі програми"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.configure(bg=self.bg_color)
        
        # Центрування вікна
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        dialog_width = 300
        dialog_height = 120
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.attributes('-topmost', 1)
        dialog.grab_set()  # Блокує інші вікна
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # Забороняємо закриття

        # Заголовок
        lbl_title = tk.Label(
            dialog, 
            text=title,
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        lbl_title.pack(pady=5)

        # Повідомлення
        lbl_message = tk.Label(
            dialog, 
            text=message,
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        lbl_message.pack(pady=5)

        # Кнопка OK
        btn_ok = ttk.Button(
            dialog, 
            text="OK", 
            command=dialog.destroy,
            style="TButton"
        )
        btn_ok.pack(pady=10)

        # Блокуємо інші вікна
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    
        
    def load_settings(self):
        """Завантажує налаштування зі збереженням українських символів."""
        default_settings = {
            "dark_mode": False,
            "dialog_enabled": True,
            "last_difficulty": "Легкий",
            "timer_enabled": False,
            "timer_pos": {"x": 100, "y": 100},
            "timer_geometry": "150x80"
        }
        try:
            with open(self.settings_file, "r", encoding='utf-8') as f:
                saved_settings = json.load(f)
                # М'яке оновлення налаштувань
                self.dark_mode = saved_settings.get("dark_mode", default_settings["dark_mode"])
                self.dialog_enabled = saved_settings.get("dialog_enabled", default_settings["dialog_enabled"])
                self.last_difficulty = saved_settings.get("last_difficulty", default_settings["last_difficulty"])
                self.timer_enabled = saved_settings.get("timer_enabled", default_settings["timer_enabled"])
                self.timer_pos = saved_settings.get("timer_pos", default_settings["timer_pos"])
                self.timer_geometry = saved_settings.get("timer_geometry", default_settings["timer_geometry"])
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Помилка завантаження налаштувань: {e}, використовуються значення за замовчуванням")
            # Ініціалізація значень за замовчуванням
            self.__dict__.update(default_settings)
            self.save_settings()


            

    def save_settings(self):
        """Зберігає поточний стан всіх налаштувань"""
        settings = {
            # Додаємо всі необхідні параметри
            "dark_mode": self.dark_mode,
            "dialog_enabled": self.dialog_enabled,
            "last_difficulty": self.difficulty_var.get(),
            "timer_enabled": self.timer_enabled,
            "timer_pos": self.timer_pos,
            "timer_geometry": self.timer_geometry
        }
        try:
            with open(self.settings_file, "w", encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження налаштувань: {e}")

    def toggle_theme(self):
        """Перемикає тему та оновлює всі елементи."""
        if not self.game_over and not self.confirm_action("theme"):
            return
        self.dark_mode = not self.dark_mode
        self.init_colors()
        
        # Оновлюємо головне вікно
        self.update_colors()
        
        # Оновлюємо ігрове поле
        for row in self.buttons:
            for btn in row:
                btn.configure(
                    bg=self.button_bg_color, 
                    fg=self.text_color,
                    activebackground=self.hover_color
                )

        # Оновлюємо додаткові вікна
        for window in [self.history_window, self.info_window]:
            if window and window.winfo_exists():
                window.configure(bg=self.bg_color)
                self._update_widgets(window)  # Викликаємо рекурсивне оновлення

            self._update_difficulty_menu_style()
            self._update_menu_colors()
            self.init_colors()
            self.update_colors()
            self.save_settings()
            self.restart_game(confirm=False)  # Відключаємо повторне підтвердження
        if self.timer_window and self.timer_window.winfo_exists():
            self.timer_window.configure(bg=self.bg_color)
            self.timer_label.config(
                bg=self.bg_color,
                fg=self.text_color,
                highlightbackground=self.button_bg_color
            )
    
        self.save_settings()
        self.restart_game(confirm=False)

    def toggle_timer(self):
        """Оновлена логіка перемикання таймера з коректним оновленням інтерфейсу"""
        self.timer_enabled = not self.timer_enabled
    
        if self.timer_enabled:
            self.create_timer_window()
            if self.game_active:
                self.start_timer()
        else:
            self.stop_timer()
            if self.timer_window:
                self.timer_window.destroy()
        
        # Оновлення кнопки в реальному часі
        if self.info_window and self.info_window.winfo_exists():
            for widget in self.info_window.winfo_children():
                if isinstance(widget, ttk.Button) and "таймер" in widget.cget("text").lower():
                    widget.config(text="Вимкнути таймер" if self.timer_enabled else "Увімкнути таймер")
        self.save_settings()
        self.update_timer_button()

    def update_timer_button(self):
        """Оновлює текст кнопки в інфо-вікні"""
        if hasattr(self, 'timer_toggle_btn'):
            self.timer_toggle_btn.config(
                text="Вимкнути таймер" if self.timer_enabled else "Увімкнути таймер"
            )

    def create_widgets(self):
        """Створює елементи інтерфейсу."""
        # Головне меню
        self.menu_frame = tk.Frame(self.root, bg=self.bg_color)
        self.menu_frame.pack(pady=10, anchor='w')
        
        # Кнопки меню
        self.start_button = ttk.Button(self.menu_frame, text="Почати гру", command=self.start_game)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.toggle_theme_button = ttk.Button(self.menu_frame, text="Темна тема", command=self.toggle_theme)
        self.toggle_theme_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.history_button = ttk.Button(self.menu_frame, text="Історія ігор", command=self.show_history)
        self.history_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Ініціалізація меню вибору рівня
        current_difficulty = self.difficulty_var.get()
        available_difficulties = [
            d for d in ["Легкий", "Середній", "Важкий"] 
            if d != current_difficulty
        ]
        
        self.difficulty_menu = ttk.OptionMenu(
            self.menu_frame,
            self.difficulty_var,
            self.last_difficulty,
            *["Легкий", "Середній", "Важкий"],
            command=self.set_difficulty
        )
        self.difficulty_menu.config(width=6.2)
        self.difficulty_menu.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        
        self.info_button = ttk.Button(self.menu_frame, text="...", command=self.show_info)
        self.info_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Ігрове поле
        self.game_frame = tk.Frame(self.root, bg=self.bg_color)
        self.game_frame.pack(pady=10)

        self._update_difficulty_menu_style()  
        self._update_menu_colors() 
        
        self.update_window_size()

    def create_timer_window(self):
        """Створення стилізованого вікна таймера"""
        if self.timer_window is not None:  # Перевіряємо лише наявність об'єкта
            if self.timer_window.winfo_exists():  # Перевіряємо існування вікна
                return
        
        # Використовуємо збережену позицію
        x = self.timer_pos.get("x", 100)
        y = self.timer_pos.get("y", 100)
        geometry_str = f"{self.timer_geometry}+{x}+{y}"
        
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.title("Таймер")
        self.timer_window.geometry(geometry_str)
        self.timer_window.resizable(False, False)
        self.timer_window.overrideredirect(1)
        self.timer_window.attributes('-topmost', 1)
        self.timer_window.configure(bg=self.bg_color)
        
        # Стилізація мітки
        self.timer_label = tk.Label(
            self.timer_window,
            text="00:00",
            font=("Arial", 24, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            relief="ridge",
            bd=3,
            padx=10,
            pady=5
        )
        self.timer_label.pack(expand=True)
        
        # Обробники пересування
        self.timer_window.bind("<ButtonPress-1>", self.start_move)
        self.timer_window.bind("<B1-Motion>", self.do_move)
        self.timer_window.bind("<ButtonRelease-1>", self.save_position)


    def save_position(self, event=None):
        """Зберігає позицію таймера з перевіркою існування вікна"""
        if self.timer_window and self.timer_window.winfo_exists():
            try:
                geometry = self.timer_window.geometry()
                parts = geometry.split('+')
                if len(parts) >= 3:
                    self.timer_geometry = parts[0]
                    self.timer_pos = {
                        "x": int(parts[-2]),
                        "y": int(parts[-1])
                    }
                    # Примусове збереження при кожній зміні
                    self.save_settings()
            except Exception as e:
                print(f"Помилка збереження позиції: {e}")
        
    def start_move(self, event):
        """Початок пересування вікна"""
        self.timer_window._drag_data = {
            "x": event.x_root,
            "y": event.y_root,
            "win_x": self.timer_window.winfo_x(),
            "win_y": self.timer_window.winfo_y()
        }

    def do_move(self, event):
        """Обробка пересування вікна"""
        delta_x = event.x_root - self.timer_window._drag_data["x"]
        delta_y = event.y_root - self.timer_window._drag_data["y"]
        new_x = self.timer_window._drag_data["win_x"] + delta_x
        new_y = self.timer_window._drag_data["win_y"] + delta_y
        
        # Обмеження в межах екрана
        new_x = max(0, min(new_x, self.root.winfo_screenwidth() - self.timer_window.winfo_width()))
        new_y = max(0, min(new_y, self.root.winfo_screenheight() - self.timer_window.winfo_height()))
        
        self.timer_window.geometry(f"+{new_x}+{new_y}")
        self.save_position()  # Зберігаємо позицію під час перетягування


    def start_timer(self):
        if not self.timer_enabled or not self.game_active:
            return
            
        difficulty_times = {
            "Легкий": 300,
            "Середній": 240,
            "Важкий": 180
        }
        self.remaining_time = difficulty_times.get(self.difficulty_var.get(), 300)
        self.update_timer()
        self.timer_id = self.root.after(1000, self.timer_tick)

    def timer_tick(self):
        """Оновлений метод оновлення таймера"""
        if self.game_active and self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_timer()
            if self.remaining_time <= 0:
                self.game_over = True
                self.stop_timer()
                self.show_custom_dialog("Час вийшов!", "Ви програли через закінчення часу!")
                self.reveal_mines()
                self.set_board_state("disabled")
            else:
                self.timer_id = self.root.after(1000, self.timer_tick)

    def update_timer(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.timer_label.config(text=f"{minutes:02}:{seconds:02}")

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    

    def _update_difficulty_menu_style(self):
        """Оновлює стиль випадаючого меню рівнів складності"""
        self.style.configure("TMenubutton",
                            background=self.button_bg_color,
                            foreground=self.text_color)
        self.style.map("TMenubutton",
                      background=[('active', self.hover_color)],
                      foreground=[('active', self.text_color)])
    

    def _update_menu_colors(self):
        """Оновлює кольори пунктів меню"""
        menu = self.difficulty_menu["menu"]
        for index in range(menu.index("end") + 1):
            menu.entryconfigure(
                index,
                foreground=self.text_color,
                background=self.button_bg_color,
                activeforeground=self.text_color,
                activebackground=self.button_active_bg
            )
        
    def update_window_size(self):
        """Оновлює розмір вікна відповідно до складності гри."""
        base_size = 450  # Мінімальний розмір для легкого рівня
        if self.size == 8:
            window_size = f"{base_size}x{base_size + 100}"  # Фіксований розмір для легкого рівня
        elif self.size == 12:
            window_size = f"{base_size + 150}x{base_size + 150}"  # Збільшений розмір для середнього рівня
        elif self.size == 16:
            window_size = f"{base_size + 300}x{base_size + 300}"  # Збільшений розмір для важкого рівня
        else:
            window_size = f"{base_size}x{base_size + 100}"  # Запасний варіант, якщо щось піде не так

        self.root.geometry(window_size)
        self.root.resizable(False, False)

    def _update_widgets(self, widget):
        """Рекурсивно оновлює кольори всіх віджетів у вікні."""
        try:
            # Оновлення стандартних віджетів
            if isinstance(widget, (tk.Label, tk.Button, tk.Listbox, tk.Text)):
                widget.configure(bg=self.bg_color, fg=self.text_color)
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=self.bg_color)
            
            # Оновлення Ttk віджетів
            if isinstance(widget, ttk.Checkbutton):
                widget.configure(style="TCheckbutton")
            elif isinstance(widget, ttk.Scrollbar):
                widget.configure(style="Vertical.TScrollbar")
            
            # Рекурсивний обхід дочірніх віджетів
            for child in widget.winfo_children():
                self._update_widgets(child)
                
        except tk.TclError:
            pass  # Ігноруємо віджети які не підтримують зміну кольорів

    def setup_initial_state(self):
        """Очищає область гри і створює нову гру."""
        self.game_active = False
        self.clear_game_frame()
        self.create_board()
        self.place_mines()
        self.update_numbers()
        self.set_board_state("disabled")
        self.game_active = False  # Вимкнення прапорця активної гри

    def update_button_styles(self):
        """Оновлює стиль кнопок у меню."""
        for btn in [self.start_button, self.toggle_theme_button, self.history_button, self.info_button]:
            btn.config(style="TButton")
        self.difficulty_menu.config(style="TMenubutton")

    def connect_db(self):
        """Підключення до бази даних з перевіркою існування файлу"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Підключено до бази даних: {self.db_path}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося підключитися до БД: {str(e)}")
            sys.exit(1)

    def create_db(self):
        """Створення таблиць якщо вони не існують"""
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS games (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        result TEXT,
                        size INTEGER,
                        difficulty TEXT
                    )
                """)
            #print("Таблиці БД успішно створені/перевірені")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка створення таблиць: {str(e)}")

    def save_game(self, result):
        """Зберігає результат гри в базу даних."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        difficulty = self.difficulty_var.get()
        with self.conn:
            self.conn.execute("INSERT INTO games (date, result, size, difficulty) VALUES (?, ?, ?, ?)", (date, result, self.size, difficulty))

    def start_game(self):
        """Початок нової гри з перевіркою таймера"""
        self.restart_game(confirm=False)
        self.game_active = True
        self.game_over = False
        self.set_board_state("normal")
        
        # Примусове оновлення таймера
        if self.timer_enabled:
            self.create_timer_window()
            self.start_timer()
            self.timer_window.attributes('-topmost', 1)
            self.timer_window.lift()

    def restart_game(self, confirm=True):
        """Перезапуск гри з повною перевіркою таймера"""
        if confirm and self.game_active and not self.confirm_action("restart"):
            return
        
        # Зупиняємо гру та таймер
        self.game_active = False
        self.game_over = False
        self.first_click = True
        self.flagged.clear()
        self.stop_timer()
        
        # Переініціалізація гри
        self.init_colors()
        self.clear_game_frame()
        self.create_board()
        self.place_mines()
        self.update_numbers()
        self.set_board_state("disabled")
        
        # Якщо таймер був активний - перезапускаємо
        if self.timer_enabled:
            if self.timer_window:
                self.timer_window.destroy()
            self.create_timer_window()
            self.start_timer()

        
    def clear_game_frame(self):
        """Очищає область гри."""
        if hasattr(self, 'game_frame'):
            for widget in self.game_frame.winfo_children():
                widget.destroy()

        self.buttons = []
        self.board = []

    def create_board(self):
        """Створює поле з оновленими кольорами"""
        button_size = 40 - (self.size - 8) * 4
        
        for row in range(self.size):
            row_buttons = []
            row_board = []
            for col in range(self.size):
                btn = tk.Button(
                    self.game_frame,
                    width=button_size,
                    height=button_size,
                    command=lambda r=row, c=col: self.left_click(r, c),
                    bg=self.button_bg_color,  # Використовуємо актуальні кольори
                    fg=self.text_color,
                    activebackground=self.hover_color,
                    highlightthickness=0
                )
                btn.bind("<Button-3>", lambda event, r=row, c=col: self.right_click(r, c))
                btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                row_buttons.append(btn)
                row_board.append(0)
            self.buttons.append(row_buttons)
            self.board.append(row_board)

        for row in range(self.size):
            self.game_frame.rowconfigure(row, weight=1)
            self.game_frame.columnconfigure(row, weight=1)

    def set_board_state(self, state):
        """Встановлює стан всіх кнопок на ігровому полі (active/disabled)."""
        for row_buttons in self.buttons:
            for btn in row_buttons:
                btn.config(state=state)

    def place_mines(self, exclude=None):
        """Розміщує міни на випадкових позиціях."""
        mines_placed = 0
        while mines_placed < self.mines:
            row, col = random.randint(0, self.size - 1), random.randint(0, self.size - 1)
            if self.board[row][col] != 'M':
                self.board[row][col] = 'M'
                mines_placed += 1

    def update_numbers(self):
        """Оновлює числові значення на клітинках навколо мін."""
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != 'M':
                    mines_count = sum(
                        self.board[r][c] == 'M'
                        for r in range(max(0, row - 1), min(self.size, row + 2))
                        for c in range(max(0, col - 1), min(self.size, col + 2))
                    )
                    self.board[row][col] = mines_count
    def custom_dialog(self):
        """Метод класу для створення діалогового вікна."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Вибір")
        dialog.geometry("340x100")
        dialog.resizable(False, False)
        dialog.configure(bg=self.bg_color)

        label = tk.Label(dialog, text="Ви натрапили на міну! Хочете продовжити?", 
                         font=("Arial", 12), bg=self.bg_color, fg=self.text_color)
        label.pack(pady=10)

        result = {"choice": None}

        def on_yes():
            result["choice"] = True
            dialog.destroy()

        def on_no():
            result["choice"] = False
            dialog.destroy()

        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=10)

        # Оновлений стиль для кнопок
        style = ttk.Style()
        style.configure("RoundedButton.TButton",
                        font=("Arial", 7, "bold"),
                        relief="flat",
                        padding=7,
                        width=7,
                        anchor="center",
                        background=self.button_bg_color,
                        foreground=self.text_color,  # Колір тексту
                        borderwidth=1,
                        focusthickness=3)
        
        style.map("RoundedButton.TButton",
                  background=[("active", self.button_active_bg)],
                  foreground=[("active", self.text_color)])

        # Кнопка "Так"
        yes_button = ttk.Button(button_frame, text="Так", style="RoundedButton.TButton", command=on_yes)
        yes_button.pack(side="left", padx=10)

        # Кнопка "Ні"
        no_button = ttk.Button(button_frame, text="Ні", style="RoundedButton.TButton", command=on_no)
        no_button.pack(side="right", padx=10)

        # Не дозволяє закрити вікно за допомогою X вікна
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        # Вікно стає модальним, чекає, поки користувач не вибере
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result["choice"]
    
    def left_click(self, row, col):
        """Обробляє лівий клік на клітинці."""
        if not self.game_active:  
            return
        if not self.game_active:
            self.game_active = True 
        if self.game_over or (row, col) in self.flagged:
            return

        if self.board[row][col] == 'M':
            if self.first_click and self.dialog_enabled:  # Діалог працює, якщо він увімкнений
                choice = self.custom_dialog()  # Викликаємо діалогове вікно
                if choice is None:  # Якщо закрили без вибору - нічого не робимо
                    return
                
                self.first_click = False  # Після першого кліку більше не з’являється діалог у цій грі

                if choice:
                    # Гравець хоче продовжити
                    self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")
                    self.reveal_cell(row, col)
                    return
                else:
                    # Гравець обрав програти
                    self.reveal_mines()
                    self.game_over = True
                    self.save_game("Програв")
                    self.show_custom_dialog("Гра завершена", "Ви програли!")
                    self.game_active = False
                    self.set_board_state("disabled")
                    return
            else:
                # Якщо діалог вимкнений або це не перший клік – одразу програємо
                self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")
                self.reveal_mines()
                self.game_over = True
                self.save_game("Програв")
                self.show_custom_dialog("Гра завершена", "Ви програли!")
                self.game_active = False
                self.set_board_state("disabled")
                return

        # Якщо це не міна, відкриваємо клітинку
        self.reveal_cell(row, col)

        # Після першого кліку змінюємо стан
        self.first_click = False

        # Перевірка на перемогу
        if self.check_win():
            self.game_over = True
            self.save_game("Виграв")
            messagebox.showinfo("Гра завершена", "Ви виграли!")
            self.game_active = False
            self.set_board_state("disabled")

    def reset_game(self):
        """Скидає гру для нового раунду."""
        self.game_over = False
        self.first_click = True  # Скидаємо стан першого кліку
        self.flagged.clear()
        self.buttons = []
        self.board = []
        self.create_widgets()  # Перестворюємо інтерфейс

    def reveal_cell(self, row, col):
        """Відкриває клітинку і показує число мін поруч."""
        if self.buttons[row][col]['state'] == 'disabled':
            return

        value = self.board[row][col]
        if value == 0:
            self.buttons[row][col].config(text="", bg=self.reveal_color, state="disabled")
            for r in range(max(0, row - 1), min(self.size, row + 2)):
                for c in range(max(0, col - 1), min(self.size, col + 2)):
                    self.reveal_cell(r, c)
        else:
            self.buttons[row][col].config(text=str(value), bg=self.reveal_color, state="disabled")

    def reveal_mines(self):
        """Відкриває всі міни на полі гри."""
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 'M':
                    self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")

    def right_click(self, row, col):
        """Обробляє правий клік (додавання/зняття прапорця)."""
        if self.buttons[row][col]['state'] == 'disabled' or self.game_over:
            return

        if (row, col) in self.flagged:
            self.buttons[row][col].config(text="")
            self.flagged.remove((row, col))
        else:
            self.buttons[row][col].config(text="🚩", fg=self.flag_color)
            self.flagged.add((row, col))

    def check_win(self):
        """Перевірка на перемогу з правильним завершенням таймера"""
        correct_flags = all(self.board[r][c] == 'M' for r, c in self.flagged)
        all_revealed = all(self.buttons[r][c]['state'] == 'disabled' 
                       for r in range(self.size) 
                       for c in range(self.size) 
                       if self.board[r][c] != 'M')
        
        if correct_flags and all_revealed:
            self.game_over = True
            self.stop_timer()
            self.save_game("Виграв")
            self.show_custom_dialog("Гра завершена", "Ви виграли!")
            self.game_active = False
            self.set_board_state("disabled")
            return True
        return False

    def set_difficulty(self, selected_difficulty):
        """Обробляє зміну рівня складності з підтвердженням"""
        # Зберігаємо поточний рівень перед зміною
        previous_difficulty = self.last_difficulty
        
        # Якщо гра активна і користувач відмовляється
        if not self.game_over and not self.confirm_action("difficulty"):
            # Відновлюємо попередній рівень у меню
            self.difficulty_var.set(previous_difficulty)
            # Оновлюємо випадаючий список
            self._update_difficulty_menu(previous_difficulty)
            return
        
        # Оновлюємо параметри гри
        difficulty_settings = {
            "Легкий": (10, 10),
            "Середній": (12, 20),
            "Важкий": (16, 40)
        }
        self.size, self.mines = difficulty_settings[selected_difficulty]
        self.last_difficulty = selected_difficulty  # Оновлюємо останній рівень
        
        # Оновлюємо інтерфейс
        self.difficulty_var.set(selected_difficulty)
        self._update_difficulty_menu()
        self.save_settings()
        self.update_window_size()
        self.restart_game(confirm=False)

    def _update_difficulty_menu(self):
        """Оновлює опції меню, залишаючи лише доступні рівні"""
        current = self.difficulty_var.get()
        menu = self.difficulty_menu["menu"]
        menu.delete(0, "end")
        
        # Додаємо лише рівні, які відрізняються від поточного
        for level in ["Легкий", "Середній", "Важкий"]:
            if level != current:
                menu.add_command(
                    label=level,
                    command=lambda v=level: self.set_difficulty(v),
                    foreground=self.text_color,
                    background=self.button_bg_color,
                    activeforeground=self.text_color,
                    activebackground=self.button_active_bg
                )
        
        # Явно оновлюємо відображене значення
        if not current:
            self.difficulty_var.set(self.last_difficulty)
        else:
            self.difficulty_var.set(current)
                
    def show_history(self):
        """Показує історію ігор з однаковим фоном."""
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Історія ігор")
        self.history_window.geometry("462x350")
        self.history_window.resizable(False, False)
        self.history_window.configure(bg=self.bg_color)

        # Головний контейнер
        main_frame = tk.Frame(self.history_window, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Список історії
        history_listbox = tk.Listbox(
            main_frame,
            bg=self.bg_color,
            fg=self.text_color,
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 10)  # Додано закриваючу дужку
        )
        history_listbox.pack(side='left', fill='both', expand=True)

        # Скролбар
        scrollbar = ttk.Scrollbar(
            main_frame,
            orient="vertical",
            style="Vertical.TScrollbar",
            command=history_listbox.yview
        )
        scrollbar.pack(side='right', fill='y')
        history_listbox.config(yscrollcommand=scrollbar.set)

        # Заповнення даними
        with self.conn:
            cursor = self.conn.execute("SELECT date, result, difficulty FROM games ORDER BY id DESC")
            rows = cursor.fetchall()

        for row in rows:
            history_listbox.insert(tk.END, f"Дата: {row[0]}, Результат: {row[1]}, Складність: {row[2]}")
        

        # Обробник закриття вікна
    def on_close(self):
        """Обробник закриття головного вікна"""
        # Оновлюємо позицію таймера перед збереженням
        if self.timer_window and self.timer_window.winfo_exists():
            self.save_position()
        
        # Зберігаємо всі налаштування
        self.save_settings()
        
        # Зупиняємо таймер
        self.stop_timer()
        
        # Закриваємо з'єднання з БД
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except Exception as e:
                print(f"Помилка закриття БД: {e}")
        
        # Закриваємо вікно
        self.root.destroy()


    def toggle_dialog(self):
        """Обробник зміни стану чекбоксу"""
        self.dialog_enabled = self.dialog_var.get()
        self.save_settings()
    
    def show_info(self):
        """Показує вікно з інформацією про гру."""
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.lift()
            return

        self.info_window = tk.Toplevel(self.root)
        self.info_window.title("Про гру")
        self.info_window.geometry("500x500")
        self.info_window.resizable(False, False)
        self.info_window.configure(bg=self.bg_color)

        def on_close():
            self.info_window.destroy()
            self.info_window = None

        self.info_window.protocol("WM_DELETE_WINDOW", on_close)

        main_frame = tk.Frame(self.info_window, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    
        #Кнопка керування таймером    
        timer_btn_text = "Вимкнути таймер" if self.timer_enabled else "Увімкнути таймер"
        self.timer_toggle_btn = ttk.Button(
            main_frame,
            text=timer_btn_text,
            command=self.toggle_timer,
            style='TButton'
        )
        self.timer_toggle_btn.pack(anchor='w', pady=(0, 10))

        # Чекбокс
        self.dialog_checkbox = ttk.Checkbutton(
            main_frame,
            text="Запит при першому кліку на міну",
            variable=self.dialog_var,
            command=self.toggle_dialog,
            style='TCheckbutton'
        )
        self.dialog_checkbox.pack(anchor='w', pady=(0, 10))

        # Текстове поле
        self.info_text = tk.Text(
            main_frame,
            wrap='word',
            height=20,
            width=50,
            bg=self.bg_color,
            fg=self.text_color,
            borderwidth=0
        )
        self.info_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(
            main_frame,
            orient="vertical",
            style="Vertical.TScrollbar",
            command=self.info_text.yview
        )
        scrollbar.pack(side='right', fill='y')
        self.info_text.config(yscrollcommand=scrollbar.set)
        
        # Вставка тексту правил...
        self._insert_info_text()
        self.info_text.config(state=tk.DISABLED)

        self.info_text.configure(
            insertbackground=self.text_color,
            selectbackground=self.button_active_bg
        )

    def _insert_info_text(self):
        """Вставляє текст правил гри у текстове поле."""
        rules_text = """
Правила гри «Мінер»:

Основні правила
1. Мета гри: Ваша мета — відкрити всі безпечні клітинки на полі, не натискаючи на міни. 
2. Клітинки: Існують дві основні типи клітинок: безпечні (числові або порожні) і міни. 

Дії гравця
3. Натискання на клітинки: Клацніть на клітинку, щоб її відкрити. Якщо ви натиснете на міну, гра закінчиться. 
4. Числові клітинки: Клітинки з числами вказують, скільки мін знаходиться у сусідніх клітинках. Використовуйте цю інформацію, щоб приймати обґрунтовані рішення. 
5. Порожні клітинки: Якщо ви відкриваєте клітинку, що не має чисел, всі сусідні порожні клітинки відкриються автоматично. 

Використання флажків
6. Додавання флажків: Клацніть правою кнопкою миші на клітинці, щоб позначити її флажком. Це вказує на те, що ви вважаєте цю клітинку небезпечною. 
7. Зняття флажків: Якщо ви змінили думку, клацніть правою кнопкою миші ще раз, щоб зняти флажок з клітинки. 

Вибір рівня складності
8. Вибір складності: Перед початком гри ви можете вибрати рівень складності: легкий, середній або важкий. Це вплине на розмір поля та кількість мін. 

Завершення гри
9. Виграш: Ви виграєте гру, відкривши всі безпечні клітинки. 
10. Програш: Якщо ви натиснете на міну, ви програєте, і всі міни на полі будуть відкриті. 

Додаткові поради
11. Слідкуйте за числами: Використовуйте числа для визначення місця розташування мін. Чим більше відкриваєте, тим більше інформації отримуєте. 
12. Будьте обережні: Якщо ви не впевнені, що клітинка безпечна, використовуйте флажок, щоб запобігти випадковому натисканню. 

Про програму: 
Цю гру розробив @kilo3528.
"""
        self.info_text.insert(tk.END, rules_text.strip())
        self.info_text.tag_configure("header", font=("Arial", 12, "bold"))
        self.info_text.tag_add("header", "1.0", "1.end")


    

            



# Створення вікна Tkinter
root = tk.Tk()
root.title("Мінер")
app = Minesweeper(root)
root.mainloop()
