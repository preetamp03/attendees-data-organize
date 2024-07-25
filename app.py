import streamlit as st
import pandas as pd
from collections import Counter

# Function to determine the most frequent First Name for each email
def get_most_frequent_first_name(df):
    def most_frequent_name(names):
        if len(names) > 0:
            return Counter(names).most_common(1)[0][0]
        return ''

    # Group by Email and find the most frequent First Name
    return df.groupby('Email').agg({
        'First Name': lambda x: most_frequent_name(list(x)),
        'Phone': 'first',  # Take the first phone number (should be the same for each email)
        'Attendance': 'sum'
    }).reset_index()

# Function to validate and process Growthflow files
def process_growthflow(file):
    try:
        df = pd.read_excel(file)
        required_columns = ['First Name', 'Email', 'Phone', 'Attendance_Day']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Missing columns in Growthflow file. Expected columns: {required_columns}")
            return None

        # Select only the necessary columns
        df = df[required_columns]

        # Convert Attendance_Day to string and handle NaN values
        df['Attendance_Day'] = df['Attendance_Day'].astype(str).fillna('')

        # Split and normalize attendance days (remove duplicates)
        df['Attendance_Day'] = df['Attendance_Day'].apply(lambda x: set(x.split(',')) if x else set())
        
        # Explode the Attendance_Day into multiple rows for each day attended
        df = df.explode('Attendance_Day')
        
        # Aggregate attendance by email
        df['Attendance'] = df.groupby('Email')['Attendance_Day'].transform('nunique')
        
        # Drop duplicate rows and get the most frequent First Name
        summary = get_most_frequent_first_name(df.drop_duplicates(['Email']))
        
        return summary
    except Exception as e:
        st.error(f"Error processing Growthflow file: {e}")
        return None

# Function to validate and process WebinarJam files
def process_webinarjam(file):
    try:
        # Determine the file extension
        file_extension = file.name.split('.')[-1].lower()

        # Read the file based on its extension
        if file_extension in ['csv', 'csv']:
            df = pd.read_csv(file, dtype=str)  # Read as strings to preserve phone numbers
        elif file_extension == 'xlsx':
            df = pd.read_excel(file, dtype=str)  # Read as strings to preserve phone numbers
        else:
            st.error("Unsupported file format. Please upload a .csv or .xlsx file.")
            return None

        required_columns = ['First name', 'Email', 'Phone number', 'Attended live']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Missing columns in WebinarJam file. Expected columns: {required_columns}")
            return None

        # Select only the necessary columns
        df = df[required_columns]

        # Ensure 'Phone number' column is treated as string
        df['Phone number'] = df['Phone number'].astype(str).str.strip()

        # Convert 'Attended live' to attendance count
        df['Attendance'] = df['Attended live'].apply(lambda x: 1 if x.lower() == 'yes' else 0)
        
        # Remove duplicates and aggregate attendance by email
        summary = df.groupby(['First name', 'Email', 'Phone number'])['Attendance'].sum().reset_index()
        
        # Rename columns for consistency
        summary.rename(columns={
            'First name': 'First Name',
            'Phone number': 'Phone'
        }, inplace=True)
        
        return summary
    except Exception as e:
        st.error(f"Error processing WebinarJam file: {e}")
        return None

st.title("Attendance Summary Web Application")

st.sidebar.title("Upload Options")

option = st.sidebar.selectbox(
    "Choose the type of file you want to upload",
    ("Growthflow", "WebinarJam")
)

# Display instructions based on selected option
if option == "Growthflow":
    st.sidebar.write("Make sure column names are: ['First Name', 'Email', 'Phone', 'Attendance_Day'].")
elif option == "WebinarJam":
    st.sidebar.write("Make sure column names are: ['First name', 'Email', 'Phone number', 'Attended live'].")

uploaded_file = st.sidebar.file_uploader("Upload your file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    if option == "Growthflow":
        result_df = process_growthflow(uploaded_file)
        if result_df is not None:
            st.write("Processed Growthflow Data")
            st.write(result_df)
            
            # Provide download option
            result_xlsx = result_df.to_excel(index=False)
            st.download_button(
                label="Download Excel file",
                data=result_xlsx,
                file_name='growthflow_summary.xlsx'
            )
    
    elif option == "WebinarJam":
        result_df = process_webinarjam(uploaded_file)
        if result_df is not None:
            st.write("Processed WebinarJam Data")
            st.write(result_df)
            
            # Provide download option
            if uploaded_file.name.endswith('.xlsx'):
                result_xlsx = result_df.to_excel(index=False)
                st.download_button(
                    label="Download Excel file",
                    data=result_xlsx,
                    file_name='webinarjam_summary.xlsx'
                )
            else:
                result_csv = result_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV file",
                    data=result_csv,
                    file_name='webinarjam_summary.csv'
                )
