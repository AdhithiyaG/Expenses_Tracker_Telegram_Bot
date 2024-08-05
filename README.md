# Expense Tracker Bot

## Overview

Expense Tracker Bot is a Telegram bot designed to help users manage and track their expenses efficiently. This bot allows users to set budgets, add expenses, view summaries, generate analytics, and download expense records. With a user-friendly interface and robust functionality, it is an ideal tool for personal finance management.

## Features

- **User Budget Management**: Set and update initial budgets for individual users.
- **Expense Tracking**: Add and categorize expenses with details such as amount, description, date, and category.
- **Expense Summary**: View summaries of expenses by category and date, along with budget remaining.
- **Monthly Summary**: Get detailed summaries of expenses for a selected month.
- **Expense Analytics**: Generate and view graphical representations of expense data.
- **Download Expenses**: Download all recorded expenses as a CSV file for offline analysis.
- **Delete Expenses**: Delete specific expenses by name.

## Installation

To set up and run the Expense Tracker Bot, follow these steps:

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/yourusername/Expense_Tracker_Bot.git
    cd Expense_Tracker_Bot
    ```

2. **Install Dependencies**:
    ```sh
    pip install python-telegram-bot pandas matplotlib
    ```

3. **Set Up Your Bot Token**:
    Replace the placeholder token in `Telegram_bot.py` with your actual Telegram bot token.

    ```python
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
    ```

4. **Run the Bot**:
    ```sh
    python Telegram_bot.py
    ```

## Usage

1. **Start the Bot**: Open Telegram, search for your bot, and start a conversation with it.
2. **Set User ID**: The bot will prompt you to enter your user ID.
3. **Set Initial Budget**: If you don't have a budget set, the bot will prompt you to enter an initial budget amount.
4. **Main Menu**: Use the main menu to navigate through the various functionalities like adding expenses, summarizing expenses, viewing monthly summaries, updating the budget, deleting expenses, and more.

## File Structure

- **Telegram_bot.py**: Main script containing the bot's logic and conversation handlers.
- **expenses.py**: Contains the `Expense` class definition.
- **budgets.json**: Stores user budget data.
- **expenses.csv**: Stores recorded expenses.
- **expense_analytics.png**: Generated expense analytics graph.

## Contributions

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License.
