import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QComboBox, QMessageBox,
    QTabWidget, QTextEdit
)
from db import get_connection


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в Trello")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Хеш пароля")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name FROM Users WHERE username=%s AND password_hash=%s", (username, password))
        user = cursor.fetchone()

        if user:
            self.hide()
            self.task_window = TaskWindow(user_id=user[0], full_name=user[1])
            self.task_window.show()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")


class TaskWindow(QWidget):
    def __init__(self, user_id, full_name):
        super().__init__()
        self.setWindowTitle(f"Trello — {full_name}")
        self.setGeometry(100, 100, 700, 550)
        self.user_id = user_id

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_task_tab(), "Мои задачи")
        self.tabs.addTab(self.create_project_tab(), "Создать проект")
        self.tabs.addTab(self.create_board_tab(), "Создать доску")
        self.tabs.addTab(self.create_task_form(), "Создать задачу")
        self.tabs.addTab(self.create_overview_tab(), "Мои проекты и доски")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.tasks_list = QListWidget()
        layout.addWidget(QLabel("Ваши задачи:"))
        layout.addWidget(self.tasks_list)

        self.status_box = QComboBox()
        self.status_box.addItems(["To Do", "In Progress", "Done"])
        layout.addWidget(QLabel("Новый статус:"))
        layout.addWidget(self.status_box)

        update_btn = QPushButton("Обновить статус")
        update_btn.clicked.connect(self.update_status)
        layout.addWidget(update_btn)

        tab.setLayout(layout)
        self.load_tasks()
        return tab

    def load_tasks(self):
        self.tasks_list.clear()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT T.task_id, T.title, T.status
            FROM Tasks T
            JOIN TaskAssignments TA ON T.task_id = TA.task_id
            WHERE TA.user_id = %s
        """, (self.user_id,))
        self.tasks = cursor.fetchall()
        for task in self.tasks:
            self.tasks_list.addItem(f"[{task[0]}] {task[1]} | {task[2]}")

    def update_status(self):
        selected = self.tasks_list.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу")
            return
        task_id = self.tasks[selected][0]
        new_status = self.status_box.currentText()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM Tasks WHERE task_id = %s", (task_id,))
        old_status = cursor.fetchone()[0]
        cursor.execute("UPDATE Tasks SET status = %s WHERE task_id = %s", (new_status, task_id))
        change = f'Изменен статус с "{old_status}" на "{new_status}"'
        cursor.execute("INSERT INTO TaskHistory (task_id, changed_by, change_description) VALUES (%s, %s, %s)",
                       (task_id, self.user_id, change))
        conn.commit()
        self.load_tasks()
        QMessageBox.information(self, "Успех", "Статус обновлен")

    def create_project_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Название проекта")
        layout.addWidget(self.project_name)

        self.project_desc = QLineEdit()
        self.project_desc.setPlaceholderText("Описание проекта")
        layout.addWidget(self.project_desc)

        create_btn = QPushButton("Создать проект")
        create_btn.clicked.connect(self.create_project)
        layout.addWidget(create_btn)

        tab.setLayout(layout)
        return tab

    def create_project(self):
        name = self.project_name.text()
        desc = self.project_desc.text()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Projects (project_name, description, created_by) VALUES (%s, %s, %s)",
                       (name, desc, self.user_id))
        conn.commit()
        QMessageBox.information(self, "Успех", "Проект создан")

    def create_board_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.board_name = QLineEdit()
        self.board_name.setPlaceholderText("Название доски")
        layout.addWidget(self.board_name)

        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("ID проекта")
        layout.addWidget(self.project_id_input)

        create_btn = QPushButton("Создать доску")
        create_btn.clicked.connect(self.create_board)
        layout.addWidget(create_btn)

        tab.setLayout(layout)
        return tab

    def create_board(self):
        name = self.board_name.text()
        project_id = self.project_id_input.text()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Boards (board_name, project_id, created_by) VALUES (%s, %s, %s)",
                       (name, project_id, self.user_id))
        conn.commit()
        QMessageBox.information(self, "Успех", "Доска создана")

    def create_task_form(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Название задачи")
        layout.addWidget(self.task_title)

        self.task_desc = QLineEdit()
        self.task_desc.setPlaceholderText("Описание задачи")
        layout.addWidget(self.task_desc)

        self.task_board_id = QLineEdit()
        self.task_board_id.setPlaceholderText("ID доски")
        layout.addWidget(self.task_board_id)

        self.task_due = QLineEdit()
        self.task_due.setPlaceholderText("Срок (YYYY-MM-DD)")
        layout.addWidget(self.task_due)

        self.task_priority = QComboBox()
        self.task_priority.addItems(["Low", "Medium", "High"])
        layout.addWidget(self.task_priority)

        create_btn = QPushButton("Создать задачу")
        create_btn.clicked.connect(self.create_task)
        layout.addWidget(create_btn)

        tab.setLayout(layout)
        return tab

    def create_task(self):
        title = self.task_title.text()
        desc = self.task_desc.text()
        board_id = self.task_board_id.text()
        due = self.task_due.text()
        priority = self.task_priority.currentText()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Tasks (title, description, board_id, status, priority, due_date, created_by)
            VALUES (%s, %s, %s, 'To Do', %s, %s, %s)
        """, (title, desc, board_id, priority, due, self.user_id))

        task_id = cursor.lastrowid
        cursor.execute("INSERT INTO TaskAssignments (task_id, user_id, assigned_by) VALUES (%s, %s, %s)",
                       (task_id, self.user_id, self.user_id))

        conn.commit()
        QMessageBox.information(self, "Успех", "Задача создана и назначена вам")

    def create_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.projects_text = QTextEdit()
        self.projects_text.setReadOnly(True)
        layout.addWidget(QLabel("Ваши проекты и доски:"))
        layout.addWidget(self.projects_text)

        refresh_btn = QPushButton("Обновить список")
        refresh_btn.clicked.connect(self.load_projects_and_boards)
        layout.addWidget(refresh_btn)

        self.load_projects_and_boards()
        tab.setLayout(layout)
        return tab

    def load_projects_and_boards(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT P.project_id, P.project_name, B.board_id, B.board_name
            FROM Projects P
            LEFT JOIN Boards B ON P.project_id = B.project_id
            WHERE P.created_by = %s
            ORDER BY P.project_id, B.board_id
        """, (self.user_id,))

        data = cursor.fetchall()

        output = ""
        current_project = None
        for row in data:
            project_id, project_name, board_id, board_name = row
            if current_project != project_id:
                output += f"\n📁 Проект #{project_id}: {project_name}\n"
                current_project = project_id
            if board_id:
                output += f"    📌 Доска #{board_id}: {board_name}\n"

        if not output:
            output = "У вас пока нет проектов."

        self.projects_text.setPlainText(output.strip())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
