// GeoJSON simplificado de estados de México
const MEXICO_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": { "name": "Coahuila" },
            "id": "Coahuila",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-103.5, 29.5], [-103.5, 25.5], [-100.5, 25.5], 
                    [-100.5, 29.5], [-103.5, 29.5]
                ]]
            }
        },
        {
            "type": "Feature", 
            "properties": { "name": "Nuevo León" },
            "id": "Nuevo León",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-100.5, 27.5], [-100.5, 23.5], [-99.0, 23.5],
                    [-99.0, 27.5], [-100.5, 27.5]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": { "name": "Tamaulipas" },
            "id": "Tamaulipas", 
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-99.0, 27.5], [-99.0, 22.5], [-97.0, 22.5],
                    [-97.0, 27.5], [-99.0, 27.5]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": { "name": "Durango" },
            "id": "Durango",
            "geometry": {
                "type": "Polygon", 
                "coordinates": [[
                    [-107.0, 26.5], [-107.0, 23.0], [-103.5, 23.0],
                    [-103.5, 26.5], [-107.0, 26.5]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": { "name": "Sinaloa" },
            "id": "Sinaloa",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-109.5, 27.0], [-109.5, 22.5], [-105.5, 22.5],
                    [-105.5, 27.0], [-109.5, 27.0]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": { "name": "Michoacán" },
            "id": "Michoacán",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-103.5, 20.5], [-103.5, 17.5], [-100.5, 17.5],
                    [-100.5, 20.5], [-103.5, 20.5]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": { "name": "Querétaro" },
            "id": "Querétaro",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-100.5, 21.5], [-100.5, 20.0], [-99.0, 20.0],
                    [-99.0, 21.5], [-100.5, 21.5]
                ]]
            }
        }
    ]
};

// Función para obtener el GeoJSON
function getMexicoGeoJSON() {
    return MEXICO_GEOJSON;
}