import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px

dash.register_page(__name__)

layout = html.Div([
    html.Div(
        className="pageBody",
        children=[
            html.H1("Data Sources"),
            html.H3("Map List Tables"),
            html.P("TF2 Wiki"),
            html.Ul(className="normalText", children=[
                html.Li("Basic map information was taken from the following sources"),
                html.Ul(className="normalText", children=[
                    html.Li(html.A("https://wiki.teamfortress.com/wiki/List_of_maps", href="https://wiki.teamfortress.com/wiki/List_of_maps")),
                    html.Li(html.A("https://wiki.teamfortress.com/wiki/Christmas_map", href="https://wiki.teamfortress.com/wiki/Christmas_map")),
                    html.Li(html.A("https://wiki.teamfortress.com/wiki/Halloween_map", href="https://wiki.teamfortress.com/wiki/Halloween_map")),
                    html.Li(html.A("https://wiki.teamfortress.com/wiki/Water", href="https://wiki.teamfortress.com/wiki/Water")),
                ]),
                html.Li("Information was condensed into a single Excel file (that way I can properly add the size values with the rest of the data)"),
                html.Li("Did opt to use web scraping to ensure as few spelling mistakes and typos as possible"),
                html.Li("While the water map list was not used in final results, still including it for documentation")
            ]),  # end of list
            html.Br(),
            html.H3("Map Size Gathering Method"),
            html.P("Uncle Dane"),
            html.Ul(className="normalText", children=[
                html.Li(html.A("https://www.youtube.com/watch?v=I9ieN1ACfP4", href="https://www.youtube.com/watch?v=I9ieN1ACfP4")),
                html.Li("Description mentions that the conversion method from hammer units to kilometers was incorrect, description did link a pastebin with correct values"),
                html.Li("If anyone wants to see these values in game, I would recommend using the command nav_flood_select to ensure that the nav mesh is both generated, and is selecting the whole map"),
                html.Li("Keep in mind that some maps are divided into separate chunks, meaning that you may need to repeat the selection and size gathering process a few times to get the total size of the map"),
                html.Li("This does have a limitation in where if a map is unable to generate a nav mesh for any reason, it will not give you a size number to work with, there is a small handful of maps that have this issue (Refer to the Map Size Comparison By Game Mode chart to see which maps do not generate a nav mesh)")
            ]),  # end of list
            html.Br(),
            html.H3("Hammer Units To Kilometers Conversion Method"),
            html.Ul(className="normalText", children=[
                html.Li("Initial research lead to no single way to convert hammer units to normal measurements, sizes can apparently vary from game to game and I could not find a straight forward answer for TF2"),
                html.Li("Opted to use the following pastebin link mentioned in the description of Uncle Dane's video on map sizes"),
                html.Ul(className="normalText", children=[html.Li(html.A("https://pastebin.com/rwXevdPs", href="https://pastebin.com/rwXevdPs"))]),
                html.Li("Pastebin file only shows the before and after conversion numbers, does not show conversion method."),
                html.Li("Deduced that the conversion method is the following (May be incorrect, will need to do additional research to verify this):"),
                html.Ul(className="normalText", children=[html.Li("Hu^2 / 27.5926 = km^2")])
            ]),  # end of list
        ]  # end of page body
    )
])
