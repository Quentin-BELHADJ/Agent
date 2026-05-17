import sys
import json
import easyocr

def extract_text(image_path):
    result = {
        "status": "success",
        "text_found": False,
        "extracted_text": ""
    }
    
    try:
        # Initialisation du lecteur avec un panel de langues (Anglais, Français, Espagnol, Allemand, Tchèque)
        # Note : le paramètre gpu=False garantit la compatibilité sur toutes les machines
        reader = easyocr.Reader(['en', 'fr', 'es', 'de', 'cs'], gpu=False, verbose=False)
        
        # detail=0 retourne une simple liste de textes, sans les coordonnées géométriques (bounding boxes)
        text_list = reader.readtext(image_path, detail=0)
        
        # Nettoyage et assemblage du texte
        clean_text = " ".join(text_list).strip()
        
        if clean_text:
            result["text_found"] = True
            result["extracted_text"] = clean_text
            
        return json.dumps(result, indent=2)

    except Exception as e:
        # EasyOCR peut lever diverses exceptions si le fichier est corrompu ou illisible
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Chemin de l'image manquant."}))
        sys.exit(1)
        
    print(extract_text(sys.argv[1]))