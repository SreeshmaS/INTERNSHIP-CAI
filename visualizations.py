import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import io
import base64

app = dash.Dash(__name__)
server=app.server
app.layout = html.Div([
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Button('Upload File', style={'fontSize': '20px', 'width': '200px'}),
            multiple=False,
            style={'display': 'inline-block'}
        ),
        html.Div(id='output-data-upload', style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'middle'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
    dcc.Store(id='stored-data'),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='visualization-dropdown',
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
                id='location-dropdown',
                placeholder='Select Location',
                style={'width': '200px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Dropdown(
                id='sales-manager-dropdown',
                placeholder='Select Sales Manager',
                style={'width': '350px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Dropdown(
                id='consultant-dropdown',
                placeholder='Select Sales Consultant',
                style={'width': '350px', 'fontSize': '16px', 'textAlign': 'left'}
            )
        ], style={'display': 'inline-block'})
    ], style={'textAlign': 'left'}),
    html.Div(id='visualization-container')
])

@app.callback(
    [Output('location-dropdown', 'options'),
     Output('sales-manager-dropdown', 'options'),
     Output('consultant-dropdown', 'options'),
     Output('stored-data', 'data'),
     Output('consultant-dropdown', 'value'),
     Output('visualization-container', 'children'),
     Output('output-data-upload', 'children')],
    [Input('upload-data', 'contents'),
     Input('visualization-dropdown', 'value'),
     Input('sales-manager-dropdown', 'value'),
     Input('consultant-dropdown', 'value'),
     Input('location-dropdown', 'value')],
    [State('upload-data', 'filename'),
     State('stored-data', 'data')]
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
            
            Total ETBR: {total:.0f}
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

if __name__ == '__main__':
    app.run_server(debug=True)
