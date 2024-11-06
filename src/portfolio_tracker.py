import yfinance as yf
import pandas as pd
import os
from tabulate import tabulate

# Define a class for stock entry
class StockEntry:
    def __init__(self, name, purchase_date, purchase_price, quantity):
        self.name = name
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.quantity = quantity
        self.sell_price = None
        self.sell_date = None

    def set_sell_data(self, sell_price, sell_date):
        self.sell_price = sell_price
        self.sell_date = sell_date

# Function to get the current stock price
def get_current_price(stock_name):
    stock = yf.Ticker(stock_name)
    data = stock.history(period="1d")
    return data['Close'].iloc[0] if not data.empty else None

# Function to calculate insights
def calculate_insights(stocks):
    total_investment = 0
    total_current_value = 0
    total_quantity_all_stocks = 0  # To track total quantity across all stocks
    report_data = []
    
    # Group stocks by name
    stock_groups = {}
    
    for stock in stocks:
        if stock.name not in stock_groups:
            stock_groups[stock.name] = []
        stock_groups[stock.name].append(stock)

    print("Stock Portfolio Insights:")
    print("=================================")

    # Prepare data for tabulation
    table_data = []

    for stock_name, stock_entries in stock_groups.items():
        total_purchase_price = 0
        total_quantity = 0
        
        # Calculate total purchase price and quantity for averaging
        for stock in stock_entries:
            total_purchase_price += stock.purchase_price * stock.quantity
            total_quantity += stock.quantity
        
        average_purchase_price = total_purchase_price / total_quantity if total_quantity > 0 else 0
        current_price = get_current_price(stock_name)
        
        if current_price is not None:
            current_value = current_price * total_quantity
            total_investment += total_purchase_price
            total_current_value += current_value
            total_quantity_all_stocks += total_quantity  # Add to total quantity across all stocks
            
            gain_loss = current_value - total_purchase_price
            gain_loss_percent = (gain_loss / total_purchase_price) * 100 if total_purchase_price != 0 else 0
            
            # Determine the color based on price comparison (logic switched)
            if average_purchase_price < current_price:
                price_color = "\033[32m"  # Green for average price below current price (gain)
            elif average_purchase_price > current_price:
                price_color = "\033[31m"  # Red for average price above current price (loss)
            else:
                price_color = "\033[0m"    # Default color for equal prices

            report_data.append({
                'Stock': stock_name,
                'Average Purchase Price (INR)': average_purchase_price,
                'Current Price (INR)': current_price,
                'Gain/Loss (INR)': gain_loss,
                'Gain/Loss (%)': gain_loss_percent,
                'Total Quantity': total_quantity  # Include total quantity in report data
            })

            # Add to table data with formatted price color
            table_data.append([
                stock_name,
                total_quantity,
                f"₹{average_purchase_price:.2f}",
                f"{price_color}₹{current_price:.2f}\033[0m",  # Color-coded current price
                f"₹{gain_loss:.2f}",
                gain_loss_percent  # Keep this as a float for sorting
            ])
        else:
            print(f"Could not retrieve current price for {stock_name}.")
    
    # Add summary row to the table
    total_gain_loss = total_current_value - total_investment
    total_gain_loss_percent = (total_gain_loss / total_investment) * 100 if total_investment != 0 else 0
    
    table_data.append([
        "Total",
        total_quantity_all_stocks,
        f"₹{total_investment:.2f}",
        f"₹{total_current_value:.2f}",
        f"₹{total_gain_loss:.2f}",
        total_gain_loss_percent  # Summary gain/loss percent for portfolio
    ])

    # Sort table_data by Gain/Loss (%) in descending order
    table_data = sorted(table_data[:-1], key=lambda x: x[5], reverse=True) + [table_data[-1]]

    # Format Gain/Loss (%) column as a percentage string for display
    formatted_table_data = [
        [row[0], row[1], row[2], row[3], row[4], f"{row[5]:.2f}%"] for row in table_data
    ]

    # Print the tabulated data with Total row
    print(tabulate(formatted_table_data, headers=["Stock", "Qty", "Avg Purchase Price", "Current Price", "Gain/Loss", "Gain/Loss"], tablefmt="grid"))
    
    return report_data, total_investment, total_current_value

# Function to save stock data to a CSV file
def save_stock_data(stocks):
    data = []
    for stock in stocks:
        data.append({
            'Stock': stock.name,
            'Purchase_Date': stock.purchase_date,
            'Purchase_Price': stock.purchase_price,
            'Quantity': stock.quantity,
            'Sell_Price': stock.sell_price,
            'Sell_Date': stock.sell_date
        })
    
    df = pd.DataFrame(data)
    df.to_csv('stock_portfolio.csv', index=False)
    print("Stock data saved to 'stock_portfolio.csv'.")

# Function to generate an Excel report
def generate_excel_report(report_data, total_investment, total_current_value):
    df = pd.DataFrame(report_data)
    summary_data = {
        'Stock': 'Total',
        'Purchase Price (INR)': total_investment,
        'Current Price (INR)': total_current_value,
        'Gain/Loss (INR)': total_current_value - total_investment,
        'Gain/Loss (%)': ((total_current_value - total_investment) / total_investment) * 100 if total_investment != 0 else 0
    }
    df = pd.concat([df, pd.DataFrame([summary_data])], ignore_index=True)
    
    df.to_excel('stock_portfolio_report.xlsx', index=False)
    print("Excel report generated: 'stock_portfolio_report.xlsx'.")

