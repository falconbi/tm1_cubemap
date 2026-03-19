import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

TM1_CONFIG = {
    'address':       os.environ['TM1_ADDRESS'],
    'port':          int(os.environ['TM1_PORT']),
    'database':      os.environ['TM1_DATABASE'],
    'client_id':     os.environ['TM1_CLIENT_ID'],
    'client_secret': os.environ['TM1_CLIENT_SECRET'],
    'user':          os.environ['TM1_USER'],
}

def get_session():
    cfg = TM1_CONFIG
    base = f"http://{cfg['address']}:{cfg['port']}/tm1"

    auth = requests.post(
        f"{base}/auth/v1/session",
        auth=(cfg['client_id'], cfg['client_secret']),
        headers={'Content-Type': 'application/json'},
        json={'User': cfg['user']}
    )

    token = auth.cookies.get('TM1SessionId')
    session = requests.Session()
    session.cookies.set('TM1SessionId', token)
    session.headers.update({'Content-Type': 'application/json'})
    session.base_url = f"{base}/api/v1/Databases('{cfg['database']}')"
    return session

if __name__ == '__main__':
    session = get_session()
    response = session.get(f"{session.base_url}/Cubes")
    cubes = response.json()['value']
    print(f"Connected to: {TM1_CONFIG['database']}")
    print(f"Cubes found: {len(cubes)}")
    for cube in cubes:
        print(f"  {cube['Name']}")
