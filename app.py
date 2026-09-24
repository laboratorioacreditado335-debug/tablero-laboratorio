import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
DB_NAME = "bitacora.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emisor TEXT NOT NULL,
                receptor TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                contenido TEXT NOT NULL,
                estado TEXT DEFAULT 'Pendiente',
                fecha TEXT NOT NULL,
                respuestas TEXT DEFAULT '[]'
            )
        ''')
        conn.commit()

init_db()

# --- PLANTILLA HTML/CSS/JS INTEGRADA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitácora Digital de Laboratorio</title>
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --normal: #10b981;
            --auditoria: #f59e0b;
            --urgente: #ef4444;
        }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .btn-main {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .btn-main:hover { opacity: 0.9; }

        /* Modal minimalista */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(4px);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal {
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 25px;
            border-radius: 12px;
            width: 90%;
            max-width: 480px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }

        .form-group { margin-bottom: 15px; }
        label { display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 5px; }
        select, textarea, input {
            width: 100%;
            padding: 10px;
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 6px;
            box-sizing: border-box;
        }

        .priority-selector {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }

        .priority-btn {
            padding: 8px;
            border: 1px solid var(--border);
            background: #0f172a;
            color: var(--text);
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            font-size: 0.85rem;
        }

        .priority-btn.selected[data-val="Normal"] { border-color: var(--normal); color: var(--normal); background: rgba(16, 185, 129, 0.1); }
        .priority-btn.selected[data-val="Auditoría"] { border-color: var(--auditoria); color: var(--auditoria); background: rgba(245, 158, 11, 0.1); }
        .priority-btn.selected[data-val="Urgente"] { border-color: var(--urgente); color: var(--urgente); background: rgba(239, 68, 68, 0.1); }

        /* Feed de Tarjetas */
        .card {
            background: var(--card-bg);
            border-radius: 10px;
            border-left: 5px solid var(--border);
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .card.Urgente { border-left-color: var(--urgente); }
        .card.Auditoría { border-left-color: var(--auditoria); }
        .card.Normal { border-left-color: var(--normal); }

        .card-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .badge.Urgente { background: rgba(239, 68, 68, 0.2); color: var(--urgente); }
        .badge.Auditoría { background: rgba(245, 158, 11, 0.2); color: var(--auditoria); }
        .badge.Normal { background: rgba(16, 185, 129, 0.2); color: var(--normal); }

        .replies {
            margin-top: 12px;
            padding-left: 12px;
            border-left: 2px solid var(--border);
            font-size: 0.88rem;
        }

        .reply-item {
            margin-top: 6px;
            color: #cbd5e1;
        }

        .action-row {
            margin-top: 12px;
            display: flex;
            gap: 10px;
        }

        .btn-ack {
            background: var(--urgente);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }

        .btn-reply {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }

        .audio-banner {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--urgente);
            color: var(--urgente);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
            text-align: center;
        }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h2>📋 Bitácora Digital</h2>
        <div>
            <button class="btn-main" onclick="activarSonido()">🔔 Activar Sonido</button>
            <button class="btn-main" onclick="abrirModal()">+ Crear Mensaje</button>
        </div>
    </header>

    <div id="audioBanner" class="audio-banner">
        🚨 <strong>ALERTA URGENTE ACTIVA</strong> - Requiere confirmación de Enterado.
    </div>

    <div id="messagesContainer"></div>
</div>

<!-- Modal para Crear Mensaje -->
<div class="modal-overlay" id="modal">
    <div class="modal">
        <h3>Nuevo Mensaje / Nota</h3>
        
        <div class="form-group">
            <label>De (Emisor):</label>
            <select id="emisor">
                <option value="Jeison Altamar">Jeison Altamar</option>
                <option value="Nicolas Arevalo">Nicolas Arevalo</option>
                <option value="Jhojan Pasachoa">Jhojan Pasachoa</option>
                <option value="Sonia Gonzales">Sonia Gonzales</option>
            </select>
        </div>

        <div class="form-group">
            <label>Para (Receptor):</label>
            <select id="receptor">
                <option value="Todos">Todos</option>
                <option value="Jeison Altamar">Jeison Altamar</option>
                <option value="Nicolas Arevalo">Nicolas Arevalo</option>
                <option value="Jhojan Pasachoa">Jhojan Pasachoa</option>
                <option value="Sonia Gonzales">Sonia Gonzales</option>
            </select>
        </div>

        <div class="form-group">
            <label>Prioridad:</label>
            <div class="priority-selector">
                <div class="priority-btn selected" data-val="Normal" onclick="seleccionarPrioridad('Normal')">🟢 Normal</div>
                <div class="priority-btn" data-val="Auditoría" onclick="seleccionarPrioridad('Auditoría')">🟡 Auditoría</div>
                <div class="priority-btn" data-val="Urgente" onclick="seleccionarPrioridad('Urgente')">🔴 Urgente</div>
            </div>
        </div>

        <div class="form-group">
            <label>Mensaje:</label>
            <textarea id="contenido" rows="3" placeholder="Escribe la novedad o indicación..."></textarea>
        </div>

        <div style="display: flex; gap: 10px; justify-content: flex-end;">
            <button class="btn-reply" onclick="cerrarModal()">Cancelar</button>
            <button class="btn-main" onclick="guardarMensaje()">Enviar</button>
        </div>
    </div>
</div>

<script>
    let prioridadSeleccionada = 'Normal';
    let audioCtx = null;
    let alarmInterval = null;

    function activarSonido() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        alert("Sistema de audio habilitado para alarmas urgentes.");
    }

    function sonarAlarma() {
        if (!audioCtx) return;
        let osc = audioCtx.createOscillator();
        let gain = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); // Nota A5
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
    }

    function seleccionarPrioridad(val) {
        prioridadSeleccionada = val;
        document.querySelectorAll('.priority-btn').forEach(b => {
            b.classList.toggle('selected', b.getAttribute('data-val') === val);
        });
    }

    function abrirModal() { document.getElementById('modal').style.display = 'flex'; }
    function cerrarModal() { document.getElementById('modal').style.display = 'none'; }

    async function cargarMensajes() {
        const res = await fetch('/api/mensajes');
        const data = await res.json();
        
        const container = document.getElementById('messagesContainer');
        container.innerHTML = '';

        let tieneUrgentePendiente = false;

        data.forEach(m => {
            if (m.prioridad === 'Urgente' && m.estado === 'Pendiente') {
                tieneUrgentePendiente = true;
            }

            const card = document.createElement('div');
            card.className = `card ${m.prioridad}`;
            
            const respuestasHTML = m.respuestas.map(r => 
                `<div class="reply-item">💬 <strong>${r.autor}:</strong> ${r.texto} <small>(${r.fecha})</small></div>`
            ).join('');

            card.innerHTML = `
                <div class="card-header">
                    <span><strong>De:</strong> ${m.emisor} ➔ <strong>Para:</strong> ${m.receptor}</span>
                    <span class="badge ${m.prioridad}">${m.prioridad.toUpperCase()} ${m.estado === 'Atendido' ? ' - ✅ ATENDIDO' : ''}</span>
                </div>
                <div style="font-size: 1.05rem; margin: 8px 0;">${m.contenido}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${m.fecha}</div>
                
                <div class="replies">${respuestasHTML}</div>

                <div class="action-row">
                    ${m.prioridad === 'Urgente' && m.estado === 'Pendiente' ? 
                        `<button class="btn-ack" onclick="darEnterado(${m.id})">✅ Dar Enterado</button>` : ''}
                    <button class="btn-reply" onclick="responderMensaje(${m.id})">💬 Responder</button>
                </div>
            `;
            container.appendChild(card);
        });

        // Control de sonido para urgencias
        const banner = document.getElementById('audioBanner');
        if (tieneUrgentePendiente) {
            banner.style.display = 'block';
            if (!alarmInterval) {
                alarmInterval = setInterval(sonarAlarma, 1000);
            }
        } else {
            banner.style.display = 'none';
            if (alarmInterval) {
                clearInterval(alarmInterval);
                alarmInterval = null;
            }
        }
    }

    async function guardarMensaje() {
        const emisor = document.getElementById('emisor').value;
        const receptor = document.getElementById('receptor').value;
        const contenido = document.getElementById('contenido').value;

        if (!contenido.trim()) return alert("El mensaje no puede estar vacío");

        await fetch('/api/mensajes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ emisor, receptor, prioridad: prioridadSeleccionada, contenido })
        });

        document.getElementById('contenido').value = '';
        cerrarModal();
        cargarMensajes();
    }

    async function darEnterado(id) {
        const usuario = prompt("Confirma tu nombre para dar el enterado:", "Jeison Altamar");
        if (!usuario) return;

        await fetch(`/api/mensajes/${id}/enterado`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ usuario })
        });
        cargarMensajes();
    }

    async function responderMensaje(id) {
        const autor = prompt("Tu nombre:");
        if (!autor) return;
        const texto = prompt("Respuesta:");
        if (!texto) return;

        await fetch(`/api/mensajes/${id}/responder`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ autor, texto })
        });
        cargarMensajes();
    }

    // Polling cada 3 segundos
    setInterval(cargarMensajes, 3000);
    cargarMensajes();
</script>
</body>
</html>
"""

# --- RUTAS DE API ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/mensajes', methods=['GET'])
def get_mensajes():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mensajes ORDER BY id DESC")
        rows = cursor.fetchall()
        
        resultado = []
        for row in rows:
            item = dict(row)
            item['respuestas'] = json.loads(item['respuestas'])
            resultado.append(item)
            
        return jsonify(resultado)

@app.route('/api/mensajes', methods=['POST'])
def create_mensaje():
    data = request.json
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mensajes (emisor, receptor, prioridad, contenido, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['emisor'], data['receptor'], data['prioridad'], data['contenido'], fecha_actual))
        conn.commit()
        
    return jsonify({"status": "ok"})

@app.route('/api/mensajes/<int:msg_id>/enterado', methods=['POST'])
def mark_enterado(msg_id):
    data = request.json
    fecha_actual = datetime.now().strftime("%H:%M:%S")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT respuestas FROM mensajes WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        
        if row:
            respuestas = json.loads(row[0])
            respuestas.append({
                "autor": data['usuario'],
                "texto": "✅ Dio ENTERADO a la urgencia (Sonido silenciado)",
                "fecha": fecha_actual
            })
            
            cursor.execute('''
                UPDATE mensajes 
                SET estado = 'Atendido', respuestas = ?
                WHERE id = ?
            ''', (json.dumps(respuestas), msg_id))
            conn.commit()
            
    return jsonify({"status": "ok"})

@app.route('/api/mensajes/<int:msg_id>/responder', methods=['POST'])
def add_reply(msg_id):
    data = request.json
    fecha_actual = datetime.now().strftime("%H:%M:%S")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT respuestas FROM mensajes WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        
        if row:
            respuestas = json.loads(row[0])
            respuestas.append({
                "autor": data['autor'],
                "texto": data['texto'],
                "fecha": fecha_actual
            })
            
            cursor.execute("UPDATE mensajes SET respuestas = ? WHERE id = ?", (json.dumps(respuestas), msg_id))
            conn.commit()
            
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
