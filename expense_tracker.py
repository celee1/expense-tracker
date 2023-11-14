from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QFrame
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QPushButton, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QMenuBar, QLineEdit
from PyQt5.QtGui import QBrush, QColor, QCursor
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from sqlite3 import IntegrityError, OperationalError
import sqlite3
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
import string
import sys

matplotlib.use('Qt5Agg')


class ExpenseTracker(QMainWindow):
    def __init__(self):
        super().__init__()

        # db

        self.db = sqlite3.connect(
            r'App_projects\expense_tracker\expenses.db')
        self.cursor = self.db.cursor()

        # geometry

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Expense tracker')
        self.setStyleSheet('background: #FFFFFF')

        # menu bar

        self.menubar = self.menuBar()

        self.statusBar()

        self.budgets = QAction(text='Budgets', parent=self)
        self.budgets.setShortcut('Ctrl+P')
        self.budgets.setStatusTip('Budget overview')
        self.budgets.triggered.connect(self.get_budgets)

        budget_menu = self.menubar.addMenu('&Budgets')
        budget_menu.addAction(self.budgets)

        balance = QAction(text='Balance', parent=self)
        balance.setShortcut('Ctrl+P')
        balance.setStatusTip('Balance overview')
        balance.triggered.connect(self.get_balance)

        statistics_menu = self.menubar.addMenu('&Statistics')
        statistics_menu.addAction(balance)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        exit_menu = self.menubar.addMenu('&Exit')
        exit_menu.addAction(exitAction)

        # widgets

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.show()

        self.grid = QGridLayout(self.central_widget)

        self.frame_1 = QFrame(self.central_widget)
        self.grid.addWidget(self.frame_1, 0, 0)

        self.frame_2 = QFrame(self.central_widget)
        self.grid.addWidget(self.frame_2, 1, 0)

        self.grid_1 = QGridLayout(self.frame_1)
        self.grid_2 = QGridLayout(self.frame_2)

        self.label_1 = Label('Expense tracker')
        self.grid_1.addWidget(self.label_1, 0, 1, 1, 2)

        self.label_2 = Label('Balance: ')
        self.grid_1.addWidget(self.label_2, 1, 0)

        self.adjust_button = QPushButton('CHANGE BALANCE')
        self.adjust_button.clicked.connect(self.new_balance)
        self.grid_1.addWidget(self.adjust_button, 1, 1)

        self.label_4 = Label('Account: ')
        self.grid_1.addWidget(self.label_4, 2, 0)

        self.change_acc = QPushButton(self)
        self.change_acc.setText('CHANGE ACCOUNT')
        self.change_acc.clicked.connect(self.change_account)
        self.grid_1.addWidget(self.change_acc, 2, 1)

        self.add_account_button = QPushButton('NEW RECORD')
        self.add_account_button.clicked.connect(self.add_an_expense)
        self.grid_1.addWidget(self.add_account_button, 1, 2)

        self.zapisi_button = QPushButton('RECORDS')
        self.zapisi_button.clicked.connect(self.get_records)
        self.grid_1.addWidget(self.zapisi_button, 2, 2)

        self.label_3 = Label('Expense composition')
        self.grid_2.addWidget(self.label_3, 0, 1)

        try:
            self.account = self.cursor.execute(
                'SELECT user FROM expenses ORDER BY time DESC LIMIT 1;').fetchall()[0][0]
            self.label_4.setText(self.label_4.text() + self.account)
        except IndexError:
            self.account = 'unknown'

        self.get_account_balance(self.account)

        self.button_frame = QFrame(self)
        self.grid.addWidget(self.button_frame, 3, 0)

        self.button_grid = QGridLayout(self.button_frame)

        self.month = PushButton('Last 30 days', 200, self.show_graph_time)
        self.button_grid.addWidget(self.month, 1, 0)

        self.year = PushButton('This year', 200, self.show_graph_time)
        self.button_grid.addWidget(self.year, 1, 1)

        self.entire_time = PushButton('Entire time', 200, self.show_graph_time)
        self.button_grid.addWidget(self.entire_time, 1, 2)

        self.show_graph()

    def add_an_expense(self):
        self.expense_window = NewExpense()
        self.expense_window.show()

    def clear_expenses(self):
        self.cursor.execute('DELETE FROM expenses')
        self.db.commit()

    def change_account(self):
        self.change_account_window = AccountPicker(self, initial=True)
        self.change_account_window.show()

    def get_account_balance(self, account, initial=True):
        try:
            balance = [item[0] for item in self.cursor.execute(
                f'SELECT amount FROM account WHERE name = "{account}";').fetchall()][0]
            self.label_2.setText('Balance: ' + balance + '€')
            self.cursor.execute(
                f'INSERT INTO balances VALUES ("{account}", "{self.get_time()}", "{balance}")')
            self.db.commit()
            if initial == False:
                self.label_4.setText(self.label_4.text().split(' ')[
                                     0] + ' ' + self.account)
        except IndexError:
            self.label_2.setText('no data')
            self.label_4.setText('no data')

    def get_balance(self):
        self.balance_window = BalanceWindow()
        self.balance_window.show()

    def get_budgets(self):
        self.budget_window = BudgetWindow()
        self.budget_window.show()

    def get_records(self):
        self.records_window = RecordsWindow()
        if type(self.records_window.table) == QTableWidget:
            self.records_window.show()
        else:
            self.records_window.close()

    def get_time(self):
        return datetime.now().strftime('%Y%m%d%H%M%S')

    def hide_pie(self):
        self.pie.hide()

    def new_balance(self):
        self.balance_window = NewBalance()
        self.balance_window.show()

    def show_graph(self, table_name='expenses', amount='amount', asset='category', date='Last 30 days'):

        now = datetime.now()

        self.pie = MplCanvasPie(self, width=6, height=5, dpi=100)

        if date == 'Entire time':
            query = self.cursor.execute(
                f'SELECT {asset}, SUM({amount}) FROM "{table_name}" WHERE type = "expense" AND user = "{self.account}" GROUP BY {asset}').fetchall()

        else:
            if date == 'Last 30 days':
                num_days = 30
            elif date == 'This year':
                num_days = 365

            days = (now - timedelta(days=num_days)).strftime('%Y%m%d%H%M%S')

            try:
                query = self.cursor.execute(
                    f'SELECT {asset}, SUM({amount}) FROM "{table_name}" WHERE type = "expense" AND time BETWEEN "{days}" AND "{self.get_time()}" AND user = "{self.account}" GROUP BY {asset}').fetchall()
            except OperationalError:
                query = self.cursor.execute(
                    f'SELECT {asset}, SUM({amount}) FROM "expenses" WHERE type = "expense" AND time BETWEEN "{days}" AND "{self.get_time()}" AND user = "{self.account}" GROUP BY {asset}').fetchall()

        try:
            self.pie.show_overview(amounts=[float(item[1]) for item in query], assets=[
                item[0] for item in query], table_name=table_name.upper(), table_title=sum([float(item[1]) for item in query]), time_period=date)

        except AttributeError:
            self.pie.show_overview(amounts=[float(item[1]) for item in query], assets=[
                item[0] for item in query], table_name="EXPENSES", table_title=sum([float(item[1]) for item in query]), time_period=date)

        self.grid_2.addWidget(self.pie, 2, 0, 1, 3)
        self.pie.show()

    def show_graph_time(self):
        date = self.sender().text()
        self.chart_1 = self.show_graph(date=date)


