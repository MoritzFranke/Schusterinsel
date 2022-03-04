import PIL.Image
import dash  # pip install dash
import dash_cytoscape as cyto  # pip install dash-cytoscape==0.2.0 or higher
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import html
from dash import dcc
from dash.dependencies import Output, Input, State
import pandas as pd  # pip install pandas
from pandas.tseries.offsets import DateOffset
import plotly.express as px
import re
import ctypes

ASSET_LIST_PATH = 'assets.txt'
NODE_LIST_PATH = 'NodeID'
BACKGROUND_IMAGE_PATH = '/assets/backgroundSchusterinsel.PNG'
HEADLINE = 'Enerthing Halle'
img = PIL.Image.open('assets/backgroundSchusterinsel.PNG')
width, heigt = img.size
Y_TO_X_RATIO = heigt/width
user32 = ctypes.windll.user32
SCREEN_X, SCREEN_Y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
print(SCREEN_X, SCREEN_Y)
RE_ID = " (.{5})"
RE_UUID = "(.*?) "
RE_X =  "(\\d*),"
RE_Y = ",(\\d*)"     
X_PIXEL = SCREEN_X/2.2
Y_PIXEL = X_PIXEL * Y_TO_X_RATIO
X_STEPS = 19
Y_STEPS = 12
print('GraphTable')
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)
######## Generate nodesAndAssetsArr
def create_nodes_and_assets_dict_arr():
    nodesAndAssetsArr= []
    with open(NODE_LIST_PATH, 'r') as f:
        for l in f.readlines():
            tmpUUID = re.findall(RE_UUID, l)[0]
            tmpID = re.findall(RE_ID, l)[0]
            tmpX = int(X_PIXEL/X_STEPS * int(re.findall(RE_X, l)[0]))
            tmpY = int(Y_PIXEL/Y_STEPS * int(re.findall(RE_Y, l)[0]))
            nodesAndAssetsArr.append({'data':{'id': tmpUUID, 'lable': tmpID},'position': {'x': tmpX,'y': tmpY}, 'locked': True, 'classes' : 'node'})
    with open(ASSET_LIST_PATH, 'r') as f:
        for l in f.readlines():
            tmpUUID = re.findall(RE_UUID, l)[0]
            tmpID = re.findall(RE_ID, l)[0]
            tmpX = X_PIXEL / X_STEPS * int(re.findall(RE_X, l)[0])
            tmpY = Y_PIXEL / Y_STEPS * int(re.findall(RE_Y, l)[0])
            nodesAndAssetsArr.append({'data':{'id': tmpUUID, 'lable': tmpID},'position': {'x': tmpX,'y': tmpY}, 'locked': True, 'classes' : 'asset'})
    return nodesAndAssetsArr


####themes https://www.youtube.com/watch?v=vqVwpL4bGKY
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])
stylesheet = [  # Group selectors for NODES
    {'selector': 'node', 'style': {'label': 'data(lable)', 'width': 15, 'height': 15, 'font-size': "12px"}},
    # Group selectors for EDGES
    {'selector': 'edge',
     'style': {'label': 'data(weight)', 'width': 2, 'height': 2, 'font-size': "9px", # 'target-arrow-shape': 'triangle'
               "source-arrow-shape": "triangle",  # Arrow shape
               'arrow-scale': 1,  # Arrow size
               'curve-style': 'bezier'  # Default curve-If it is style, the arrow will not be displayed, so specify it
               }},
    {'selector': '.node', 'style': {'background-color': 'blue'}},
    {'selector': '.asset', 'style': {'background-color': 'purple', 'shape': 'square', 'line-color': 'purple'}},
    {'selector': '.nodeSelected', 'style': {'background-color': 'black', 'width': 35, 'height': 35, 'font-size': "20px"}},
    {'selector': '.assetSelected', 'style': {'background-color': 'black', 'shape': 'square', 'width': 35, 'height': 35, 'font-size': "20px"}},
    {'selector': '[weight < 65]', 'style': {'line-color': 'orange'}},
    {'selector': '[weight >= -70]', 'style': {'line-color': 'green'}},
    {'selector': '[weight < -70]', 'style': {'line-color': 'orange'}},
    {'selector': '[weight = -74]', 'style': {'line-color': 'red'}},
    {'selector': '[selected = 1]', 'style': {'line-color': 'black', 'arrow-scale': 2, 'width':5, 'font-size': '30px', 'text-color':'red'}},
]
nodesAndAssetsArr = create_nodes_and_assets_dict_arr()

