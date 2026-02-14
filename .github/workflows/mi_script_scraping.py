import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os

# --- CONFIGURACIÓN DE MÚLTIPLES BÚSQUEDAS ---
URLS_BUSQUEDA = [
    "https://www.argenprop.com/departamento-alquiler-barrio-palermo",
    "https://www.argenprop.com/departamento-alquiler-barrio-recoleta",
    "https://www.argenprop.com/departamento-alquiler-barrio-belgrano"
]
ARCHIVO_VISTOS = "avisos_enviados.txt"

def obtener_propiedades(urls):
    headers = {'User-Agent': 'Mozilla/5.0'}
    todas_las_propiedades = []

    for url in urls:
        print(f"Buscando en: {url}")
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_='listing__item')

            for item in items:
                try:
                    link = "https://www.argenprop.com" + item.find('a')['href']
                    precio = item.find('p', class_='card__price').text.strip()
                    direccion = item.find('p', class_='card__address').text.strip()
                    
                    todas_las_propiedades.append({
                        'id': link,
                        'texto': f"📍 {direccion} - 💰 {precio}\n🔗 {link}"
                    })
                except:
                    continue
        except Exception as e:
            print(f"Error al acceder a {url}: {e}")
            
    return todas_las_propiedades

def filtrar_nuevos(propiedades):
    if os.path.exists(ARCHIVO_VISTOS):
        with open(ARCHIVO_VISTOS, 'r') as f:
            vistos = f.read().splitlines()
    else:
        vistos = []

    nuevos = [p for p in propiedades if p['id'] not in vistos]
    
    with open(ARCHIVO_VISTOS, 'a') as f:
        for n in nuevos:
            f.write(n['id'] + "\n")
            
    return nuevos

def enviar_email(nuevos_avisos):
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    # Armamos un cuerpo de mail con todas las novedades juntas
    cuerpo = f"Se encontraron {len(nuevos_avisos)} nuevas propiedades:\n\n"
    cuerpo += "\n\n---\n\n".join([a['texto'] for a in nuevos_avisos])
    
    msg = MIMEText(cuerpo)
    msg['Subject'] = f"🔔 {len(nuevos_avisos)} Novedades Inmobiliarias"
    msg['From'] = email_user
    msg['To'] = email_user

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(email_user, email_pass)
        server.send_message(msg)

# --- EJECUCIÓN ---
avisos_totales = obtener_propiedades(URLS_BUSQUEDA)
novedades = filtrar_nuevos(avisos_totales)

if novedades:
    enviar_email(novedades)
    print(f"Proceso terminado. {len(novedades)} avisos nuevos enviados.")
else:
    print("No hubo novedades en ninguna de las URLs.")
