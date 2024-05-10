# Add Needed Libraries
# For creating and managing datasets
import numpy as np
import pandas as pd

# For getting data from websites, so they can be put into a dataframe
from bs4 import BeautifulSoup
import requests
from io import StringIO

import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px

dash.register_page(__name__, path='/')

# Options here allow me to see the dataset without any truncating in PyCharm
pd.options.display.width = None
pd.options.display.max_columns = None
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)

# Import Excel sheet into dataframe, separating each sheet into its own frame
excelFile = pd.ExcelFile(r"dataSource\TF2MapData.xlsx")
origData = pd.read_excel(excelFile, "MainMapData")
waterData = pd.read_excel(excelFile, "WaterMapData")
eventData = pd.read_excel(excelFile, "EventMapList")

# print(origData.head())
# print(origData.info())

# Set the NativeNavmesh column to be a boolean and change the values as needed
# origData["NativeNavmesh"].replace("Yes", "True", inplace=True) # While this still works, Pandas is apparently trying to phase this out, use below method instead
origData["NativeNavmesh"] = origData["NativeNavmesh"].replace("Yes", True)
origData["NativeNavmesh"] = origData["NativeNavmesh"].replace("No", False)
# print(origData["NativeNavmesh"].head())
origData["NativeNavmesh"] = origData["NativeNavmesh"].astype(bool)
# print(origData["NativeNavmesh"].info())

# Realized that I kept a space in the column Map Name, so lets go ahead and remove that space for ease of use later
origData.rename(columns={"Map Name": "MapName"}, inplace=True)

# With the Excel sheet completed, now we shall extract the same data, but this time via web scraping
# urlData = requests.get("https://wiki.teamfortress.com/wiki/List_of_maps").text

# Since we saved the contents of the html file to a text file, we will load those now
urlRawText = open("wikiHtmlText.txt", "r", encoding="utf-8")
urlData = urlRawText

# print(urlData)
mapSoup = BeautifulSoup(urlData, "html.parser")
# print(mapSoup)

# To avoid issues where the site is down, we will save the results of urlData to a text file and use this in future cases
# In other words, once this finishes, this will stay commented
# urlRawText = open("wikiHtmlText.txt", "w", encoding="utf-8")
# urlRawText.write(str(mapSoup))
# urlRawText.close()

# Get the table we need
# Page has 3 tables, table we need has the following class on the table object: wikitable sortable grid jquery-tablesorter
# Looking at the raw soup output, the class is actually just wikitable sortable grid
# soupTable = mapSoup.find("table", {"class" : "wikitable sortable grid jquery-tablesorter"})
soupTable = mapSoup.find("table", class_="wikitable sortable grid")
# print(soupTable)
# print(type(soupTable))

# Convert the soup into a dataframe
soupFrame = pd.read_html(StringIO(str(soupTable)))[
    0]  # On its own, this command will give a deprecation warning, so we need to add and use StringIO to this as well
# Remove the extra column it added
soupFrame.drop(columns="Unnamed: 0", inplace=True)
# Rename the developers column to remove the ()
soupFrame.rename(columns={"Developer(s)": "Developers"}, inplace=True)

# Date Added is stored as an object data type, we need to change this
# First we need to change all instance of Launch to the actual launch date (October 10, 2007)
soupFrame["Date added"] = soupFrame["Date added"].replace("Launch", "October 10, 2007")
# We also need to remove the word patch from each row
for x in soupFrame.index:
    # soupFrame["Date added"][x] = soupFrame["Date added"][x].replace("Patch", "")  # works but throws a warning error
    soupFrame.loc[x, "Date added"] = soupFrame.loc[x, "Date added"].replace("Patch", "")

# Now we convert the column to the date data type
soupFrame["Date added"] = soupFrame["Date added"].astype('datetime64[ns]')
# print(soupFrame.info())
# print(soupFrame.head())

# To minimize the chance of there being a spelling mistake or incorrect data, we will append the Mapsize and Navmesh columns from the Excel sheet to the web dataframe, making a new main dataset to work with
# mainData = pd.concat([soupFrame, origData[["MapSize(kHu^2)", "NativeNavmesh"]]], axis=1)
# mainData = origData.set_index("MapFileName").join(soupFrame.set_index("File name"))
mainData = origData.merge(soupFrame, left_on="MapFileName", right_on="File name")

# To test and make sure the values are properly set and not out of order, show a specific section of the table
# print(mainData[mainData["Game mode"].isin(["Control Point"])])

# Merge worked, but now we have duplicate columns, so we need to remove that
# We'll remove the text and date columns from the origData set and then re-arrange the rest to be in a semi-logical fashion
# print(list(mainData.columns.values))
mainData.drop(columns=['MapName', "MapFileName", "GameMode", "DateAdded(MM/DD/YYYY)", "Developers_x"], inplace=True)
mainData.rename(columns={"Developers_y": "Developers"}, inplace=True)
mainData = mainData[["Map", "File name", "Game mode", "Date added", "Developers", "MapSize(kHu^2)", "NativeNavmesh"]]
# print(mainData.head())
# print(mainData.info())


# With the data nice and set up now, we can actually begin the analysis process
# To start, we will create a figure to place all of our graphs and visualizations on to keep everything in one place for now
# fig, ax = plt.subplots(2, 2)

# Question 1: What is the ratio between Valve made maps and community maps?
# To start with this, we need a way to separate which maps are made by the community and which ones are made by Valve
# valveMaps = mainData[mainData["Developers"].isin(["Valve", "Valve Bad Robot Escalation Studios"])]  # Works, but hard-coded way of going about this
# s = df.stack().str.contains('<',na=False)
# output_indices = s[s].index
valveMaps = mainData[mainData["Developers"].str.contains("Valve", na=False)]
valveMaps = valveMaps.reset_index()
communityMaps = mainData[~mainData["Developers"].str.contains("Valve", na=False)]
communityMaps = communityMaps.reset_index()