nodeId = []
assetId = []
nodeDictNumCon = {}
assetDictNumCon = {}
globalSelectedConPage2 = []
selectedRowPage2 = []

def get_lable_for_id(id):
    for device in nodesAndAssetsArr:
        for data in device['data'].values():
            if data == id:
                return device['data']['lable']
    return 'FFFFFF'

def get_node_or_asset_info_from_id(id):
    for device in nodesAndAssetsArr:
        if device['data']['lable'] == id:
            return device['classes'].replace('Selected', '')                ####### Returns node type without selected state
    return 'Not in List'

########read Raw Data
df = pd.read_csv('connectionList.csv')
RE_UUID = "(.*?) "
elemtsUUID = []
with open('assets.txt', 'r') as f:
    for l in f.readlines():
        elemtsUUID.append(re.findall(RE_UUID, l)[0])
with open('NodeID', 'r') as f:
    for l in f.readlines():
        elemtsUUID.append(re.findall(RE_UUID, l)[0])
dfNew = []
for UUID in elemtsUUID:
    dfNew.append(df[df['target'].str.startswith(UUID)].to_dict('records'))
new = []
for d in dfNew:
    if d != []:
        for dd in d:
            new.append(dd)

df = pd.DataFrame(new)

#######redesign List and add ids
for index, row in df.iterrows():
    nodeId.append(get_lable_for_id(row['source']))
    assetId.append(get_lable_for_id(row['target']))
df.insert(loc=1, column='Node ID', value=nodeId)
df.insert(loc=3, column='Asset ID', value=assetId)
df['weight'] = - df['weight']
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') + pd.Timedelta('01:00:00')  # Timezone BER +1
df.rename(columns={"source": "Node", "target": "Asset", "weight": "RSSI", "timestamp": "Uhrzeit"}, inplace=True)
dfgeneral = df
dfgeneralDictArr = dfgeneral.to_dict('records')

######### Get unique connections
# connection = df.pivot_table(columns=['Node', 'Asset'], aggfunc='size').to_dict()
# countAsset = df.pivot_table(columns=['Asset', 'Node'], aggfunc='size').to_dict()
def get_filtered_connections(min):
    df1 = df
    if min > 0:
        now = pd.Timestamp.now()
        timeFilter = now - DateOffset(minutes=min)
        df1 = dfgeneral[dfgeneral['Uhrzeit'] >= timeFilter]
    df1 = df1.sort_values(by=['RSSI'])
    df1 = df1.drop_duplicates(subset=['Node', 'Asset'], keep='last')
    graphConnectionList = []
    tmpDf = df1.drop(columns=['Uhrzeit'])
    tmpDf.rename(columns={"Node": "source", "Asset": "target", "RSSI": "weight"}, inplace=True)
    tmpDfDictArr = tmpDf.to_dict('records')
    tmpDfDictArr
    for connection in tmpDfDictArr:
        connection.update({'selected': 0})
        graphConnectionList.append({'data': connection})
    return graphConnectionList


