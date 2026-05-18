import requests

def get_location():
    try:
        data = requests.get("https://ipapi.co/json/", timeout=5).json()
        return {
            "ville"    : data.get("city"),
            "région"   : data.get("region"),
            "pays"     : data.get("country_name"),
            "latitude" : data.get("latitude"),
            "longitude": data.get("longitude"),
        }
    except requests.RequestException as e:
        print(f"Erreur : {e}")
        return None

if __name__ == "__main__":
    print(get_location())