class NewBalance(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 300, 300)
        self.setWindowTitle('SET BALANCE')
        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.label = QLabel(self)
        self.label.setText('Set balance')
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.label, 0, 0, 1, 2)

        self.edit = QLineEdit(self)
        self.grid.addWidget(self.edit, 1, 0, 1, 2)

        self.insert_button = QPushButton(self)
        self.insert_button.setText('Insert')
        self.insert_button.clicked.connect(self.change_balance)
        self.grid.addWidget(self.insert_button, 2, 0)

        self.close_button = QPushButton(self)
        self.close_button.setText('Exit window')
        self.close_button.clicked.connect(self.close)
        self.grid.addWidget(self.close_button, 2, 1)

    def change_balance(self, a='11'):
        user_found = e.cursor.execute(
            f'SELECT name FROM account WHERE name = "{e.account}";').fetchall()
        if user_found != []:
            e.cursor.execute(
                f'UPDATE account SET amount = "{self.edit.text()}" WHERE name = "{e.account}";')
        else:
            e.cursor.execute(
                f'INSERT INTO account VALUES ("{e.account}", "{self.edit.text()}");')

        e.db.commit()
        e.get_account_balance(e.account)
        self.close()


class NewExpense(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 300, 300)
        self.setWindowTitle('ADD AN ENTRY')
        self.setStyleSheet('background: #FFFFFF')

        # grid + frames

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid.addWidget(self.frame_1, 0, 0)

        self.frame_2 = QFrame(self)
        self.grid.addWidget(self.frame_2, 1, 0)

        self.frame_3 = QFrame(self)
        self.grid.addWidget(self.frame_3, 2, 0)

        # frame 1

        self.grid_1 = QGridLayout(self.frame_1)

        self.close_button = QPushButton(self.frame_1)
        self.close_button.setText('Close window')
        self.close_button.clicked.connect(self.close)
        self.grid_1.addWidget(self.close_button, 0, 0)

        self.accept = QPushButton(self.frame_1)
        self.accept.setText('Enter an entry')
        self.accept.clicked.connect(self.insert_expense)
        self.grid_1.addWidget(self.accept, 0, 1)

        self.income = QPushButton(self.frame_1)
        self.income.setText('Income')
        self.income.clicked.connect(self.change_to_income)
        self.grid_1.addWidget(self.income, 1, 0)

        self.expense = QPushButton(self.frame_1)
        self.expense.setText('Expense')
        self.expense.clicked.connect(self.change_to_expense)
        self.grid_1.addWidget(self.expense, 1, 1)

        # frame 2

        self.grid_2 = QGridLayout(self.frame_2)

        self.operator = QLabel(self.frame_2)
        self.grid_2.addWidget(self.operator, 0, 0)

        self.amount = QLabel(self.frame_2)
        self.amount.setAlignment(QtCore.Qt.AlignCenter)
        self.amount.setText('')
        self.grid_2.addWidget(self.amount, 0, 1)

        # currency pick function
        self.currency = QLabel(self.frame_2)
        self.currency.setText('EUR')
        self.currency.setAlignment(QtCore.Qt.AlignCenter)
        self.grid_2.addWidget(self.currency, 0, 2)

        self.account = QPushButton(self.frame_2)
        self.account.clicked.connect(self.choose_account)
        self.account_text = 'Račun: '

        self.grid_2.addWidget(self.account, 1, 0)

        self.category = QPushButton(self.frame_2)
        self.category.clicked.connect(self.choose_category)
        self.category_text = 'Kategorija: '
        self.grid_2.addWidget(self.category, 1, 2)

        # frame 3

        self.grid_3 = QGridLayout(self.frame_3)

        self.seven = QPushButton('7')
        self.seven.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.seven, 0, 0)
        self.eight = QPushButton('8')
        self.eight.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.eight, 0, 1)
        self.nine = QPushButton('9')
        self.nine.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.nine, 0, 2)

        self.four = QPushButton('4')
        self.four.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.four, 1, 0)
        self.five = QPushButton('5')
        self.five.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.five, 1, 1)
        self.six = QPushButton('6')
        self.six.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.six, 1, 2)

        self.one = QPushButton('1')
        self.one.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.one, 2, 0)
        self.two = QPushButton('2')
        self.two.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.two, 2, 1)
        self.three = QPushButton('3')
        self.three.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.three, 2, 2)

        self.point = QPushButton('.')
        self.grid_3.addWidget(self.point, 3, 0)
        self.point.clicked.connect(self.change_amount)
        self.zero = QPushButton('0')
        self.zero.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.zero, 3, 1)
        self.back = QPushButton('<')
        self.back.clicked.connect(self.change_amount)
        self.grid_3.addWidget(self.back, 3, 2)

        self.user = e.account
        self.table_category = 'unknown'
        self.type = 'unknown'

        self.get_inital_values()

    def change_amount(self):
        current_amount = self.amount.text()
        sender = self.sender().text()
        if sender == '<':
            if len(current_amount) == 0:
                pass
            else:
                self.amount.setText(current_amount[:-1])
        elif sender == '.':
            if '.' not in current_amount:
                if len(current_amount) == 0:
                    pass
                else:
                    self.amount.setText(current_amount + '.')
        else:
            self.amount.setText(current_amount + sender)

    def change_to_income(self):
        if self.type == 'income':
            pass
        else:
            self.expense.setStyleSheet('background: #FFFFFF;')
            self.income.setStyleSheet('background: #FFFF00;')
            self.type = 'income'

    def change_to_expense(self):
        if self.type == 'expense':
            pass
        else:
            self.income.setStyleSheet('background: #FFFFFF')
            self.expense.setStyleSheet('background: #FFFF00')
            self.type = 'expense'

    def choose_account(self):
        self.account_window = AccountPicker(parent=self)
        self.account_window.show()

    def choose_category(self):
        self.category_window = CategoryPicker()
        self.category_window.show()

    def get_inital_values(self):
        try:
            self.table_category, self.type = e.cursor.execute(
                'SELECT category, type FROM expenses').fetchall()[-1]
            self.account.setText(self.account_text + self.user)
            self.category.setText(self.category_text + self.table_category)
            if self.type == 'expense':
                self.expense.setStyleSheet('background: #FFFF00;')
            else:
                self.income.setStyleSheet('background: #FFFF00;')
        except IndexError:
            self.account.setText('unknown')
            self.category.setText('unknown')

    def insert_expense(self):

        try:
            new_amount = e.cursor.execute(
                f'SELECT amount FROM account WHERE name = "{self.user}"').fetchall()
            if new_amount != []:
                new_amount = float(new_amount[0][0])
            else:
                msg = QMessageBox(QMessageBox.Warning,
                                  'User not found', f'No user named {self.user}')
                msg.exec_()
                return

            e.cursor.execute(
                f'INSERT INTO expenses VALUES ("{self.user}", "{self.table_category}", "{self.amount.text()}", "{e.get_time()}", "{self.type}")')

            if self.amount.text() == '':
                msg = QMessageBox(
                    QMessageBox.Warning, 'Invalid number', 'Number field cannot be empty')
                msg.exec_()
                return
            if self.type == 'expense':
                new_amount -= float(self.amount.text())
            elif self.type == 'income':
                new_amount += float(self.amount.text())
            else:
                msg = QMessageBox(QMessageBox.Warning, 'Type incorrect',
                                  'Type cannot be unknown, please select a valid type')
                msg.exec_()
                return

            e.cursor.execute(
                f'UPDATE account SET amount = "{new_amount}" WHERE name = "{self.user}";')

            e.db.commit()

        except AttributeError:
            msg = QMessageBox(QMessageBox.Warning, 'No accounts found',
                              'Please make an account to enter an expense')
            msg.exec_()
            return

        e.pie.hide()
        e.show_graph()
        e.get_account_balance(self.user)


