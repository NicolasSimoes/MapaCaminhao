
import pandas as pd
import folium

# 1) Ler o CSV com ponto e vírgula como separador e realizar a limpeza dos dados
df = pd.read_csv('dbcaminhoes.csv', sep=';', encoding='utf-8')
df.columns = df.columns.str.strip()

for col in df.select_dtypes(include=['object']):
    df[col] = df[col].str.strip()

# 2) Converter as colunas PESO e CARGA para numérico 
# (se houver vírgulas como separador decimal, substituímos por ponto)
df['PESO'] = pd.to_numeric(df['PESO'].str.replace(',', '.'), errors='coerce')


# 3) Agrupar os dados por caminhão para calcular o total de peso transportado
#    e obter a carga útil (usando 'first', assumindo que esse valor se repete para o caminhão)
df_group = df.groupby('CAMINHAO').agg(
    PESO_TOTAL=('PESO', 'sum'),
    CARGA_UTIL=('CARGA', 'first')
).reset_index()

# 4) Calcular a porcentagem de uso de cada caminhão
df_group['USO_%'] = (df_group['PESO_TOTAL'] / df_group['CARGA_UTIL']) * 100


# 6) Configurar as cores dos caminhões para o mapa
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
          'beige', 'darkblue', 'darkgreen', 'cadetblue', 
          'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
          'black', 'lightgray']
truck_colors = {}
unique_trucks = df['CAMINHAO'].unique()
for i, truck in enumerate(unique_trucks):
    truck_colors[truck] = colors[i % len(colors)]

# 7) Criar o mapa base, centralizado na região de interesse
mapa = folium.Map(location=[-3.8666699, -38.5773332], zoom_start=10)

# 8) Adicionar os marcadores e as rotas ao mapa, agrupados por caminhão
for truck, group in df.groupby('CAMINHAO'):
    feature_group = folium.FeatureGroup(name=f"Caminhão: {truck}")
    truck_color = truck_colors.get(truck, 'gray')
    
    for _, row in group.iterrows():
        # Coordenadas da loja (destino)
        lat_dest = row['LATITUDE']
        lon_dest = row['LONGITUDE']
        
        # Coordenadas da casa (origem)
        lat_casa = row['LATITUDE CASA']
        lon_casa = row['LONGITUDE CASA']
        
        # Criar o popup exibindo informações do registro
        popup_text = f"""
        <b>Caminhão:</b> {row['CAMINHAO']}<br>
        <b>Cliente:</b> {row['NOME FANTASIA']}<br>
        <b>Peso:</b> {row['PESO']}<br>
        <b>Faturamento Bruto:</b> {row['FATURAMENTO']}
        """
        
        folium.Marker(
            location=[lat_dest, lon_dest],
            popup=popup_text,
            tooltip=row['NOME FANTASIA'],
            icon=folium.Icon(color=truck_color, icon='shopping-cart')
        ).add_to(feature_group)
        
        folium.Marker(
            location=[lat_casa, lon_casa],
            popup="Casa de origem",
            icon=folium.Icon(color='green', icon='home')
        ).add_to(feature_group)
        
        folium.PolyLine(
            locations=[(lat_casa, lon_casa), (lat_dest, lon_dest)],
            color=truck_color,
            weight=2,
            opacity=0.8
        ).add_to(feature_group)
    
    feature_group.add_to(mapa)

# 9) Adicionar o controle de camadas
folium.LayerControl().add_to(mapa)

# 10) Contar o número de clientes únicos
unique_markers = df['NOME FANTASIA'].nunique()

# 11) Gerar uma lista HTML com o uso percentual de cada caminhão
truck_usage_list = "<ul>"
for _, row in df_group.iterrows():
    truck_usage_list += f"<li>{row['CAMINHAO']}: {row['USO_%']:.0f}%</li>"
truck_usage_list += "</ul>"

# 12) Criar uma caixa de informação (legend) para exibir os dados no mapa
legend_html = f'''
<div style="
    position: fixed; 
    bottom: 50px; 
    left: 50px; 
    width: 300px;              
    background-color: white; 
    border: 2px solid grey; 
    z-index:9999; 
    font-size:14px;
    padding: 10px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    white-space: normal;
">
    <b>🏬 Número de Clientes:</b> {unique_markers}<br>
    <b>🔄 Atualizado:</b> 10/04/2025<br><br>
    <b> %  de carga usada por Caminhão:</b> {truck_usage_list}

</div>
'''
mapa.get_root().html.add_child(folium.Element(legend_html))

# 13) Salvar o mapa em um arquivo HTML
mapa.save('mapa_clientes.html')
print("Mapa salvo como mapa_clientes.html")