####################### Verbindungsliste Übersicht
def create_connection_detail_Dataframe(min):
    dfTimeFiltered = dfgeneral
    if min > 0:
        now = pd.Timestamp.now()
        timeFilter = now - DateOffset(minutes=min)
        dfTimeFiltered = dfgeneral[dfgeneral['Uhrzeit'] >= timeFilter]
        # print(dfTimeFiltered)
    dfd = dfTimeFiltered.to_dict('records')
    resultDisctArr = []
    df1 = dfgeneral.sort_values(by=['RSSI'])
    df1 = df1.drop_duplicates(subset=['Node', 'Asset'], keep='last')
    df1d = df1.to_dict('records')
    for con in df1d:
        tmpD = []
        for d in dfd:
            # for f in data:
            if d['Node'] == con['Node'] and d['Asset'] == con['Asset']:
                tmpD.append(d)
        if tmpD != []:
            dataf = pd.DataFrame(tmpD)
            minRow = dataf['RSSI'].min()
            maxRow = dataf['RSSI'].max()
            meanRow = dataf['RSSI'].mean()
            medianRow = dataf['RSSI'].median()
            numberRow = dataf['RSSI'].count()
            conLosses = 0
            for val in dataf['RSSI']:
                if val == -74:
                    conLosses += 1
            prozent = 0
            if numberRow != 0:
                prozent = int(conLosses*100/numberRow)
            tmpDict = {'Node ID': tmpD[0]['Node ID'], 'Asset ID': tmpD[0]['Asset ID'], 'Min': minRow, 'Max': maxRow,
                       'Detla': maxRow - minRow, 'Mittelwert': int(meanRow), 'Median': medianRow, 'Anzahl': numberRow, 'Verluste': conLosses, 'In %': prozent}
            resultDisctArr.append(tmpDict)
    # connectionDetailDf = pd.DataFrame(resultDisctArr)
    # print(pd.DataFrame(resultDisctArr))
    tmpdf = pd.DataFrame(resultDisctArr).sort_values(by=['Verluste'],ascending=False)
    return tmpdf.to_dict('records')


networkCard = dbc.Card([
    dbc.CardImg(src=BACKGROUND_IMAGE_PATH, top=True, alt='Bild nicht Verfügbar',
                style={'width': X_PIXEL, 'height': Y_PIXEL, 'margin':'1rem', 'margin-top':'1.5rem', 'opacity':0.5}),
    dbc.CardImgOverlay(
            cyto.Cytoscape(
                id='networkGraph',
                layout={'name': 'preset'},
                style={'width': X_PIXEL*1.04, 'height': Y_PIXEL*1.04, 'margin':0},
                elements=nodesAndAssetsArr + get_filtered_connections(0),
                stylesheet=stylesheet,
                userPanningEnabled=False,
            ))])

######### Web Oberfläche
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(html.H1(HEADLINE, className='text-center'), width={'size':3,'offset':3,'order':1}),
                dbc.Col(
                    html.Div(
                        [
                            dcc.Location(id='url', refresh=False),
                            dcc.Link('Seite 1', href='/'),
                        ],className='text-center'
                    ), width={'size':1, 'order':0}
                ),
                dbc.Col(
                    html.Div(dcc.Link('Seite 2', href='/page-2'), className='text-center'), width={'size':1,'offset':1,'order':2}
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.Label(['Zeitraum Wählen'],style={'font-weight': 'bold', "text-align": "center"}),
                            dcc.Dropdown(
                                id='my-dropdown',
                                options=[
                                    {'label': 'Gesamter Zeitraum', 'value': 0},
                                    {'label': 'Letzten 7 Tage', 'value': 7*24*60},
                                    {'label': 'Letzten 2 Tage', 'value': 2*24*60},
                                    {'label': 'Letzten 24 Stunden', 'value': 1*24*60},
                                    {'label': 'Letzten 6 Stunden', 'value': 6*60},
                                    {'label': 'Letzten 3 Stunden', 'value': 3*60},
                                    {'label': 'Letzte 1 Stunden', 'value': 1*60},
                                    {'label': 'Letzten 30 Minuten', 'value': 30},
                                ],
                                optionHeight=25,  # height/space between dropdown options
                                value=0,  # dropdown value selected automatically when page loads
                                disabled=False,  # disable dropdown value selection
                                multi=False,  # allow multiple dropdown values to be selected
                                searchable=False,  # allow user-searching of dropdown values
                                search_value='',  # remembers the value searched in dropdown
                                clearable=False,  # allow user to removes the selected value
                                style={'width': "100%"},  # use dictionary to define CSS styles of your dropdown
                                # className='select_box',           #activate separate CSS document in assets folder
                                # persistence=True,                 #remembers dropdown value. Used with persistence_type
                                # persistence_type='memory'         #remembers dropdown value selected until...
                            )
                    ], className='text-center'), width={'size':2,'order':3}
                )

            ],
            justify='between'
        ),
        dbc.Row(
                html.Div(id='page-content'),
        )
    ],
    fluid=True      #Fill Screen
)