class AccountPicker(QWidget):
    def __init__(self, parent, initial=False):
        super().__init__()

        self.initial = initial

        self.parent = parent

        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('CHOOSE AN ACCOUNT')
        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.new_account = QLabel(self)
        self.new_account.setText('Add a new account: ')
        self.grid.addWidget(self.new_account, 0, 0)

        self.new_account_edit = QLineEdit(self)
        self.grid.addWidget(self.new_account_edit, 0, 1)

        self.add_button = QPushButton(self)
        self.add_button.setText('ADD A NEW ACCOUNT')
        self.add_button.clicked.connect(self.add_new)
        self.grid.addWidget(self.add_button, 0, 2)

        self.attempt()

    def add_new(self):
        account = self.new_account_edit.text()
        try:
            if account != '':
                e.cursor.execute(
                    f'INSERT INTO account VALUES ("{account}", "0")')
                e.db.commit()
                self.attempt()
                self.new_account_edit.setText('')
            else:
                msg = QMessageBox(
                    QMessageBox.Warning, 'Account name blank', 'Account name cannot be empty')
                msg.exec_()
        except IntegrityError:
            msg = QMessageBox(QMessageBox.Warning, 'Account already present',
                              'Account already present in the database, cannot duplicate usernames')
            msg.exec_()

    def attempt(self):
        items = e.cursor.execute('SELECT name FROM account').fetchall()
        style_sheet = ""  # napravit stylesheet
        if items != []:
            items = [item[0] for item in items]
            for i in range(len(items)):
                new_button = QPushButton(self)
                new_button.setText(items[i])
                new_button.setStyleSheet(style_sheet)
                new_button.clicked.connect(self.get_account)
                self.grid.addWidget(new_button, i + 1, 1)
        else:
            new_label = QLabel(self)
            new_label.setText(
                'No accounts found, please make an account to proceed')
            self.grid.addWidget(new_label, 0, 0)

    def get_account(self):
        if not self.initial:
            e.expense_window.user = self.sender().text()
            e.expense_window.account.setText(
                e.expense_window.account_text + e.expense_window.user)
        if self.initial:
            e.account = self.sender().text()
            e.get_account_balance(e.account, initial=False)
        e.show_graph()
        self.close()