# print("Since the launch of the game Valve has created " + str(len(valveMaps.index)) + " maps while the community has created " + str(len(communityMaps.index)) + " maps (Not including maps that have yet to be added in a official capacity)")
# print("Meaning that out of the current 183 maps, valve has made " + "{:.2f}".format(len(valveMaps.index) / len(mainData.index) * 100) + "% of the total maps, while the community made " + "{:.2f}".format(len(communityMaps.index) / len(mainData.index) * 100) + "% of the total maps")
# To better show the results here, we are going to use a simple pie chart
# Creating a function that allows us to see both the % of maps made and the total number for both sides
# def ShowPieChartTotalValue(values):
#    def PieChartFormat(pct):
#        total = sum(values)
#        val = int(round(pct * total / 100.0))
#        return "{:.1f}%\n({v:d})".format(pct, v=val)

#    return PieChartFormat

# Actually create the pie chart
# Creating the chart in matplot lib at first since that is what I first started with
# ax[0, 0].pie(np.array([str(len(valveMaps.index)), str(len(communityMaps.index))]),
#              labels=["Valve Made Maps", "Community Made Maps"], colors=["#B8383B", "#5885A2"],
#              autopct=ShowPieChartTotalValue(np.array([len(valveMaps.index), len(communityMaps.index)])))
# ax[0, 0].set(title="% Of Maps Made By Valve And The Community")

# Creating the chart in plotly since that is what I'll be making the dashboard on
# First store the data for the chart
totalCountData = {"MapCount": [str(len(valveMaps.index)), str(len(communityMaps.index))],
                  "Type": ["Valve Maps", "Community Maps"]}
totalMapFrame = pd.DataFrame(data=totalCountData)
# print(totalMapFrame.head())

# Then make the chart itself
chart1 = px.pie(totalMapFrame,
                values="MapCount",
                names="Type",
                title="% of Maps Made by the Community and Valve",
                color="Type",
                color_discrete_map={"Valve Maps": "#B8383B", "Community Maps": "#5885A2"})
chart1.update_traces(textposition="inside", textinfo="percent+label")
# chart1.update_layout({"plot_bgcolor": "rgba(51, 51, 51, 255)", "plot_bgcolor": "rgba(51, 51, 51, 255)"})
chart1.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), font_family="TF2")
# chart1.show()


# Question 2: how many maps were added per year? How many of those maps are community made
# Best approach of this will be a stacked bar chart, x being the year, y being the total amount of maps made
# Try to add a way that allows the user to see the number of maps made by Valve, community, and the combined total all-in-one chart (May need to be to have an interactive feature that shows this as you hover the cursor over the bar)

# To start simple, lets just get the total amount of maps added per year regardless of developer
# Get the years ready to be charted
# MapYears = mainData["Date added"].dt.year
# MapYears = MapYears.drop_duplicates()
# MapYears = MapYears.astype(
#     "string")  # We convert this to string as this prevents matplotlib for trying to add un-needed decimal places and skip numbers
# MapYears = MapYears.sort_values()
# # print(MapYears)
#
# # Get how many maps were made per year
# MapCount = mainData["Date added"].dt.year.value_counts()
# MapCount = MapCount.sort_index()
# # print(MapCount)
#
# # Make the chart itself
# # plt.figure(figsize=(10, 6))
# # plt.bar(MapYears, MapCount)
# # plt.title("TF2 Maps Added Per Year")
# # plt.xlabel("Year")
# # plt.ylabel("Number of maps added")
# # plt.show()
# # plt.close()
#
# # With the basic plot, now to do the same thing, but create a stacked chart showing how many maps were made by the community
# # We'll keep the MapYears variable as that can still be used here
# # First we get the amount of maps made by the community
# CommMapCount = communityMaps["Date added"].dt.year.value_counts()
# CommMapCount = CommMapCount.sort_index()
# # The following steps are used to prevent a shape size error (Both series need to have the same year count otherwise it throws an error)
# # Idea here is to add the original map size value to a temporary variable, then update the main variable and remove the extra numbers added by the original count
# TempSeries = CommMapCount + MapCount
# CommMapCount = TempSeries - MapCount
# CommMapCount = CommMapCount.fillna(0)
#
# # We repeat the previous steps for Dev maps
# DevMapCount = valveMaps["Date added"].dt.year.value_counts()
# DevMapCount = DevMapCount.sort_index()
# TempSeries = DevMapCount + MapCount
# DevMapCount = TempSeries - MapCount
# DevMapCount = DevMapCount.fillna(0)
# # DevMapCount = DevMapCount.rename(columns={""})
# # print(DevMapCount)
# # print(CommMapCount)
#
# # Then we make the chart itself
# # ax[0, 1].bar(MapYears, DevMapCount, color="#B8383B", label="Valve Made Maps")
# # ax[0, 1].bar(MapYears, CommMapCount, bottom=DevMapCount, color="#5885A2", label="Community Made Maps")
# # ax[0, 1].set(xlabel="Year", ylabel="Number of maps added", title="TF2 Maps Added Per Year")
# # ax[0, 1].grid(axis="y")
# # ax[0, 1].legend()
#
# # Re-creating the chart in plotly since that is what we are going to be masking the dashboard on
# # First to keep everything on the same dataframe, we are going to combine both dataframes into one
# MapDataPerYear = {"Date Added": MapYears.values, "Valve Maps": DevMapCount.values,
#                   "Community Maps": CommMapCount.values, "Total Maps": DevMapCount.values + CommMapCount.values}
# MapsPerYear = pd.DataFrame(data=MapDataPerYear)
# # print(MapsPerYear)
#
# # Let's also create a line to mark the average amount of maps created per year
# avgMaps = MapsPerYear["Total Maps"].mean()
# avgValve = MapsPerYear["Valve Maps"].mean()
# avgCommunity = MapsPerYear["Community Maps"].mean()
#
# # Create the chart itself
# chart2 = px.bar(MapsPerYear,
#                 x="Date Added",
#                 y=["Valve Maps", "Community Maps"],
#                 color_discrete_map={"Valve Maps": "#B8383B", "Community Maps": "#5885A2"},
#                 title="Number of Maps Added Per Year")
# # Create the lines that mark the average amount of maps
# chart2.add_hline(y=avgMaps, line_dash="dash", line_color="#CF7336", annotation_text="Average Maps Per Year (Total)",
#                  annotation_position="top left")
# chart2.add_hline(y=avgValve, line_dash="dash", line_color="#B8383B", annotation_text="Average Maps Per Year (Valve)",
#                  annotation_position="top left")
# chart2.add_hline(y=avgCommunity, line_dash="dash", line_color="#5885A2",
#                  annotation_text="Average Maps Per Year (Community)", annotation_position="top left")
# chart2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"),
#                      font_family="TF2")
# chart2.update_yaxes(title_text="Maps Added")
# chart2.show()

