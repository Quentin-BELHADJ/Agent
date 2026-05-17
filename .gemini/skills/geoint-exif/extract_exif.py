import sys
import json
import exifread

def convert_to_decimal(values, ref):
    """Convertit les coordonnées EXIF en degrés décimaux."""
    try:
        degrees = values[0].num / values[0].den
        minutes = values[1].num / values[1].den
        seconds = values[2].num / values[2].den
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None

def extract_exif(image_path):
    result = {
        "status": "success",
        "has_gps": False,
        "data": {}
    }
    
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            if not tags:
                result["status"] = "error"
                result["message"] = "Aucune donnée EXIF trouvée."
                return json.dumps(result, indent=2)

            # Extraction des données de base
            if 'Image DateTime' in tags:
                result["data"]["date"] = str(tags['Image DateTime'])
            if 'Image Make' in tags and 'Image Model' in tags:
                result["data"]["camera"] = f"{tags['Image Make']} {tags['Image Model']}"
            
            # Extraction et conversion GPS
            if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                lat = convert_to_decimal(tags['GPS GPSLatitude'].values, str(tags.get('GPS GPSLatitudeRef', 'N')))
                lon = convert_to_decimal(tags['GPS GPSLongitude'].values, str(tags.get('GPS GPSLongitudeRef', 'E')))
                
                if lat and lon:
                    result["has_gps"] = True
                    result["data"]["gps"] = {"latitude": lat, "longitude": lon}
                    result["data"]["google_maps_link"] = f"https://www.google.com/maps?q={lat},{lon}"

        return json.dumps(result, indent=2)

    except FileNotFoundError:
        return json.dumps({"status": "error", "message": f"Fichier introuvable : {image_path}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Chemin de l'image manquant."}))
        sys.exit(1)
        
    print(extract_exif(sys.argv[1]))