import random
import csv
from flask import Flask, request, jsonify
from geopy.geocoders import Nominatim
from flask_cors import CORS
import time as tp
import numpy as np
import folium
from fourmis import *
from tabou import *
import json
#---------------------------------------------------------------Fonctions----------------------------------------------------------------
def load_random_cities_from_csv(file_path, num_cities):
    cities = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            cities.append(row[0]) 
    return random.sample(cities, num_cities)

def load_villes_names_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        villes_names = {}
        for key, value in data.items():
            villes_names[key] = [ville[0] for ville in value['villes']]
    return villes_names

def load_all_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        all_data = {}
        for key, value in data.items():
            all_data[key] = {
                'Pulp': {
                    'Distance': value['Pulp']['Distance'],
                    'NombreCamion': value['Pulp']['NombreCamion'],
                    'Temps': value['Pulp']['Temps']
                },
                'Fourmi': {
                    'Distance': value['Fourmi']['Distance'],
                    'NombreCamion': value['Fourmi']['NombreCamion'],
                    'Temps': value['Fourmi']['Temps']
                },
                'Tabu': {
                    'Distance': value['Tabu']['Distance'],
                    'NombreCamion': value['Tabu']['NombreCamion'],
                    'Temps': value['Tabu']['Temps']
                }
            }
    return all_data


app = Flask(__name__)
CORS(app)  



@app.route('/api/fourmis', methods=['POST'])
def fourmie_route():
    data = request.json
    t0 = tp.time()
    # Declare global variables at the module level
    nb_fourmis = 180
    max_iteration = 900
    t_evaporation = 0.1  
    i_phero, i_visi, depot_phero = 1, 2, 100  
    capacite_max = 20
    cache_probabilites = {}

    random.seed(48)

    city_names = data
    villes = get_city_coordinates(city_names)
    distances = generate_distance_matrix(villes)
    nom_ville = [city[0] for city in villes]
    ville_d = {nom_ville[0]: 0} 
    ville_d.update({valeur: random.randint(1, 10) for valeur in nom_ville[1:]})

    n = len(nom_ville)
    v_phero = np.ones((n, n), dtype=float) - np.eye(n)  
    visibilités = 1 / (distances + np.eye(n))  

    # Initialisation des solutions
    meilleur_solution, meilleur_distance, meilleur_capacite = None, float('inf'), None
    solution, capacite, distance = resoudre(v_phero, meilleur_distance, meilleur_solution, meilleur_capacite, max_iteration, nb_fourmis,nom_ville, distances, capacite_max, ville_d, v_phero, visibilités, i_phero, i_visi, cache_probabilites,t_evaporation, depot_phero)
    tf = tp.time()
    afficher_carte(solution, nom_ville, distances)
    return jsonify({
        'message': 'Solution trouvée',
        'solution': solution,
        'capacite': capacite,
        'distance': distance,
        'nb_camions': len(solution),
        'temps_execution': tf - t0,
        'test': ville_d
    })

@app.route('/api/tabou', methods=['POST'])
def tabou_route():
    start = tp.process_time()
    data = request.json

    random.seed(48)

    city_names = data
    villes = get_city_coordinates(city_names)
    distances = generate_distance_matrix(villes)
    distance_matrix = distances
    nom_ville = [city[0] for city in villes]
    ville_d = {nom_ville[0]: 0} 
    ville_d.update({valeur: random.randint(1, 10) for valeur in nom_ville[1:]})

    # Initialisation des paramètres
    nb_villes = len(nom_ville)
    capacite_max = 20
    path = generate_path(nb_villes, capacite_max, ville_d, nom_ville)
    solution_initiale = path


    # Run multi start
    nb_test = 100
    sol_max, val_max, nb_test, solutions, best_solutions, poids = multi_start(nb_villes, solution_initiale, distance_matrix, nb_test, nom_ville, ville_d, capacite_max)
    stop = tp.process_time()

    create_map_with_routes(sol_max)

    return jsonify({
        'message': 'Solution trouvée',
        'solution': sol_max,
        'capacite': poids,
        'distance': val_max,
        'nb_camions': len(sol_max),
        'temps_execution': stop - start,
        'test': ville_d
    })


@app.route('/api/reset', methods=['POST'])
def get_reset():
    data = request.json
    city_name = data.get('city_name')
    if city_name == 'reset':
        m = folium.Map(location=[48.8566, 2.3522], zoom_start=6)
        m.save('map.html')
        return jsonify({'message': 'Map reset successfully'})
    else:
        return jsonify({'error': 'Location not found'}), 404
    

@app.route('/api/random_cities', methods=['GET'])
def get_random_cities():
    num_cities = int(request.args.get('num_cities', 10))  
    file_path = 'cities.csv' 
    random_cities = load_random_cities_from_csv(file_path, num_cities)
    geolocator = Nominatim(user_agent="city_locator")
    cities_info = []
    for city_name in random_cities:
        location = geolocator.geocode(city_name)
        if location:
            cities_info.append(
                {    
                    'Cityname': city_name,
                }
            )
    return jsonify(cities_info)

@app.route('/api/test', methods=['GET'])
def result_json():
    file_path = 'result.json'
    villes_names = load_all_data_from_json(file_path)
    return jsonify(villes_names)

if __name__ == '__main__':
    app.run(debug=True)