# Wanted to create a newer version of this chart using what I have learned from later charts, with the goal of allowing the user to filter this chart by game mode
# Will still keep the process of this older chart here, for documentation and in case I mess up really badly
# Get the data we need
MapPerYearData = mainData[["Map", "Game mode", "Date added", "Developers"]].copy()
MapPerYearData["Date added"] = MapPerYearData["Date added"].dt.year
MapPerYearData["Community"] = True
MapPerYearData.loc[MapPerYearData["Developers"].str.contains("Valve", na=False), "Community"] = False

# This will be moved to the callback section, so we can freely tamper with it
# GroupedData = MapPerYearData.copy()
# #GroupedData = GroupedData.loc[test1["Game mode"] == "Capture the Flag"]
# GroupedData = GroupedData.groupby(["Date added", "Community"], as_index=False).count()
# GroupedData = GroupedData.drop(columns=["Game mode", "Developers"])
# # print(GroupedData.head())
#
# chart2 = px.bar(GroupedData,
#                 x="Date added",
#                 y="Map",
#                 color="Community",
#                 color_discrete_map={False: "#B8383B", True: "#5885A2"},
#                 title="Number of Maps Added Per Year"
#                 )
# # testChart.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"), font_family="TF2")
# chart2.update_layout(xaxis={"dtick": 1})
# chart2.update_yaxes(title_text="Maps Added")
# legendNames = {"False": "Valve Maps", "True": "Community Maps"}
# chart2.for_each_trace(lambda t: t.update(name=legendNames[t.name],
#                                          legendgroup=legendNames[t.name],
#                                          hovertemplate=t.hovertemplate.replace(t.name, legendNames[t.name])
#                                          )
#                       )
# chart2.show()


# Question 3: Check Game Mode Map Count Correlation Between Community And Valve, Is There A Game Mode Where One Surpasses The Other?
# I would say the best way of going about this would be an interactive Pie Chart, show the total amount of maps and the % between the two
# It would also need some functionality to allow the user to change which Game Mode is in focus (Either that or we make like 10 different charts)
# Due to the fact that this chart requires it to be interactive, Matplotlib on its wont be enough (Technically there is a way, but it won't look good)
# For this chart, we'll attempt to make it using Plotly and Dash

# For the sake of testing, I'll also be making a chart in locally just to make sure I have the logic down
gameModeData = mainData[["Game mode", "Developers"]].copy()
gameModeData["Community"] = True
# TempFrame["Community"].loc[TempFrame["Developers"].str.contains("Valve", na=False)] = True #Works but throws a few errors in the console
gameModeData.loc[gameModeData["Developers"].str.contains("Valve", na=False), "Community"] = False
gameModeData.rename(columns={"Game mode": "GameMode"}, inplace=True)
# print(gameModeData.head())
# print([gameModeData[gameModeData.Community == True].shape[0], gameModeData[gameModeData.Community == False].shape[0]])
# Valve has 4 ctf maps while comm has 11 maps (15)
# print(len(gameModeData.loc[(gameModeData.Community == False) & (gameModeData.GameMode == "Capture the Flag")]))
# Test it in matplot lib to make sure everything works
# ax[1, 0].pie([len(gameModeData.loc[(gameModeData.Community == False) & (gameModeData.GameMode == "Capture the Flag")]),
#              len(gameModeData.loc[(gameModeData.Community == True) & (gameModeData.GameMode == "Capture the Flag")])],
#             autopct="%1.0f%%")
# ax[1, 0].pie(np.array([str(len(valveMaps.index)), str(len(communityMaps.index))]), labels=["Valve Made Maps", "Community Made Maps"], colors=["#B8383B", "#5885A2"])
# communityMaps = mainData[~mainData["Developers"].str.contains("Valve", na=False)]

# Create a dataframe to store this information properly
# typeCountData = {"MapCount": [
#    len(gameModeData.loc[(gameModeData.Community == False) & (gameModeData.GameMode == "Capture the Flag")]),
#    len(gameModeData.loc[(gameModeData.Community == True) & (gameModeData.GameMode == "Capture the Flag")])],
#    "Type": ["Valve Maps", "Community Maps"]}
# typeCountFrame = pd.DataFrame(data=typeCountData)
# print(tempFrame.head())

# Create the test chart in plotly
# chart3 = px.pie(typeCountFrame,
#                 values="MapCount",
#                 names="Type",
#                 title="% of Maps Made by the Community and Valve in Specific Game Modes",
#                 color="Type",
#                 color_discrete_map={"Valve Maps": "#B8383B", "Community Maps": "#5885A2"})
# chart3.update_traces(textposition="inside", textinfo="percent+label")
# chart3.show()
# This chart will be used in the dash website section, so it will be commented out here


