import pandas as pd
import folium

# 1) Ler o CSV com ponto e vírgula como separador e realizar a limpeza dos dados
df = pd.read_csv('dbcaminhoes.csv', sep=';', encoding='utf-8')
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include=['object']):
    df[col] = df[col].str.strip()

# 2) Definir uma lista de cores e mapear cada caminhão a uma cor única
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
          'beige', 'darkblue', 'darkgreen', 'cadetblue', 
          'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
          'black', 'lightgray']
truck_colors = {}
unique_trucks = df['CAMINHAO'].unique()
for i, truck in enumerate(unique_trucks):
    truck_colors[truck] = colors[i % len(colors)]

# 3) Criar o mapa base (centralizado na região de interesse)
mapa = folium.Map(location=[-3.8666699, -38.5773332], zoom_start=10)

# 4) Agrupar os dados por caminhão e criar os elementos no mapa
for truck, group in df.groupby('CAMINHAO'):
    feature_group = folium.FeatureGroup(name=f"Caminhão: {truck}")
    truck_color = truck_colors[truck]
    
    for _, row in group.iterrows():
        # Coordenadas da loja (destino)
        lat_dest = row['LATITUDE']
        lon_dest = row['LONGITUDE']
        
        # Coordenadas da casa (origem)
        lat_casa = row['LATITUDE CASA']
        lon_casa = row['LONGITUDE CASA']
        
        # Criar o popup exibindo Caminhão e Faturamento Bruto
        popup_text = f"""
        <b>Caminhão:</b> {row['CAMINHAO']}<br>
        <b>Cliente:</b> {row['NOME FANTASIA']}<br>
        <b>Faturamento Bruto:</b> {row['FATURAMENTO']}
        """
        
        # Marcador da loja com ícone colorido conforme o caminhão
        folium.Marker(
            location=[lat_dest, lon_dest],
            popup=popup_text,
            tooltip=row['NOME FANTASIA'],
            icon=folium.Icon(color=truck_color, icon='shopping-cart')
        ).add_to(feature_group)
        
        # Marcador da casa com ícone de lar
        folium.Marker(
            location=[lat_casa, lon_casa],
            popup="Casa de origem",
            icon=folium.Icon(color='green', icon='home')
        ).add_to(feature_group)
        
        # Desenhar a rota (linha reta) entre a casa e a loja com a mesma cor
        folium.PolyLine(
            locations=[(lat_casa, lon_casa), (lat_dest, lon_dest)],
            color=truck_color,
            weight=2,
            opacity=0.8
        ).add_to(feature_group)
    
    feature_group.add_to(mapa)

# 5) Adicionar o controle de camadas
folium.LayerControl().add_to(mapa)

# 6) Calcular a contagem de marcadores com base no valor único de NOME FANTASIA
unique_markers = df['NOME FANTASIA'].nunique()

# 7) Inserir uma caixa de informação no canto inferior esquerdo do mapa
legend_html = f'''
<div style="
    position: fixed; 
    bottom: 50px; 
    left: 50px; 
    width: 250px;              /* Mantém a largura */
    background-color: white; 
    border: 2px solid grey; 
    z-index:9999; 
    font-size:14px;
    padding: 10px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    white-space: normal;       /* Permite quebra de linha */
">
   <br> 🏬 Número de Clientes: {unique_markers}<br>
     🔄 Atualizado : 08/04/2025
</div>
'''
mapa.get_root().html.add_child(folium.Element(legend_html))

# 8) Salvar o mapa em um arquivo HTML
mapa.save('mapa_clientes.html')
print("Mapa salvo como mapa_clientes.html")