class CategoryPicker(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle('CHOOSE A CATEGORY')
        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.new_category = QLabel(self)
        self.new_category.setText('ADD A NEW CATEGORY: ')
        self.grid.addWidget(self.new_category, 0, 0)

        self.new_category_edit = QLineEdit(self)
        self.grid.addWidget(self.new_category_edit, 0, 1)

        self.add_button = QPushButton(self)
        self.add_button.setText('ADD A NEW CATEGORY')
        self.add_button.clicked.connect(self.add_new)
        self.grid.addWidget(self.add_button, 0, 2)

        self.attempt()

    def add_new(self):
        category = self.new_category_edit.text()
        try:
            if category != '':
                e.cursor.execute(
                    f'INSERT INTO expense_categories VALUES ("{category}")')
                e.db.commit()
                self.attempt()
                self.new_category_edit.setText('')
            else:
                msg = QMessageBox(
                    QMessageBox.Warning, 'Category name blank', 'Category name cannot be empty')
                msg.exec_()
        except IntegrityError:
            msg = QMessageBox(QMessageBox.Warning, 'Category already present',
                              'Category already present in the database, cannot duplicate category names')
            msg.exec_()

    def attempt(self):
        items = e.cursor.execute(
            'SELECT category FROM expense_categories').fetchall()
        style_sheet = ""  # napravit stylesheet
        if items != []:
            items = [item[0] for item in items]
            for i in range(len(items)):
                new_button = QPushButton(self)
                new_button.setText(items[i])
                new_button.setStyleSheet(style_sheet)
                new_button.clicked.connect(self.get_account)
                self.grid.addWidget(new_button, i + 1, 1)
        else:
            new_label = QLabel(self)
            new_label.setText(
                'No categories found, please make a category to proceed')
            self.grid.addWidget(new_label, 0, 0)

    def get_account(self):
        e.expense_window.table_category = self.sender().text()
        e.expense_window.category.setText(
            e.expense_window.category_text + e.expense_window.table_category)
        self.close()


class RecordsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Records window')
        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.table = self.show_table()
        if type(self.table) == QTableWidget:
            self.grid.addWidget(self.table, 0, 0)
        else:
            self.grid.addWidget(QLabel(self), 0, 0)

        self.set_table_width()

        try:
            max_h = sum([self.table.rowHeight(row)
                         for row in range(self.table.rowCount())]) + 40
            self.table.setMaximumHeight(max_h)
        except AttributeError:
            pass

    def get_column_names(self, table_name):
        columns = e.cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE name='{table_name}';").fetchall()[0][0]

        first_sections = columns.split(f'"{table_name}"')[
            1].split('PRIMARY KEY')[0]

        upper = string.ascii_uppercase
        other = ['', ' ', '(', ')', '\n', '\t', '"']

        almost_done = [
            item for item in first_sections if item not in upper and item not in other]

        return [item for item in ''.join(
            almost_done).split(',') if item != '']

    def set_table_width(self):
        try:
            width = self.table.verticalHeader().width()
            width += self.table.horizontalHeader().length()
            if self.table.verticalScrollBar().isVisible():
                width += self.table.verticalScrollBar().width()
            width += self.table.frameWidth() * 2
            self.table.setFixedWidth(width)
        except AttributeError:
            pass

    def show_table(self, table_name='expenses'):
        columns = self.get_column_names(table_name)

        try:
            content = e.cursor.execute(
                f'SELECT * FROM {table_name} WHERE user = "{e.account}"').fetchall()
        except OperationalError:
            msg = QMessageBox(QMessageBox.Warning,
                              'Error with columns', f'Columns: {columns}')
            msg.exec_()

        try:
            if len(content) == 0 and len(content[0]) == 0:
                msg = QMessageBox(QMessageBox.Warning,
                                  'Empty table', 'Table has no entries')
                msg.exec_()
                return None
            table = QTableWidget(len(content), len(content[0]), self)
            for i in range(len(content)):
                for j in range(len(content[0])):
                    if j == 3:
                        item = QTableWidgetItem(
                            str(pd.to_datetime(content[i][j])))
                    else:
                        item = QTableWidgetItem(content[i][j])

                    item.setForeground(QBrush(QColor("#000000")))
                    table.setItem(i, j, item)

            table.setHorizontalHeaderLabels(columns)

            return table

        except IndexError:
            msg = QMessageBox(QMessageBox.Warning, 'Table empty',
                              'Table empty, cannot show data')
            msg.exec_()


class BudgetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 700, 700)

        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.main_label = QLabel(self)
        self.grid.addWidget(self.main_label, 0, 0, 1, 3)

        self.weekly = QFrame(self)
        self.grid.addWidget(self.weekly, 1, 0)
        self.weekly_grid = QGridLayout(self.weekly)
        self.weekly_label = Label('Weekly budgets')
        self.weekly_grid.addWidget(self.weekly_label, 0, 0)

        self.monthly = QFrame(self)
        self.grid.addWidget(self.monthly, 1, 1)
        self.monthly_grid = QGridLayout(self.monthly)
        self.monthly_label = Label('Monthly budgets')
        self.monthly_label.setAlignment(QtCore.Qt.AlignCenter)
        self.monthly_grid.addWidget(self.monthly_label, 0, 0)

        self.yearly = QFrame(self)
        self.grid.addWidget(self.yearly, 1, 2)
        self.yearly_grid = QGridLayout(self.yearly)
        self.yearly_label = Label('Yearly budgets')
        self.yearly_grid.addWidget(self.yearly_label, 0, 0)

        self.new_budget = QFrame(self)
        self.grid.addWidget(self.new_budget, 2, 0, 1, 3)
        self.new_budget_grid = QGridLayout(self.new_budget)

        self.make_budget = PushButton(
            'Make a new budget', 300, self.make_a_new_budget)
        self.new_budget_grid.addWidget(self.make_budget, 0, 0)

        self.delete_budget = PushButton(
            'Delete a budget', 300, self.delete_a_budget)
        self.new_budget_grid.addWidget(self.delete_budget, 0, 1)

        self.budgets = []

        self.get_budgets()

        # dodat funkcionalnost za promijenit iznos budgeta kao i dodat novi te izbrisat

    def delete_a_budget(self):
        self.delete_a_budget_window = DeleteBudget()
        self.delete_a_budget_window.show()

    def get_budgets(self):
        budgets_raw = e.cursor.execute(
            f'SELECT category, amount, time FROM budgets WHERE account = "{e.account}"').fetchall()

        expenses = e.cursor.execute(
            f'SELECT category, amount, time FROM expenses WHERE user = "{e.account}"').fetchall()

        budgets_dict = {}

        now = datetime.now().strftime('%Y%m%d%H%M%S')

        year = int(now[:4]) - 1
        yearly = str(year) + now[4:6] + '00000000'

        month = int(now[:6]) - 1
        monthly = str(month) + '00000000'

        week = int(now[:8]) - date.today().weekday()
        weekly = str(week) + '000000'

        for budget in budgets_raw:
            budgets_dict[budget[0]] = {}
            budgets_dict[budget[0]]['amount'] = budget[1]
            budgets_dict[budget[0]]['amount_spent'] = 0

            if budget[2] == 'yearly':
                budgets_dict[budget[0]]['time'] = yearly
                budgets_dict[budget[0]]['interval'] = 'yearly'
            elif budget[2] == 'monthly':
                budgets_dict[budget[0]]['time'] = monthly
                budgets_dict[budget[0]]['interval'] = 'monthly'
            elif budget[2] == 'weekly':
                budgets_dict[budget[0]]['time'] = weekly
                budgets_dict[budget[0]]['interval'] = 'weekly'

        for expense in expenses:
            if expense[0] in budgets_dict.keys():
                if expense[2] > budgets_dict[expense[0]]['time']:
                    budgets_dict[expense[0]]['amount_spent'] += int(expense[1])

        weekly = 1
        monthly = 1
        yearly = 1

        for key in budgets_dict.keys():
            budget_frame = QFrame(self)
            grid = QGridLayout(budget_frame)
            amount = budgets_dict[key]['amount_spent']

            budget_name = Label(key)
            grid.addWidget(budget_name, 0, 0)
            amount_label = Label(str(amount) + '/' +
                                 budgets_dict[key]['amount'])
            grid.addWidget(amount_label, 1, 0)

            if amount > float(budget[1]):
                amount_label.setStyleSheet('color: red;')
            elif amount == float(budget[1]):
                amount_label.setStyleSheet('color: yellow')
            if budgets_dict[key]['interval'] == 'weekly':
                self.weekly_grid.addWidget(budget_frame, weekly, 0)
                weekly += 1
            elif budgets_dict[key]['interval'] == 'monthly':
                self.monthly_grid.addWidget(budget_frame, monthly, 0)
                monthly += 1
            else:
                self.yearly_grid.addWidget(budget_frame, yearly, 0)
                yearly += 1

    def hide_budgets(self):
        [[item.hide() for item in time.children() if type(item) == QFrame]
         for time in [self.weekly, self.monthly, self.yearly]]

    def make_a_new_budget(self):
        self.new_budget_window = NewBudget()
        self.new_budget_window.show()


class BalanceWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 700, 700)
        self.setWindowTitle('Balance overview')
        self.setStyleSheet('background: #FFFFFF')

        self.balances = self.calc_balance()

        self.canvas = MplCanvas()
        self.canvas.axes.plot(self.balances[0], self.balances[1])

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid_1 = QGridLayout(self.frame_1)

        self.grid_1.addWidget(self.canvas, 1, 0)

        self.frame_2 = QFrame(self)
        self.grid.addWidget(self.frame_2, )
        self.grid_2 = QGridLayout(self.frame_2)

        self.button_1 = PushButton('1 month', 300, self.make_graph)
        self.button_2 = PushButton('6 months', 300, self.make_graph)
        self.button_3 = PushButton('1 year', 300, self.make_graph)
        self.button_4 = PushButton('Entire time', 300, self.make_graph)

        self.grid_2.addWidget(self.button_1, 0, 0)
        self.grid_2.addWidget(self.button_2, 0, 1)
        self.grid_2.addWidget(self.button_3, 0, 2)
        self.grid_2.addWidget(self.button_4, 0, 3)

    def calc_balance(self):
        data = e.cursor.execute(
            f'SELECT date, amount FROM balances WHERE user = "{e.account}"').fetchall()

        dates = [item[0] for item in data]
        balances = [item[1] for item in data]

        return dates, balances

    def entire_time(self):

        self.df = pd.DataFrame(
            {'timestamp': self.balances[0], 'balance': self.balances[1]})

        self.canvas = MplCanvas(self)
        self.canvas.axes.plot(self.df.timestamp, self.df.balance)
        self.grid.addWidget(self.canvas, 1, 0)
        self.canvas.show()

    def make_graph(self):

        self.df = pd.DataFrame(
            {'timestamp': self.balances[0], 'balance': self.balances[1]})

        try:
            text = self.sender().text()

            now = datetime.now()

            if text == '1 year':
                delta = now-timedelta(days=365)
            elif text == '6 months':
                delta = now-timedelta(weeks=26)
            elif text == '1 month':
                delta = now-timedelta(days=30)

            if text != 'Entire time':
                self.df = self.df[self.df["timestamp"]
                                  > delta.strftime("%Y%m%d%H%M%S")]
            else:
                pass

        except (AttributeError, ValueError):
            pass

        self.canvas = MplCanvas(self)
        self.canvas.axes.plot(self.df.timestamp, self.df.balance)
        self.grid.addWidget(self.canvas, 1, 0)
        self.canvas.show()


