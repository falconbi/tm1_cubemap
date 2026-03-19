import requests

TM1_CONFIG = {
    'address':       '192.168.1.178',
    'port':          4444,
    'database':      'TM1 Governance',
    'client_id':     'N10fSjnjkzYSNJl4djGSBL2OpLbalyXX',
    'client_secret': 'VgkxMKlitfPg3K4b4kERoK0SVNjdA2UzdW6Ig1OlNE2bcho8l0mytOTWh2SJVmvH',
    'user':          'akadmin',
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
