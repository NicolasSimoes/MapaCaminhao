import pandas as pd
import folium

# 1. Leitura do CSV (ajuste o 'sep' e 'encoding' conforme necessário)
df = pd.read_csv('dbcaminhoes.csv', sep=';', encoding='utf-8')

# 2. Limpeza dos nomes das colunas e espaços extras
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include=['object']):
    df[col] = df[col].str.strip()

# 3. Converter coluna PESO para numérico (trocando vírgula por ponto)
df['PESO'] = pd.to_numeric(df['PESO'].str.replace(',', '.'), errors='coerce')

# 4. Converter coluna FATURAMENTO para numérico
#    a) Remover "R$" se existir
#    b) Remover pontos de milhar (escape no ponto: r'\.')
#    c) Trocar vírgula pelo ponto decimal
#    d) Remover espaços extras e converter para float

df['FATURAMENTO'] = (
    df['FATURAMENTO']
    .str.replace(r'R\$', '', regex=True)   # remove "R$"
    .str.replace(r'\.', '', regex=True)      # remove pontos de milhar (literal)
    .str.replace(',', '.', regex=True)       # troca vírgula por ponto
    .str.strip()                             # remove espaços
)
# Opcional: visualizar os primeiros valores da coluna para conferência
print("Valores limpos de FATURAMENTO:")
print(df['FATURAMENTO'].head(10))

df['FATURAMENTO'] = pd.to_numeric(df['FATURAMENTO'], errors='coerce')

# 5. Agrupar dados dos caminhões para calcular o uso da carga
df_group = df.groupby('CAMINHAO').agg(
    PESO_TOTAL=('PESO', 'sum'),
    CARGA_UTIL=('CARGA', 'first'),
    VALOR_TOTAL=('FATURAMENTO', 'sum')
).reset_index()

df_group['USO_%'] = (df_group['PESO_TOTAL'] / df_group['CARGA_UTIL']) * 100 
df_group['VALOR_CARGA'] = df_group['VALOR_TOTAL']

# 6. Computar o faturamento total de todos os caminhões
faturamento_total = df_group['VALOR_TOTAL'].sum()

# 7. Mapeamento de cores para cada caminhão
colors = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred',
    'beige', 'darkblue', 'darkgreen', 'cadetblue',
    'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray',
    'black', 'lightgray'
]
truck_colors = {}
unique_trucks = df['CAMINHAO'].unique()
for i, truck in enumerate(unique_trucks):
    truck_colors[truck] = colors[i % len(colors)]

# 8. Criação do mapa
mapa = folium.Map(location=[-3.8666699, -38.5773332], zoom_start=10)

# 9. Loop para adicionar os elementos de cada caminhão
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
            icon_marker = folium.Icon(color=truck_color, icon='sun', prefix='fa')
        elif turno == 'DIURNO':
            icon_marker = folium.Icon(color=truck_color, icon='🌚')
        else:
            icon_marker = folium.Icon(color=truck_color, icon='shopping-cart')
        
        popup_text = f"""
        <b>Caminhão:</b> {row['CAMINHAO']}<br>
        <b>Cliente:</b> {row['NOME FANTASIA']}<br>
        <b>Peso:</b> {row['PESO']}<br>
        <b>TURNO DE RECEBIMENTO:</b> {row['TURNO RECEBIMENTO']}<br>
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

# 10. Dados para a legenda
unique_markers = df['NOME FANTASIA'].nunique()

truck_usage_list = "<ul>"
for _, row in df_group.iterrows():
    truck_usage_list += (
        f"<li><b>{row['CAMINHAO']}</b> - "
        f"Faturamento: R$ {row['VALOR_TOTAL']:.2f} / "
        f"Uso: {row['USO_%']:.0f}%</li>"
    )
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
    <b>💰 Faturamento Total de Todos os Caminhões:</b> R$ {faturamento_total:.2f}<br>
    <b>🔄 Atualizado:</b> 24/04/2025<br><br>
    <b>Caminhões:</b> {truck_usage_list}
</div>
'''
mapa.get_root().html.add_child(folium.Element(legend_html))

# 11. Salvar o mapa em um arquivo HTML
mapa.save('mapa_clientes.html')
print("Mapa salvo como mapa_clientes.html")