########## Page arranging
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    # print(pathname)
    if pathname == '/':
        return html.Div(
            [##########Detailansicht
                dbc.Row(
                    [
                        ########## Deatil Connection Graph https://www.youtube.com/watch?v=G8r2BB3GFVY&t=946s
                        dbc.Col(
                            dbc.Row([
                                dcc.Graph(id='connectionGraph',config={'displayModeBar':False}),
                                ################## Detail Table
                                dash_table.DataTable(
                                    id='datatableNodeAssetFiltered',
                                    columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in
                                             pd.DataFrame(create_connection_detail_Dataframe(0)).columns],
                                    data=[],  # the contents of the table
                                    editable=False,  # allow editing of data inside all cells
                                    filter_action="native",
                                    # allow filtering of data by user ('native') or not ('none')
                                    sort_action="native",
                                    # enables data to be sorted per-column by user or not ('none')
                                    sort_mode="multi",  # sort across 'multi' or 'single' columns
                                    column_selectable=False,  # allow users to select 'multi' or 'single' columns
                                    row_selectable='single',  # allow users to select 'multi' or 'single' rows
                                    row_deletable=False,  # choose if user can delete a row (True) or not (False)
                                    selected_columns=[],  # ids of columns that user selects
                                    selected_rows=[],  # indices of rows that user selects
                                    page_action="native",  # all data is passed to the table up-front or not ('none')
                                    page_current=0,  # page number that user is on
                                    page_size=6,  # number of rows visible per page
                                    style_cell={  # ensure adequate header width when text is shorter than cell's text
                                        # 'width': '1000px',
                                        #'maxWidth': SCREEN_X/2*10,
                                        'minWidth': '40px',
                                    },
                                    style_cell_conditional=[
                                        # align text columns to left. By default they are aligned to right
                                        {'if': {'column_id': c}, 'textAlign': 'left'} for c in
                                        ['Node', 'Node ID', 'Asset', 'Asset ID']],
                                    style_data={  # overflow cells' content into multiple lines
                                        'whiteSpace': 'normal', 'height': 'auto'})
                                ]), width=6),
                        ########### Network Graph
                        dbc.Col(networkCard,width=6)
                    ])])
    else:  #######################Page 2
        return html.Div([
            dbc.Col(
            dash_table.DataTable(id='datatableNodeAssetAll',
            columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in
                     pd.DataFrame(create_connection_detail_Dataframe(0)).columns],
            data=create_connection_detail_Dataframe(0),  # the contents of the table
            editable=False,  # allow editing of data inside all cells
            filter_action="native",  # allow filtering of data by user ('native') or not ('none')
            sort_action="native",  # enables data to be sorted per-column by user or not ('none')
            sort_mode="multi",  # sort across 'multi' or 'single' columns
            column_selectable=False,  # allow users to select 'multi' or 'single' columns
            row_selectable='single',  # allow users to select 'multi' or 'single' rows
            row_deletable=False,  # choose if user can delete a row (True) or not (False)
            selected_columns=[],  # ids of columns that user selects
            selected_rows=selectedRowPage2,  # indices of rows that user selects
            page_action="native",  # all data is passed to the table up-front or not ('none')
            page_current=0,  # page number that user is on
            page_size=22,  # number of rows visible per page
            # style_cell={  # ensure adequate header width when text is shorter than cell's text
            #     'minWidth': 20, 'maxWidth': 50, 'width': 50},
            style_cell_conditional=[  # align text columns to left. By default they are aligned to right
                {'if': {'column_id': c}, 'textAlign': 'left'} for c in ['Node', 'Node ID', 'Asset', 'Asset ID']],
            style_data={  # overflow cells' content into multiple lines
                'whiteSpace': 'normal', 'height': 'auto'}),width={'size': 9,'offset':1})
        ]),