# Function to edit existing stock data
def edit_existing_stock(stocks):
    edit_choice = input("Do you want to edit any existing stock? (yes/no): ").lower()
    if edit_choice == 'no':
        return stocks

    # Display available stocks
    stock_names = list({stock.name for stock in stocks})
    print("\nAvailable Stocks:")
    for idx, name in enumerate(stock_names, 1):
        print(f"{idx}. {name}")
    
    stock_index = int(input("Select the stock number to edit: ")) - 1
    selected_stock_name = stock_names[stock_index]

    # Filter stocks with the selected name and display purchase dates
    selected_stocks = [stock for stock in stocks if stock.name == selected_stock_name]
    print(f"\nAvailable purchase dates for {selected_stock_name}:")
    for idx, stock in enumerate(selected_stocks, 1):
        print(f"{idx}. {stock.purchase_date} (Quantity: {stock.quantity}, Purchase Price: ₹{stock.purchase_price})")
    
    date_index = int(input("Select the purchase date number to edit: ")) - 1
    stock_to_edit = selected_stocks[date_index]

    # Edit selected stock details
    stock_to_edit.purchase_date = input(f"Enter the new purchase date (YYYY-MM-DD) [{stock_to_edit.purchase_date}]: ") or stock_to_edit.purchase_date
    stock_to_edit.purchase_price = float(input(f"Enter the new purchase price per share (INR) [{stock_to_edit.purchase_price}]: ") or stock_to_edit.purchase_price)
    stock_to_edit.quantity = int(input(f"Enter the new quantity [{stock_to_edit.quantity}]: ") or stock_to_edit.quantity)

    # Optional sell data update
    sell_input = input("Do you want to update the sell data? (yes/no): ").lower()
    if sell_input == 'yes':
        stock_to_edit.sell_price = float(input(f"Enter the new sell price per share (INR) [{stock_to_edit.sell_price}]: ") or stock_to_edit.sell_price)
        stock_to_edit.sell_date = input(f"Enter the new sell date (YYYY-MM-DD) [{stock_to_edit.sell_date}]: ") or stock_to_edit.sell_date

    return stocks

# Function to delete a stock entry
def delete_stock_entry(stocks):
    delete_choice = input("Do you want to delete any stock data? (yes/no): ").lower()
    if delete_choice == 'no':
        return stocks

    # Display available stocks
    stock_names = list({stock.name for stock in stocks})
    print("\nAvailable Stocks:")
    for idx, name in enumerate(stock_names, 1):
        print(f"{idx}. {name}")
    
    stock_index = int(input("Select the stock number to delete: ")) - 1
    selected_stock_name = stock_names[stock_index]

    # Filter stocks with the selected name and display purchase dates
    selected_stocks = [stock for stock in stocks if stock.name == selected_stock_name]
    print(f"\nAvailable purchase dates for {selected_stock_name}:")
    for idx, stock in enumerate(selected_stocks, 1):
        print(f"{idx}. {stock.purchase_date} (Quantity: {stock.quantity}, Purchase Price: ₹{stock.purchase_price})")
    
    date_index = int(input("Select the purchase date number to delete: ")) - 1
    stock_to_delete = selected_stocks[date_index]

    # Confirm deletion
    confirm_delete = input(f"Are you sure you want to delete {selected_stock_name} purchased on {stock_to_delete.purchase_date}? (yes/no): ").lower()
    if confirm_delete == 'yes':
        stocks.remove(stock_to_delete)
        save_stock_data(stocks)  # Save updated stock list after deletion
        print(f"Deleted {selected_stock_name} purchased on {stock_to_delete.purchase_date}.")
    else:
        print("Deletion cancelled.")

    return stocks

# Main function
def main():
    print("Welcome to the Stock Portfolio Tracker!")
    # Load stock data from CSV or initialize an empty list
    stocks = get_stock_data()
    stocks = edit_existing_stock(stocks)  # Call to edit function after loading data
    stocks = delete_stock_entry(stocks)   # Call to delete function after edit
    report_data, total_investment, total_current_value = calculate_insights(stocks)
    generate_excel_report(report_data, total_investment, total_current_value)

# Input function to get stock data from the user
def get_stock_data():
    stocks = []

    # Check if the file exists and is not empty
    if os.path.exists('stock_portfolio.csv') and os.path.getsize('stock_portfolio.csv') > 0:
        try:
            existing_data = pd.read_csv('stock_portfolio.csv')
            for _, row in existing_data.iterrows():
                stock = StockEntry(row['Stock'], row['Purchase_Date'], row['Purchase_Price'], row['Quantity'])
                if pd.notna(row['Sell_Price']):
                    stock.set_sell_data(row['Sell_Price'], row['Sell_Date'])
                stocks.append(stock)
        except Exception as e:
            print(f"Error reading existing data: {e}. Starting fresh.")
    
    if not stocks:
        print("The stock data file is empty or does not exist. Starting fresh.")

    while True:
        name = input("Enter the stock symbol (e.g., RELIANCE.NS) or 'done' to finish: ")
        if name.lower() == 'done':
            break
        purchase_date = input("Enter the purchase date (YYYY-MM-DD): ")
        purchase_price = float(input("Enter the purchase price per share (INR): "))
        quantity = int(input("Enter the quantity purchased: "))
        
        stock = StockEntry(name, purchase_date, purchase_price, quantity)
        
        sell_input = input("Do you have sell data for this stock? (yes/no): ").lower()
        if sell_input == 'yes':
            sell_price = float(input("Enter the selling price per share (INR): "))
            sell_date = input("Enter the selling date (YYYY-MM-DD): ")
            stock.set_sell_data(sell_price, sell_date)
        
        stocks.append(stock)

    # Save data to CSV
    save_stock_data(stocks)

    return stocks

if __name__ == "__main__":
    main()

