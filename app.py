# Géolocalisation et filtres (commercial, département, entreprise)

import streamlit as st
import folium
import pandas as pd
from streamlit_folium import folium_static
from geopy.distance import geodesic

# Charger les données
csv_file = "global_clients_valid_coords.csv"

try:
    df = pd.read_csv(csv_file)

    # Vérifie si les colonnes nécessaires existent
    required_columns = {'latitude',
                        'longitude',
                        'Nom tiers',
                        'Rep1 Tiers',
                        'Département',
                        'Tel 1 Ct',
                        'Rue1 Tiers'
                        }
    if not required_columns.issubset(df.columns):
        st.error(f"Le fichier CSV ne contient pas toutes les colonnes nécessaires: {required_columns}")
        st.stop()

    # Supprimer les lignes avec des coordonnées manquantes (si nécessaire)
    # df = df.dropna(subset=['latitude', 'longitude'])

    # Convertir les colonnes latitude et longitude en float (si nécessaire)
    # df['latitude'] = df['latitude'].astype(float)
    # df['longitude'] = df['longitude'].astype(float)

    # Début de l'interface Streamlit
    st.title("📍 Visualisation des Clients Géocodés")
    st.write("Filtrez par commercial, département ou recherchez une entreprise spécifique.")

    # Sélection d'un commercial
    commercial_list = df["Rep1 Tiers"].dropna().unique().tolist()
    selected_commercial = st.selectbox("🧑‍💼 Sélection Commercial", ["Tous"] + sorted(commercial_list))

    # Sélection d'un département
    department_list = df["Département"].dropna().unique().tolist()
    selected_department = st.selectbox("🌍 Sélection Département", ["Tous"] + sorted(department_list))

    # Appliquer les filtres
    df_filtered = df.copy()

    if selected_commercial != "Tous":
        df_filtered = df_filtered[df_filtered["Rep1 Tiers"] == selected_commercial]

    if selected_department != "Tous":
        df_filtered = df_filtered[df_filtered["Département"] == selected_department]

    # Sélection d'une entreprise spécifique
    selected_company = st.selectbox("🏢 Rechercher une entreprise", [""] + sorted(df_filtered["Nom tiers"].unique()))

    # Fonction pour filtrer les entreprises dans un rayon de 5 km
    def get_nearby_companies(lat, lon, radius_km=5):
        def haversine(row):
            point1 = (lat, lon)
            point2 = (row['latitude'], row['longitude'])
            return geodesic(point1, point2).km <= radius_km

        return df_filtered[df_filtered.apply(haversine, axis=1)]

    # Fonction pour créer une carte Folium avec zoom dynamique
    def create_map(data, center_lat=None, center_lon=None, zoom=None):
        if center_lat is None or center_lon is None:
            center_lat, center_lon = data['latitude'].mean(), data['longitude'].mean()
            zoom = 6 if zoom is None else zoom  # Zoom large si aucune entreprise sélectionnée

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)

        for _, row in data.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"{row['Nom tiers']},\n {row['Tel 1 Ct']},\n {row['Rue1 Tiers']}, {row['Département']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        return m

    # Si une entreprise est sélectionnée, centrer la carte dessus et afficher les entreprises à 5 km
    if selected_company:
        selected_row = df_filtered[df_filtered["Nom tiers"] == selected_company].iloc[0]
        center_lat, center_lon = selected_row["latitude"], selected_row["longitude"]

        # Trouver les entreprises dans un rayon de 5 kms
        nearby_companies = get_nearby_companies(center_lat, center_lon)

        st.write(f"📍 **Centré sur : {selected_company}** ({center_lat}, {center_lon})")
        st.write(f"🏢 **Entreprises sur 5kms de rayon :** {len(nearby_companies)} trouvées")

        # Générer et afficher la carte avec un zoom sur l'entreprise
        map_obj = create_map(nearby_companies, center_lat, center_lon, zoom=17)
        folium_static(map_obj)
    elif selected_department != "Tous":
        # Afficher la carte complète du département avec un zoom sur le département
        map_obj = create_map(df_filtered[df_filtered["Département"] == selected_department], zoom=9)
        folium_static(map_obj)
    else:
        # Afficher la carte complète avec un zoom plus large
        map_obj = create_map(df_filtered, zoom=6)
        folium_static(map_obj)

except FileNotFoundError:   # Retourne une erreur si le fichier CSV n'est pas trouvé
    st.error(f"Le fichier `{csv_file}` est introuvable. Assurez-vous qu'il est disponible.")