class NewBudget(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 700, 700)

        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.frame_1.setMaximumHeight(100)
        self.grid_1 = QGridLayout(self.frame_1)
        self.grid.addWidget(self.frame_1, 0, 0, 1, 2)

        self.close_button = PushButton('Close window', 200, self.close)
        self.grid_1.addWidget(self.close_button, 0, 0)

        self.save_button = PushButton('Save budget', 200, self.save_budget)
        self.grid_1.addWidget(self.save_button, 0, 1)

        self.name = Label('Category')
        self.name.setFocus()
        self.grid.addWidget(self.name, 1, 0)

        self.category_entry = LineEdit()
        self.grid.addWidget(self.category_entry, 1, 1)

        self.grid.addWidget(Label('Amount'), 2, 0)

        self.amount_entry = LineEdit()
        self.grid.addWidget(self.amount_entry, 2, 1)

        self.grid.addWidget(Label('Time period'), 3, 0)

        self.period_entry = LineEdit()
        self.grid.addWidget(self.period_entry, 3, 1)

        self.grid.addWidget(Label('Account'), 5, 0)

        self.account_entry = LineEdit()
        self.account_entry.setText(e.account)
        self.grid.addWidget(self.account_entry, 5, 1)

    def save_budget(self):
        data = [self.category_entry.text(), self.period_entry.text(
        ), self.account_entry.text(), self.amount_entry.text()]

        budgets = [name[0] for name in e.cursor.execute(f'SELECT name FROM budgets'
                                                        ).fetchall()]
        if data[0] in budgets:
            msg = QMessageBox(QMessageBox.Warning, 'Budget already present',
                              'Budget with this name already exists in the database')
            msg.exec_()
            return

        if '' in data:
            msg = QMessageBox(QMessageBox.Warning, 'Empty entries',
                              'Please fill out all the entries')
            msg.exec_()
            return

        if data[1].lower() not in ['weekly', 'monthly', 'yearly']:
            msg = QMessageBox(QMessageBox.Warning, 'Invalid timeframe',
                              'Please choose either beetwen a weekly, a monthly or a yearly period')
            msg.exec_()
            return

        accounts = [account[0] for account in e.cursor.execute(
            'SELECT name FROM account;').fetchall()]

        if data[2] not in accounts:
            msg = QMessageBox(
                QMessageBox.Warning, 'Account unknown', 'Please select a valid account')
            msg.exec_()
            return

        e.cursor.execute(
            f'INSERT INTO budgets VALUES ("{data[0]}", "{data[3]}", "{data[2]}", "{data[1]}")')
        e.db.commit()

        e.budget_window.get_budgets()


