import sqlite3
from datetime import datetime, timedelta, date

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


for expense in expenses:
    if expense[0] in budgets_dict.keys():
        if expense[2] > budgets_dict[expense[0]]['time']:
            print('a')
            budgets_dict[expense[0]]['amount_spent'] += int(expense[1])

print('         ')

print('Budgets reworked')
print(budgets_dict)
