import requests

def get_location():
    try:
        data = requests.get("http://ip-api.com/json", timeout=5).json()
        if data.get("status") != "success":
            print(f"Erreur API : {data.get('message')}")
            return None
        return {
            "ville"    : data.get("city"),
            "région"   : data.get("regionName"),
            "pays"     : data.get("country"),
            "latitude" : data.get("lat"),
            "longitude": data.get("lon"),
        }
    except requests.RequestException as e:
        print(f"Erreur : {e}")
        return None

if __name__ == "__main__":
    print(get_location())