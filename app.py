import pandas as pd
import streamlit as st

# Title of the Streamlit app
st.title("Product Finder App")

# Example displayed on the website to explain model number input
st.write("### Example Model Number Format:")
st.write("Schoek Example:")
st.write("T-D-MM1-VV2-REI120-CV35-X80-H170-6.0")

# Paths to the CSV files
csv_path_1 = r"Isokorb_T_combined_cleaned.csv"
csv_path_2 = r"Isokorb_XT_combined_cleaned.csv"
csv_path_Leviat_1 = r"masterfile_HIT_HP.csv"
csv_path_Leviat_2 = r"masterfile_HIT_SP.csv"

# Load the CSV files
df1 = pd.read_csv(csv_path_1)
df2 = pd.read_csv(csv_path_2)
df_Leviat_1 = pd.read_csv(csv_path_Leviat_1)
df_Leviat_2 = pd.read_csv(csv_path_Leviat_2)

# Exclude the first row from the second DataFrame and combine them
df2 = df2.iloc[1:].reset_index(drop=True)  # Exclude the first row and reset the index
df_Schoeck = pd.concat([df1, df2], ignore_index=True)

# Create Proper DataFrame for Leviat Products
df_Leviat_2 = df_Leviat_2.iloc[1:].reset_index(drop=True)
df_Leviat = pd.concat([df_Leviat_1, df_Leviat_2], ignore_index=True)

# Corrected preprocessing function for additional file
def preprocess_additional_file(df_Leviat):
    # Filter the DataFrame based on the "c" column value
    filtered_df = df_Leviat[df_Leviat['c'] == "25/30"]
    
    # Ensure columns are treated as strings
    filtered_df['mrd'] = filtered_df['mrd'].astype(str).str.replace(',', '.').str.replace('-', '')
    filtered_df['vrd'] = filtered_df['vrd'].astype(str).str.replace(',', '.').str.replace('-', '')
    
    # Convert columns to float
    filtered_df['mrd'] = filtered_df['mrd'].astype(float)
    filtered_df['vrd'] = filtered_df['vrd'].astype(float)
    
    # Drop unnecessary columns
    filtered_df = filtered_df[['mrd', 'vrd', 'mrd_type', 'vrd_type', 'new_product_type', 'hh']]
    
    # Combine rows with the same 'new_product_type' and create ranges
    result_df = filtered_df.groupby('new_product_type').agg(
        MRD_Range=pd.NamedAgg(column='mrd', aggfunc=lambda x: f"{x.min()}-{x.max()}"),
        VRD_Range=pd.NamedAgg(column='vrd', aggfunc=lambda x: f"{x.min()}-{x.max()}"),
        Height=pd.NamedAgg(column='hh', aggfunc='first')
    ).reset_index()
    
    return result_df

# Function to fetch alternative products by model number from combined CSVs (Schoek)
def fetch_alternative_products_by_model(df_Schoeck, encoded_value):
    # Fetch the specific product details
    specific_product = df_Schoeck[df_Schoeck['Encoded'] == encoded_value]
    
    if specific_product.empty:
        st.write("No such product found in the Schoek files.")
        return pd.DataFrame(), pd.DataFrame()
    
    # Extract MrD, vRd, and height values
    mrd_value = specific_product['MrD'].values[0]
    vrd_value = specific_product['vRd'].values[0]
    height_value = int(encoded_value.split('-')[7][1:])  # Extract height from model number
    
    # Calculate the range for MrD and vRd
    mrd_min = mrd_value * 1.0  # 100% of the value
    mrd_max = mrd_value * 1.03  # 103% of the value
    vrd_min = vrd_value * 1.0  # 100% of the value
    vrd_max = vrd_value * 1.03  # 103% of the value

    # Filter the DataFrame based on the range and height
    filtered_df = df_Schoeck[
        (df_Schoeck['MrD'] >= mrd_min) & (df_Schoeck['MrD'] <= mrd_max) &
        (df_Schoeck['vRd'] >= vrd_min) & (df_Schoeck['vRd'] <= vrd_max) &
        (df_Schoeck['Encoded'].str.contains(f"H{height_value}"))
    ]

    return specific_product, filtered_df

# Function to fetch alternative products by specifications from combined CSVs (Schoek)
def fetch_alternative_products_by_specs(df_Schoeck, mrd_value, vrd_value, height_value):
    # Calculate the range for MrD and vRd
    mrd_min = mrd_value * 1.0  # 100% of the value
    mrd_max = mrd_value * 1.03  # 103% of the value
    vrd_min = vrd_value * 1.0  # 100% of the value
    vrd_max = vrd_value * 1.03  # 103% of the value

    # Calculate the range for height
    height_min = height_value - 20
    height_max = height_value + 20

    # Extract height values from the 'Encoded' column
    df_Schoeck['Height'] = df_Schoeck['Encoded'].str.extract(r'H(\d+)')
    
    # Convert extracted height values to numeric, but avoid coercing errors
    df_Schoeck['Height'] = pd.to_numeric(df_Schoeck['Height'], errors='raise')
    
    # Filter the DataFrame based on the range and height
    filtered_df = df_Schoeck[
        (df_Schoeck['MrD'] >= mrd_min) & (df_Schoeck['MrD'] <= mrd_max) &
        (df_Schoeck['vRd'] >= vrd_min) & (df_Schoeck['vRd'] <= vrd_max) &
        (df_Schoeck['Height'].between(height_min, height_max))
    ]

    return filtered_df

