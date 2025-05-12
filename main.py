from fastapi import FastAPI, Request, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import io
import qrcode
import socket
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="Assistance Réglementaire Pêche API", version="1.0.0")

# Configuration des templates
templates = Jinja2Templates(directory="templates")

# Configuration CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des fichiers statiques
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Middleware pour vérifier l'authentification
async def check_auth(request: Request):
    # Vérifier si l'utilisateur est connecté (via cookie ou session)
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return False
    return True

# Fonction pour vérifier l'authentification et rediriger si nécessaire
async def require_auth(request: Request):
    is_authenticated = await check_auth(request)
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return None

@app.get("/")
async def root(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/api/auth/login")
async def login(request: Request):
    try:
        # Accepter à la fois JSON et FormData
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            user_data = await request.json()
            email = user_data.get("email")
            password = user_data.get("password")
        else:
            form_data = await request.form()
            email = form_data.get("email")
            password = form_data.get("password")
        
        # Vérifier que tous les champs requis sont présents
        if not all([email, password]):
            raise ValueError("Email et mot de passe sont requis")
            
        # Ici, vous devriez vérifier les identifiants dans votre base de données
        # Pour cet exemple, nous acceptons n'importe quel email/mot de passe
        
        # Créer une réponse avec un cookie d'authentification
        response = JSONResponse(content={"status": "success", "message": "Connexion réussie"})
        response.set_cookie(key="auth_token", value="demo_token", httponly=True, max_age=3600)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erreur de connexion: {str(e)}")

@app.post("/api/auth/register")
async def register(request: Request):
    try:
        # Accepter à la fois JSON et FormData
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            user_data = await request.json()
            name = user_data.get("name")
            email = user_data.get("email")
            password = user_data.get("password")
        else:
            form_data = await request.form()
            name = form_data.get("name")
            email = form_data.get("email")
            password = form_data.get("password")
        
        # Vérifier que tous les champs requis sont présents
        if not all([name, email, password]):
            raise ValueError("Tous les champs sont requis")
            
        # Ici, vous devriez enregistrer l'utilisateur dans votre base de données
        # Pour cet exemple, nous simulons un enregistrement réussi
        
        return JSONResponse(content={"status": "success", "message": "Inscription réussie"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'inscription: {str(e)}")

@app.get("/reglements")
async def reglements_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("reglements.html", {"request": request})

@app.get("/especes")
async def especes_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("especes.html", {"request": request})

@app.get("/calendrier")
async def calendrier_page(request: Request):
    return templates.TemplateResponse("calendrier.html", {"request": request})

@app.get("/assistance")
async def assistance_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("assistance_new.html", {"request": request})

@app.get("/documents")
async def documents_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/carte")
async def carte_page(request: Request):
    return templates.TemplateResponse("carte.html", {"request": request})

@app.get("/learning")
async def learning_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("learning.html", {"request": request})

@app.get("/contribution")
async def contribution_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("contribution.html", {"request": request})

@app.get("/report")
async def report_page(request: Request):
    # Vérifier l'authentification
    redirect = await require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("report.html", {"request": request})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def generate_qr_code(ip, port):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    data = f"http://{ip}:{port}"
    qr.add_data(data)
    qr.make(fit=True)
    
    # Créer une représentation ASCII améliorée
    matrix = qr.get_matrix()
    output = ""
    for row in matrix:
        line = ""
        for cell in row:
            if cell:
                line += "██"
            else:
                line += "  "
        output += line + "\n"
    print(output)

def run_server(host, port):
    # Utilisation de uvicorn.run avec reload=False pour éviter les conflits
    # quand on exécute plusieurs instances
    uvicorn.run("main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    print("Choisissez une option de démarrage :")
    print("1. Localhost (127.0.0.1)")
    print("2. Mode test (0.0.0.0)")
    print("3. Les deux")
    
    choice = input("Votre choix (1-3): ")
    port = 8003
    
    if choice == "1":
        print(f"\nServeur démarré sur http://127.0.0.1:{port}")
        run_server("127.0.0.1", port)
    elif choice == "2":
        ip = get_local_ip()
        print(f"\nServeur démarré sur http://{ip}:{port}")
        print(f"\nScannez ce QR code pour accéder à l'application:")
        generate_qr_code(ip, port)
        run_server("0.0.0.0", port)
    elif choice == "3":
        ip = get_local_ip()
        print(f"\nServeurs démarrés sur:")
        print(f"- http://127.0.0.1:{port}")
        print(f"- http://{ip}:{port} (accessible depuis d'autres appareils)")
        print(f"\nScannez ce QR code pour accéder à l'application:")
        generate_qr_code(ip, port)
        
        # Utilisation d'un processus séparé pour le serveur localhost
        import multiprocessing
        
        # Fonction pour exécuter le serveur localhost dans un processus séparé
        def run_localhost_server():
            run_server("127.0.0.1", port)
        
        # Démarrer le serveur localhost dans un processus séparé
        localhost_process = multiprocessing.Process(target=run_localhost_server)
        localhost_process.daemon = True  # Le processus s'arrêtera quand le programme principal s'arrête
        localhost_process.start()
        
        # Exécuter le serveur 0.0.0.0 dans le processus principal
        run_server("0.0.0.0", port)
    else:
        print("Choix invalide. L'application va s'arrêter.")