class DeleteBudget(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 400, 200)

        self.setStyleSheet('background: #FFFFFF')

        self.grid = QGridLayout(self)

        self.label = Label('Budget name: ')
        self.grid.addWidget(self.label, 0, 0)
        self.edit = LineEdit()
        self.grid.addWidget(self.edit, 0, 1)
        self.button = QPushButton()
        self.button.setText('Delete the budget')
        self.button.clicked.connect(self.delete_budget)
        self.button.setMaximumWidth(200)
        self.grid.addWidget(self.button, 0, 2)

        self.frame = QFrame()
        self.frame_grid = QGridLayout(self.frame)
        self.grid.addWidget(self.frame, 1, 0, 1, 3)

    def delete_budget(self):
        name = self.edit.text()
        e.cursor.execute(f'DELETE FROM budgets WHERE name = "{name}";')
        e.db.commit()
        label = Label('Budget successfuly deleted')
        self.frame_grid.addWidget(label, 0, 0)

        e.budget_window.hide_budgets()
        e.budget_window.get_budgets()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MplCanvasPie(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvasPie, self).__init__(fig)

    def show_overview(self, amounts, assets, table_name='overview', table_title='overview', time_period='Last 30 days'):
        def func(pct, allvals):
            absolute = int(np.round(pct/100.*np.sum(allvals)))
            return "{:.1f}%\n({:d} €)".format(pct, absolute)

        wedges, texts, autotexts = self.axes.pie(amounts, autopct=lambda pct: func(pct, amounts),
                                                 textprops=dict(color="w"))

        self.axes.legend(wedges, assets,
                         title='Kategorije troškova',
                         loc="lower right",
                         bbox_to_anchor=(0, 0, 0, 0))

        plt.setp(autotexts, size=8, weight="bold")

        self.axes.set_title(f'{time_period}: {table_title} €')


class Label(QLabel):
    def __init__(self, text, width=300):
        super().__init__()
        self.setText(text)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMaximumWidth(width)


class LineEdit(QLineEdit):
    def __init__(self, width=300):
        super().__init__()
        self.setMaximumWidth(width)


class PushButton(QPushButton):
    def __init__(self, text, width=0, action=0):
        super().__init__()
        self.stylesheet = ["*{border: 4px solid '#000000';", "border-radius: 45px;",
                           "font-size: 25px;", "color: '#000000';", "padding: 30px;}", "*:hover{background: '#9604f5';}"]
        self.setStyleSheet(''.join(self.stylesheet))
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.setText(text)

        if width:
            self.setMaximumWidth(width)
        if action:
            self.clicked.connect(action)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    e = ExpenseTracker()
    e.show()
    app.exec()
