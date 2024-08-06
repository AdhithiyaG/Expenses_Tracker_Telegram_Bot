from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import datetime
import calendar
import csv
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from expenses import Expense

BUDGET_FILE = 'budgets.json'
EXPENSES_FILE_PATH = 'expenses.csv'
TOKEN = 'Your Bot Token'

# Conversation states
GET_USER_ID, SET_INITIAL_BUDGET, MAIN_MENU, ADD_EXPENSE_NAME, ADD_EXPENSE_AMOUNT, ADD_EXPENSE_DESCRIPTION, ADD_EXPENSE_DATE, ADD_EXPENSE_CATEGORY, UPDATE_BUDGET_AMOUNT, DELETE_EXPENSE_NAME, SELECT_MONTH = range(11)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Hello Welcome back👋!\n\nEnter your user_id:")
    return GET_USER_ID

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.text
    context.user_data['user_id'] = user_id
    if not has_budget(user_id):
        await update.message.reply_text("You don't have a budget set. Enter your initial budget amount:")
        return SET_INITIAL_BUDGET
    else:
        previous_budget = get_previous_budget(user_id)
        context.user_data['budget'] = previous_budget
        await update.message.reply_text(f"Budget for user {user_id}: ₹ {previous_budget}")
        return await main_menu(update, context)