###### Detail RSSI Verläufe
@app.callback(
    Output('connectionGraph', 'figure'),
    [
        Input('networkGraph', 'tapEdgeData'),
        Input('my-dropdown', 'value'),
        Input('datatableNodeAssetFiltered', 'selected_rows'),
        State('datatableNodeAssetFiltered', 'data'),
        State('networkGraph', 'tapNodeData')
    ]
)
def build_connectiongraph(selectedConnection, min, FilteredDataselectedRowNum, FilteredData, selectedNodeAsset):
    if  globalSelectedConPage2 != []:
        selectedConnection = globalSelectedConPage2
    dfDictListTabSelected = []
    dfDictListDatatableSelected = []
    test = []
    filteredAssetId = ''
    filteredNodeId = ''
    heading = ''
    if selectedConnection != None:
        heading = 'Verbindung von ' + selectedConnection['Asset ID'] + ' zu ' + selectedConnection['Node ID']
    if FilteredDataselectedRowNum != [] and FilteredData != []:
        ###check if same connetions are aktive
        if heading == '':
            heading = 'Verbindung von ' + FilteredData[FilteredDataselectedRowNum[0]]['Asset ID'] + ' zu ' + FilteredData[FilteredDataselectedRowNum[0]]['Node ID']
        elif selectedConnection['Asset ID'] == FilteredData[FilteredDataselectedRowNum[0]]['Asset ID'] and \
                selectedConnection['Node ID'] == FilteredData[FilteredDataselectedRowNum[0]]['Node ID']:
            pass
        else:
            heading = heading.replace('Verbindung', 'Verbindungen') + ' und ' + \
                      FilteredData[FilteredDataselectedRowNum[0]]['Asset ID'] + \
                      ' zu ' + FilteredData[FilteredDataselectedRowNum[0]]['Node ID']
    for d in dfgeneralDictArr:
        if selectedConnection != None:
            if d['Node ID'] == selectedConnection['Node ID'] and d['Asset ID'] == selectedConnection['Asset ID']:
                dfDictListTabSelected.append(d)
                test.append(d)
        if FilteredDataselectedRowNum != [] and FilteredData != []:
            if d['Node ID'] == FilteredData[FilteredDataselectedRowNum[0]]['Node ID'] and d['Asset ID'] == FilteredData[FilteredDataselectedRowNum[0]]['Asset ID']:
                dfDictListDatatableSelected.append(d)
                test.append(d)
                # print(d)
    if selectedNodeAsset != None and selectedConnection != None:
        type = get_node_or_asset_info_from_id(selectedNodeAsset['lable'])
        if type == 'node':
            if selectedConnection['Node ID'] == selectedNodeAsset['lable']:
                color = 'Asset ID'
            else:
                color = 'Node ID'
        else:
            if selectedConnection['Asset ID'] == selectedNodeAsset['lable']:
                color = 'Node ID'
            else:
                color = 'Asset ID'
    else:
        color = 'Asset ID'
    dftest = pd.DataFrame(test)
    if min > 0:
        now = pd.Timestamp.now()
        timeFilter = now - DateOffset(minutes=min)
        dfTimeFiltered = dftest[dftest['Uhrzeit'] >= timeFilter]
        fig = px.line(dfTimeFiltered, x='Uhrzeit', y='RSSI', color=color, markers=True)
    else:
        fig = px.line(dftest, x='Uhrzeit', y='RSSI', color=color, markers=True)
    fig.update_layout(yaxis={'title': 'RSSI'}, xaxis={'title': 'Uhrzeit'}, title={
        'text': heading, 'font':{'size':20},'x':0.5,'xanchor':'center'})
    return fig


############### Page 2 overall view Update TimeSpan
@app.callback(Output('datatableNodeAssetAll', 'data'), Input('my-dropdown', 'value'),
        Input('datatableNodeAssetAll', 'selected_rows'),
        State('datatableNodeAssetAll', 'data'))
