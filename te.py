import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import Toplevel, Label, Button
import random
import sqlite3
from datetime import datetime
import os
import sys
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
        self.dark_mode = False  # Встановлюємо кольорову тему за замовчуванням
        self.flagged = set()  # Множина з флажками
        self.first_click = True 

        # Налаштування кольорів за замовчуванням
        self.bg_color = "#ffffff"
        self.button_bg_color = "#e0e0e0"
        self.button_active_bg = "#e0e0e0"
        self.text_color = "#000000"
        self.reveal_color = "#d0d0d0"
        self.mine_color = "#000000"  # Колір для бомб - чорний
        self.flag_color = "#0000ff"

        # Налаштування бази даних
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_db()

        # Створення кнопок і елементів інтерфейсу
        self.create_widgets()
    

    def update_colors(self):
        """Оновлює кольори в залежності від теми."""
        if self.dark_mode:
            self.bg_color = "#2c2f33"
            self.button_bg_color = "#23272a"
            self.button_active_bg = "#7289da"
            self.text_color = "#ffffff"
            self.reveal_color = "#36393f"
            self.mine_color = "#000000"  # Чорний колір для бомб в темному режимі
            self.flag_color = "#f39c12"
            theme_text = "Світла тема"
        else:
            self.bg_color = "#ffffff"
            self.button_bg_color = "#e0e0e0"
            self.button_active_bg = "#e0e0e0"
            self.text_color = "#000000"
            self.reveal_color = "#d0d0d0"
            self.mine_color = "#000000"  # Чорний колір для бомб в світлому режимі
            self.flag_color = "#0000ff"
            theme_text = "Темна тема"

        # Налаштування стилів
        self.style = ttk.Style()
        self.style.configure("TButton",
                             background=self.button_bg_color,
                             foreground=self.text_color)
        self.style.configure("TMenubutton",
                             background=self.button_bg_color,
                             foreground=self.text_color)

        # Оновлення кольорів вікна
        if hasattr(self, 'menu_frame'):
            self.menu_frame.configure(bg=self.bg_color)
        if hasattr(self, 'game_frame'):
            self.game_frame.configure(bg=self.bg_color)

        # Update colors for all open windows
        for window in self.root.winfo_children():
            if isinstance(window, tk.Toplevel):
                window.configure(bg=self.bg_color)
                for widget in window.winfo_children():
                    if isinstance(widget, tk.Listbox):
                        widget.configure(bg=self.button_bg_color, fg=self.text_color)
                    elif isinstance(widget, tk.Text):
                        widget.configure(bg=self.button_bg_color, fg=self.text_color)
                    elif isinstance(widget, tk.Frame):
                        widget.configure(bg=self.bg_color)

        self.update_button_styles()

        # Оновлюємо текст кнопки теми
        self.toggle_theme_button.config(text=theme_text)

    def create_widgets(self):
        """Створює всі кнопки і елементи інтерфейсу."""
        # Налаштування вікна
        self.root.configure(bg=self.bg_color)
        self.menu_frame = tk.Frame(self.root, bg=self.bg_color)
        self.menu_frame.pack(pady=10, anchor='w')

        # Створення кнопок меню
        self.start_button = ttk.Button(self.menu_frame, text="Почати гру", command=self.restart_game)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.toggle_theme_button = ttk.Button(self.menu_frame, text="Темна тема", command=self.toggle_theme)
        self.toggle_theme_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.history_button = ttk.Button(self.menu_frame, text="Історія ігор", command=self.show_history)
        self.history_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.difficulty_var = tk.StringVar(value="Легкий")
        self.difficulty_menu = ttk.OptionMenu(self.menu_frame, self.difficulty_var, "Легкий", "Середній", "Важкий", command=self.set_difficulty)
        self.difficulty_menu.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        self.info_button = ttk.Button(self.menu_frame, text="...", command=self.show_info)
        self.info_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        # Налаштування стилю
        self.update_colors()

        # Налаштування вікна гри
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

    def toggle_theme(self):
        """Перемикає між темним і світлим режимом."""
        self.dark_mode = not self.dark_mode
        self.update_colors()
        self.clear_game_frame()
        self.create_board()
        self.set_board_state("disabled")

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
            if not any('clicked' in button.keys() for row_buttons in self.buttons for button in row_buttons):
                # Це перший клік - запускаємо кастомне вікно
                choice = self.custom_dialog()  # Передаємо головне вікно гри
                if choice is None:  # Якщо діалог закрили без вибору, нічого не робимо
                    return
                
                self.first_click = False  # Після першого ходу діалог більше не з'явиться

                if choice:
                    # Гравець обрав продовжити гру
                    self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")
                    self.reveal_cell(row, col)  # Відкриваємо клітинку з міною
                    return
                else:
                    # Гравець обрав програти
                    self.reveal_mines()
                    self.game_over = True
                    self.save_game("Програв")
                    messagebox.showinfo("Гра завершена", "Ви програли!")
                    return
            else:
                # Гра вже триває, відкриваємо міну
                self.buttons[row][col].config(text="💣", bg="red", fg=self.mine_color, state="disabled")
                self.reveal_mines()
                self.game_over = True
                self.save_game("Програв")
                messagebox.showinfo("Гра завершена", "Ви програли!")
                return

        self.reveal_cell(row, col)

        if self.first_click:
            self.first_click = False

        if self.check_win():
            self.game_over = True
            self.save_game("Виграв")
            messagebox.showinfo("Гра завершена", "Ви виграли!")


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

    def set_difficulty(self, value):
        """Змінює рівень складності гри та оновлює меню."""
        
        # Оновлення меню рівнів, щоб воно завжди містило всі варіанти
        self.difficulty_menu["menu"].delete(0, "end")  # Очищення меню
        options = ["Легкий", "Середній", "Важкий"]

        for option in options:
            self.difficulty_menu["menu"].add_command(
                label=option, 
                command=lambda v=option: self.set_difficulty(v)  # Викликає цю ж функцію при виборі
            )
        
        self.difficulty_var.set(value)  # Встановлюємо вибраний рівень

        # Оновлення налаштувань гри відповідно до вибраної складності
        difficulty_settings = {
            "Легкий": (10, 10),
            "Середній": (12, 20),
            "Важкий": (16, 40)
        }

        if value in difficulty_settings:
            self.size, self.mines = difficulty_settings[value]
            self.update_window_size()  # Оновлення розміру вікна
            
            # Перезапуск гри з оновленням всіх елементів
            self.restart_game()
            self.create_board()  # Використовуємо правильний метод


    def show_history(self):
        """Показує історію ігор з бази даних."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Історія ігор")
        history_window.geometry("400x300")
        history_window.configure(bg=self.bg_color)

        history_listbox = tk.Listbox(history_window, bg=self.button_bg_color, fg=self.text_color)
        history_listbox.pack(fill="both", expand=True)

        with self.conn:
            cursor = self.conn.execute("SELECT date, result, difficulty FROM games ORDER BY id DESC")
            rows = cursor.fetchall()

        for row in rows:
            history_listbox.insert(tk.END, f"Дата: {row[0]}, Результат: {row[1]}, Складність: {row[2]}")
     

    def show_info(self):
            """Показує інформацію про гру і правила."""
            info_window = tk.Toplevel(self.root)
            info_window.title("Про гру")
            info_window.geometry("500x450")
            info_window.resizable(False, False)
            info_window.configure(bg=self.bg_color)
            
            # Створюємо фрейм для прокрутки
            frame = tk.Frame(info_window, bg=self.bg_color)
            frame.pack(fill='both', expand=True)
            

            # Додаємо текстове поле
            self.info_text = tk.Text(frame, wrap='word', height=20, width=50, bg=self.button_bg_color, fg=self.text_color)
            self.info_text.pack(side=tk.LEFT, fill='both', expand=True)
            
            # Додаємо смугу прокрутки
            scrollbar = tk.Scrollbar(frame, command=self.info_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill='y')

            # Прив'язуємо смугу прокрутки до текстового поля
            self.info_text.config(yscrollcommand=scrollbar.set)
            

            # Вставляємо текст правил гри
            self.info_text.insert(tk.END, "Правила гри «Мінер»:\n\n"
                                    "Основні правила\n"
                                    "1. Мета гри: Ваша мета — відкрити всі безпечні клітинки на полі, не натискаючи на міни. \n"
                                    "2. Клітинки: Існують дві основні типи клітинок: безпечні (числові або порожні) і міни. \n\n"
                                    "Дії гравця\n"
                                    "3. Натискання на клітинки: Клацніть на клітинку, щоб її відкрити. Якщо ви натиснете на міну, гра закінчиться. \n"
                                    "4. Числові клітинки: Клітинки з числами вказують, скільки мін знаходиться у сусідніх клітинках. Використовуйте цю інформацію, щоб приймати обґрунтовані рішення. \n"
                                    "5. Порожні клітинки: Якщо ви відкриваєте клітинку, що не має чисел, всі сусідні порожні клітинки відкриються автоматично. \n\n"
                                    "Використання флажків\n"
                                    "6. Додавання флажків: Клацніть правою кнопкою миші на клітинці, щоб позначити її флажком. Це вказує на те, що ви вважаєте цю клітинку небезпечною. \n"
                                    "7. Зняття флажків: Якщо ви змінили думку, клацніть правою кнопкою миші ще раз, щоб зняти флажок з клітинки. \n"
                                    "Вибір рівня складності"
                                    "8. Вибір складності: Перед початком гри ви можете вибрати рівень складності: легкий, середній або важкий. Це вплине на розмір поля та кількість мін. \n"
                                    "Завершення гри\n"
                                    "9. Виграш: Ви виграєте гру, відкривши всі безпечні клітинки. \n"
                                    "10. Програш: Якщо ви натиснете на міну, ви програєте, і всі міни на полі будуть відкриті. \n\n"
                                    "Додаткові поради\n"
                                    "11. Слідкуйте за числами: Використовуйте числа для визначення місця розташування мін. Чим більше відкриваєте, тим більше інформації отримуєте. \n"
                                    "12. Будьте обережні: Якщо ви не впевнені, що клітинка безпечна, використовуйте флажок, щоб запобігти випадковому натисканню. \n\n"
                                    "Про програму: \n\n"
                                    "Цю гру розробив @kilo3528.\n")

            
            self.info_text.config(state=tk.DISABLED)  # Дезактивуємо редагування текстового поля


# Створення вікна Tkinter
root = tk.Tk()
root.title("Мінер")
app = Minesweeper(root)
root.mainloop()
