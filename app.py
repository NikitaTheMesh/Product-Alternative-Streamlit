import pandas as pd
import streamlit as st

# Title of the Streamlit app
st.title("Product Finder App")

# Example displayed on the website to explain model number input
st.write("## Examples of Model Number Format:")

col1, col2 = st.columns(2)

with col1:
    st.write("### Schoek Example:")
    st.write("T-D-MM1-VV2-REI120-CV35-X80-H170-6.0")

with col2:
    st.write("### Halfen/Leviat Example:")
    st.write("HIT-HP MVX-0708-27-100-45")

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
df2 = df2.iloc[1:].reset_index(drop=True)
df_Schoeck = pd.concat([df1, df2], ignore_index=True)

# Create Proper DataFrame for Leviat Products
df_Leviat_2 = df_Leviat_2.iloc[1:].reset_index(drop=True)
df_Leviat = pd.concat([df_Leviat_1, df_Leviat_2], ignore_index=True)

# Corrected preprocessing function for additional file
def preprocess_additional_file(df_Leviat):
    filtered_df = df_Leviat[df_Leviat['c'] == "25/30"].copy()
    filtered_df['mrd'] = filtered_df['mrd'].astype(str).str.replace(',', '.').str.replace('-', '')
    filtered_df['vrd'] = filtered_df['vrd'].astype(str).str.replace(',', '.').str.replace('-', '')
    filtered_df['mrd'] = filtered_df['mrd'].astype(float)
    filtered_df['vrd'] = filtered_df['vrd'].astype(float)
    filtered_df = filtered_df[['mrd', 'vrd', 'mrd_type', 'vrd_type', 'new_product_type', 'hh']]
    result_df = filtered_df.groupby('new_product_type').agg(
        MRD_Range=pd.NamedAgg(column='mrd', aggfunc=lambda x: f"{x.min()}-{x.max()}"),
        VRD_Range=pd.NamedAgg(column='vrd', aggfunc=lambda x: f"{x.min()}-{x.max()}"),
        Height=pd.NamedAgg(column='hh', aggfunc='first')
    ).reset_index()
    return result_df

# Function to fetch alternative products by model number from combined CSVs (Schoeck)
def fetch_alternative_products_by_model(df_Schoeck, encoded_value):
    specific_product = df_Schoeck[df_Schoeck['Encoded'] == encoded_value]
    if specific_product.empty:
        st.write("No such product found in the Schoeck's Database.")
        return pd.DataFrame(), pd.DataFrame()
    
    mrd_value = specific_product['MrD'].values[0]
    vrd_value = specific_product['vRd'].values[0]
    height_value = int(encoded_value.split('-')[7][1:])  # Extract height from model number

    mrd_min = mrd_value * 0.99  # 99% of the value
    mrd_max = mrd_value * 1.03  # 103% of the value
    vrd_min = vrd_value * 0.99  # 99% of the value
    vrd_max = vrd_value * 1.03  # 103% of the value
    height_min = height_value - 20  # +/- 20 height range
    height_max = height_value + 20  # +/- 20 height range

    # Ensure 'Height' column is numeric
    df_Schoeck['Height'] = pd.to_numeric(df_Schoeck['Encoded'].str.extract(r'H(\d+)')[0], errors='coerce')

    # Filter based on MrD, vRd, and height range
    filtered_df = df_Schoeck[
        (df_Schoeck['MrD'] >= mrd_min) & (df_Schoeck['MrD'] <= mrd_max) &
        (df_Schoeck['vRd'] >= vrd_min) & (df_Schoeck['vRd'] <= vrd_max) &
        (df_Schoeck['Height'].between(height_min, height_max))
    ]

    return specific_product, filtered_df

# Function to fetch alternative products by specifications from combined CSVs (Schoeck)
def fetch_alternative_products_by_specs(df_Schoeck, mrd_value, vrd_value, height_value):
    mrd_min = mrd_value * 0.99
    mrd_max = mrd_value * 1.03
    vrd_min = vrd_value * 0.99
    vrd_max = vrd_value * 1.03
    height_min = height_value - 20
    height_max = height_value + 20

    # Ensure 'Height' column is numeric
    df_Schoeck['Height'] = pd.to_numeric(df_Schoeck['Encoded'].str.extract(r'H(\d+)')[0], errors='coerce')

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
        return pd.DataFrame(), pd.DataFrame()
    
    # Find alternative products within Leviat database
    mrd_value = specific_product['MRD_Range'].values[0].split('-')
    vrd_value = specific_product['VRD_Range'].values[0].split('-')
    height_value = specific_product['Height'].values[0]
    
    mrd_min = float(mrd_value[0]) * 0.99
    mrd_max = float(mrd_value[1]) * 1.03
    vrd_min = float(vrd_value[0]) * 0.99
    vrd_max = float(vrd_value[1]) * 1.03
    height_min = height_value - 20
    height_max = height_value + 20
    
    preprocessed_df[['MRD_min', 'MRD_max']] = preprocessed_df['MRD_Range'].str.split('-', expand=True).astype(float)
    preprocessed_df[['VRD_min', 'VRD_max']] = preprocessed_df['VRD_Range'].str.split('-', expand=True).astype(float)

    alternative_products = preprocessed_df[
        (preprocessed_df['MRD_min'] <= mrd_max) & (preprocessed_df['MRD_max'] >= mrd_min) &
        (preprocessed_df['VRD_min'] <= vrd_max) & (preprocessed_df['VRD_max'] >= vrd_min) &
        (preprocessed_df['Height'].between(height_min, height_max))
    ]

    return specific_product, alternative_products