def update_Page_2(min,selectedRow,selectedCon):
    global globalSelectedConPage2, selectedRowPage2
    selectedRowPage2 = selectedRow
    globalSelectedConPage2 = selectedCon[selectedRow[0]]
    return create_connection_detail_Dataframe(min)

########## clear slected rows
@app.callback(Output('datatableNodeAssetFiltered', 'selected_rows'), Input('networkGraph', 'tapNodeData'))
def clear_selection(val):
    return []
#Input('datatableNodeAssetFiltered', 'selected_row_ids'))


############# Update Connections
@app.callback(
    Output('networkGraph', 'elements'),
    [
        Input('my-dropdown', 'value'),
        State('networkGraph', 'elements'),
        Input('networkGraph', 'tapEdgeData'),
        Input('networkGraph', 'tapNodeData'),
        Input('datatableNodeAssetFiltered', 'selected_rows'),
        State('datatableNodeAssetFiltered', 'data'),
    ]
)
def update_networkgraph(min, connections, tabCon, tabNode, FilteredDataselectedRowNum, FilteredData):
    global globalSelectedConPage2
    tmpNodeId = ''
    tmpAssetId = ''
    if globalSelectedConPage2 != []:
        tmpNodeId = globalSelectedConPage2['Node ID']
        tmpAssetId = globalSelectedConPage2['Asset ID']
        globalSelectedConPage2 = []
    conDataArr = get_filtered_connections(min)
    if FilteredData != [] and FilteredDataselectedRowNum != []:
        tmpNodeId = FilteredData[FilteredDataselectedRowNum[0]]['Node ID']
        tmpAssetId = FilteredData[FilteredDataselectedRowNum[0]]['Asset ID']
    if tmpNodeId != '' and tmpAssetId != '':
        for con in conDataArr:
            if con['data']['Node ID'] == tmpNodeId and con['data']['Asset ID'] == tmpAssetId:
                con['data']['selected'] = 1
    if tabCon != None:
        for con in conDataArr:
            if con['data']['source'] == tabCon['source'] and con['data']['target'] == tabCon['target']:
                con['data']['selected'] = 1
    newReturn = []
    for entry in connections:
        if not 'weight' in entry['data'].keys():
            if entry['classes'] == 'assetSelected':
                entry['classes'] = 'asset'
            elif entry['classes'] == 'nodeSelected':
                entry['classes'] = 'node'
            if tabNode != None and tabNode['id'] == entry['data']['id']:
                if entry['classes'] == 'asset':
                    entry['classes'] = 'assetSelected'
                else:
                    entry['classes'] = 'nodeSelected'
            newReturn.append(entry)

    return newReturn + conDataArr

###### Table Asset Node Selected
@app.callback(Output('datatableNodeAssetFiltered', 'data'), [Input('networkGraph', 'tapNodeData'),Input('my-dropdown','value')])
def update_columns(tapNodeData, min):
    # print(tapNodeData,min)
    # id = tapNodeData['data']
    # print(id)
    # print(get_lable_for_id(tapNodeData['id']))
    resultDisctArr = create_connection_detail_Dataframe(min)
    resultDataDictArray = []
    if tapNodeData['lable'] in nodeId:
        # print('node')
        for con in resultDisctArr:
            if con['Node ID'] == tapNodeData['lable']:
                resultDataDictArray.append(con)
    elif tapNodeData['lable'] in assetId:
        # print('asset')
        for con in resultDisctArr:
            if con['Asset ID'] == tapNodeData['lable']:
                resultDataDictArray.append(con)
    # print(resultDataDictArray)
    tmpDf = pd.DataFrame(resultDataDictArray)
    tmpDf = tmpDf.sort_values(by=['Verluste'],ascending=False)        #######ascending=Flase -> absteigend
    resultDataDictArray = tmpDf.to_dict('records')
    return resultDataDictArray


if __name__ == '__main__':
    app.run_server(debug=True)