# Question 4: Is there a noticeable difference in map sizes between Community and Valve
# Idea here is to have 3 bar charts, showing average map size, max map size, and min map size per game mode per developer

# First grab the data we require
# We will need the map name, game mode, developers, and map size (in both hammer units and in a normal unit of measure)
mapSizeFrame = mainData[["Map", "Game mode", "Developers", "MapSize(kHu^2)"]].copy()
# Change the column name for Game mode to use no spaces
mapSizeFrame = mapSizeFrame.rename(columns={"Game mode": "GameMode"})
# Add a column to quickly tell if a map is community made or not
mapSizeFrame["Community"] = True
mapSizeFrame.loc[gameModeData["Developers"].str.contains("Valve", na=False), "Community"] = False
# Add a column that converts the map size in hammer units to km
# First before we can do any calculations, we need to take care of the null values found here
# For the sake of ease, given how maps vary in size from game modes, we will opt to remove these maps for now
mapSizeFrame.dropna(inplace=True)
# According to the pastebin link left in Uncle Dane's video, the conversion rate appears to be Hu^2 / 27.5926 = km^2
mapSizeFrame["MapSize(km^2)"] = mapSizeFrame["MapSize(kHu^2)"] / 27.5926
# print(mapSizeFrame.head())
# print(mapSizeFrame.info())
# print(mapSizeFrame["MapSize(kHu^2)"].mean())
# print(mapSizeFrame["MapSize(kHu^2)"].min())
# print(mapSizeFrame["MapSize(kHu^2)"].max())

# We will start with the average map size per game mode per developer
# Chart will be a grouped bar chart, with the game modes on the x-axis, and the average map size on the y-axis
# We will create a new data frame to store all the values into
# This new frame will have the different game modes at the primary key, with the other 3 columns being the average, max value, and min value
# First we will get a list of all game modes to check
gameModeList = mapSizeFrame["GameMode"]
gameModeList.drop_duplicates(inplace=True)
# There are a few game modes that don't really matter here (Mainly the training mode and test maps), so for the sake of making the chart easier to read, we shall remove them
gameModeList = gameModeList[gameModeList != "Test"]
gameModeList = gameModeList[gameModeList != "Training Mode"]
# gameModeList = gameModeList.reset_index()
gameModeList = gameModeList.to_numpy()
# print(gameModeList)

# To test to make sure we have the proper method down, print out a few average values, start with getting all maps of a game mode, then start filtering by developers
# print(mapSizeFrame["MapSize(kHu^2)"].loc[mapSizeFrame["GameMode"] == "Capture the Flag"].mean())  # Average size of all maps of this game mode
# print(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == "Capture the Flag") & (~mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())  # Average size of all community of this game mode
# print(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == "Capture the Flag") & (mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())  # Average size of all valve of this game mode

# Initialize the row names for the dataframe
GameModeName = []
AllMap = []
ValveMap = []
CommMap = []
AllMapK = []
ValveMapK = []
CommMapK = []

# Loop through game modes calculating the average size of all maps per game mode
for x in gameModeList:
    # gameMode = gameModeList[x]
    # print(gameModeList[x])
    GameModeName.append(x)
    AllMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[mapSizeFrame["GameMode"] == x].mean())
    ValveMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())
    CommMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())
    AllMapK.append(mapSizeFrame["MapSize(km^2)"].loc[mapSizeFrame["GameMode"] == x].mean())
    ValveMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())
    CommMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].mean())
    # Note that if there are no developers of a type in a game mode (I.E. no community MVM maps have been added), the value will be nan, we will need to address that before making the chart

# Store the results in a dictionary, that way we can easily add them to a dataframe
GameModeDictionary = {"GameMode": GameModeName,
                      "AllMapsSize": AllMap,
                      "ValveMapsSize": ValveMap,
                      "CommunityMapsSize": CommMap,
                      "AllMapsSizeK": AllMapK,
                      "ValveMapsSizeK": ValveMapK,
                      "CommunityMapsSizeK": CommMapK}
# Create and clean the dataframe, removing all null values and replacing them with 0s
MapAverageFrame = pd.DataFrame(GameModeDictionary)
MapAverageFrame = MapAverageFrame.fillna(0)
# print(MapAverageFrame)

# Repeat the process again, creating new dataframes for the max and min values
# Reset the list values
GameModeName = []
AllMap = []
ValveMap = []
CommMap = []
AllMapK = []
ValveMapK = []
CommMapK = []

# Starting with the min values
for x in gameModeList:
    # gameMode = gameModeList[x]
    # print(gameModeList[x])
    GameModeName.append(x)
    AllMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[mapSizeFrame["GameMode"] == x].min())
    ValveMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].min())
    CommMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].min())
    AllMapK.append(mapSizeFrame["MapSize(km^2)"].loc[mapSizeFrame["GameMode"] == x].min())
    ValveMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].min())
    CommMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].min())

# Store the results in a dictionary, that way we can easily add them to a dataframe
GameModeDictionary = {"GameMode": GameModeName,
                      "AllMapsSize": AllMap,
                      "ValveMapsSize": ValveMap,
                      "CommunityMapsSize": CommMap,
                      "AllMapsSizeK": AllMapK,
                      "ValveMapsSizeK": ValveMapK,
                      "CommunityMapsSizeK": CommMapK}
# Create and clean the dataframe, removing all null values and replacing them with 0s
MapMinFrame = pd.DataFrame(GameModeDictionary)
MapMinFrame = MapMinFrame.fillna(0)
# print(MapMinFrame)

# And again for the max values
# Reset the list values
GameModeName = []
AllMap = []
ValveMap = []
CommMap = []
AllMapK = []
ValveMapK = []
CommMapK = []