async def set_initial_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        initial_amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the initial budget amount.")
        return SET_INITIAL_BUDGET

    user_id = context.user_data['user_id']
    budgets = load_budgets()
    budgets[str(user_id)] = initial_amount
    save_budgets(budgets)
    context.user_data['budget'] = initial_amount
    await update.message.reply_text(f"Initial budget set: ₹ {initial_amount}")
    return await main_menu(update, context)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Add Expense', 'Summarize Expenses', 'Summary by Month', 'Update Budget', 'Delete Expense', 'Expense Analytics', 'Download Expenses', 'Exit']]
    await update.message.reply_text(
        "Main Menu:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == 'Add Expense':
        await update.message.reply_text("Enter the expense name:")
        return ADD_EXPENSE_NAME
    elif choice == 'Summarize Expenses':
        await summarize_expenses(update, context)
        return MAIN_MENU
    elif choice == 'Summary by Month':
        await select_month(update, context)
        return SELECT_MONTH
    elif choice == 'Update Budget':
        await update.message.reply_text("Enter the additional budget amount:")
        return UPDATE_BUDGET_AMOUNT
    elif choice == 'Delete Expense':
        await update.message.reply_text("Enter the expense name to delete:")
        return DELETE_EXPENSE_NAME
    elif choice == 'Expense Analytics':
        await expense_analytics(update, context)
        return MAIN_MENU
    elif choice == 'Download Expenses':
        await download_expenses(update, context)
        return MAIN_MENU
    elif choice == 'Exit':
        await update.message.reply_text("Exiting the app. Goodbye!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid choice. Please try again.")
        return MAIN_MENU

async def add_expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expense_name = update.message.text
    context.user_data['expense_name'] = expense_name
    await update.message.reply_text("Enter the expense amount:")
    return ADD_EXPENSE_AMOUNT

async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        expense_amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the expense amount.")
        return ADD_EXPENSE_AMOUNT

    context.user_data['expense_amount'] = expense_amount
    await update.message.reply_text("Enter the expense description:")
    return ADD_EXPENSE_DESCRIPTION

async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expense_description = update.message.text
    context.user_data['expense_description'] = expense_description
    await update.message.reply_text("Enter the expense date (YYYY-MM-DD):")
    return ADD_EXPENSE_DATE

async def add_expense_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expense_date = update.message.text
    context.user_data['expense_date'] = expense_date

    expense_categories = {
        1: "🍲Food",
        2: "🏘 Home",
        3: "👷Work",
        4: "🕺Fun",
        5: "🤷Unknown"
    }
    context.user_data['expense_categories'] = expense_categories

    reply_keyboard = [[f"{k}.{v}" for k, v in expense_categories.items()]]
    await update.message.reply_text(
        "Select a category:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ADD_EXPENSE_CATEGORY

async def add_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_category = int(update.message.text.split('.')[0])
    expense_categories = context.user_data['expense_categories']
    category = expense_categories[selected_category]

    new_expense = Expense(
        name=context.user_data['expense_name'],
        category=category,
        amount=context.user_data['expense_amount'],
        description=context.user_data['expense_description'],
        date=context.user_data['expense_date']
    )
    store_expense(new_expense, EXPENSES_FILE_PATH)
    await update.message.reply_text(f"Expense \"{new_expense.name}\" added:\n"
                                    f"Category: {new_expense.category}\n"
                                    f"Amount: ₹ {new_expense.amount}\n"
                                    f"Description: {new_expense.description}\n"
                                    f"Date: {new_expense.date}")
    return await main_menu(update, context)

async def summarize_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    budget = context.user_data['budget']
    await update.message.reply_text(f"🙋 Summarizing the expenses!")
    expenses = []
    
    # Open the CSV file and skip the header row if present
    with open(EXPENSES_FILE_PATH, "r", newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the header row
        if header != ['Category', 'Name', 'Amount', 'Description', 'Date']:
            # If the header does not match, treat it as a data row
            expenses.append(Expense(
                category=header[0],
                name=header[1],
                amount=float(header[2]),
                description=header[3],
                date=header[4]
            ))
        
        for row in reader:
            if len(row) == 5:
                try:
                    category, name, amount, description, date = row
                    line_expense = Expense(
                        name=name,
                        category=category,
                        amount=float(amount),
                        description=description,
                        date=date
                    )
                    expenses.append(line_expense)
                except ValueError:
                    print(f"Skipping invalid line: {','.join(row)}")
            else:
                print(f"Skipping invalid line: {','.join(row)}")

    amount_by_category = {}
    for expense in expenses:
        key = expense.category
        if key not in amount_by_category:
            amount_by_category[key] = []
        amount_by_category[key].append((expense.date, expense.amount))

    summary_message = "Expenses by category and date 💰:\n"
    for key, values in amount_by_category.items():
        summary_message += f"{key}:\n"
        for date, amount in values:
            summary_message += f"    {date}: ₹ {amount:.2f}\n"

    total_spent = sum(ex.amount for ex in expenses)
    summary_message += f"\n💸 You've spent ₹ {total_spent:.2f}.\n"

    remaining_budget = budget - total_spent
    summary_message += f"📌 Budget remaining: ₹ {remaining_budget:.2f}.\n"

    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    remaining_days = days_in_month - now.day
    summary_message += f"Remaining days in the current month: {remaining_days}.\n"

    daily_budget = remaining_budget / remaining_days
    summary_message += f"🎯 Roughly budget per day: ₹ {daily_budget:.2f}"

    await update.message.reply_text(summary_message)
    return main_menu(update, context)

async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [[f"{i} - {calendar.month_name[i]}" for i in range(1, 13)]]
    await update.message.reply_text(
        "Select a month to view expenses:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MONTH

async def monthly_expense_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_month = int(update.message.text.split(' - ')[0])
    current_year = datetime.datetime.now().year

    if not os.path.exists(EXPENSES_FILE_PATH):
        await update.message.reply_text("No expenses recorded yet.")
        return await main_menu(update, context)

    df = pd.read_csv(EXPENSES_FILE_PATH)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    monthly_expenses = df[(df['Date'].dt.month == selected_month) & (df['Date'].dt.year == current_year)]

    if monthly_expenses.empty:
        await update.message.reply_text(f"No expenses recorded for {calendar.month_name[selected_month]} {current_year}.")
        return await main_menu(update, context)

    summary = monthly_expenses.groupby('Category')['Amount'].sum().reset_index()
    total_expenses = monthly_expenses['Amount'].sum()

    summary_message = f"Monthly Expense Summary for {calendar.month_name[selected_month]} {current_year}:\n"
    for index, row in summary.iterrows():
        summary_message += f"Category: {row['Category']} - Amount: ₹ {row['Amount']:.2f}\n"
    summary_message += f"Total Expenses: ₹ {total_expenses:.2f}\n"

    await update.message.reply_text(summary_message)
    return await main_menu(update, context)

async def update_budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        additional_amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the additional budget amount.")
        return UPDATE_BUDGET_AMOUNT

    user_id = context.user_data['user_id']
    budgets = load_budgets()
    budgets[str(user_id)] += additional_amount
    save_budgets(budgets)
    context.user_data['budget'] = budgets[str(user_id)]
    await update.message.reply_text(f"Budget updated. New budget: ₹ {budgets[str(user_id)]}")
    return await main_menu(update, context)

async def delete_expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expense_name = update.message.text

    if not os.path.exists(EXPENSES_FILE_PATH):
        await update.message.reply_text("Expense file not found.")
        return await main_menu(update, context)

    df = pd.read_csv(EXPENSES_FILE_PATH)
    initial_count = len(df)
    df = df[df['Name'] != expense_name]

    if len(df) < initial_count:
        df.to_csv(EXPENSES_FILE_PATH, index=False)
        await update.message.reply_text(f"Expense \"{expense_name}\" deleted.")
    else:
        await update.message.reply_text(f"No expense found with the name \"{expense_name}\".")
    
    return await main_menu(update, context)

async def download_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating the CSV file of all expenses...")
    
    if not os.path.exists(EXPENSES_FILE_PATH):
        await update.message.reply_text("No expenses recorded yet.")
        return await main_menu(update, context)

    chat_id = update.message.chat_id
    with open(EXPENSES_FILE_PATH, 'rb') as file:
        await context.bot.send_document(chat_id=chat_id, document=file, filename=EXPENSES_FILE_PATH)

    return await main_menu(update, context)

async def expense_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating expense analytics...")

    if not os.path.exists(EXPENSES_FILE_PATH):
        await update.message.reply_text("No expenses recorded yet.")
        return await main_menu(update, context)

    df = pd.read_csv(EXPENSES_FILE_PATH)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    category_sum = df.groupby('Category')['Amount'].sum()
    category_sum.plot(kind='bar', title='Total Expenses by Category', ylabel='Amount (₹)', xlabel='Category', legend=False)
    plt.tight_layout()
    plt.savefig('expense_analytics.png')
    plt.close()

    chat_id = update.message.chat_id
    with open('expense_analytics.png', 'rb') as file:
        await context.bot.send_photo(chat_id=chat_id, photo=file, caption='Total Expenses by Category')

    return await main_menu(update, context)

def store_expense(expense: Expense, file_path: str):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Category', 'Name', 'Amount', 'Description', 'Date'])
        writer.writerow([expense.category, expense.name, expense.amount, expense.description, expense.date])

def load_budgets():
    if not os.path.isfile(BUDGET_FILE):
        return {}
    with open(BUDGET_FILE, 'r') as file:
        return json.load(file)

def save_budgets(budgets):
    with open(BUDGET_FILE, 'w') as file:
        json.dump(budgets, file)

def has_budget(user_id):
    budgets = load_budgets()
    return str(user_id) in budgets

def get_previous_budget(user_id):
    budgets = load_budgets()
    return budgets.get(str(user_id), 0)

def load_expenses():
    if not os.path.exists(EXPENSES_FILE_PATH):
        return pd.DataFrame()
    return pd.read_csv(EXPENSES_FILE_PATH)

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_id)],
            SET_INITIAL_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_initial_budget)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            ADD_EXPENSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_name)],
            ADD_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            ADD_EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_description)],
            ADD_EXPENSE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_date)],
            ADD_EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_category)],
            UPDATE_BUDGET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_budget_amount)],
            DELETE_EXPENSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_expense_name)],
            SELECT_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, monthly_expense_summary)]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
