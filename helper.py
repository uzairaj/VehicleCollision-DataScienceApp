import io
import pandas as pd
import streamlit as st
import plotly.express as px


def df_info(df: pd.DataFrame) -> None:
    '''
    This function imports a dataframe and creates a table with info on the names, 
    number of non-null values, data type of the fields
    ...
    var df: A dataframe with the data on several incidents in NYC
    type: pd.DataFrame
    ...
    return: Displays a table with info on the dataframe
    rtype: None
    '''

    buffer = io.StringIO() 
    df.info(buf=buffer)
    s = buffer.getvalue() 
    df_info = s.split('\n')
    counts = []
    names = []
    nn_count = []
    dtype = []
    for i in range(5, len(df_info)-3):
        line = df_info[i].split()
        counts.append(line[0])
        names.append(line[1])
        nn_count.append(line[2])
        dtype.append(line[4])
    df_info_dataframe = pd.DataFrame(data = {'#': counts, 'variable': names, 'Non-Null Count': nn_count, 'Data Type': dtype})
    return df_info_dataframe.drop('#', axis = 1)


def space(num_lines: int) -> None:
    '''
    This function is used to create empty spaces
    ...
    var num_lines: Number of lines to be left as space
    type: int
    ...
    return: Leaves space
    rtype: None
    '''
    for _ in range(num_lines):
        st.write("")


def sidebar_space(num_lines: int) -> None:
    '''
    This function is used to create empty spaces for the sidebar
    ...
    var num_lines: Number of lines to be left as space
    type: int
    ...
    return: Leaves space
    rtype: None
    '''
    for _ in range(num_lines):
        st.sidebar.write("")


def df_isnull(df: pd.DataFrame) -> pd.DataFrame:
    '''
    This function checks for missing values in the dataset and returns a dataframe with number of missing values for each variable
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: Dataframe with number of missing values for each variable
    rtype: pd.DataFrame
    '''

    res = pd.DataFrame(df.isnull().sum()).reset_index()
    res['Percentage'] = round(res[0] / df.shape[0] * 100, 2)
    res['Percentage'] = res['Percentage'].astype(str) + '%'
    return res.rename(columns = {'index':'variable', 0:'Number of null values'})


def number_of_outliers(df):
    '''
    This function returns a dataframe with number of outliers for each variable in the dataset
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: Dataframe with number of outliers for each variable
    rtype: pd.DataFrame
    '''

    df = df.select_dtypes(exclude = 'object')
    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1
    ans = ((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).sum()
    df = pd.DataFrame(ans).reset_index().rename(columns = {'index':'variable', 0:'count_of_outliers'})
    return df


def multiselect_container(message, arr, key):
    '''
    This function creates a dropdown and allows selecting options from it
    ...
    var message: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: Dataframe with number of missing values for each variable
    rtype: pd.DataFrame
    '''
    
    container = st.container()
    select_all_button = st.checkbox("Select all for " + key + " plots")
    if select_all_button:
        selected_num_cols = container.multiselect(message, arr, default = list(arr))
    else:
        selected_num_cols = container.multiselect(message, arr, default = arr[0])

    return selected_num_cols    


def exploratory_data_analysis(df: pd.DataFrame) -> None:
    '''
    This function performs exploratory data analysis based on the option selected by users
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: Performs analysis based on the type of analysis selected
    rtype: None
    '''

    # List of Analysis
    all_vizuals = (['Info', 'Missing Value Info', 'Descriptive Analysis', 'Target Analysis', 
                   'Distribution of Numerical variables', 'Count Plots of Categorical variables', 
                   'Box Plots', 'Outlier Analysis'])
          
    vizuals = st.multiselect("Choose which visualizations you want to see below", all_vizuals)

    # Analysis-1: Dataset info
    if 'Info' in vizuals:
        st.subheader('Info:')
        c1, c2, c3 = st.columns([1, 2, 1])
        c2.dataframe(df_info(df))

    # Analysis-2: Missing value in the Dataset info
    if 'Missing Value Info' in vizuals:
        st.subheader('NA Value Information:')
        if df.isnull().sum().sum() == 0:
            st.write('There are no NA values in your dataset')
        else:
            c1, c2, c3 = st.columns([0.5, 2, 0.5])
            c2.dataframe(df_isnull(df), width=1500)
            space(3)
            
    # Analysis-3: Descriptive statistics of the Dataset
    if 'Descriptive Analysis' in vizuals:
        st.subheader('Descriptive Analysis:')
        st.dataframe(df.describe())
        
    # Analysis-4: Target Analysis of individual variables in the Dataset
    if 'Target Analysis' in vizuals:
        st.subheader("Select target variable:")    
        target_column = st.selectbox("", df.columns, index = len(df.columns) - 1)
    
        st.subheader("Histogram of target variable")
        fig = px.histogram(df, x = target_column)
        c1, c2, c3 = st.columns([0.5, 2, 0.5])
        c2.plotly_chart(fig)

    # Analysis-5: Distribution Analysis - for numerical variables in the Dataset
    num_columns = df.select_dtypes(exclude = 'object').columns
    cat_columns = df.select_dtypes(include = 'object').columns

    if 'Distribution of Numerical variables' in vizuals:

        if len(num_columns) == 0:
            st.write('There are no numerical variables in the data')
        else:
            selected_num_cols = multiselect_container('Choose variables for Distribution plots:', num_columns, 'Distribution')
            st.subheader('Distribution of numerical variables')
            i = 0
            while (i < len(selected_num_cols)):
                c1, c2 = st.columns(2)
                for j in [c1, c2]:

                    if (i >= len(selected_num_cols)):
                        break
                    fig = px.histogram(df, x = selected_num_cols[i])
                    j.plotly_chart(fig, use_container_width = True)
                    i += 1

    # Analysis-6: Count Plots - for non-numerical variables in the Dataset
    if 'Count Plots of Categorical variables' in vizuals:
        if len(cat_columns) == 0:
            st.write('There are no categorical variables in the data')
        else:
            selected_cat_cols = multiselect_container('Choose variables for Count plots:', cat_columns, 'Count')
            st.subheader('Count plots of categorical variables')
            i = 0
            while (i < len(selected_cat_cols)):
                c1, c2 = st.columns(2)
                for j in [c1, c2]:

                    if (i >= len(selected_cat_cols)):
                        break

                    fig = px.histogram(df, x = selected_cat_cols[i], color_discrete_sequence=['indianred'])
                    j.plotly_chart(fig)
                    i += 1

    # Analysis-7: Box plots - for numerical variables in the Dataset
    if 'Box Plots' in vizuals:
        if len(num_columns) == 0:
            st.write('There is no numerical variables in the data.')
        else:
            selected_num_cols = multiselect_container('Choose variables for Box plots:', num_columns, 'Box')
            st.subheader('Box plots')
            i = 0
            while (i < len(selected_num_cols)):
                c1, c2 = st.columns(2)
                for j in [c1, c2]:
                    
                    if (i >= len(selected_num_cols)):
                        break
                    
                    fig = px.box(df, y = selected_num_cols[i])
                    j.plotly_chart(fig, use_container_width = True)
                    i += 1

    # Analysis-8: Outlier Analysis - for numerical variables in the Dataset
    if 'Outlier Analysis' in vizuals:
        st.subheader('Outlier Analysis')
        c1, c2, c3 = st.columns([1, 2, 1])
        c2.dataframe(number_of_outliers(df))