for x in gameModeList:
    # gameMode = gameModeList[x]
    # print(gameModeList[x])
    GameModeName.append(x)
    AllMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[mapSizeFrame["GameMode"] == x].max())
    ValveMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].max())
    CommMap.append(mapSizeFrame["MapSize(kHu^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].max())
    AllMapK.append(mapSizeFrame["MapSize(km^2)"].loc[mapSizeFrame["GameMode"] == x].max())
    ValveMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        mapSizeFrame["Developers"].str.contains("Valve", na=False))].max())
    CommMapK.append(mapSizeFrame["MapSize(km^2)"].loc[(mapSizeFrame["GameMode"] == x) & (
        ~mapSizeFrame["Developers"].str.contains("Valve", na=False))].max())

# Store the results in a dictionary, that way we can easily add them to a dataframe
GameModeDictionary = {"GameMode": GameModeName,
                      "AllMapsSize": AllMap,
                      "ValveMapsSize": ValveMap,
                      "CommunityMapsSize": CommMap,
                      "AllMapsSizeK": AllMapK,
                      "ValveMapsSizeK": ValveMapK,
                      "CommunityMapsSizeK": CommMapK}
# Create and clean the dataframe, removing all null values and replacing them with 0s
MapMaxFrame = pd.DataFrame(GameModeDictionary)
MapMaxFrame = MapMaxFrame.fillna(0)
# print(MapMaxFrame)

# Create the chart
# It should be noted that when using the max and min values, the all maps variable will always be tied with either the valve maps or the community maps variable, so we should try to omit that when making charts using those frames
# Because of that, we will likely need two versions of this chart being ready when added to the dash site to account for this
# Since the chart will be updated and created in the site itself, the below is just the exoskeleton of the chart
# chart4 = px.bar(MapAverageFrame,
#                x="GameMode",
#                y=["AllMapsSize", "ValveMapsSize", "CommunityMapsSize"],
#                color_discrete_map={"AllMapsSize": "#CF7336", "ValveMapsSize": "#B8383B",
#                                    "CommunityMapsSize": "#5885A2"},
#                title="Average Map Size Per Game Mode")
# chart4.update_layout(plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"), barmode="group", font_family="TF2")
# chart4.update_yaxes(title_text="Average Map Size")
# chart4.show()


# Question 5: What is the ratio between normal map and holiday themed maps. Does limiting date or game mode change this
# Can we also avoid making a third pie chart to avoid repetition (Or at the very least make this one more visually different)
# We will need to drop down controls to allow for the limiting of date to a specific year as well as a specific game mode
# Test question: out of all the 36 maps added in 2023, how many of them were holiday themed

# Get the data we need for this chart
# This one will use both the main data and the holiday data sheets
# From the main data sheet, we will take the map, game mode, and date added columns
# From the event data sheet, we will take the map name and event columns
# The idea is to create a dataframe that will join these two together based on the map name
#   The idea is if the map name appears on the holiday sheet, the event it is linked with is added to its column
# print(mainData.head())
# First we need to rename the column in event data to match with the column name in the main data sheet
eventData = eventData.rename(columns={"MapName": "Map"})
# print(eventData)
# Create a new frame that is a merge between the both
EventFrame = pd.merge(mainData, eventData, how="left", on="Map")
# Drop the columns we don't need and fill in the null values
EventFrame.drop(["File name", "MapSize(kHu^2)", "NativeNavmesh", "OriginalMap", "Developers"], axis=1, inplace=True)
EventFrame["Event"] = EventFrame["Event"].fillna("None")
EventFrame = EventFrame.dropna()
# print(EventFrame)

# Group the results by events and get the total amount of maps made by each event type
# EventCount = EventFrame.groupby(["Event"])["Map"].count().reset_index()
# EventCount = EventFrame.loc[(EventFrame["Date added"].dt.year == 2023) & (EventFrame["Game mode"] == "Capture the Flag")].groupby(["Event"])["Map"].count().reset_index()
# print(EventFrame.loc[EventFrame["Date added"].dt.year == 2023].groupby(["Event"])["Map"].count().reset_index())
# temp = EventFrame.loc[EventFrame["Date added"].dt.year == 2023]
# temp = EventFrame.copy()
# temp = temp.loc[temp["Game mode"] == "Capture the Flag"]
# EventCount = temp.groupby(["Event"])["Map"].count().reset_index()
# Get the percentage of how many maps are in each category
# EventCount["MapPercent"] = (EventCount["Map"] / EventCount["Map"].sum()) * 100
# EventCount = EventCount.round({"MapPercent": 2})
# Convert the results into a string, so we can append a % to the end of it
# EventCount["MapPercent"].astype(object)
# EventCount["MapPercent"] = (EventCount["MapPercent"].astype(str) + "%")
# print(EventCount)

# Create the chart
# chart5 = px.bar(EventCount,
#                 x="Map",
#                 y="Event",
#                 orientation="h",
#                 text="MapPercent",
#                 color="Event",
#                 color_discrete_map={"None": "#CF7336", "Halloween": "#85589c", "Christmas": "#4d8757"},
#                 title="Maps Grouped By Holiday Events"
#                 )
# chart5.update_layout(plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"), font_family="TF2")
# chart5.update_traces(width=1, textfont_color="white")
# chart5.update_xaxes(title_text="Total Maps Per Category")
# chart5.show()


# Question 6: What are the biggest maps in each game mode?
# Thinking of using another horizontal bar chart, with a drop-down per game mode
# Also want to change the bar color in the chart depending on if the map was community made or valve made (And perhaps have a way to filter one or the other out)
# Also needs a drop-down to convert hammer units to normal measurement again
# Do note that there are some maps that do not have a valid map size, so the plan for those is to set them to 0 and leave a foot-note explaining why they are at 0
# Test question: What is the biggest valve made payload map in kilometers

