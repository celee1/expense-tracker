import sqlite3
from datetime import datetime, timedelta

db = sqlite3.connect(
    r'App_projects\expense_tracker\expenses.db')
cursor = db.cursor()
account = 'cele'

budgets_raw = cursor.execute(
    f'SELECT category, amount, time FROM budgets WHERE account = "{account}"').fetchall()

print('### budgets ###')
print(budgets_raw)

expenses = cursor.execute(
    f'SELECT category, amount, time FROM expenses WHERE user = "{account}" GROUP BY category;').fetchall()

print('### expenses ###')
print(expenses)

expense_dict = {}

budgets_dict = {}

for budget in budgets_raw:
    budgets_dict[budget[0]] = {}
    budgets_dict[budget[0]]['amount'] = budget[1]
    budgets_dict[budget[0]]['period'] = budget[2]
    budgets_dict[budget[0]]['amount_spent'] = 0

print('### budgets_dict ###')
print(budgets_dict)
