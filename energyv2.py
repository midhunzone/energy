import streamlit as st
import pandas as pd
import csv
import os
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

# Initialize session state for common power ratings
if 'common_ratings' not in st.session_state:
    st.session_state['common_ratings'] = {
        "Ceiling Fan": 70,
        "LED Light": 10,
        "Air Conditioner": 1500,
        "Water Pump": 1000,
        "Refrigerator": 150,
        "Television": 100,
        "Washing Machine": 500
    }

# Function to get user input
def get_user_input():
    equipment_list = list(st.session_state['common_ratings'].keys())
    equipment = st.selectbox("Select the name of the equipment:", equipment_list + ["Other"])
    
    if equipment == "Other":
        equipment = st.text_input("Enter the name of the equipment:")
        rating_watts = st.number_input("Enter the power rating of the equipment in watts:", min_value=0, step=1)
    else:
        rating_watts = st.number_input("Enter the power rating of the equipment in watts:", min_value=0, step=1, value=st.session_state['common_ratings'][equipment])
        
    daily_usage = st.number_input("Enter the daily average usage in hours:", min_value=0.0, step=0.1)
    count = st.number_input("Enter the number of such equipment:", min_value=1, step=1)
    rating_kw = rating_watts / 1000  # Convert watts to kilowatts
    return equipment, rating_watts, rating_kw, daily_usage, count

# Function to calculate consumption
def calculate_consumption(rating_kw, daily_usage, count):
    daily_consumption = rating_kw * daily_usage * count
    bi_monthly_consumption = daily_consumption * 30  # Assuming 30 days for a bi-monthly period
    return daily_consumption, bi_monthly_consumption

# Function to calculate bill
def calculate_bill(consumption, rate_per_kwh):
    return round(consumption * rate_per_kwh, 2)

# Function to save data to CSV
def save_to_csv(data, filename='electricity_consumption.csv'):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Equipment', 'Rating (W)', 'Rating (kW)', 'Daily Usage (hours)', 'Count', 'Daily Consumption (kWh)', 'Bi-monthly Consumption (kWh)', 'Estimated Bill'])
        writer.writerow(data)

# Function to create an Excel file
def create_excel(data, pie_chart):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, index=False, sheet_name='Electricity Consumption')
    
    # Insert pie chart into Excel
    workbook = writer.book
    worksheet = writer.sheets['Electricity Consumption']
    
    image_data = BytesIO()
    pie_chart.savefig(image_data, format='png')
    image_data.seek(0)
    worksheet.insert_image('J2', 'pie_chart.png', {'image_data': image_data})
    
    writer.close()
    output.seek(0)
    return output

# Streamlit app
def main():
    st.title("Electricity Consumption Estimator")

    rate_per_kwh = st.number_input("Enter the power rate per kWh:", min_value=0.0, step=0.01, format="%.2f")
    currency = st.selectbox("Select the currency for the power rate:", ["INR", "USD", "EUR", "GBP"])

    if 'data' not in st.session_state:
        st.session_state['data'] = []

    # Display and edit common power ratings
    st.write("Common Power Ratings (W):")
    common_ratings_df = pd.DataFrame(list(st.session_state['common_ratings'].items()), columns=["Equipment", "Power Rating (W)"])
    edited_common_ratings = st.data_editor(common_ratings_df)
    st.session_state['common_ratings'] = dict(zip(edited_common_ratings['Equipment'], edited_common_ratings['Power Rating (W)']))

    equipment, rating_watts, rating_kw, daily_usage, count = get_user_input()

    if st.button("Add Equipment"):
        if equipment and rating_watts > 0 and daily_usage > 0 and count > 0:
            daily_consumption, bi_monthly_consumption = calculate_consumption(rating_kw, daily_usage, count)
            estimated_bill = calculate_bill(bi_monthly_consumption, rate_per_kwh)

            st.write(f"Daily Consumption for {count} {equipment}(s): {daily_consumption:.2f} kWh")
            st.write(f"Bi-monthly Consumption for {count} {equipment}(s): {bi_monthly_consumption:.2f} kWh")
            st.write(f"Estimated Bi-monthly Bill: {estimated_bill:.2f} {currency}")

            save_to_csv([equipment, rating_watts, rating_kw, daily_usage, count, daily_consumption, bi_monthly_consumption, f"{estimated_bill} {currency}"])

            st.session_state['data'].append([equipment, rating_watts, rating_kw, daily_usage, count, daily_consumption, bi_monthly_consumption, f"{estimated_bill} {currency}"])

            # Display the data in a table
            st.write("Current Equipment Data:")
            df = pd.DataFrame(st.session_state['data'], columns=['Equipment', 'Rating (W)', 'Rating (kW)', 'Daily Usage (hours)', 'Count', 'Daily Consumption (kWh)', 'Bi-monthly Consumption (kWh)', 'Estimated Bill'])
            st.table(df)
        else:
            st.write("Please enter valid values for all fields.")

    if st.button("Calculate Total Bill and Show Pie Chart"):
        if st.session_state['data']:
            total_consumption = sum(item[6] for item in st.session_state['data'])
            total_bill = calculate_bill(total_consumption, rate_per_kwh)
            st.write(f"Total Bi-monthly Consumption: {total_consumption:.2f} kWh")
            st.write(f"Total Estimated Bi-monthly Bill: {total_bill:.2f} {currency}")

            # Pie chart of energy consumption
            df = pd.DataFrame(st.session_state['data'], columns=['Equipment', 'Rating (W)', 'Rating (kW)', 'Daily Usage (hours)', 'Count', 'Daily Consumption (kWh)', 'Bi-monthly Consumption (kWh)', 'Estimated Bill'])
            pie_data = df.groupby('Equipment')['Bi-monthly Consumption (kWh)'].sum()
            fig, ax = plt.subplots(figsize=(10, 6))
            pie_data.plot(kind='pie', autopct='%1.1f%%', ax=ax)
            plt.ylabel('')
            plt.title('Energy Consumption by Equipment')
            st.pyplot(fig)

            # Display the table
            st.write("Total Consumption Data:")
            st.table(df)

            # Download options
            st.write("Download the data:")
            excel_data = create_excel(df, fig)
            st.download_button(label="Download as Excel", data=excel_data, file_name='electricity_consumption.xlsx')
        else:
            st.write("No equipment data available to calculate total bill.")

    if st.button("Reset"):
        st.session_state['data'] = []

if __name__ == "__main__":
    main()