# Step 1 is to get the data we need
# For this we will need the map name, game mode, developers, and map size columns
# We actually have a dataframe that uses these exact columns from question 5, but it removed all null map size values, which we want to keep this time, so we will re-make it
# print(mainData.info())
# print(mapSizeFrame.info())
MapComp = mainData[["Map", "Game mode", "Developers", "MapSize(kHu^2)"]].copy()
# replace all null values in the map size list with 0
MapComp["MapSize(kHu^2)"] = MapComp["MapSize(kHu^2)"].fillna(0)
MapComp["Community"] = "#5885A2"
MapComp.loc[gameModeData["Developers"].str.contains("Valve", na=False), "Community"] = "#B8383B"
MapComp["MapSize(km^2)"] = MapComp["MapSize(kHu^2)"] / 27.5926
# print(MapComp.head())

# Next for the purpose of testing the chart, we will make 3 variables to mimic the drop-down options that would normally be present
testGm = "Capture the Flag"
testDev = "All"
testSizeType = "Kilo Hammer Units Squared"

# Now with the filters in place, we can then filter the results into a new dataframe, which will be used in the chart
# temp = MapComp.loc[MapComp["Game mode"] == testGm]
# if testDev == "Valve":
#     temp = temp.loc[temp["Developers"].str.contains("Valve", na=False)]
# elif testDev == "Community":
#     temp = temp.loc[~temp["Developers"].str.contains("Valve", na=False)]
# print(temp)
#
# # Finally we make the chart itself
# if testSizeType == "Kilo Hammer Units Squared":
#     chart6 = px.bar(temp,
#                     x="MapSize(kHu^2)",
#                     y="Map",
#                     orientation="h",
#                     color="Community",
#                     color_discrete_sequence=temp.Community.unique(),
#                     title="Map Size Comparison By Game Mode")
# else:
#     chart6 = px.bar(temp,
#                     x="MapSize(km^2)",
#                     y="Map",
#                     orientation="h",
#                     color="Community",
#                     color_discrete_sequence=temp.Community.unique(),
#                     title="Map Size Comparison By Game Mode")
# chart6.update_layout(yaxis={"categoryorder": "total ascending"})
# # set the legend, so it doesn't just show the hex code
# legendNames = {"#B8383B": "Valve Maps", "#5885A2": "Community Maps"}
# chart6.for_each_trace(lambda t: t.update(name=legendNames[t.name],
#                                          legendgroup=legendNames[t.name],
#                                          hovertemplate=t.hovertemplate.replace(t.name, legendNames[t.name])
#                                          )
#                       )
# chart6.add_annotation(showarrow=False,
#                       text="* Some maps were unable to properly generate a nav mesh and as such were unable to give a proper map size.  These maps have had their size set to 0 that way they remain on the chart.",
#                       x=0,
#                       xref="paper",
#                       y=-0.1,
#                       yref="paper")
# # chart6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"), barmode="group", font_family="TF2")
# chart6.show()


layout = html.Div([
    html.Div(
        className="mapCountStats",
        children=[
            html.H3("Number Of Maps Added To TF2: " + str(len(mainData.index))),
            html.H3("Number of Valve-Made Maps: " + str(
                len(MapPerYearData.loc[MapPerYearData["Community"] == False].index))),
            html.H3("Number of Community-Made Maps: " + str(
                len(MapPerYearData.loc[MapPerYearData["Community"] == True].index)))
        ]
    ),

    # First graph goes here
    dcc.Graph(id="TotalMapGraph", figure=chart1),

    # Third graph and all needed drop-downs go here
    html.Div(
        className="ChartCombiner",
        children=[
            dcc.Graph(id="GMPerGraph"),
            html.Div(
                className="DropDownContainer",
                children=[
                    dcc.Dropdown(
                        id="GMPerDropDown",
                        options=["Capture the Flag", "Control Point", "Attack/Defend", "Payload", "Arena",
                                 "Payload Race",
                                 "King of the Hill", "Special Delivery", "Mann vs. Machine", "Robot Destruction",
                                 "Mannpower",
                                 "PASS Time", "Player Destruction", "Versus Saxton Hale", "Zombie Infection"],
                        value="Capture the Flag"
                    )
                ]
            )
        ]
    ),

    # Second graph goes here
    html.Div(
        className="ChartCombiner",
        children=[
            dcc.Graph(id="MapsPerYearGraph"),
            html.Div(
                className="DropDownContainer",
                children=[
                    dcc.Dropdown(
                        id="MapPerYearGameMode",
                        options=["All Game Modes", "Capture the Flag", "Control Point", "Attack/Defend", "Payload",
                                 "Arena",
                                 "Payload Race",
                                 "King of the Hill", "Special Delivery", "Mann vs. Machine", "Player Destruction",
                                 "Versus Saxton Hale", "Zombie Infection"],
                        value="All Game Modes"
                    )
                ]
            )
        ]
    ),

    # Fifth graph and all needed drop-downs go here
    html.Div(
        className="ChartCombiner",
        children=[
            dcc.Graph(id="HolidayCount"),
            html.Div(
                className="DropDownContainer",
                children=[
                    dcc.Dropdown(
                        id="HolidayCountYear",
                        options=["All Years", "2009", "2010", "2011", "2012", "2013", "2014", "2015",
                                 "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"],
                        value="All Years"
                    ),
                    dcc.Dropdown(
                        id="HolidayCountGameMode",
                        options=["All Game Modes", "Capture the Flag", "Control Point", "Attack/Defend", "Payload",
                                 "Arena",
                                 "Payload Race",
                                 "King of the Hill", "Special Delivery", "Mann vs. Machine", "Player Destruction",
                                 "Zombie Infection"],
                        value="All Game Modes"
                    )
                ]
            )
        ]
    ),

    # Fourth graph and all needed drop-downs go here
    html.Div(
        className="ChartCombiner",
        children=[
            dcc.Graph(id="MapSizeGMMode"),
            html.Div(
                className="DropDownContainer",
                children=[
                    dcc.Dropdown(
                        id="MapSizeDropDown",
                        options=["Average Map Size", "Max Map Size", "Min Map Size"],
                        value="Average Map Size"
                    ),
                    dcc.Dropdown(
                        id="MapSizeDistanceType",
                        options=["Kilo Hammer Units Squared", "Kilometers Squared"],
                        value="Kilo Hammer Units Squared"
                    ),
                ]
            ),
        ]
    ),

    # Sixth graph and all needed drop-downs go here
    html.Div(
        className="ChartCombiner",
        children=[
            dcc.Graph(id="MapSizeChart2"),
            html.Div(
                className="DropDownContainer",
                children=[
                    dcc.Dropdown(
                        id="MapSizeGameModes2",
                        options=["Capture the Flag", "Control Point", "Attack/Defend", "Payload", "Arena",
                                 "Payload Race",
                                 "King of the Hill", "Special Delivery", "Mann vs. Machine", "Player Destruction",
                                 "Versus Saxton Hale",
                                 "Zombie Infection"],
                        value="Capture the Flag"
                    ),
                    dcc.Dropdown(
                        id="CommunityMapDropDown2",
                        options=["All Maps", "Valve Maps", "Community Maps"],
                        value="All Maps"
                    ),
                    dcc.Dropdown(
                        id="MapSizeDistanceType2",
                        options=["Kilo Hammer Units Squared", "Kilometers Squared"],
                        value="Kilo Hammer Units Squared"
                    )
                ]
            )
        ]
    )
])