# Function to fetch products from additional file by model number (Leviat)
def fetch_products_from_additional_file_by_model(df_Leviat, encoded_value):
    preprocessed_df = preprocess_additional_file(df_Leviat)
    
    specific_product = preprocessed_df[preprocessed_df['new_product_type'] == encoded_value]
    
    if specific_product.empty:
        st.write("No such product found in the Leviat files.")
        return pd.DataFrame()
    
    return specific_product

# Function to fetch products from additional file by specifications (Leviat)
def fetch_products_from_additional_file_by_specs(df_Leviat, mrd_value, vrd_value, height_value):
    preprocessed_df = preprocess_additional_file(df_Leviat)
    
    # Calculate the range for MrD and vRd
    mrd_min = mrd_value * 1.0  # 100% of the value
    mrd_max = mrd_value * 1.03  # 103% of the value
    vrd_min = vrd_value * 1.0  # 100% of the value
    vrd_max = vrd_value * 1.03  # 103% of the value

    # Calculate the range for height
    height_min = height_value - 20
    height_max = height_value + 20

    # Split the ranges from the MRD_Range and VRD_Range columns
    preprocessed_df[['MRD_min', 'MRD_max']] = preprocessed_df['MRD_Range'].str.split('-', expand=True).astype(float)
    preprocessed_df[['VRD_min', 'VRD_max']] = preprocessed_df['VRD_Range'].str.split('-', expand=True).astype(float)

    # Filter the DataFrame based on the MrD, vRd, and height ranges
    filtered_df = preprocessed_df[
        (preprocessed_df['MRD_min'] <= mrd_max) & (preprocessed_df['MRD_max'] >= mrd_min) &
        (preprocessed_df['VRD_min'] <= vrd_max) & (preprocessed_df['VRD_max'] >= vrd_min) &
        (preprocessed_df['Height'].between(height_min, height_max))
    ]
    
    return filtered_df

# Drop-down menu to choose input type
input_type = st.selectbox("Choose input type:", ["Model Number", "Specifications"])

# Conditional display of input boxes based on selection
if input_type == "Model Number":
    # Input box for model number
    encoded_value = st.text_input("Input Model Number:")
    
    # Fetch and display alternative products based on model number
    if encoded_value:
        specific_product, alternative_products = fetch_alternative_products_by_model(df_Schoeck, encoded_value)
        
        if not alternative_products.empty:
            alternative_products = alternative_products.drop(columns=['TableName'])
            specific_product = specific_product.drop(columns=['TableName'])

            # Highlight the specific product in the alternatives
            def highlight_product(row):
                if row['Encoded'] == encoded_value:
                    return ['background-color: yellow'] * len(row)
                else:
                    return [''] * len(row)
            
            st.write("Your Alternative Products from Schoeck CSVs:")
            st.write(alternative_products.style.apply(highlight_product, axis=1))
        else:
            st.write("No alternative products found in the Schoeck files.")
        
        # Fetch and display additional products based on model number
        additional_products = fetch_products_from_additional_file_by_model(df_Leviat, encoded_value)
        if not additional_products.empty:
            st.write("Additional Products from Leviat CSVs:")
            st.write(additional_products)
        else:
            st.write("No additional products found in the Leviat files.")

else:
    # Input boxes for specifications
    mrd_value = st.number_input("Input mRd value:", format="%.2f")
    vrd_value = st.number_input("Input vRd value:", format="%.2f")
    height_value = st.number_input("Input Height value (in intervals of 10):", step=10, format="%d")
    
    # Fetch and display alternative products based on specifications
    if mrd_value != 0.00 and vrd_value != 0.00:
        alternative_products = fetch_alternative_products_by_specs(df_Schoeck, mrd_value, vrd_value, height_value)
        
        if not alternative_products.empty:
            alternative_products = alternative_products.drop(columns=['TableName'])

            st.write("Your Alternative Products from Schoeck CSVs:")
            st.write(alternative_products)
        else:
            st.write("No alternative products found in the Schoeck files.")
        
        # Fetch and display additional products based on specifications
        additional_products = fetch_products_from_additional_file_by_specs(df_Leviat, mrd_value, vrd_value, height_value)
        if not additional_products.empty:
            st.write("Additional Products from Leviat CSVs:")
            st.write(additional_products)
        else:
            st.write("No additional products found in the Leviat files.")

# Explanation of methods
st.write("## There are two ways to use this app:")

col1, col2 = st.columns(2)

with col1:
    st.write("### Method 1:")
    st.write("You input the exact model number of a model off of the company's website and the app will give you the existing alternative models to compare to the one you input.")

with col2:
    st.write("### Method 2:")
    st.write("You can input the required moment and shear load resistances needed for your project and get the exact model configuration you require.")
