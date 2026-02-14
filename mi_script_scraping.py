import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os

# --- CONFIGURACIÓN ---
# Puedes agregar todas las URLs de Argenprop que quieras en esta lista
URLS_BUSQUEDA = [
    "https://www.argenprop.com/departamento-alquiler-barrio-palermo",
    "https://www.argenprop.com/departamento-alquiler-barrio-recoleta"
]
ARCHIVO_VISTOS = "avisos_enviados.txt"

def obtener_propiedades(urls):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    todas_las_propiedades = []

    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Argenprop usa la clase 'listing__item' para cada aviso
            items = soup.find_all('div', class_='listing__item')

            for item in items:
                try:
                    card_click = item.find('a', class_='card')
                    if not card_click: continue
                    
                    link = "https://www.argenprop.com" + card_click['href']
                    precio = item.find('p', class_='card__price').text.strip()
                    direccion = item.find('p', class_='card__address').text.strip()
                    
                    todas_las_propiedades.append({
                        'id': link,
                        'texto': f"📍 {direccion}\n💰 {precio}\n🔗 {link}"
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error al acceder a {url}: {e}")
            
    return todas_las_propiedades

def filtrar_nuevos(propiedades):
    # Verificamos si ya tenemos una lista de avisos enviados
    if os.path.exists(ARCHIVO_VISTOS):
        with open(ARCHIVO_VISTOS, 'r') as f:
            vistos = f.read().splitlines()
    else:
        vistos = []

    nuevos = [p for p in propiedades if p['id'] not in vistos]
    
    # Guardamos los nuevos IDs para no repetirlos mañana
    if nuevos:
        with open(ARCHIVO_VISTOS, 'a') as f:
            for n in nuevos:
                f.write(n['id'] + "\n")
            
    return nuevos

def enviar_email(nuevos_avisos):
    # GitHub Actions inyecta estas variables desde los "Secrets"
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    if not email_user or not email_pass:
        print("Error: No se encontraron las credenciales en los Secrets de GitHub.")
        return

    cuerpo = f"Se encontraron {len(nuevos_avisos)} nuevas propiedades que coinciden con tus búsquedas:\n\n"
    cuerpo += "\n\n---\n\n".join([a['texto'] for a in nuevos_avisos])
    
    msg = MIMEText(cuerpo)
    msg['Subject'] = f"🏠 {len(nuevos_avisos)} Nuevos Avisos Inmobiliarios"
    msg['From'] = email_user
    msg['To'] = email_user # Te lo envías a ti mismo

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        print("Email enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el email: {e}")

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    avisos_totales = obtener_propiedades(URLS_BUSQUEDA)
    novedades = filtrar_nuevos(avisos_totales)

    if novedades:
        enviar_email(novedades)
    else:
        print("No se encontraron propiedades nuevas hoy.")