# Create the callbacks so the system knows to change when the drop-down value is changed
# This callback is used to make chart 2, the one that shows how many maps were made per year
@callback(
    Output("MapsPerYearGraph", "figure"),
    Input("MapPerYearGameMode", "value"))
def MapPerYearGraph(mode):
    GroupedData = MapPerYearData.copy()
    if mode != "All Game Modes":
        GroupedData = GroupedData.loc[GroupedData["Game mode"] == mode]
    GroupedData = GroupedData.groupby(["Date added", "Community"], as_index=False).count()
    GroupedData = GroupedData.drop(columns=["Game mode", "Developers"])
    # print(GroupedData.head())

    fig2 = px.bar(GroupedData,
                  x="Date added",
                  y="Map",
                  color="Community",
                  color_discrete_map={False: "#B8383B", True: "#5885A2"},
                  title="Number of Maps Added Per Year"
                  )
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"),
                       font_family="TF2", xaxis={"dtick": 1})
    fig2.update_yaxes(title_text="Maps Added")
    legendNames = {"False": "Valve Maps", "True": "Community Maps"}
    fig2.for_each_trace(lambda t: t.update(name=legendNames[t.name],
                                           legendgroup=legendNames[t.name],
                                           hovertemplate=t.hovertemplate.replace(t.name, legendNames[t.name])
                                           )
                        )
    return fig2


# This callback is used to make chart 3, the one that shows the % of maps made by game-mode
@callback(
    Output("GMPerGraph", "figure"),
    Input("GMPerDropDown", "value"))
# The function that creates the chart itself on the site
def GMPerGraphChangeMode(mode):
    # Create a dataframe to store this information properly
    typeCountData = {"MapCount": [
        len(gameModeData.loc[(gameModeData.Community == False) & (gameModeData.GameMode == mode)]),
        len(gameModeData.loc[(gameModeData.Community == True) & (gameModeData.GameMode == mode)])],
        "Type": ["Valve Maps", "Community Maps"]}
    typeCountFrame = pd.DataFrame(data=typeCountData)
    # Create the test chart in plotly
    fig0 = px.pie(typeCountFrame,
                  values="MapCount",
                  names="Type",
                  title="% of Maps Made by the Community and Valve in Specific Game Modes",
                  color="Type",
                  color_discrete_map={"Valve Maps": "#B8383B", "Community Maps": "#5885A2"})
    fig0.update_traces(textposition="inside", textinfo="percent+label")
    fig0.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), font_family="TF2")
    return fig0


# This callback is used to make chart 4, which shows various map sizes per game mode
@callback(
    Output("MapSizeGMMode", "figure"),
    [Input("MapSizeDropDown", "value"), Input("MapSizeDistanceType", "value")])
def GMSizeGraph(mode, sizeType):
    # print(mode)
    # print(sizeType)
    # First determine what chart type is used, then determine the measurement type, then create the chart
    if mode == "Average Map Size":
        if sizeType == "Kilo Hammer Units Squared":
            # Hammer units sized chart
            fig1 = px.bar(MapAverageFrame,
                          x="GameMode",
                          y=["AllMapsSize", "ValveMapsSize", "CommunityMapsSize"],
                          color_discrete_map={"AllMapsSize": "#CF7336", "ValveMapsSize": "#B8383B",
                                              "CommunityMapsSize": "#5885A2"},
                          title="Average Map Size Per Game Mode")
            fig1.update_yaxes(title_text="Map Size (kHu^2)")
        else:
            # Kilometers sized chart
            fig1 = px.bar(MapAverageFrame,
                          x="GameMode",
                          y=["AllMapsSizeK", "ValveMapsSizeK", "CommunityMapsSizeK"],
                          color_discrete_map={"AllMapsSizeK": "#CF7336", "ValveMapsSizeK": "#B8383B",
                                              "CommunityMapsSizeK": "#5885A2"},
                          title="Average Map Size Per Game Mode")
            fig1.update_yaxes(title_text="Map Size (km^2)")
    else:
        if mode == "Max Map Size":
            if sizeType == "Kilo Hammer Units Squared":
                # Hammer units sized chart
                fig1 = px.bar(MapMaxFrame,
                              x="GameMode",
                              y=["ValveMapsSize", "CommunityMapsSize"],
                              color_discrete_map={"ValveMapsSize": "#B8383B",
                                                  "CommunityMapsSize": "#5885A2"},
                              title="Max Map Size Per Game Mode")
                fig1.update_yaxes(title_text="Map Size (kHu^2)")
            else:
                # Kilometers sized chart
                fig1 = px.bar(MapMaxFrame,
                              x="GameMode",
                              y=["ValveMapsSizeK", "CommunityMapsSizeK"],
                              color_discrete_map={"ValveMapsSizeK": "#B8383B",
                                                  "CommunityMapsSizeK": "#5885A2"},
                              title="Max Map Size Per Game Mode")
                fig1.update_yaxes(title_text="Map Size (km^2)")
        else:
            if sizeType == "Kilo Hammer Units Squared":
                # Hammer units sized chart
                fig1 = px.bar(MapMinFrame,
                              x="GameMode",
                              y=["ValveMapsSize", "CommunityMapsSize"],
                              color_discrete_map={"ValveMapsSize": "#B8383B",
                                                  "CommunityMapsSize": "#5885A2"},
                              title="Min Map Size Per Game Mode")
                fig1.update_yaxes(title_text="Map Size (kHu^2)")
            else:
                # Kilometers sized chart
                fig1 = px.bar(MapMinFrame,
                              x="GameMode",
                              y=["ValveMapsSizeK", "CommunityMapsSizeK"],
                              color_discrete_map={"ValveMapsSizeK": "#B8383B",
                                                  "CommunityMapsSizeK": "#5885A2"},
                              title="Min Map Size Per Game Mode")
                fig1.update_yaxes(title_text="Map Size (km^2)")
    # Update the layout, so it matches with other charts and return it
    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"),
                       barmode="group", font_family="TF2")
    return fig1


