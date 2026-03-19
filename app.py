"""
app.py — TM1 CubeMap Flask Server
──────────────────────────────────
Serves the CubeMap diagram and provides a live refresh API
that pulls fresh data from TM1 V12 on demand.

Usage:
    cd ~/apps/tm1_governance
    ./run.sh

Then open: http://localhost:8080

Endpoints:
    GET  /                   → serves tm1_cube_lineage.html
    GET  /api/model          → returns cached tm1_model.json
    POST /api/refresh        → re-extracts from TM1, updates cache
    GET  /api/status         → server + last-refresh info
"""

import os
import re
import sys
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, abort, request

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
MODEL_FILE = BASE_DIR / 'cube_map' / 'tm1_model.json'

sys.path.insert(0, str(BASE_DIR))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('cubemap')

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(BASE_DIR))

# Thread lock — prevents two simultaneous refreshes
_refresh_lock = threading.Lock()
_refresh_status = {
    'running':    False,
    'lastRun':    None,
    'lastResult': 'never',
    'error':      None,
}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the CubeMap HTML diagram."""
    static_dir = BASE_DIR / 'cube_map' / 'static'
    if not (static_dir / 'tm1_cube_lineage.html').exists():
        abort(404, 'cube_map/static/tm1_cube_lineage.html not found')
    return send_from_directory(str(static_dir), 'tm1_cube_lineage.html')


@app.route('/workbook-tree')
def workbook_tree():
    """Serve the PAW Workbook Tree governance explorer."""
    static_dir = BASE_DIR / 'paw_tree' / 'static'
    if not (static_dir / 'tm1_paw_tree.html').exists():
        abort(404, 'paw_tree/static/tm1_paw_tree.html not found')
    return send_from_directory(str(static_dir), 'tm1_paw_tree.html')


@app.route('/health-monitor')
def health_monitor():
    """Serve the Health Monitor dashboard."""
    static_dir = BASE_DIR / 'health_monitor' / 'static'
    if not (static_dir / 'tm1_health_monitor.html').exists():
        abort(404, 'health_monitor/static/tm1_health_monitor.html not found')
    return send_from_directory(str(static_dir), 'tm1_health_monitor.html')


@app.route('/api/model')
def api_model():
    """Return the cached TM1 model JSON."""
    if not MODEL_FILE.exists():
        return jsonify({'error': 'Model cache not found — POST /api/refresh to extract'}), 404
    with open(MODEL_FILE, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Re-extract the TM1 model and update the cache."""
    if _refresh_status['running']:
        return jsonify({'status': 'already_running'}), 409

    def do_refresh():
        with _refresh_lock:
            _refresh_status['running'] = True
            _refresh_status['error'] = None
            try:
                from cube_map.extract_tm1_model import extract_model
                extract_model()
                _refresh_status['lastResult'] = 'ok'
                log.info('Model refresh completed successfully')
            except Exception as e:
                _refresh_status['lastResult'] = 'error'
                _refresh_status['error'] = str(e)
                log.error(f'Model refresh failed: {e}')
            finally:
                _refresh_status['running'] = False
                _refresh_status['lastRun'] = datetime.now(timezone.utc).isoformat()

    threading.Thread(target=do_refresh, daemon=True).start()
    return jsonify({'status': 'started'})


@app.route('/api/status')
def api_status():
    """Return server info and last-refresh status."""
    return jsonify({
        'status':      'ok',
        'baseDir':     str(BASE_DIR),
        'modelFile':   str(MODEL_FILE),
        'modelCached': MODEL_FILE.exists(),
        'refresh':     _refresh_status,
    })