# Function to fetch products from additional file by specifications (Leviat)
def fetch_products_from_additional_file_by_specs(df_Leviat, mrd_value, vrd_value, height_value):
    preprocessed_df = preprocess_additional_file(df_Leviat)
    mrd_min = mrd_value * 0.99
    mrd_max = mrd_value * 1.03
    vrd_min = vrd_value * 0.99
    vrd_max = vrd_value * 1.03
    height_min = height_value - 20
    height_max = height_value + 20

    preprocessed_df[['MRD_min', 'MRD_max']] = preprocessed_df['MRD_Range'].str.split('-', expand=True).astype(float)
    preprocessed_df[['VRD_min', 'VRD_max']] = preprocessed_df['VRD_Range'].str.split('-', expand=True).astype(float)

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
    
    if encoded_value:
        # Fetch from Schoeck
        specific_product_schoeck, alternative_products_schoeck = fetch_alternative_products_by_model(df_Schoeck, encoded_value)
        
        if not alternative_products_schoeck.empty:
            alternative_products_schoeck = alternative_products_schoeck.drop(columns=['TableName'])
            specific_product_schoeck = specific_product_schoeck.drop(columns=['TableName'])

            def highlight_product_schoeck(row):
                if row['Encoded'] == encoded_value:
                    return ['background-color: yellow'] * len(row)
                else:
                    return [''] * len(row)
            
            st.write("Your Alternative Products from Schoeck's Database:")
            st.write(alternative_products_schoeck.style.apply(highlight_product_schoeck, axis=1))
        else:
            st.write("No alternative products found in Schoeck's files.")
        
        # Fetch from Leviat
        specific_product_leviat, alternative_products_leviat = fetch_products_from_additional_file_by_model(df_Leviat, encoded_value)
        if not alternative_products_leviat.empty:
            def highlight_product_leviat(row):
                if row['new_product_type'] == encoded_value:
                    return ['background-color: yellow'] * len(row)
                else:
                    return [''] * len(row)
                    
            st.write("Your Alternative Products from Leviat's Database:")
            st.write(alternative_products_leviat.style.apply(highlight_product_leviat, axis=1))
        else:
            st.write("No alternative products found in Leviat's files.")

else:
    # Input boxes for specifications
    mrd_value = st.number_input("Input mRd value:", format="%.2f")
    vrd_value = st.number_input("Input vRd value:", format="%.2f")
    height_value = st.number_input("Input Height value (in intervals of 10):", step=10, format="%d")
    
    if mrd_value != 0.00 and vrd_value != 0.00:
        alternative_products_schoeck = fetch_alternative_products_by_specs(df_Schoeck, mrd_value, vrd_value, height_value)
        
        if not alternative_products_schoeck.empty:
            alternative_products_schoeck = alternative_products_schoeck.drop(columns=['TableName'])
            st.write("Your Alternative Products from Schoeck's Database:")
            st.write(alternative_products_schoeck)
        else:
            st.write("No alternative products found in Schoeck's files.")
        
        additional_products_leviat = fetch_products_from_additional_file_by_specs(df_Leviat, mrd_value, vrd_value, height_value)
        if not additional_products_leviat.empty:
            st.write("Additional Products from Leviat's Database:")
            st.write(additional_products_leviat)
        else:
            st.write("No additional products found in the Leviat's files.")

# Explanation of methods
st.write("## There are two ways to use this app:")

col1, col2 = st.columns(2)

with col1:
    st.write("### Method 1:")
    st.write("You input the exact model number of a model off of the company's website and the app will give you the existing alternative models to compare to the one you input.")

with col2:
    st.write("### Method 2:")
    st.write("You can input the required moment and shear load resistances along with the total height needed for your project and get the exact model configuration you require. The output product heights are +-20mm of your input, in case the exact specifications you would prefer are not available.")