# This callback is used to make chart 5, which shows the total maps per holiday theming
@callback(
    Output("HolidayCount", "figure"),
    [Input("HolidayCountYear", "value"), Input("HolidayCountGameMode", "value")])
def HolidayCountGraph(year, gmmode):
    # Group the results by events and get the total amount of maps made by each event type
    # We are also filtering by year and game mode on this step
    # EventCount = EventFrame.groupby(["Event"])["Map"].count().reset_index()
    if year != "All Years":
        temp = EventFrame.loc[EventFrame["Date added"].dt.year == int(year)]
    else:
        temp = EventFrame.copy()
        # print(temp)
    if gmmode != "All Game Modes":
        temp = temp.loc[temp["Game mode"] == gmmode]
    EventCount = temp.groupby(["Event"])["Map"].count().reset_index()
    # Get the percentage of how many maps are in each category
    EventCount["MapPercent"] = (EventCount["Map"] / EventCount["Map"].sum()) * 100
    EventCount = EventCount.round({"MapPercent": 2})
    # Convert the results into a string, so we can append a % to the end of it
    EventCount["MapPercent"].astype(object)
    EventCount["MapPercent"] = (EventCount["MapPercent"].astype(str) + "%")

    # Create the chart itself
    fig5 = px.bar(EventCount,
                  x="Map",
                  y="Event",
                  orientation="h",
                  text="MapPercent",
                  color="Event",
                  color_discrete_map={"None": "#CF7336", "Halloween": "#85589c", "Christmas": "#4d8757"},
                  title="Maps Grouped By Holiday Events"
                  )
    fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"),
                       font_family="TF2")
    fig5.update_traces(width=1, textfont_color="white")
    fig5.update_xaxes(title_text="Total Maps Per Category")
    return fig5


# This callback is used to make chart 6, which shows the map size of all maps per game mode
@callback(
    Output("MapSizeChart2", "figure"),
    [Input("MapSizeGameModes2", "value"), Input("CommunityMapDropDown2", "value"),
     Input("MapSizeDistanceType2", "value")]
)
def MapSizeGraph2(gameMode, mapDevelopers, sizeType):
    temp = MapComp.copy()
    temp = temp.loc[temp["Game mode"] == gameMode]
    if mapDevelopers == "Valve Maps":
        temp = temp.loc[temp["Developers"].str.contains("Valve", na=False)]
    elif mapDevelopers == "Community Maps":
        temp = temp.loc[~temp["Developers"].str.contains("Valve", na=False)]
    temp = temp.sort_values(by=["MapSize(kHu^2)"])

    # Finally we make the chart itself
    if sizeType == "Kilo Hammer Units Squared":
        fig6 = px.bar(temp,
                      x="MapSize(kHu^2)",
                      y="Map",
                      orientation="h",
                      # color="Community",
                      # color_discrete_sequence=temp.Community.unique(),
                      title="Map Size Comparison By Game Mode")
    else:
        fig6 = px.bar(temp,
                      x="MapSize(km^2)",
                      y="Map",
                      orientation="h",
                      # color="Community",
                      # color_discrete_sequence=temp.Community.unique(),
                      title="Map Size Comparison By Game Mode")
    # fig6.update_layout(yaxis={"categoryorder": "total ascending"})
    # We have to set up the colors here because if we do so, plotly will group them
    # If we then force normal grouping, it causes a bug where maps from other game modes will start appearing in the chart
    fig6.update_traces(width=1,
                       textfont_color="white",
                       marker_color=["#5885A2" if i == "#5885A2" else "#B8383B" for i in temp.Community]
                       )
    # set the legend, so it doesn't just show the hex code
    # legendNames = {"#B8383B": "Valve Maps", "#5885A2": "Community Maps"}
    # fig6.for_each_trace(lambda t: t.update(name=legendNames[t.name],
    #                                        legendgroup=legendNames[t.name],
    #                                        hovertemplate=t.hovertemplate.replace(t.name, legendNames[t.name])
    #                                        )
    #                     )
    fig6.add_annotation(showarrow=False,
                        text="* Some maps were unable to properly generate a nav mesh and as such were unable to give a proper map size.  These maps have had their size set to 0 that way they remain on the chart.",
                        x=0,
                        xref="paper",
                        y=-0.2,
                        yref="paper")
    fig6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgb(51, 51, 51)", font=dict(color="white"),
                       font_family="TF2")
    return fig6