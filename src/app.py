# Add Needed Libraries
# For creating and managing datasets
import numpy as np
import pandas as pd

# For getting data from websites, so they can be put into a dataframe
from bs4 import BeautifulSoup
import requests
from io import StringIO

# For creating the visualizations for this project
# import matplotlib.pyplot as plt
import dash
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px


# Create the website to show all of these graphs
# First we create the dash app for everything to go into
app = Dash(__name__, use_pages=True)
server = app.server
app.title = "TF2 Map Analysis"
app._favicon = ("favicon.ico")

# Set the layout for the header bar of the site and create the links to the other pages
app.layout = html.Div(
    children=[
        # Create the header part of the page
        html.Div(
            className="headerBanner",
            children=[
                html.Img(className="headerLogo", src="assets/TF2Logo.png"),
                html.P(),
                html.Div(
                    className="headerLinksParent",
                    children=[
                        html.Div(
                            className="headerLink",
                            children=[dcc.Link(f"{page['name']}", href=page["relative_path"])]
                        ) for page in dash.page_registry.values()
                    ]
                )
                # html.A("Charts ", href=""),
                # html.A("Findings Overview", href="assets/findings.html"),
                # html.A("Sources", href="assets/sources.html")
            ]
        ),

        dash.page_container
    ]
)

# Run the website
app.run_server(debug=True)
