import dash
from dash import dcc, html, Input, Output, State, ALL
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import io
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Layout for Page 1 (Welcome Page)
layout_page1 = html.Div([
    html.H1("ETBR REPORT", style={'textAlign': 'center', 'marginBottom': '20px', 'fontSize': '36px', 'fontWeight': 'bold'}),
    html.Div([
        dcc.Upload(
            id='page1-upload-data',
            children=html.Button('Upload File', style={'fontSize': '20px', 'width': '200px'}),
            multiple=False,
            style={'display': 'inline-block'}
        ),
        html.Div(id='page1-output-data-upload', style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'middle'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
    dcc.Store(id='page1-stored-data'),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='page1-visualization-dropdown',
                options=[
                    {'label': 'ETBR Report', 'value': 'ETBR Report'},
                    {'label': 'LMTD VS MTD ETBR', 'value': 'LMTD ETBR'},
                    {'label': 'Model ETBR', 'value': 'Model ETBR'},
                    {'label': 'Enquiry Type vs ETBR', 'value': 'Enquiry Type vs ETBR'},
                    {'label': 'Enquiry Source vs ETBR', 'value': 'Enquiry Source vs ETBR'},
                    {'label': 'Team vs ETBR', 'value': 'Team vs Enquiry, Booking, Test Drive, Retail'},
                    {'label': 'Team vs Enquiry Type ETBR', 'value': 'Team vs Enquiry Type Report'},
                    {'label': 'Walk In ETBR', 'value': 'Walk In ETBR'},
                    {'label': 'All Visualisations', 'value': 'All Visualisations'}
                ],
                placeholder='Select Visualization',
                style={'width': '200px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Dropdown(
                id='page1-location-dropdown',
                placeholder='Select Location',
                style={'width': '200px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Dropdown(
                id='page1-sales-manager-dropdown',
                placeholder='Select Sales Manager',
                style={'width': '350px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Dropdown(
                id='page1-consultant-dropdown',
                placeholder='Select Sales Consultant',
                style={'width': '350px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'left'}),
    html.Div(id='page1-visualization-container'),
    html.Div([
        html.Button("Go to Page 2", id="go-to-page2", n_clicks=0, 
                    style={'fontSize': '20px', 'padding': '0px 2px'})
    ], style={'position': 'fixed', 'right': '20px', 'top': '5%', 'transform': 'translateY(-50%)'})
])


@app.callback(
    [Output('page1-location-dropdown', 'options'),
     Output('page1-sales-manager-dropdown', 'options'),
     Output('page1-consultant-dropdown', 'options'),
     Output('page1-stored-data', 'data'),
     Output('page1-consultant-dropdown', 'value'),
     Output('page1-visualization-container', 'children'),
     Output('page1-output-data-upload', 'children')],
    [Input('page1-upload-data', 'contents'),
     Input('page1-visualization-dropdown', 'value'),
     Input('page1-sales-manager-dropdown', 'value'),
     Input('page1-consultant-dropdown', 'value'),
     Input('page1-location-dropdown', 'value')],
    [State('page1-upload-data', 'filename'),
     State('page1-stored-data', 'data')]
)
def update_visualizations(contents, selected_visualization, selected_sales_manager, selected_consultant, selected_location, filename, stored_data):

    location_options, sales_manager_options, consultant_options = [], [], []
    location_display = ''
    upload_message = None
    filtered_df = pd.DataFrame()
    retained_consultant = selected_consultant
    visualization_output = []

    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        data_df = pd.read_excel(io.BytesIO(decoded))

        required_columns = ['Dealer Location', 'Sales Manager', 'Sales Consultant', 'Enquiry Type']
        missing_columns = [col for col in required_columns if col not in data_df.columns]
        if missing_columns:
            return location_options, sales_manager_options, consultant_options, stored_data, retained_consultant, [html.Div(f"Missing columns: {', '.join(missing_columns)}")], None

        locations = data_df['Dealer Location'].dropna().unique()
        location_options = [{'label': loc, 'value': loc} for loc in locations]
        stored_data = data_df.to_dict('records')
        upload_message = f'File "{filename}" successfully uploaded!'

    if stored_data:
        data_df = pd.DataFrame(stored_data)

        location_display = selected_location if selected_location else "All Locations"
        manager_display = f", {selected_sales_manager}" if selected_sales_manager else ""
        consultant_display = f", {selected_consultant}" if selected_consultant else ""

        filtered_df = data_df

        if selected_location:
            filtered_df = filtered_df[filtered_df['Dealer Location'] == selected_location]

        locations = data_df['Dealer Location'].dropna().unique()
        location_options = [{'label': loc, 'value': loc} for loc in locations]

        sales_managers = filtered_df['Sales Manager'].dropna().unique()
        sales_manager_options = [{'label': manager, 'value': manager} for manager in sales_managers]

        if selected_sales_manager:
            filtered_df = filtered_df[filtered_df['Sales Manager'] == selected_sales_manager]

        consultants = filtered_df['Sales Consultant'].dropna().unique()
        consultant_options = [{'label': consultant, 'value': consultant} for consultant in consultants]

        if selected_consultant and selected_consultant not in [opt['value'] for opt in consultant_options]:
            retained_consultant = None

        if retained_consultant:
            filtered_df = filtered_df[filtered_df['Sales Consultant'] == retained_consultant]

        def create_title(base_title):
            return f"{base_title} for {location_display}{manager_display}{consultant_display}"

        def create_etbr_report():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            values = [filtered_df[metric].sum() if metric in filtered_df.columns else 0 for metric in metrics]
            if not selected_location:
                values = [v / 2 for v in values]
            chart_df = pd.DataFrame({'Metric': metrics, 'Value': values})
            fig = px.pie(chart_df, values='Value', names='Metric', title=create_title('ETBR Report'))
            
            fig.update_traces(
                textposition='inside',
                texttemplate='%{label}<br>%{value:.2f}<br>%{percent}',
                hovertemplate='<b>%{label}</b><br>Value: %{value:.2f}<br>Percentage: %{percent}'
            )
            fig.update_layout(
                height=600,
                width=600)
            
            total = sum(values)
            description = f"""
            This pie chart shows the distribution of Enquiry, Test Drive, Booking, and Retail metrics for the Month-To-Date (MTD) period.
            

            Enquiries: {values[0]:.0f} ({values[0]/total*100:.1f}%)
            Test Drives: {values[1]:.0f} ({values[1]/total*100:.1f}%)
            Bookings: {values[2]:.0f} ({values[2]/total*100:.1f}%)
            Retails: {values[3]:.0f} ({values[3]/total*100:.1f}%)
            """
            
            return fig, description

        def create_lmtd_etbr():
            metrics = ['ENQUIRY', 'TD', 'BOOKING', 'RETAIL']
            mtd_values = [filtered_df[f'{metric} MTD'].sum() if f'{metric} MTD' in filtered_df.columns else 0 for metric in metrics]
            lmtd_values = [filtered_df[f'{metric} LMTD'].sum() if f'{metric} LMTD' in filtered_df.columns else 0 for metric in metrics]
            if not selected_location:
                mtd_values = [v / 2 for v in mtd_values]
                lmtd_values = [v / 2 for v in lmtd_values]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=metrics, y=mtd_values, name='MTD', text=mtd_values, textposition='outside'))
            fig.add_trace(go.Bar(x=metrics, y=lmtd_values, name='LMTD', text=lmtd_values, textposition='outside'))
            fig.update_layout(
                barmode='group', 
                title=create_title('LMTD vs MTD ETBR'), 
                xaxis_title='Metrics', 
                yaxis_title='Values', 
                height=600,
                width=1000,
                legend_title='Period', 
                legend=dict(orientation="h"),
                bargap=0.2, 
                bargroupgap=0.1,
                xaxis=dict(tickangle=0)
            )
            
            mtd_total = sum(mtd_values)
            lmtd_total = sum(lmtd_values)
            percent_change = ((mtd_total - lmtd_total) / lmtd_total) * 100
            
            description = f"""
            This grouped bar chart compares Month-To-Date (MTD) and Last Month-To-Date (LMTD) values for Enquiry, Test Drive, Booking, and Retail metrics.
            
            Total MTD: {mtd_total:.0f}
            Total LMTD: {lmtd_total:.0f}
            Percent change: {percent_change:.1f}%
            """
            
            return fig, description

        def create_model_etbr():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            data = []
            for metric in metrics:
                metric_df = filtered_df.groupby('Model').agg({metric: 'sum'}).reset_index()
                metric_df['Metric'] = metric
                metric_df = metric_df.rename(columns={metric: 'Value'})
                data.append(metric_df)
            chart_df = pd.concat(data)
            fig = px.bar(
                chart_df,
                x='Model',
                y='Value',
                color='Metric',
                barmode='group',
                title=create_title('MODEL ETBR'),
                labels={'Value': 'Total Value', 'Model': 'Model'},
                text='Value'
            )
            fig.update_layout(
                yaxis=dict(title='Total Value'),
                xaxis=dict(title='Model'),
                showlegend=True,
                margin=dict(l=40, r=40, t=40, b=40),
                height=600,
                width=1000,
                bargap=0.2,
                font=dict(size=12)
            )
            
            top_model = chart_df.groupby('Model')['Value'].sum().idxmax()
            top_model_value = chart_df.groupby('Model')['Value'].sum().max()

            if chart_df.empty:
        # Return an empty figure and a message if there's no data
                fig = go.Figure()
                fig.update_layout(
                title=create_title('MODEL ETBR - No Data Available'),
                annotations=[dict(
                text='No data available for the current selection',
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                font=dict(size=20)
            )]
        )
            
            description = f"""
            This grouped bar chart shows the performance of different car models across Enquiry, Test Drive, Booking, and Retail metrics for the Month-To-Date period.
            
            Top performing model: {top_model}
            Total value for top model: {top_model_value:.0f}
            """
            
            return fig, description

        def create_enquiry_type_etbr():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            data = []
            metric_abbr = {
                'ENQUIRY MTD': 'E',
                'TD MTD': 'T',
                'BOOKING MTD': 'B',
                'RETAIL MTD': 'R'
            }
            for metric in metrics:
                metric_df = filtered_df.groupby('Enquiry Type').agg({metric: 'sum'}).reset_index()
                metric_df['Metric'] = metric
                metric_df = metric_df.rename(columns={metric: 'Value'})
                data.append(metric_df)
            chart_df = pd.concat(data)
            chart_df['Metric'] = chart_df['Metric'].map(metric_abbr)
            chart_df['Hierarchy'] = chart_df['Enquiry Type'] + ' - ' + chart_df['Metric']
            fig = px.sunburst(
                chart_df,
                path=['Enquiry Type', 'Metric'],
                values='Value',
                title=create_title('Enquiry Type vs ETBR Report')
            )
            fig.update_traces(
                texttemplate='%{label}<br>%{value}',
                textfont=dict(size=12, color='black')
            )
            fig.update_layout(
                height=600,
                width=1000)
            
            top_enquiry_type = chart_df.groupby('Enquiry Type')['Value'].sum().idxmax()
            top_enquiry_value = chart_df.groupby('Enquiry Type')['Value'].sum().max()
            
            description = f"""
            This sunburst chart shows the distribution of Enquiry Types across ETBR (Enquiry, Test Drive, Booking, Retail) metrics.
            
            Top performing Enquiry Type: {top_enquiry_type}
            Total value for top Enquiry Type: {top_enquiry_value:.0f}
            """
            
            return fig, description


        def create_enquiry_source_etbr():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            data = []
            for metric in metrics:
                metric_df = filtered_df.groupby('Enquiry Source').agg({metric: 'sum'}).reset_index()
                metric_df['Metric'] = metric
                metric_df = metric_df.rename(columns={metric: 'Value'})
                data.append(metric_df)
                chart_df = pd.concat(data)
                fig = px.bar(chart_df, x='Metric', y='Value', color='Enquiry Source', title=f'Enquiry Source vs ETBR for {location_display}')
                fig.update_traces(texttemplate='%{y}', textposition='outside')
                fig.update_layout(
                height=600,
                width=1000)
                top_source = chart_df.groupby('Enquiry Source')['Value'].sum().idxmax()
                top_source_value = chart_df.groupby('Enquiry Source')['Value'].sum().max()
    
                description = f"""
    This stacked bar chart shows how different Enquiry Sources contribute to ETBR metrics.
    
    Top performing Enquiry Source: {top_source}
    Total value for top Enquiry Source: {top_source_value:.0f}
    """
    
            return fig, description


        def create_team_etbr():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            data = []
            for metric in metrics:
                metric_df = filtered_df.groupby('Sales Consultant').agg({metric: 'sum'}).reset_index()
                metric_df['Metric'] = metric
                metric_df = metric_df.rename(columns={metric: 'Value'})
                data.append(metric_df)
            chart_df = pd.concat(data)
            fig = px.bar(chart_df, x='Metric', y='Value', color='Sales Consultant', title=f'Team vs Enquiry, Booking, Test Drive, Retail for {location_display}')
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            fig.update_layout(
                height=600,
                width=1000)
            top_consultant = chart_df.groupby('Sales Consultant')['Value'].sum().idxmax()
            top_consultant_value = chart_df.groupby('Sales Consultant')['Value'].sum().max()
            
            description = f"""
            This stacked bar chart shows the performance of individual Sales Consultants across ETBR metrics.
            
            Top performing Sales Consultant: {top_consultant}
            Total value for top Sales Consultant: {top_consultant_value:.0f}
            """
            
            return fig, description

        def create_team_enquiry_type():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            data = []
            for metric in metrics:
                metric_df = filtered_df.groupby('Enquiry Type').agg({metric: 'sum'}).reset_index()
                metric_df['Metric'] = metric
                metric_df = metric_df.rename(columns={metric: 'Value'})
                data.append(metric_df)
            chart_df = pd.concat(data)
            fig = px.bar(chart_df, x='Enquiry Type', y='Value', color='Metric', title=create_title('Team vs Enquiry Type ETBR Report'))
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            fig.update_layout(barmode='group',
                height=600,
                width=1000)
            
            top_enquiry_type = chart_df.groupby('Enquiry Type')['Value'].sum().idxmax()
            top_enquiry_type_value = chart_df.groupby('Enquiry Type')['Value'].sum().max()
            
            description = f"""
            This grouped bar chart shows how different Enquiry Types perform across ETBR metrics.
            
            Top performing Enquiry Type: {top_enquiry_type}
            Total value for top Enquiry Type: {top_enquiry_type_value:.0f}
            """
            
            return fig, description

        def create_walk_in_etbr():
            metrics = ['ENQUIRY MTD', 'TD MTD', 'BOOKING MTD', 'RETAIL MTD']
            walk_in_df = filtered_df[filtered_df['Enquiry Type'] == 'Walk-in']
            values = [walk_in_df[metric].sum() if metric in walk_in_df.columns else 0 for metric in metrics]
            chart_df = pd.DataFrame({'Metric': metrics, 'Value': values})
            fig = px.pie(chart_df, names='Metric', values='Value', title=create_title('Walk In Report'))
            fig.update_traces(
                textinfo='label+percent',
                textposition='inside',
                textfont=dict(
                    color='black',
                    family='Arial',
                    size=12
                )
            )
            fig.update_layout(
                title_text='Walk In ETBR',
                title_x=0.5,
                height=600,
                width=1000,
                uniformtext_minsize=12,
                uniformtext_mode='hide'
            )
            
            total = sum(values)
            description = f"""
            This pie chart shows the distribution of Walk-in enquiries across ETBR metrics.
            
            Total Walk-in ETBR: {total:.0f}
            Enquiries: {values[0]:.0f} ({values[0]/total*100:.1f}%)
            Test Drives: {values[1]:.0f} ({values[1]/total*100:.1f}%)
            Bookings: {values[2]:.0f} ({values[2]/total*100:.1f}%)
            Retails: {values[3]:.0f} ({values[3]/total*100:.1f}%)
            """
            
            return fig, description

        if selected_visualization == 'All Visualisations':
            # Create all visualizations
            viz_data = [
                create_etbr_report(),
                create_lmtd_etbr(),
                create_model_etbr(),
                create_enquiry_type_etbr(),
                create_enquiry_source_etbr(),
                create_team_etbr(),
                create_team_enquiry_type(),
                create_walk_in_etbr()
            ]
            
            # Create a layout with all visualizations and descriptions
            visualization_output = [
                html.Div([
                    dcc.Graph(figure=fig, style={'width': '100%', 'height': '600px'}),
                    html.Div(description, style={
                        'marginTop': '20px',
                        'marginBottom': '40px',
                        'padding': '15px',
                        'backgroundColor': '#f0f0f0',
                        'borderRadius': '5px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'fontSize': '14px',
                        'lineHeight': '1.5'
                    })
                ]) for fig, description in viz_data
            ]
        else:
            # Create the selected visualization
            if selected_visualization == 'ETBR Report':
                fig, description = create_etbr_report()
            elif selected_visualization == 'LMTD ETBR':
                fig, description = create_lmtd_etbr()
            elif selected_visualization == 'Model ETBR':
                fig, description = create_model_etbr()
            elif selected_visualization == 'Enquiry Type vs ETBR':
                fig, description = create_enquiry_type_etbr()
            elif selected_visualization == 'Enquiry Source vs ETBR':
                fig, description = create_enquiry_source_etbr()
            elif selected_visualization == 'Team vs Enquiry, Booking, Test Drive, Retail':
                fig, description = create_team_etbr()
            elif selected_visualization == 'Team vs Enquiry Type Report':
                fig, description = create_team_enquiry_type()
            elif selected_visualization == 'Walk In ETBR':
                fig, description = create_walk_in_etbr()
            else:
                fig, description = go.Figure(), "No visualization selected"

            visualization_output = [
                dcc.Graph(figure=fig, style={'width': '90vw', 'height': '600px'}),
                html.Div(description, style={
                    'marginTop': '20px',
                    'padding': '15px',
                    'backgroundColor': '#f0f0f0',
                    'borderRadius': '5px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'fontSize': '14px',
                    'lineHeight': '1.5',
                    'whiteSpace': 'pre-wrap'
                })
            ]

    return location_options, sales_manager_options, consultant_options, stored_data, retained_consultant, visualization_output, upload_message


# Layout for Page 2 (Visualization Page)
layout_page2 = html.Div([
    html.H1("Data Visualization", style={'textAlign': 'center'}),
    html.Div([
        dcc.Upload(
            id='page2-upload-data',
            children=html.Button('Upload File', style={'fontSize': '20px', 'width': '200px'}),
            multiple=False,
            style={'display': 'inline-block'}
        ),
        html.Div(id='page2-output-data-upload', style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'middle'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'justifyContent': 'center'}),
    dcc.Store(id='page2-stored-data'),
    html.Div(
        dcc.Dropdown(
            id='page2-visualization-dropdown',
            options=[
                {'label': 'Existing Vehicle Model', 'value': 'vehicle'},
                {'label': 'Product Family', 'value': 'family'},
                {'label': 'Followup Tracks', 'value': 'followup'}
            ],
            value='None',
            placeholder='Select Visualization',
            style={'width': '300px', 'fontSize': '16px', 'textAlign': 'left'}
        ),
        style={'textAlign': 'center', 'marginBottom': '20px'}
    ),
    html.Div(id='page2-conditional-dropdowns', style={'textAlign': 'center', 'display': 'flex', 'flexDirection': 'row', 'gap': '-1px', 'justifyContent': 'center'}),
    dcc.Graph(id='page2-selected-graph', style={'height': '600px', 'width': '80%', 'margin': '0 auto'}),
    html.Div(id='page2-visualization-description', style={'width': '80%', 'margin': '20px auto', 'textAlign': 'left', 'fontSize': '16px'}),
    html.Div(id='page2-error-message', style={'color': 'red', 'marginTop': '10px', 'textAlign': 'center'}),
    html.Div([
        html.Button("Go Back to Welcome Page", id="go-to-page1", n_clicks=0, 
                    style={'fontSize': '20px', 'margin': '20px'})
    ], style={'textAlign': 'center'})
])

# Main app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback for rendering page content
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/page2':
        return layout_page2
    else:
        return layout_page1

# Callbacks for navigation
@app.callback(Output('url', 'pathname'), Input('go-to-page2', 'n_clicks'))
def go_to_page2(n_clicks):
    if n_clicks > 0:
        return '/page2'
    return '/'

@app.callback(Output('url', 'pathname', allow_duplicate=True),
              Input('go-to-page1', 'n_clicks'),
              prevent_initial_call=True)
def go_to_page1(n_clicks):
    if n_clicks > 0:
        return '/'
    return dash.no_update

# Utility functions
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, 'Unsupported file type.'
        logger.info(f"File {filename} parsed successfully. Shape: {df.shape}")
        return df, 'Data uploaded successfully.'
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return None, f'There was an error processing this file: {str(e)}'

def create_vehicle_chart(df):
    df_count = df['Existing vehicle Latest1'].value_counts().reset_index()
    df_count.columns = ['Existing vehicle Latest1', 'Interested_Count']
    x_col = 'Existing vehicle Latest1'
    title = "Number of Interested Customers by Existing Vehicle Model"
    
    fig = px.bar(df_count, x=x_col, y='Interested_Count', title=title)
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title="Number of Interested Customers",
        height=600,
        width=4500
    )
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    
    return fig

def create_family_etbr(df):
    total_enquiries_df = df.groupby('Product Family').size().reset_index(name='Total_Enquiries')
    interested_df = df[df['Intrested In Exchange'] == True]
    interested_df = interested_df.groupby('Product Family').size().reset_index(name='Interested_Enquiries')
    merged_df = pd.merge(total_enquiries_df, interested_df, on='Product Family', how='left').fillna(0)
    melted_df = merged_df.melt(id_vars=['Product Family'], 
                               value_vars=['Total_Enquiries', 'Interested_Enquiries'],
                               var_name='Category', value_name='Count')
    fig = px.bar(
        melted_df,
        x='Product Family',
        y='Count',
        color='Category',
        barmode='group',
        title="Total Enquiries and Interested Enquiries by Product Family",
        labels={'Count': 'Number of Enquiries', 'Product Family': 'Product Family'},
        text='Count'
    )
    fig.update_layout(xaxis_title="Product Family", yaxis_title="Number of Enquiries", height=600, width=1000)
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    return fig

def create_followup_tracks(df, location=None, manager=None, consultant=None):
    if 'Completed Followup Count' not in df.columns:
        raise ValueError("'Completed Followup Count' column not found in the data.")
    
    # Apply filters
    if location:
        df = df[df['Dealer Location'] == location]
    if manager:
        df = df[df['Sales Manager'] == manager]
    if consultant:
        df = df[df['Sales Consultant'] == consultant]
    
    df_filtered = df[df['Completed Followup Count'].isin([0, 1])]
    
    groupby_column = 'Sales Consultant' if consultant else ('Sales Manager' if manager else ('Dealer Location' if location else 'Sales Consultant'))
    
    df_count = df_filtered.groupby([groupby_column, 'Completed Followup Count']).size().reset_index(name='Count')
    df_pivot = df_count.pivot(index=groupby_column, columns='Completed Followup Count', values='Count').fillna(0)
    df_pivot = df_pivot.reset_index().rename(columns={0: 'Followup_0', 1: 'Followup_1'})
    df_pivot['Total_Followups'] = df_pivot['Followup_0'] + df_pivot['Followup_1']
    df_melted = df_pivot.melt(id_vars=[groupby_column], value_vars=['Followup_0', 'Followup_1'], 
                              var_name='Followup_Status', value_name='Count')
    
    title_suffix = f"for {consultant}" if consultant else (f"by {groupby_column}")
    fig = px.bar(
        df_melted,
        x=groupby_column,
        y='Count',
        color='Followup_Status',
        barmode='group',
        title=f"Followup Tracks {title_suffix}",
        labels={'Count': 'Number of Followups', groupby_column: groupby_column, 'Followup_Status': 'Followup Status'},
        text='Count'
    )
    fig.update_layout(xaxis_title=groupby_column, yaxis_title="Number of Followups", height=600, width=1000)
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    return fig

def get_vehicle_description(df):
    total_customers = len(df)
    unique_models = df['Existing vehicle Latest1'].nunique()
    top_model = df['Existing vehicle Latest1'].value_counts().index[0]
    return f"This graph shows the distribution of interested customers across different existing vehicle models. There are {total_customers} total customers interested in an exchange, spread across {unique_models} unique vehicle models. The most common existing vehicle model is '{top_model}'."

def get_family_description(df):
    total_enquiries = df['Product Family'].count()
    interested_enquiries = df[df['Intrested In Exchange'] == True]['Product Family'].count()
    top_family = df['Product Family'].value_counts().index[0]
    return f"This graph compares the total enquiries and interested enquiries for each product family. Out of {total_enquiries} total enquiries, {interested_enquiries} showed interest in an exchange. The product family with the most enquiries is '{top_family}'."

def get_followup_description(df, location, manager, consultant):
    total_followups = len(df)
    called_once = df[df['Completed Followup Count'] == 1].shape[0]
    called_at_least_once = df[df['Completed Followup Count'] >= 1].shape[0]
    not_called = df[df['Completed Followup Count'] == 0].shape[0]
    call_rate = (called_at_least_once / total_followups) * 100 if total_followups > 0 else 0
    
    filter_text = f"Location: {location}, " if location else ""
    filter_text += f"Manager: {manager}, " if manager else ""
    filter_text += f"Consultant: {consultant}" if consultant else ""
    filter_text = filter_text.rstrip(", ")
    
    if filter_text:
        description = f"This graph shows the followup tracks for {filter_text}. "
    else:
        description = "This graph shows the overall followup tracks. "
    
    description += f"Out of {total_followups} total followups, {called_once} have been called at least once, "
    description += f"{not_called} have not been called yet, "
    description += f"resulting in a call rate of {call_rate:.2f}%. "
    description += "The 'Followup_1' bar represents customers who have been called at least once, "
    description += "while 'Followup_0' represents customers who haven't been called yet. "
    description += "The 'Total_Followups' bar shows the total number of customers in each category."
    
    return description

@app.callback(
    Output('page2-conditional-dropdowns', 'children'),
    Input('page2-visualization-dropdown', 'value')
)
def update_dropdowns(selected_viz):
    if selected_viz == 'followup':
        return [
            dcc.Dropdown(
                id={'type': 'page2-dynamic-dropdown', 'index': 'location'}, 
                placeholder='Select Location', 
                style={'width': '100%', 'margin': '0', 'padding': '0'}
            ),
            dcc.Dropdown(
                id={'type': 'page2-dynamic-dropdown', 'index': 'manager'}, 
                placeholder='Select Sales Manager', 
                style={'width': '100%', 'margin': '0', 'padding': '0'}
            ),
            dcc.Dropdown(
                id={'type': 'page2-dynamic-dropdown', 'index': 'consultant'}, 
                placeholder='Select Sales Consultant', 
                style={'width': '100%', 'margin': '0', 'padding': '0'}
            )
        ]
    return []

@app.callback(
    [Output('page2-output-data-upload', 'children'),
     Output('page2-selected-graph', 'figure'),
     Output('page2-error-message', 'children'),
     Output('page2-stored-data', 'data'),
     Output('page2-visualization-description', 'children')],
    [Input('page2-upload-data', 'contents'),
     Input('page2-visualization-dropdown', 'value'),
     Input({'type': 'page2-dynamic-dropdown', 'index': ALL}, 'value')],
    [State('page2-upload-data', 'filename'),
     State('page2-stored-data', 'data')]
)
def update_output(upload_contents, selected_viz, dynamic_values, filename, stored_data):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    fig = go.Figure()
    error_message = ''
    description = ''

    if upload_contents is None and stored_data is None:
        return 'No data uploaded yet.', fig, '', None, ''

    if triggered_id == 'page2-upload-data':
        df, message = parse_contents(upload_contents, filename)
        if df is None:
            return message, fig, message, None, ''
        stored_data = df.to_json(date_format='iso', orient='split')
    elif stored_data:
        df = pd.read_json(stored_data, orient='split')
    else:
        return 'No data available.', fig, 'Please upload data first.', None, ''

    try:
        if selected_viz == 'vehicle':
            fig = create_vehicle_chart(df)
            description = get_vehicle_description(df)
        elif selected_viz == 'family':
            fig = create_family_etbr(df)
            description = get_family_description(df)
        elif selected_viz == 'followup':
            location = dynamic_values[0] if len(dynamic_values) > 0 else None
            manager = dynamic_values[1] if len(dynamic_values) > 1 else None
            consultant = dynamic_values[2] if len(dynamic_values) > 2 else None
            fig = create_followup_tracks(df, location, manager, consultant)
            description = get_followup_description(df, location, manager, consultant)

        logger.info(f"Visualization {selected_viz} created successfully")
    except Exception as e:
        error_message = f"Error creating visualization: {str(e)}"
        logger.error(error_message)

    return 'Data processed successfully.', fig, error_message, stored_data, description

@app.callback(
    Output({'type': 'page2-dynamic-dropdown', 'index': 'location'}, 'options'),
    [Input('page2-upload-data', 'contents'),
     Input('page2-visualization-dropdown', 'value')],
    State('page2-upload-data', 'filename')
)
def update_location_options(upload_contents, selected_viz, filename):
    if selected_viz != 'followup' or upload_contents is None:
        return []

    df, _ = parse_contents(upload_contents, filename)
    if df is None:
        return []

    locations = df['Dealer Location'].unique()
    return [{'label': loc, 'value': loc} for loc in locations]

@app.callback(
    Output({'type': 'page2-dynamic-dropdown', 'index': 'manager'}, 'options'),
    [Input({'type': 'page2-dynamic-dropdown', 'index': 'location'}, 'value'),
     Input('page2-upload-data', 'contents'),
     Input('page2-visualization-dropdown', 'value')],
    State('page2-upload-data', 'filename')
)
def update_manager_options(selected_location, upload_contents, selected_viz, filename):
    if selected_viz != 'followup' or upload_contents is None:
        return []

    df, _ = parse_contents(upload_contents, filename)
    if df is None:
        return []

    if selected_location:
        df = df[df['Dealer Location'] == selected_location]
    
    managers = df['Sales Manager'].unique()
    return [{'label': mgr, 'value': mgr} for mgr in managers]

@app.callback(
    Output({'type': 'page2-dynamic-dropdown', 'index': 'consultant'}, 'options'),
    [Input({'type': 'page2-dynamic-dropdown', 'index': 'manager'}, 'value'),
     Input({'type': 'page2-dynamic-dropdown', 'index': 'location'}, 'value'),
     Input('page2-upload-data', 'contents'),
     Input('page2-visualization-dropdown', 'value')],
    State('page2-upload-data', 'filename')
)
def update_consultant_options(selected_manager, selected_location, upload_contents, selected_viz, filename):
    if selected_viz != 'followup' or upload_contents is None:
        return []

    df, _ = parse_contents(upload_contents, filename)
    if df is None:
        return []

    if selected_location:
        df = df[df['Dealer Location'] == selected_location]
    if selected_manager:
        df = df[df['Sales Manager'] == selected_manager]
    
    consultants = df['Sales Consultant'].unique()
    return [{'label': cons, 'value': cons} for cons in consultants]

if __name__ == '__main__':
    app.run_server(debug=True)