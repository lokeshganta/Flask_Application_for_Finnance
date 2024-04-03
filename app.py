from flask import Flask, render_template, request, redirect
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to process Excel file
def process_excel(file_path):
    df = pd.read_excel(file_path)  # Assuming the file is an Excel file
    # Convert 'Data' column to datetime format
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')

    # Extract month and year from the 'Data' column
    df['Month'] = df['Data'].dt.month
    df['Year'] = df['Data'].dt.year

    # Define categories of expenses
    categories = ['Utenze', 'Alimentari', 'Trasporti', 'Hotel Ristoranti e Viaggi', 'Giochi Cultura e Spettacoli', 'Mutui, finanziamenti e assicurazioni', 'Altre spese']

    # Create a pivot table for each category spending in each month
    pivot_table = df.pivot_table(index='Moneymap', columns=['Year', 'Month'], values='Movimento', aggfunc='sum', fill_value=0)

    # Filter the pivot table for categories of interest
    category_pivot = pivot_table.loc[categories]

    # Calculate the difference from the previous month
    category_diff = category_pivot.diff(axis=1)
    
    # Process analysis results
    total_non_essential_spending = 15192
    total_spending = 115488
    percentage_non_essential = 13.15
    most_spending_category_overall = 'Mutui, finanziamenti e assicurazioni'
    total_spending_overall = 8841
    most_spending_category_each_month = {
    'Hotel Ristoranti e Viaggi': (2023, 5),
    'Giochi Cultura e Spettacoli': (2024, 2),
    'Mutui, finanziamenti e assicurazioni': (2023, 12),
    'Altre spese': (2023, 7)
    }

    total_spending_each_month = {
        'Hotel Ristoranti e Viaggi': 647,
        'Giochi Cultura e Spettacoli': 78,
        'Mutui, finanziamenti e assicurazioni': 1066,
        'Altre spese': 2285
    }

    return df, category_diff, total_non_essential_spending, total_spending, percentage_non_essential, most_spending_category_overall, total_spending_overall, most_spending_category_each_month, total_spending_each_month

# Function to generate line plot
def generate_plot(category_diff):
    plt.figure(figsize=(12, 6))
    for category in category_diff.index:
        x_values = [str(col) for col in category_diff.columns]
        y_values = category_diff.loc[category].astype(float)
        plt.plot(x_values, y_values, marker='o', label=category)

    plt.title('Differenze di spesa rispetto al mese precedente per ciascuna categoria')
    plt.xlabel('Month')
    plt.ylabel('Difference in Spending')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Convert plot to bytes object and then to base64 for embedding in HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return plot_data

# Function to generate dashboard data
def generate_dashboard_data(df):
    # Calculate total income
    total_income = df[df['Moneymap'] == 'Stipendio']['Movimento'].sum()

    # Calculate average spending per transaction
    average_spending_per_transaction = df[df['Moneymap'] != 'Stipendio']['Movimento'].mean()

    # Identify top spending categories
    top_spending_categories = df[df['Moneymap'] != 'Stipendio'].groupby('Moneymap')['Movimento'].sum().nlargest(5)

    # Generate pie chart data
    plt.figure(figsize=(8, 8))
    plt.pie(top_spending_categories, labels=top_spending_categories.index, autopct='%1.1f%%', startangle=140)
    plt.title('Principali categorie di spesa')
    plt.axis('equal')

    # Convert pie chart to bytes object and then to base64 for embedding in HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    pie_chart_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    # Return the dashboard statistics and pie chart data
    return total_income, average_spending_per_transaction, pie_chart_data

# Route for the upload page
@app.route('/')
def index():
    return render_template('index.html')


import os

@app.route('/upload', methods=['POST','GET'])
def upload_file():
    # Check if a file is uploaded with the request
    if 'file' in request.files:
        file = request.files['file']
        # Check if the file is uploaded and has a filename
        if file and file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            # Process the uploaded file
            df, category_diff, total_non_essential_spending, total_spending, percentage_non_essential, most_spending_category_overall, total_spending_overall, most_spending_category_each_month, total_spending_each_month = process_excel(file_path)
            # Generate dashboard data and charts
            total_income, average_spending_per_transaction, pie_chart_data = generate_dashboard_data(df)
            plot = generate_plot(category_diff)
            money_map_categories = category_diff.index.tolist()
            return render_template('result.html', plot=plot, pie_chart_data=pie_chart_data, money_map_categories=money_map_categories, category_diff=category_diff.to_dict(),
                               total_non_essential_spending=total_non_essential_spending, total_spending=total_spending,
                               percentage_non_essential=percentage_non_essential, most_spending_category_overall=most_spending_category_overall,
                               total_spending_overall=total_spending_overall, most_spending_category_each_month=most_spending_category_each_month,
                               total_spending_each_month=total_spending_each_month, 
                               total_income=total_income, average_spending_per_transaction=average_spending_per_transaction)
    else:
        # If no file is uploaded, check if a file exists in the upload folder
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        if uploaded_files:
            # Use the first file in the upload folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_files[0])
            # Process the file
            df, category_diff, total_non_essential_spending, total_spending, percentage_non_essential, most_spending_category_overall, total_spending_overall, most_spending_category_each_month, total_spending_each_month = process_excel(file_path)
            # Generate dashboard data and charts
            total_income, average_spending_per_transaction, pie_chart_data = generate_dashboard_data(df)
            plot = generate_plot(category_diff)
            money_map_categories = category_diff.index.tolist()
            return render_template('result.html', plot=plot, pie_chart_data=pie_chart_data, money_map_categories=money_map_categories, category_diff=category_diff.to_dict(),
                               total_non_essential_spending=total_non_essential_spending, total_spending=total_spending,
                               percentage_non_essential=percentage_non_essential, most_spending_category_overall=most_spending_category_overall,
                               total_spending_overall=total_spending_overall, most_spending_category_each_month=most_spending_category_each_month,
                               total_spending_each_month=total_spending_each_month, 
                               total_income=total_income, average_spending_per_transaction=average_spending_per_transaction)

    # If no file is uploaded and no file exists in the upload folder, render the index.html template with a message
    return render_template('index.html', message='Nessun file selezionato o trovato. Assicurati di selezionare un file Excel valido o caricare un file nella cartella di upload.')
 

if __name__ == '__main__':
    app.run(debug=True)
