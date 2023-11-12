import sqlite3
from datetime import datetime, date

db = sqlite3.connect(
    r'App_projects\expense_tracker\expenses.db')
cursor = db.cursor()
account = 'cele'

budgets_raw = cursor.execute(
    f'SELECT category, amount, time FROM budgets WHERE account = "{account}"').fetchall()

print('### Raw budgets ###')
print(budgets_raw)
print('    ')

expenses = cursor.execute(
    f'SELECT category, amount, time FROM expenses WHERE user = "{account}"').fetchall()

print('### expenses ###')
print(expenses)
print('    ')

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
    elif budget[2] == 'monthly':
        budgets_dict[budget[0]]['time'] = monthly
    elif budget[2] == 'weekly':
        budgets_dict[budget[0]]['time'] = weekly

print('### budgets_dict ###')
print(budgets_dict)
print('   ')

for expense in expenses:
    if expense[0] in budgets_dict.keys():
        if expense[2] > budgets_dict[expense[0]]['time']:
            budgets_dict[expense[0]]['amount_spent'] += int(expense[1])

print('Budgets reworked')
print(budgets_dict)
