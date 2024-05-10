import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px

dash.register_page(__name__)

layout = html.Div([
    html.Div(
        className="pageBody",
        children=[
            html.H1("OverView Of Data"),
            html.P("Note that the following are just the points and conclusions I have made, you are welcome to come to your own conclusions regarding this dataset and its meaning."),
            html.H3("The most amount of maps added was in 2023"),
            html.Ul(className="normalText", children=[
                html.Li("In 2023, a grand total of 36 maps were added to the game"),
                html.Li("All of these maps were community made"),
                html.Li("Over half of these maps (52.77%) were holiday themed")
            ]),  # end of list
            html.P(),
            html.H3("There is a noticeable spike in maps made in 2015"),
            html.Ul(className="normalText", children=[
                html.Li("This year included the following updates: Gun Mettle, Invasion, Scream Fortress 7, and Tough Break"),
                html.Li("Out of the 20 maps added this year, only 4 of them were Halloween themed"),
                html.Li("This year is the year with the second most amount of maps made by the community")
            ]),  # end of list
            html.P(),
            html.H3("Valve Made More Arena Maps Than The Community"),
            html.Ul(className="normalText", children=[
                html.Li("This stands as the only game mode where Valve is in the lead in terms of maps made (7 maps compared to 5 maps), not including game modes were there are no community developers"),
                html.Li("Almost every other game mode has the community in the lead in terms of maps made"),
                html.Li("Arena also takes lead in the fact that it contains the smallest maps in the game (The smallest map currently being Offblast)")
            ]),  # end of list
            html.P(),
            html.H3("There is a decent % of maps made for holiday events"),
            html.Ul(className="normalText", children=[
                html.Li("In total, 39.72% of maps currently in the game are holiday themed."),
                html.Li("There are 3 years that just have holiday themed maps added to them: 2018, 2019, 2022"),
                html.Li("The only years where holiday themed maps were not added were in 2008 and 2017"),
                html.Li("Christmas maps were introduced to the game starting in 2020")
            ]),  # end of list
            html.P(),
            html.H3("There are only two years where community maps were not added to the game"),
            html.Ul(className="normalText", children=[
                html.Li("No community-made maps were added in 2008 and 2014"),
                html.Li("Updates in 2014 include the following: End of the Line, Scream Fortress 6, Love & War"),
                html.Li("It should be noted that the End of the Line update was supposed to have a map added to it, but was moved back to another update"),
                html.Li("It should also be noted that 2008 was the year the game was launched, meaning that since then, the community has been creating maps and having them be added to the game")
            ])  # end of list
        ]  # end of main page body
    )
])