@app.route('/api/groups')
def api_groups():
    """Serve the groups.json security configuration."""
    groups_file = BASE_DIR / 'core' / 'groups.json'
    if not groups_file.exists():
        return jsonify({'groups': []})
    with open(groups_file, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/paw/tree')
def api_paw_tree():
    try:
        from core.paw_connect import get_paw_session, get_asset_by_id, PAW_CONFIG
        from urllib.parse import quote
        import json as _json

        session = get_paw_session()
        csrf    = session.cookies.get('ba-sso-csrf', '')
        headers = {'ba-sso-authenticity': csrf}
        paw     = PAW_CONFIG['paw_host']

        def encode_path(path):
            return quote(quote(path, safe=''), safe='')

        def extract_tabs(content):
            tabs = []
            if not content or 'layout' not in content:
                return tabs
            def walk(items, tab_name=None):
                for item in items:
                    if item.get('type') == 'container':
                        name = item.get('title',{}).get('translationTable',{}).get('Default','Tab')
                        walk(item.get('items',[]), name)
                    else:
                        pa  = item.get('features',{}).get('PAProperties',{})
                        tm1 = pa.get('tm1',{})
                        if tm1.get('cube') and tab_name:
                            if not any(t['name']==tab_name for t in tabs):
                                tabs.append({'name':tab_name,'type':'Cube View',
                                    'server':tm1.get('server',''),'cube':tm1.get('cube',''),'view':tm1.get('view','')})
                        walk(item.get('items',[]), tab_name)
            walk(content.get('layout',{}).get('items',[]))
            if not tabs:
                for item in content.get('layout',{}).get('items',[]):
                    if item.get('type') == 'container':
                        tabs.append({'name':item.get('title',{}).get('translationTable',{}).get('Default','Tab'),
                            'type':'View','server':'','cube':'','view':''})
            return tabs

        def build_node(asset, with_content=False):
            sp = asset.get('system_properties',{})
            node = {
                'id':asset['id'],'name':asset['name'],'path':asset['path'],
                'type':'book' if asset['type'] in ('dashboard','workbench') else 'folder',
                'assetType':asset['type'],'state':asset.get('state',''),
                'createdBy':sp.get('created_user_pretty_name',''),
                'createdDate':sp.get('created_date',''),
                'modifiedBy':sp.get('modified_user_pretty_name',''),
                'modifiedDate':sp.get('modified_date',''),
                'usedBy':sp.get('used_user_pretty_name',''),
                'usedDate':sp.get('used_date',''),
                'permissions':sp.get('permissions',[]),
                'version':asset.get('custom_properties',{}).get('version',''),
                'description':asset.get('description',''),
            }
            if with_content:
                full = get_asset_by_id(session, asset['id'], expand_content=True)
                node['tabs'] = extract_tabs(full.get('content',{}))
            return node

        def walk_folder(path):
            encoded = encode_path(path)
            r = session.get(f"{paw}/pacontent/v1/Assets(path='{encoded}')/Assets", headers=headers)
            r.raise_for_status()
            children = []
            for asset in r.json().get('value',[]):
                if asset['type'] == 'folder':
                    node = build_node(asset)
                    node['children'] = walk_folder(asset['path'])
                    children.append(node)
                else:
                    node = build_node(asset, with_content=True)
                    node['children'] = []
                    children.append(node)
            return children

        tree = [{'id':'f-shared','type':'folder','name':'Shared Content','path':'/shared',
                 'system':True,'createdBy':'','modifiedDate':'',
                 'description':'Team content shared across all users.',
                 'children':walk_folder('/shared')}]

        log.info(f"PAW tree built successfully")
        return jsonify({'status':'ok','tree':tree})

    except Exception as e:
        log.error(f'PAW tree error: {e}')
        return jsonify({'status':'error','message':str(e)}), 500


if __name__ == '__main__':
    log.info('══════════════════════════════════════════')
    log.info('  TM1 CubeMap Server')
    log.info(f'  Serving from: {BASE_DIR}')
    log.info(f'  Model file:   {MODEL_FILE}')
    log.info(f'  Model cached: {"✅ yes" if MODEL_FILE.exists() else "⚠️  no — refresh to extract"}')
    log.info('══════════════════════════════════════════')
    log.info('  Open: http://localhost:8080               (Cube Lineage)')
    log.info('  Open: http://localhost:8080/workbook-tree (Workbook Tree)')
    log.info('  API:  http://localhost:8080/api/paw/tree  (PAW Live Data)')
    log.info('══════════════════════════════════════════')
    app.run(host='0.0.0.0', port=8080, debug=False)
