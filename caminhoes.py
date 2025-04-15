import pandas as pd
import folium

# Leitura e limpeza do arquivo
df = pd.read_csv('dbcaminhoes.csv', sep=';', encoding='utf-8')
df.columns = df.columns.str.strip()

for col in df.select_dtypes(include=['object']):
    df[col] = df[col].str.strip()

# Converter coluna PESO para numérico
df['PESO'] = pd.to_numeric(df['PESO'].str.replace(',', '.'), errors='coerce')

# Agrupar dados dos caminhões para calcular o uso da carga
df_group = df.groupby('CAMINHAO').agg(
    PESO_TOTAL=('PESO', 'sum'),
    CARGA_UTIL=('CARGA', 'first')
).reset_index()

df_group['USO_%'] = (df_group['PESO_TOTAL'] / df_group['CARGA_UTIL']) * 100

# Mapeamento de cores para cada caminhão
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
          'beige', 'darkblue', 'darkgreen', 'cadetblue', 
          'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
          'black', 'lightgray']
truck_colors = {}
unique_trucks = df['CAMINHAO'].unique()
for i, truck in enumerate(unique_trucks):
    truck_colors[truck] = colors[i % len(colors)]

# Criação do mapa
mapa = folium.Map(location=[-3.8666699, -38.5773332], zoom_start=10)

# Loop para adicionar os elementos de cada caminhão
for truck, group in df.groupby('CAMINHAO'):
    feature_group = folium.FeatureGroup(name=f"Caminhão: {truck}")
    truck_color = truck_colors.get(truck, 'gray')
    
    for _, row in group.iterrows():
        lat_dest = row['LATITUDE']
        lon_dest = row['LONGITUDE']
        
        lat_casa = row['LATITUDE CASA']
        lon_casa = row['LONGITUDE CASA']
        
        # Seleciona o ícone de acordo com o TURNO RECEBIMENTO
        turno = row['TURNO RECEBIMENTO'].strip().upper() if pd.notnull(row['TURNO RECEBIMENTO']) else ''
        if turno == 'MANHA':
            # Ícone de sol para turno da manhã
            icon_marker = folium.Icon(color=truck_color, icon='sun', prefix='fa')
        elif turno == 'DIURNO':
            # Ícone de pôr do sol para turno diurno
            icon_marker = folium.Icon(color=truck_color, icon='🌚')
        else:
            # Ícone padrão, caso não caia nos casos acima
            icon_marker = folium.Icon(color=truck_color, icon='shopping-cart')
        
        popup_text = f"""
        <b>Caminhão:</b> {row['CAMINHAO']}<br>
        <b>Cliente:</b> {row['NOME FANTASIA']}<br>
        <b>Peso:</b> {row['PESO']}<br>
          <b>TURNO DE RECEBIMENTO:</b> {row['TURNO RECEBIMENTO']}
        <b>Faturamento Bruto:</b> {row['FATURAMENTO']}

        """
        
        # Marcador para o destino (loja)
        folium.Marker(
            location=[lat_dest, lon_dest],
            popup=popup_text,
            tooltip=row['NOME FANTASIA'],
            icon=icon_marker
        ).add_to(feature_group)
        
        # Marcador para a loja VALEMILK-CD
        folium.Marker(
            location=[lat_casa, lon_casa],
            popup="VALEMILK-CD",
            icon=folium.Icon(color='green', icon='home')
        ).add_to(feature_group)
        
        # Linha ligando os pontos
        folium.PolyLine(
            locations=[(lat_casa, lon_casa), (lat_dest, lon_dest)],
            color=truck_color,
            weight=2,
            opacity=0.8
        ).add_to(feature_group)
    
    feature_group.add_to(mapa)

folium.LayerControl().add_to(mapa)

# Dados para a legenda
unique_markers = df['NOME FANTASIA'].nunique()

truck_usage_list = "<ul>"
for _, row in df_group.iterrows():
    truck_usage_list += f"<li>{row['CAMINHAO']}: {row['USO_%']:.0f}%</li>"
truck_usage_list += "</ul>"

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
    <b>🔄 Atualizado:</b> 15/04/2025<br><br>
    <b> ☀ Cliente recebe apenas de manhã <br>
    <b> % de carga usada por Caminhão:</b> {truck_usage_list}
</div>
'''
mapa.get_root().html.add_child(folium.Element(legend_html))

# Salvar o mapa em um arquivo HTML
mapa.save('mapa_clientes.html')
print("Mapa salvo como mapa_clientes.html")