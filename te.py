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
        self.size = size
        self.mines = mines
        self.buttons = []
        self.board = []
        self.game_over = False
        self.flagged = set()
        self.first_click = True
        self.settings_file = "settings.json"
        
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.history_window = None
        self.info_window = None 
        
        # Завантажити налаштування
        self.load_settings()
        
        # Ініціалізація Tkinter змінних
        self.dialog_var = tk.BooleanVar(value=self.dialog_enabled)
        self.difficulty_var = tk.StringVar(value="Легкий")
        
        # Ініціалізація кольорів
        self.init_colors()
        
        # Створення віджетів
        self.create_widgets()
        
        # Оновлення кольорів
        self.update_colors()
        
        # Ініціалізація бази даних
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_db()
        
        # Початковий стан гри
        self.setup_initial_state()

    def init_colors(self):
        """Ініціалізує кольорові змінні на основі теми."""
        if self.dark_mode:
            self.bg_color = "#2c2f33"
            self.button_bg_color = "#23272a"
            self.button_active_bg = "#7289da"
            self.text_color = "#ffffff"
            self.reveal_color = "#36393f"
            self.mine_color = "#000000"
            self.flag_color = "#f39c12"
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
            self.style.map("TCheckbutton",
                          background=[("active", self.bg_color)],
                          indicatorcolor=[("selected", self.text_color)],
                          indicatorbackground=[("selected", self.button_active_bg)]) 
        else:
            self.bg_color = "#ffffff"
            self.button_bg_color = "#e0e0e0"
            self.button_active_bg = "#e0e0e0"
            self.text_color = "#000000"
            self.reveal_color = "#d0d0d0"
            self.mine_color = "#000000"
            self.flag_color = "#0000ff"
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
            self.style.map("TCheckbutton",
                          background=[("active", self.bg_color)],
                          indicatorcolor=[("selected", self.text_color)],
                          indicatorbackground=[("selected", "#4682B4")])


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

        

        
    
        
    def load_settings(self):
        """Завантажує налаштування з файлу."""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.dark_mode = settings.get("dark_mode", False)
                self.dialog_enabled = settings.get("dialog_enabled", True)
        except (FileNotFoundError, json.JSONDecodeError):
            self.dark_mode = False
            self.dialog_enabled = True
            self.save_settings()

    def save_settings(self):
        """Зберігає поточні налаштування у файл."""
        with open(self.settings_file, "w") as f:
            json.dump({
                "dark_mode": self.dark_mode,
                "dialog_enabled": self.dialog_enabled
            }, f, indent=4)

    def toggle_theme(self):
        """Перемикає тему та оновлює всі елементи."""
        self.dark_mode = not self.dark_mode
        self.init_colors()
        
        # Оновлюємо головне вікно
        self.update_colors()
        
        # Оновлюємо ігрове поле
        for row in self.buttons:
            for btn in row:
                btn.configure(bg=self.button_bg_color, fg=self.text_color)

        # Оновлюємо додаткові вікна
        for window in [self.history_window, self.info_window]:
            if window and window.winfo_exists():
                window.configure(bg=self.bg_color)
                self._update_widgets(window)  # Викликаємо рекурсивне оновлення

        # Оновлюємо стилі скролбарів
        self._refresh_scrollbars()
        self.save_settings()
        self.restart_game()

    def create_widgets(self):
        """Створює елементи інтерфейсу."""
        # Головне меню
        self.menu_frame = tk.Frame(self.root, bg=self.bg_color)
        self.menu_frame.pack(pady=10, anchor='w')
        
        # Кнопки меню
        self.start_button = ttk.Button(self.menu_frame, text="Почати гру", command=self.restart_game)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.toggle_theme_button = ttk.Button(self.menu_frame, text="Темна тема", command=self.toggle_theme)
        self.toggle_theme_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.history_button = ttk.Button(self.menu_frame, text="Історія ігор", command=self.show_history)
        self.history_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Ініціалізація меню вибору рівня
        self.difficulty_var.set("Легкий")  # Встановлюємо початкове значення
        available_difficulties = ["Середній", "Важкий"]  # Доступні рівні на старті
        
        self.difficulty_menu = ttk.OptionMenu(
            self.menu_frame,
            self.difficulty_var,
            self.difficulty_var.get(),
            *available_difficulties,
            command=self.set_difficulty
        )
        self.difficulty_menu.config(width=6.2)
        self.difficulty_menu.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self.info_button = ttk.Button(self.menu_frame, text="...", command=self.show_info)
        self.info_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Ігрове поле
        self.game_frame = tk.Frame(self.root, bg=self.bg_color)
        self.game_frame.pack(pady=10)
        
        self.update_window_size()
        
        
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
        self.clear_game_frame()
        self.create_board()
        self.place_mines()
        self.update_numbers()
        self.set_board_state("disabled")

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
        """Розпочинає нову гру."""
        self.clear_game_frame()
        self.create_board()
        self.place_mines()
        self.update_numbers()
        self.set_board_state("normal")

    def restart_game(self):
        """Перезапускає гру."""
        self.game_over = False
        self.flagged.clear()  # Очистити набір флажків
        self.clear_game_frame()
        self.create_board()
        self.place_mines()
        self.update_numbers()
        self.set_board_state("normal")

    def clear_game_frame(self):
        """Очищає область гри."""
        if hasattr(self, 'game_frame'):
            for widget in self.game_frame.winfo_children():
                widget.destroy()

        self.buttons = []
        self.board = []

    def create_board(self):
        """Створює поле гри з динамічним розміром клітинок відповідно до рівня складності."""
        button_size = 40 - (self.size - 8) * 4  # Динамічний розмір кнопок

        for row in range(self.size):
            row_buttons = []
            row_board = []
            for col in range(self.size):
                btn = tk.Button(self.game_frame, width=button_size, height=button_size,
                                command=lambda r=row, c=col: self.left_click(r, c),
                                bg=self.button_bg_color, fg=self.text_color)
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
                    messagebox.showinfo("Гра завершена", "Ви програли!")
                    return
            else:
                # Якщо діалог вимкнений або це не перший клік – одразу програємо
                self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")
                self.reveal_mines()
                self.game_over = True
                self.save_game("Програв")
                messagebox.showinfo("Гра завершена", "Ви програли!")
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
        """Перевіряє, чи виграв гравець (всі міни відмічені флажками)."""
        correct_flags = all(self.board[r][c] == 'M' for r, c in self.flagged)
        all_revealed = all(self.buttons[r][c]['state'] == 'disabled' for r in range(self.size) for c in range(self.size) if self.board[r][c] != 'M')
        return correct_flags and all_revealed

    def set_difficulty(self, selected_difficulty):
        """Обробляє зміну рівня складності."""
        # Оновлюємо поточний рівень
        self.difficulty_var.set(selected_difficulty)
        
        # Генеруємо список доступних рівнів
        all_difficulties = ["Легкий", "Середній", "Важкий"]
        available = [d for d in all_difficulties if d != selected_difficulty]
        
        # Оновлюємо випадаюче меню
        menu = self.difficulty_menu["menu"]
        menu.delete(0, "end")
        for difficulty in available:
            menu.add_command(
                label=difficulty,
                command=lambda v=difficulty: self.set_difficulty(v)
            )
        
        # Оновлюємо параметри гри
        difficulty_settings = {
            "Легкий": (10, 10),
            "Середній": (12, 20),
            "Важкий": (16, 40)
        }
        self.size, self.mines = difficulty_settings[selected_difficulty]
        self.update_window_size()
        self.restart_game()


    # Оновлений метод show_history():
    def show_history(self):
        """Показує історію ігор з однаковим фоном."""
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Історія ігор")
        self.history_window.geometry("500x400")
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
        def on_close():
            self.history_window.destroy()
            self.history_window = None

        self.history_window.protocol("WM_DELETE_WINDOW", on_close)


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

        # Решта коду створення інтерфейсу залишається незмінною
        main_frame = tk.Frame(self.info_window, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Чекбокс
        self.dialog_checkbox = ttk.Checkbutton(
            main_frame,
            text="Запит при першому кліку на міну",
            variable=self.dialog_var,
            command=self.toggle_dialog,
            style="TCheckbutton"
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

        # Додамо оновлення курсора
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
