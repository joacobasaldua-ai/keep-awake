#!/usr/bin/env python3
"""
keep_awake.py — Simulador de actividad humana para macOS
Evita la suspensión simulando comportamiento natural de lectura.
Detener: presiona F10.
"""

import pyautogui
import random
import time
import signal
import sys
import threading
import math
from statistics import NormalDist

try:
    from pynput import keyboard as kb
    PYNPUT_DISPONIBLE = True
except ImportError:
    PYNPUT_DISPONIBLE = False

# ─────────────────────────────────────────────
# PYAUTOGUI
# ─────────────────────────────────────────────
pyautogui.FAILSAFE = True

# ─────────────────────────────────────────────
# FLAG GLOBAL DE PARADA
# ─────────────────────────────────────────────
detener = threading.Event()

def salir_limpiamente(sig=None, frame=None):
    detener.set()

signal.signal(signal.SIGINT, salir_limpiamente)


# ─────────────────────────────────────────────
# LISTENER: PARA SOLO CON F10
# ─────────────────────────────────────────────
def iniciar_listener():
    if not PYNPUT_DISPONIBLE:
        return None
    def on_press(key):
        if key == kb.Key.f10:
            detener.set()
            return False
    listener = kb.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    return listener


# ─────────────────────────────────────────────
# PRIMITIVAS DE ALEATORIEDAD
# ─────────────────────────────────────────────

def gauss(media, sigma, minimo, maximo):
    """Gaussiana acotada."""
    while True:
        v = random.gauss(media, sigma)
        if minimo <= v <= maximo:
            return v


def rjitter(valor):
    """
    Meta-jitter: el sigma del ruido es en sí mismo aleatorio en cada llamada
    (entre 5% y 30%). Así los tiempos nunca tienen la misma dispersión.
    """
    sigma = random.uniform(0.05, 0.30)
    return valor * (1 + random.gauss(0, sigma))


def _press_realista(tecla):
    """
    Presiona una tecla con hold time realista (80-150ms).
    pyautogui.press() suelta instantáneamente (~0ms entre DOWN y UP),
    lo cual es una firma obvia de automatización.
    """
    hold = random.gauss(0.045, 0.012)
    hold = max(0.025, min(0.080, hold))
    pyautogui.keyDown(tecla)
    time.sleep(hold)
    pyautogui.keyUp(tecla)


def _typewrite_realista(char):
    """Escribe un carácter con hold time humano."""
    _press_realista(char)


def dirichlet_weights(base_weights, concentracion=6.0):
    """
    Perturba los pesos con una muestra Dirichlet.
    concentracion baja → pesos muy variables; alta → cercanos a base.
    Rango 4–9 da variabilidad natural sin degenerar a una sola acción.
    Con esto los pesos cambian cada ciclo: ningún chi-squared los detectará.
    """
    alpha = [w * concentracion for w in base_weights]
    sample = [random.gammavariate(a, 1) for a in alpha]
    total  = sum(sample)
    return [s / total for s in sample]


# ─────────────────────────────────────────────
# MODELO DE TECLADO QWERTY (distancia física entre teclas)
# Un humano real tarda más entre teclas lejanas y menos
# entre teclas cercanas o de manos alternadas.
# ─────────────────────────────────────────────

# Posición (fila, columna) de cada tecla en QWERTY estándar
# La columna tiene offset por fila para reflejar el escalonamiento real
_KEY_POS = {
    'q': (0, 0),   'w': (0, 1),   'e': (0, 2),   'r': (0, 3),   't': (0, 4),
    'y': (0, 5),   'u': (0, 6),   'i': (0, 7),   'o': (0, 8),   'p': (0, 9),
    'a': (1, 0.25),'s': (1, 1.25),'d': (1, 2.25),'f': (1, 3.25),'g': (1, 4.25),
    'h': (1, 5.25),'j': (1, 6.25),'k': (1, 7.25),'l': (1, 8.25),
    'z': (2, 0.75),'x': (2, 1.75),'c': (2, 2.75),'v': (2, 3.75),'b': (2, 4.75),
    'n': (2, 5.75),'m': (2, 6.75),
}

# Mano izquierda vs derecha
_LEFT_HAND  = set("qwertasdfgzxcvb")
_RIGHT_HAND = set("yuiophjklnm")


def _key_distance(k1, k2):
    """Distancia euclidiana entre dos teclas en el layout QWERTY."""
    if k1 not in _KEY_POS or k2 not in _KEY_POS:
        return 2.0  # distancia default para teclas no mapeadas
    r1, c1 = _KEY_POS[k1]
    r2, c2 = _KEY_POS[k2]
    return math.sqrt((r2 - r1) ** 2 + (c2 - c1) ** 2)


def _same_hand(k1, k2):
    """True si ambas teclas se teclean con la misma mano."""
    left1  = k1 in _LEFT_HAND
    left2  = k2 in _LEFT_HAND
    return left1 == left2


def delay_entre_teclas(k1, k2, vel_base):
    """
    Calcula el delay realista entre dos teclas basado en:
    - Distancia física en el teclado (más lejos = más lento)
    - Misma mano vs mano alternada (alternada = más rápido)
    - Jitter natural
    """
    dist = _key_distance(k1, k2)
    # Normalizar distancia: 0 (misma tecla) a ~10 (extremos)
    factor_dist = 0.7 + 0.3 * min(dist / 5.0, 1.0)

    # Manos alternadas son ~20-35% más rápidas
    if not _same_hand(k1, k2):
        factor_mano = random.uniform(0.65, 0.80)
    else:
        factor_mano = random.uniform(0.95, 1.10)

    delay = vel_base * factor_dist * factor_mano
    return abs(rjitter(delay))


# ─────────────────────────────────────────────
# MOVIMIENTO DE MOUSE CON CURVAS BÉZIER + RUIDO
# pyautogui.moveTo usa tweening lineal/simple.
# Un humano real mueve el mouse en curvas orgánicas
# con micro-correcciones y aceleración variable.
# ─────────────────────────────────────────────

def _bezier_point(t, p0, p1, p2, p3):
    """Punto en una curva Bézier cúbica en t=[0,1]."""
    u = 1 - t
    return (u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1])


def _mover_mouse_bezier(x_inicio, y_inicio, x_fin, y_fin, duracion):
    """
    Mueve el mouse siguiendo una curva Bézier cúbica con:
    - Puntos de control aleatorios (curvatura orgánica)
    - Ruido per-step de 1-4px (micro-correcciones humanas)
    - Velocidad variable (más lenta al inicio/final, como un humano)
    """
    dx = x_fin - x_inicio
    dy = y_fin - y_inicio

    # Puntos de control: desviación lateral proporcional a la distancia
    desvio = math.sqrt(dx**2 + dy**2) * random.uniform(0.05, 0.35)
    angulo = math.atan2(dy, dx) + random.uniform(-0.8, 0.8)

    cp1 = (x_inicio + dx * random.uniform(0.2, 0.4) + desvio * math.cos(angulo + 1.2),
            y_inicio + dy * random.uniform(0.2, 0.4) + desvio * math.sin(angulo + 1.2))
    cp2 = (x_inicio + dx * random.uniform(0.6, 0.8) + desvio * math.cos(angulo - 0.8),
            y_inicio + dy * random.uniform(0.6, 0.8) + desvio * math.sin(angulo - 0.8))

    p0 = (x_inicio, y_inicio)
    p3 = (x_fin, y_fin)

    # Más pasos = más suave (mínimo 20 para suavidad)
    n_pasos = max(20, int(duracion * random.uniform(75, 120)))

    # Exponente de la curva ease in-out (se fija por movimiento, varía entre movimientos)
    expo = random.uniform(1.8, 3.2)

    for i in range(1, n_pasos + 1):
        if detener.is_set():
            break

        # Parametrización no-lineal: más lento al inicio y final (ease in-out)
        t_lineal = i / n_pasos
        t_curvo = t_lineal ** expo / (t_lineal ** expo + (1 - t_lineal) ** expo)

        bx, by = _bezier_point(t_curvo, p0, cp1, cp2, p3)

        # Micro-ruido muy sutil que decrece al acercarse al destino
        ruido_escala = max(0.0, 1.0 - t_lineal * 0.95)
        ruido_x = random.gauss(0, random.uniform(0.05, 0.25) * ruido_escala)
        ruido_y = random.gauss(0, random.uniform(0.05, 0.25) * ruido_escala)

        px = int(bx + ruido_x)
        py = int(by + ruido_y)

        # Asegurar que no se sale de la pantalla
        w, h = pyautogui.size()
        px = max(5, min(w - 5, px))
        py = max(5, min(h - 5, py))

        pyautogui.moveTo(px, py, _pause=False)

        # Timing entre pasos: variable, no constante
        dt_base = duracion / n_pasos
        dt = dt_base * random.uniform(0.5, 1.8)
        time.sleep(max(0.003, dt))

        # Micro-pausa ocasional (~1.5%): como si el humano dudara
        if random.random() < 0.015:
            time.sleep(random.uniform(0.01, 0.06))

    # Paso final exacto al destino (sin ruido)
    pyautogui.moveTo(x_fin, y_fin, _pause=False)


# ─────────────────────────────────────────────
# MICRO-TEMBLOR DEL MOUSE DURANTE PAUSAS
# Un humano real nunca tiene el mouse perfectamente
# quieto — siempre hay micro-movimientos de 1-3px.
# ─────────────────────────────────────────────

def _micro_temblor():
    """Mueve el mouse 1 píxel en dirección aleatoria, muy sutil."""
    try:
        x, y = pyautogui.position()
        dx = random.choice([-1, 0, 0, 0, 1])
        dy = random.choice([-1, 0, 0, 0, 1])
        if dx == 0 and dy == 0:
            return  # a veces no se mueve
        nx = x + dx
        ny = y + dy
        w, h = pyautogui.size()
        nx = max(5, min(w - 5, nx))
        ny = max(5, min(h - 5, ny))
        pyautogui.moveTo(nx, ny, duration=random.uniform(0.15, 0.40), _pause=False)
    except Exception:
        pass


# ─────────────────────────────────────────────
# SISTEMA DE "HUMOR" (mood)
# Cada N ciclos el script adopta un humor diferente que
# desvía todos los parámetros a la vez. Esto crea clusters
# naturales de actividad intensa / pausada que son
# estadísticamente indistinguibles de comportamiento humano.
# ─────────────────────────────────────────────

_MOODS = {
    # nombre : (escala_tiempo, escala_distancia, prob_typo, desc)
    "concentrado":  (0.85, 1.10, 0.06, "leyendo con atención"),
    "distraido":    (1.10, 0.75, 0.12, "con la mente en otro lado"),
    "activo":       (0.65, 1.35, 0.05, "navegando rápido"),
    "cansado":      (1.15, 0.65, 0.14, "con sueño, lento"),
    "normal":       (1.00, 1.00, 0.09, "ritmo estándar"),
}

_mood_actual      = "normal"
_ciclos_mood      = 0
_duracion_mood    = 0  # cuántos ciclos dura el mood actual

# ─────────────────────────────────────────────
# FATIGA CIRCADIANA
# Un humano se cansa con el tiempo: más lento, más errores,
# pausas más largas. Sin esto, la hora 3 es igual a la hora 1.
# ─────────────────────────────────────────────
_inicio_global = None

def fatiga():
    """
    Factor de fatiga que crece lentamente con el tiempo.
    Minuto 0: 1.0 (sin fatiga)
    Minuto 60: ~1.08
    Minuto 180: ~1.24
    Nunca supera 1.45 para no romper el equilibrio de pausas.
    Incluye micro-fluctuaciones (a veces uno se "despeja" un poco).
    """
    if _inicio_global is None:
        return 1.0
    mins = (time.time() - _inicio_global) / 60.0
    base = 1.0 + 0.08 * (mins / 60.0)
    base = min(base, 1.45)
    # Micro-fluctuaciones: a veces baja un poco (segundo café, etc.)
    fluctuacion = random.gauss(0, 0.03)
    return max(0.90, base + fluctuacion)

def actualizar_mood(ciclo):
    """
    Cambia el humor cada 4–14 ciclos con transiciones correlacionadas.
    Cada mood tiene más probabilidad de ir a ciertos moods que a otros
    (como un humano real: concentrado → cansado es más probable que
    concentrado → activo).
    """
    global _mood_actual, _ciclos_mood, _duracion_mood
    if ciclo == 1 or _ciclos_mood >= _duracion_mood:
        # Matriz de transición: desde cada mood, probabilidades de ir a otro
        transiciones = {
            "concentrado": {"cansado": 0.30, "normal": 0.30, "distraido": 0.25,
                            "activo": 0.10, "concentrado": 0.05},
            "distraido":   {"normal": 0.30, "activo": 0.25, "concentrado": 0.20,
                            "cansado": 0.15, "distraido": 0.10},
            "activo":      {"concentrado": 0.30, "normal": 0.25, "cansado": 0.20,
                            "distraido": 0.15, "activo": 0.10},
            "cansado":     {"distraido": 0.30, "normal": 0.30, "activo": 0.15,
                            "concentrado": 0.15, "cansado": 0.10},
            "normal":      {"concentrado": 0.25, "activo": 0.25, "distraido": 0.20,
                            "cansado": 0.15, "normal": 0.15},
        }
        trans   = transiciones[_mood_actual]
        destinos = list(trans.keys())
        pesos    = dirichlet_weights(list(trans.values()),
                                     concentracion=random.uniform(6, 14))
        _mood_actual   = random.choices(destinos, weights=pesos, k=1)[0]
        _ciclos_mood   = 0
        _duracion_mood = int(round(gauss(7, 2.5, 4, 14)))
    _ciclos_mood += 1

def mood():
    return _MOODS[_mood_actual]


# ─────────────────────────────────────────────
# ACCIONES
# ─────────────────────────────────────────────

def movimiento_mouse():
    """
    Múltiples movimientos rápidos en distintas direcciones,
    como un humano que navega, lee, busca cosas en pantalla.
    Total ~10-30s pero cada tramo es rápido (1-4s).
    """
    esc_t, esc_d, _, _ = mood()
    f = fatiga()
    w, h = pyautogui.size()

    # Cuántos tramos hacer: entre 3 y 8 movimientos seguidos
    n_tramos = int(round(gauss(5, 1.5, 3, 8)))

    for _ in range(n_tramos):
        if detener.is_set():
            break

        x, y = pyautogui.position()

        # Destino con distancia escalada por mood
        dx = gauss(0, 380 * esc_d, -700 * esc_d, 700 * esc_d)
        dy = gauss(0, 270 * esc_d, -500 * esc_d, 500 * esc_d)
        nx = int(max(100, min(w - 100, x + dx)))
        ny = int(max(100, min(h - 100, y + dy)))

        # Cada tramo es RÁPIDO: 1-4 segundos
        dur = rjitter(gauss(2.5 * esc_t * f, 0.8, 1.0, 4.5))

        # Tipo de movimiento
        modos      = ["desvio", "overshoot", "directo"]
        pesos_modo = dirichlet_weights([0.25, 0.13, 0.62],
                                       concentracion=random.uniform(4, 12))
        modo = random.choices(modos, weights=pesos_modo, k=1)[0]

        if modo == "desvio":
            frac_1 = random.uniform(0.30, 0.55)
            px = int((x + nx) / 2 + gauss(0, 45, -90, 90))
            py = int((y + ny) / 2 + gauss(0, 30, -60, 60))
            _mover_mouse_bezier(x, y, px, py, rjitter(dur * frac_1))
            time.sleep(rjitter(gauss(0.10, 0.04, 0.02, 0.20)))
            _mover_mouse_bezier(px, py, nx, ny, rjitter(dur * (1 - frac_1)))

        elif modo == "overshoot":
            ox = int(nx + gauss(0, 18, -35, 35))
            oy = int(ny + gauss(0, 12, -24, 24))
            ox = max(80, min(w - 80, ox))
            oy = max(80, min(h - 80, oy))
            frac_o = random.uniform(0.70, 0.90)
            _mover_mouse_bezier(x, y, ox, oy, rjitter(dur * frac_o))
            time.sleep(rjitter(gauss(0.06, 0.02, 0.01, 0.12)))
            _mover_mouse_bezier(ox, oy, nx, ny, rjitter(dur * (1 - frac_o)))

        else:
            _mover_mouse_bezier(x, y, nx, ny, rjitter(dur))

        # Pausa corta entre tramos (como si el humano mira algo brevemente)
        time.sleep(rjitter(gauss(0.6, 0.3, 0.1, 1.5)))

    # Micro-pausa post-movimiento
    time.sleep(rjitter(gauss(0.10, 0.04, 0.02, 0.25)))


def teclas_flechas():
    """
    Pulsa solo letras sueltas (a-z), con frecuencia basada en español.
    La distribución se perturba con Dirichlet cada llamada para que
    nunca sea exactamente la misma curva de frecuencia.
    """
    esc_t, _, _, _ = mood()
    f = fatiga()

    # Frecuencias reales del español (perturbadas con Dirichlet cada llamada)
    _LETRAS_ES = list("abcdefghijklmnopqrstuvwxyz")
    _FREQ_ES   = [0.125, 0.014, 0.047, 0.059, 0.137, 0.007, 0.010, 0.007,
                  0.062, 0.004, 0.0001, 0.050, 0.032, 0.067, 0.087, 0.025,
                  0.009, 0.069, 0.080, 0.046, 0.039, 0.009, 0.0001, 0.002,
                  0.009, 0.005]
    pesos_letras = dirichlet_weights(_FREQ_ES, concentracion=random.uniform(5, 15))

    n = int(round(gauss(6, 3, 2, 16)))
    vel_base = gauss(0.26 * esc_t * f, 0.10, 0.07, 0.65)

    i = 0
    tecla_prev = None
    while i < n:
        if detener.is_set():
            break

        tecla = random.choices(_LETRAS_ES, weights=pesos_letras, k=1)[0]

        # Ráfaga rápida de la misma letra (~15% de veces)
        if random.random() < 0.15:
            rafaga    = int(round(gauss(3, 1.2, 2, 6)))
            vel_raf   = rjitter(gauss(0.09 * esc_t * f, 0.03, 0.03, 0.20))
            for _ in range(rafaga):
                if detener.is_set():
                    break
                _press_realista(tecla)
                time.sleep(abs(rjitter(vel_raf)))
            i += rafaga
        else:
            # Delay basado en distancia física entre teclas
            if tecla_prev:
                delay = delay_entre_teclas(tecla_prev, tecla, vel_base)
            else:
                delay = abs(rjitter(vel_base))
            time.sleep(delay)
            _press_realista(tecla)
            i += 1

        tecla_prev = tecla

        # Pausa interna aleatoria (~13%)
        if random.random() < 0.13:
            time.sleep(gauss(2.0 * esc_t, 0.8, 0.7, 5.0))

        # Cambio de ritmo gradual (~18%)
        if random.random() < 0.18:
            vel_base = abs(rjitter(vel_base * random.uniform(0.6, 1.6)))
            vel_base = max(0.06, min(0.85, vel_base))


def scroll_suave():
    """
    Scroll con parámetros que varían por mood.
    - Dirección: balanceada según acumulado para no terminar siempre abajo.
    - Pasos: escalados por mood.
    - Velocidad de ticks: variable dentro de la misma pasada.
    - Pausas internas en puntos NO fijos (fracción aleatoria).
    - Relectura ocasional.
    """
    global _scroll_acumulado
    esc_t, _, _, _ = mood()
    f = fatiga()
    w, h = pyautogui.size()
    if _zona_segura is not None:
        x, y = _zona_segura
    else:
        x, y = pyautogui.position()

    # -1 = scroll abajo, 1 = scroll arriba (pyautogui convention)
    # Bias dinámico: cuanto más acumulado en una dirección, más probable la opuesta
    # Con acumulado=0 es 50/50, con acumulado=-15 es ~85% arriba
    bias = max(-0.40, min(0.40, -_scroll_acumulado * 0.03))
    prob_arriba = 0.50 + bias
    dir_principal = random.choices([-1, 1], weights=[1 - prob_arriba, prob_arriba])[0]

    pasos = int(round(gauss(40 / esc_t, 8, 18, 70)))

    # 0–3 puntos de pausa interna en fracciones aleatorias del recorrido
    n_pausas      = random.choices([0, 1, 2, 3], weights=[0.25, 0.40, 0.25, 0.10], k=1)[0]
    puntos_pausa  = set(int(pasos * random.uniform(0.15, 0.90)) for _ in range(n_pausas))

    # Velocidad base del tick — más lento para que el scroll dure ~1.5-3s
    vel_tick = rjitter(gauss(0.18 * esc_t * f, 0.05, 0.08, 0.35))

    for i in range(pasos):
        if detener.is_set():
            break
        # Micro-drift del mouse durante scroll (1-3px, como un humano real)
        if random.random() < 0.18:
            x += int(random.gauss(0, 1.8))
            y += int(random.gauss(0, 1.2))
            x = max(5, min(w - 5, x))
            y = max(5, min(h - 5, y))
        pyautogui.scroll(dir_principal, x=x, y=y)
        _scroll_acumulado += dir_principal
        time.sleep(abs(rjitter(vel_tick)))

        # Pausas internas en puntos aleatorios
        if i in puntos_pausa and random.random() < 0.75:
            time.sleep(rjitter(gauss(1.1 * esc_t, 0.4, 0.3, 3.0)))

        # Cambio de velocidad gradual (~15%)
        if random.random() < 0.15:
            vel_tick = abs(rjitter(vel_tick * random.uniform(0.7, 1.5)))
            vel_tick = max(0.04, min(0.35, vel_tick))

    # Relectura: sube algunos pasos (~12% de veces)
    if random.random() < 0.12 and not detener.is_set():
        time.sleep(abs(rjitter(gauss(0.6, 0.2, 0.2, 1.4))))
        pasos_v  = int(round(gauss(3.5, 1.5, 1, 7)))
        vel_v    = rjitter(gauss(0.07 * esc_t, 0.02, 0.02, 0.18))
        for _ in range(pasos_v):
            if detener.is_set():
                break
            pyautogui.scroll(-dir_principal, x=x, y=y)
            _scroll_acumulado += -dir_principal
            time.sleep(abs(rjitter(vel_v)))


# ─────────────────────────────────────────────
# POOL DE PALABRAS PARA ESCRITURA
# Mucho más grande y variado: se construyen frases al vuelo
# combinando palabras de categorías distintas.
# Así las secuencias escritas nunca se repiten igual.
# ─────────────────────────────────────────────
_VERBOS     = ["revisar", "verificar", "anotar", "buscar", "confirmar",
               "comparar", "analizar", "investigar", "leer", "profundizar",
               "entender", "recordar", "contrastar", "chequear", "estudiar"]
_SUSTANTIVOS= ["dato", "fuente", "referencia", "argumento", "contexto",
               "evidencia", "hipotesis", "concepto", "ejemplo", "caso",
               "tema", "punto", "pagina", "seccion", "nota",
               "idea", "conclusion", "detalle", "patron", "resultado"]
_ADJETIVOS  = ["importante", "relevante", "util", "clave", "interesante",
               "critico", "central", "debil", "fuerte", "ambiguo",
               "claro", "confuso", "valioso", "dudoso", "solido"]
_CONECTORES = ["y", "con", "de", "en", "sobre", "para"]


_FRAGMENTOS = ["ok", "no", "si", "ver", "hmm", "ojo", "???", "...", "!!", "ver despues",
               "no se", "puede ser", "falta", "sobra", "mal", "bien", "cap 3", "pag 12",
               "fig 4", "ref", "aca", "esto", "ahi va", "claro", "nop", "sip", "maso"]
_NUMEROS = ["1", "2", "3", "12", "45", "100", "7", "p5", "cap2", "sec3", "v2"]


def _frase_aleatoria():
    """Genera una frase única — a veces estructurada, a veces fragmento suelto."""
    # 20% de veces: fragmento corto (como notas reales)
    if random.random() < 0.20:
        return random.choice(_FRAGMENTOS)
    # 8% de veces: número o referencia
    if random.random() < 0.10:
        return random.choice(_NUMEROS)

    estructura = random.choice([
        ["verbo", "sustantivo"],
        ["verbo", "adjetivo", "sustantivo"],
        ["sustantivo", "adjetivo"],
        ["verbo", "sustantivo", "conector", "sustantivo"],
        ["adjetivo", "sustantivo"],
        ["verbo", "sustantivo", "adjetivo"],
        ["sustantivo", "conector", "adjetivo", "sustantivo"],
        ["verbo"],
        ["adjetivo", "conector", "sustantivo", "adjetivo"],
        ["sustantivo"],
        ["verbo", "conector", "verbo", "sustantivo"],
        ["sustantivo", "conector", "sustantivo"],
        ["fragmento"],
        ["sustantivo", "fragmento"],
    ])
    partes = []
    for cat in estructura:
        if cat == "verbo":
            partes.append(random.choice(_VERBOS))
        elif cat == "sustantivo":
            partes.append(random.choice(_SUSTANTIVOS))
        elif cat == "adjetivo":
            partes.append(random.choice(_ADJETIVOS))
        elif cat == "conector":
            partes.append(random.choice(_CONECTORES))
        elif cat == "fragmento":
            partes.append(random.choice(_FRAGMENTOS))
    return " ".join(partes)


def simular_escritura():
    """
    Tipeo humano con variabilidad máxima:
    - Frases generadas dinámicamente (no fijas)
    - Velocidad y typo-rate escalados por mood
    - Probabilidad de typo varía por sesión (no siempre 8%)
    - Borrado al final con velocidad variable
    - Ocasionalmente borra por palabras (Cmd+Backspace no: solo backspace continuo)
    - A veces escribe solo la mitad y borra (indecisión)
    """
    esc_t, _, prob_typo, _ = mood()
    f = fatiga()

    # Frases generadas al vuelo: entre 3 y 8 (más escritura)
    n_frases = int(round(gauss(5, 1.5, 3, 8)))
    # Separador variable: 1 espacio, 2 espacios, o punto+espacio (nunca siempre igual)
    seps  = [" ", " ", "  ", ". ", ", "]
    texto = ""
    for j in range(n_frases):
        texto += _frase_aleatoria()
        if j < n_frases - 1:
            texto += random.choice(seps)

    # Probabilidad de typo varía por sesión (3%–18%) — sube con fatiga
    p_typo   = min(0.22, max(0.03, random.gauss(prob_typo * f, 0.03)))
    # Velocidad base de tipeo varía por sesión — más lenta con fatiga
    vel_base = gauss(0.110 * esc_t * f, 0.025, 0.040, 0.260)

    chars_escritos = 0
    tope = len(texto)
    char_prev = None

    # 15% de veces: indecisión → escribe solo entre 30% y 70% del texto
    if random.random() < 0.15:
        tope = int(len(texto) * random.uniform(0.30, 0.70))

    for i, char in enumerate(texto[:tope]):
        if detener.is_set():
            break

        # Typo con probabilidad variable por sesión
        if random.random() < p_typo:
            typo = random.choice("abcdefghijklmnopqrstuvwxyz")  # solo letras
            _typewrite_realista(typo)
            time.sleep(abs(rjitter(gauss(0.17 * esc_t * f, 0.06, 0.06, 0.42))))
            _press_realista("backspace")
            time.sleep(abs(rjitter(gauss(0.11 * esc_t * f, 0.04, 0.04, 0.26))))

        if char == " ":
            _press_realista("space")
            # Espacio post-palabra: ligeramente más largo (natural en tipeo)
            time.sleep(abs(rjitter(gauss(0.20 * esc_t * f, 0.08, 0.06, 0.52))))
        else:
            _typewrite_realista(char)
            # Delay basado en distancia física entre teclas QWERTY
            if char_prev and char_prev != " " and char in _KEY_POS:
                delay = delay_entre_teclas(char_prev, char, vel_base)
            else:
                delay = abs(rjitter(vel_base))
            time.sleep(delay)

        char_prev = char
        chars_escritos += 1

        # Pausa "pensando" en punto aleatorio (no siempre a mitad)
        if random.random() < 0.06:
            time.sleep(gauss(0.85 * esc_t * f, 0.30, 0.25, 2.8))

        # Cambio de velocidad de vez en cuando (cansancio / relax)
        if random.random() < 0.08:
            vel_base = abs(rjitter(vel_base * random.uniform(0.7, 1.45)))
            vel_base = max(0.028, min(0.300, vel_base))

    # Borrar lo escrito — pero NO siempre (un humano a veces deja lo que escribió)
    if chars_escritos > 0 and not detener.is_set():
        # ~25% de las veces: no borra nada (deja el texto como anotación)
        # ~10% borra solo 1-3 chars (corrigió un typo y dejó el resto)
        dado_borrar = random.random()
        if dado_borrar < 0.25:
            # No borra — deja el texto
            return
        elif dado_borrar < 0.35:
            # Solo corrige un typo (1-3 backspaces)
            chars_a_borrar = int(round(gauss(2, 0.8, 1, 3)))
        else:
            time.sleep(abs(rjitter(gauss(0.55, 0.20, 0.18, 1.30))))

            # Cuántos chars borrar: variado
            modo_borrado = random.random()
            if modo_borrado < 0.55:
                chars_a_borrar = chars_escritos
            elif modo_borrado < 0.80:
                chars_a_borrar = int(chars_escritos * random.uniform(0.40, 0.90))
            else:
                chars_a_borrar = int(chars_escritos * random.uniform(0.10, 0.40))

        chars_a_borrar = max(1, min(chars_a_borrar, chars_escritos))

        # Patrón de borrado varía: continuo, ráfagas, o con pausas
        vel_borro = rjitter(gauss(0.042 * esc_t * f, 0.015, 0.012, 0.110))
        borrados = 0
        while borrados < chars_a_borrar:
            if detener.is_set():
                break

            # 20% de veces: ráfaga rápida de 3-8 backspaces
            if random.random() < 0.20:
                burst = min(int(round(gauss(5, 2, 3, 8))),
                            chars_a_borrar - borrados)
                vel_burst = abs(rjitter(vel_borro * 0.5))
                for _ in range(burst):
                    if detener.is_set():
                        break
                    _press_realista("backspace")
                    time.sleep(max(0.008, vel_burst))
                borrados += burst
                # Pausa post-ráfaga
                if borrados < chars_a_borrar:
                    time.sleep(abs(rjitter(gauss(0.25, 0.10, 0.08, 0.55))))
            else:
                _press_realista("backspace")
                borrados += 1
                if random.random() < 0.10:
                    vel_borro = abs(rjitter(vel_borro * random.uniform(0.7, 1.4)))
                    vel_borro = max(0.010, min(0.120, vel_borro))
                time.sleep(abs(rjitter(vel_borro)))


def accion_combo():
    """
    Combina 1–3 acciones con micro-pausas variables entre ellas.
    La cantidad, selección y orden son aleatorios cada vez.
    """
    pool      = ["scroll", "teclas", "mouse", "escritura"]
    n_acciones = random.choices([1, 2, 3], weights=[0.20, 0.55, 0.25], k=1)[0]
    seleccion  = random.sample(pool, min(n_acciones, len(pool)))
    for accion in seleccion:
        if detener.is_set():
            break
        ejecutar_accion(accion)
        time.sleep(abs(rjitter(gauss(0.35, 0.14, 0.10, 0.85))))


# ─────────────────────────────────────────────
# PAUSA LECTORA ADAPTATIVA
# ─────────────────────────────────────────────

# ── Target de pausa por VENTANA (persiste ~15-40 ciclos ≈ 5-15 min) ──
_ventana_target   = None   # % de pausa objetivo actual
_ventana_ciclos   = 0      # ciclos transcurridos en esta ventana
_ventana_duracion = 0      # cuántos ciclos dura esta ventana

def _nuevo_target_ventana():
    """
    Distribución bimodal: picos en 25% y 75% pausa, sigma=22.
    Rangos 20-80% quedan parejos (~9-10% cada decil).
    Extremos (0-10%, 90-100%) ~6% cada uno.
    Promedio global converge a 50%.
    """
    global _ventana_target, _ventana_ciclos, _ventana_duracion
    # 65/35 entre pico activo (5) y pico pasivo (40) → media ~17%
    media = 5.0 if random.random() < 0.65 else 40.0
    _ventana_target   = max(0.0, min(100.0, random.gauss(media, 22.0)))
    _ventana_ciclos   = 0
    _ventana_duracion = int(round(gauss(25, 8, 15, 45)))

def _get_target_ventana():
    """Devuelve el target actual, renovándolo si expiró."""
    global _ventana_ciclos
    if _ventana_target is None or _ventana_ciclos >= _ventana_duracion:
        _nuevo_target_ventana()
    _ventana_ciclos += 1
    return _ventana_target


def pausa_lectora(pct_pausa=50.0, dur_accion=6.0, t_act=0.0, t_pau=0.0):
    """
    Pausa proporcional al target de la ventana actual.
    Si target = 50% pausa → pausa ≈ duración de la acción (ratio 1:1).
    Si target = 30% pausa → pausa ≈ 0.43× la acción (alta actividad).
    Si target = 70% pausa → pausa ≈ 2.3× la acción (baja actividad).
    """
    esc_t, _, _, _ = mood()
    objetivo = _get_target_ventana()

    # Ratio directo: pause_time / action_time = target / (100 - target)
    objetivo_clamped = max(8.0, min(92.0, objetivo))
    ratio = objetivo_clamped / (100.0 - objetivo_clamped)

    # Pausa base proporcional a la acción
    pausa_base = dur_accion * ratio

    # Jitter moderado para que no sea predecible dentro de la ventana
    pausa_base *= random.uniform(0.55, 1.10)
    segundos = abs(rjitter(pausa_base))

    # Piso y techo según nivel de actividad de la ventana
    if objetivo < 20:
        segundos = max(0.2, min(2.0, segundos))
    elif objetivo > 80:
        segundos = max(8.0, min(40.0, segundos))
    else:
        segundos = max(0.3, min(12.0, segundos))

    if segundos < 5:
        tipo = "corta"
    elif segundos < 12:
        tipo = "media"
    elif segundos < 22:
        tipo = "larga"
    else:
        tipo = "muy_larga"

    return segundos, tipo


# ─────────────────────────────────────────────
# SELECCIÓN DE ACCIÓN
# ─────────────────────────────────────────────

ACCIONES_BASE  = ["escritura", "scroll", "teclas", "mouse", "combo", "pestana", "nada"]
PESOS_BASE     = [  0.10,       0.28,    0.08,     0.36,    0.10,   0.06,      0.02 ]

# ── Ventana de preferencia input: mouse vs teclado ──
# Cada ventana sesga los pesos hacia mouse o teclado.
# 50/50 probabilidad de cuál domina. Persiste ~15-35 ciclos.
_input_bias        = 0.0   # -1.0 = full teclado, +1.0 = full mouse
_input_bias_ciclos = 0
_input_bias_dur    = 0

def _nuevo_input_bias():
    """Genera un bias aleatorio: positivo = más mouse, negativo = más teclado."""
    global _input_bias, _input_bias_ciclos, _input_bias_dur
    # gauss(-0.05, 0.4) casi centrado → 50/50 mouse vs teclado a largo plazo
    # Valores van de ~-0.8 a ~+0.8
    _input_bias = max(-0.8, min(0.8, random.gauss(0.25, 0.4)))
    _input_bias_ciclos = 0
    _input_bias_dur = int(round(gauss(22, 7, 12, 38)))

def _get_input_bias():
    global _input_bias_ciclos
    if _input_bias_ciclos >= _input_bias_dur:
        _nuevo_input_bias()
    _input_bias_ciclos += 1
    return _input_bias

def _aplicar_input_bias(pesos):
    """Sesga los pesos según el bias actual de input."""
    bias = _get_input_bias()
    # indices: escritura=0, scroll=1, teclas=2, mouse=3, combo=4, pestana=5, nada=6
    # mouse group: scroll(1) + mouse(3) + pestana(5)
    # keyboard group: escritura(0) + teclas(2)
    factor = 1.0 + abs(bias) * 1.5  # multiplicador hasta 2.2x
    ajustados = list(pesos)
    if bias > 0:  # más mouse
        ajustados[1] *= factor  # scroll
        ajustados[3] *= factor  # mouse
    else:  # más teclado
        ajustados[0] *= factor  # escritura
        ajustados[2] *= factor  # teclas
    total = sum(ajustados)
    return [p / total for p in ajustados]

# Coordenada segura para clicks (se define al inicio)
_zona_segura = None
_scroll_acumulado = 0  # positivo = abajo, negativo = arriba

# Transiciones contextuales: qué acción es más probable después de otra.
# Un humano real tiene flujos naturales: scroll → pausa → scroll,
# escritura → pausa → mouse (para reposicionar), etc.
_TRANSICION_ACCIONES = {
    "escritura": {"escritura": 0.10, "scroll": 0.20, "teclas": 0.12,
                  "mouse": 0.28, "combo": 0.10, "pestana": 0.10, "nada": 0.10},
    "scroll":    {"escritura": 0.12, "scroll": 0.16, "teclas": 0.10,
                  "mouse": 0.32, "combo": 0.10, "pestana": 0.10, "nada": 0.10},
    "teclas":    {"escritura": 0.15, "scroll": 0.16, "teclas": 0.07,
                  "mouse": 0.32, "combo": 0.10, "pestana": 0.10, "nada": 0.10},
    "mouse":     {"escritura": 0.15, "scroll": 0.22, "teclas": 0.12,
                  "mouse": 0.18, "combo": 0.12, "pestana": 0.12, "nada": 0.09},
    "combo":     {"escritura": 0.15, "scroll": 0.18, "teclas": 0.10,
                  "mouse": 0.28, "combo": 0.07, "pestana": 0.12, "nada": 0.10},
    "pestana":   {"escritura": 0.12, "scroll": 0.25, "teclas": 0.10,
                  "mouse": 0.30, "combo": 0.10, "pestana": 0.03, "nada": 0.10},
    "nada":      {"escritura": 0.15, "scroll": 0.20, "teclas": 0.10,
                  "mouse": 0.30, "combo": 0.08, "pestana": 0.10, "nada": 0.07},
}

_ultimo_accion = None
_decay_factor  = 0.0


def click_seguro():
    """
    Click en la zona segura que el usuario eligió al inicio.
    Mueve el mouse suavemente hasta ahí, clickea, y vuelve.
    """
    if _zona_segura is None:
        return
    esc_t, _, _, _ = mood()
    f = fatiga()
    x, y = pyautogui.position()
    zx, zy = _zona_segura

    # Pequeña variación alrededor de la zona segura (+-15px)
    zx += int(random.gauss(0, 6))
    zy += int(random.gauss(0, 6))
    w, h = pyautogui.size()
    zx = max(5, min(w - 5, zx))
    zy = max(5, min(h - 5, zy))

    # Ir a la zona segura
    dur_ida = rjitter(gauss(0.5 * esc_t * f, 0.15, 0.2, 1.2))
    _mover_mouse_bezier(x, y, zx, zy, dur_ida)

    # Pausa antes de clickear (como si leyera algo)
    time.sleep(rjitter(gauss(0.3, 0.1, 0.1, 0.7)))

    # Click
    pyautogui.click(zx, zy)

    # A veces vuelve a donde estaba, a veces se queda
    if random.random() < 0.6:
        time.sleep(rjitter(gauss(0.4, 0.15, 0.1, 0.9)))
        dur_vuelta = rjitter(gauss(0.5 * esc_t * f, 0.15, 0.2, 1.2))
        _mover_mouse_bezier(zx, zy, x, y, dur_vuelta)


def cambio_pestana():
    """
    Cambia de pestaña con Ctrl+número y vuelve a Ctrl+1.
    Pestañas 2-5, con más probabilidad las cercanas.
    """
    esc_t, _, _, _ = mood()
    f = fatiga()

    # Elegir pestaña destino: Ctrl+2 a Ctrl+5 (más probable las cercanas)
    pestana = random.choices(['2', '3', '4', '5'], weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]

    # Ir a la pestaña
    hold = random.gauss(0.045, 0.012)
    hold = max(0.025, min(0.080, hold))
    pyautogui.keyDown('ctrl')
    time.sleep(hold)
    pyautogui.press(pestana)
    time.sleep(hold)
    pyautogui.keyUp('ctrl')

    # Mirar la otra pestaña un rato (2-8 seg)
    tiempo_otra = rjitter(gauss(4.0 * esc_t * f, 1.5, 2.0, 8.0))
    esperar(tiempo_otra)

    if detener.is_set():
        return

    # Volver a la primera pestaña con Ctrl+1
    hold = random.gauss(0.045, 0.012)
    hold = max(0.025, min(0.080, hold))
    pyautogui.keyDown('ctrl')
    time.sleep(hold)
    pyautogui.press('1')
    time.sleep(hold)
    pyautogui.keyUp('ctrl')


def elegir_accion():
    """
    Selecciona acción usando una mezcla de:
    1. Pesos base (personalidad del script)
    2. Transiciones contextuales (qué hizo antes → qué es natural después)
    Ambos perturbados con Dirichlet. La mezcla varía cada ciclo.
    """
    global _ultimo_accion, _decay_factor

    conc = random.uniform(3.5, 10.0)

    # Pesos base perturbados
    pesos_base = dirichlet_weights(PESOS_BASE, concentracion=conc)

    # Si hay acción anterior, mezclar con transiciones contextuales
    if _ultimo_accion and _ultimo_accion in _TRANSICION_ACCIONES:
        trans = _TRANSICION_ACCIONES[_ultimo_accion]
        pesos_trans = [trans.get(a, 0.05) for a in ACCIONES_BASE]
        pesos_trans = dirichlet_weights(pesos_trans, concentracion=random.uniform(4, 10))

        # Proporción de mezcla varía cada ciclo (40-70% contexto)
        alfa = random.uniform(0.40, 0.70)
        pesos = [alfa * pt + (1 - alfa) * pb
                 for pt, pb in zip(pesos_trans, pesos_base)]
        total = sum(pesos)
        pesos = [p / total for p in pesos]
    else:
        pesos = pesos_base

    # Aplicar bias de ventana mouse/teclado
    pesos = _aplicar_input_bias(pesos)

    accion = random.choices(ACCIONES_BASE, weights=pesos, k=1)[0]

    # Decay probabilístico: si se repite, hay chance de elegir otra
    if accion == _ultimo_accion:
        _decay_factor = min(_decay_factor + random.uniform(0.20, 0.45), 0.90)
        if random.random() < _decay_factor:
            pool   = [a for a in ACCIONES_BASE if a != accion]
            pesos2 = dirichlet_weights([1/len(pool)]*len(pool), concentracion=conc)
            accion = random.choices(pool, weights=pesos2, k=1)[0]
    else:
        _decay_factor = 0.0

    _ultimo_accion = accion
    return accion


def ejecutar_accion(accion):
    if accion == "scroll":
        scroll_suave()
        return "[↓] Scroll               "
    elif accion == "teclas":
        teclas_flechas()
        return "[→] Flechas              "
    elif accion == "escritura":
        simular_escritura()
        return "[✎] Escribiendo          "
    elif accion == "mouse":
        movimiento_mouse()
        return "[~] Mouse suave          "
    elif accion == "combo":
        accion_combo()
        return "[⇄] Combo                "
    elif accion == "pestana":
        cambio_pestana()
        return "[⇥] Cambio pestaña       "
    elif accion == "click":
        click_seguro()
        return "[●] Click zona segura    "
    else:
        return "[·] Leyendo...           "


# ─────────────────────────────────────────────
# ESPERA INTERRUPTIBLE
# ─────────────────────────────────────────────

def esperar(segundos):
    """
    Espera en fragmentos de tamaño variable con distribución gaussiana
    (no uniforme). El prob_temblor muta durante la espera para que
    no sea constante en pausas largas.
    """
    fin = time.time() + segundos
    prob_temblor = random.uniform(0.005, 0.02)
    # Centro y sigma del chunk varían por espera
    chunk_mu = random.uniform(0.15, 0.28)
    chunk_sigma = random.uniform(0.04, 0.10)
    while time.time() < fin:
        if detener.is_set():
            break
        chunk = max(0.06, min(0.50, random.gauss(chunk_mu, chunk_sigma)))
        time.sleep(chunk)
        # Micro-temblor del mouse durante la pausa
        if random.random() < prob_temblor:
            _micro_temblor()
        # Mutar prob_temblor gradualmente (~10% de veces)
        if random.random() < 0.10:
            prob_temblor = max(0.002, min(0.035, prob_temblor * random.uniform(0.6, 1.6)))


# ─────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print("=" * 57)
    print("  keep_awake.py — Simulador de lectura humana")
    print("  Plataforma: macOS | pyautogui + pynput")
    print("-" * 57)
    print("  Scroll · Flechas · Escritura · Mouse · Combos")
    print("  Pausas con objetivo normal (mu=55, alta variabilidad)")
    print()
    if PYNPUT_DISPONIBLE:
        print("  Para DETENER: presiona  F10")
    else:
        print("  Para DETENER: Ctrl+C  (pynput no instalado)")
    print("  Emergencia:   mueve el mouse a la esquina sup-izq.")
    print("=" * 57)
    print()

    for i in range(10, 0, -1):
        print(f"  Cambia a tu ventana — iniciando en {i}s...  ", end="\r")
        time.sleep(1)
    print("  Activo. Presiona F10 para detener.               ")
    print()

    iniciar_listener()

    global _inicio_global
    inicio  = time.time()
    _inicio_global = inicio
    t_act   = 0.0
    t_pau   = 0.0
    ciclos  = 0

    # Break largo: cada ~1 hora, pausa de 1-4 min (baño, café, celular)
    proximo_break = time.time() + gauss(60 * 60, 10 * 60, 45 * 60, 80 * 60)

    while not detener.is_set():
        ciclos += 1

        # ── Break largo (humano real se levanta) ────────────────
        if time.time() >= proximo_break:
            dur_break = gauss(120, 45, 60, 240)  # 1-4 minutos
            print(f"\n  ☕ Break largo ({dur_break:.0f}s) — "
                  f"como si fueras al baño o al celular...", end="\r")
            t0_break = time.time()
            esperar(dur_break)
            t_pau += time.time() - t0_break
            proximo_break = time.time() + gauss(60 * 60, 10 * 60, 45 * 60, 80 * 60)
            if detener.is_set():
                break

        # Actualizar pyautogui.PAUSE con un valor levemente aleatorio
        # (rompe la cadencia constante de llamadas a la API)
        pyautogui.PAUSE = random.uniform(0.018, 0.055)

        # Actualizar humor cada N ciclos
        actualizar_mood(ciclos)

        elapsed = int(time.time() - inicio)
        mm, ss  = divmod(elapsed, 60)
        total   = t_act + t_pau
        pct_p   = (t_pau / total * 100) if total > 0 else 50.0

        _, _, _, desc_mood = mood()

        # ── Acción ────────────────────────────────────────────
        accion = elegir_accion()
        t0     = time.time()
        sym    = ejecutar_accion(accion)
        dur_accion = time.time() - t0
        t_act += dur_accion

        if detener.is_set():
            break

        # ── Pausa adaptativa ──────────────────────────────────
        espera, tipo = pausa_lectora(pct_p, dur_accion, t_act, t_pau)

        print(f"  {mm:02d}:{ss:02d} | #{ciclos:03d} | {sym} | "
              f"pausa {espera:.0f}s ({tipo}) | {pct_p:.0f}% | {desc_mood}   ",
              end="\r")

        t0 = time.time()

        # Micro-actividad: umbral variable por ciclo (no siempre 18s)
        umbral_micro = gauss(16, 5, 8, 28)
        prob_micro   = random.uniform(0.30, 0.55)
        if espera > umbral_micro and random.random() < prob_micro and not detener.is_set():
            frac   = random.uniform(0.28, 0.75)
            primer = espera * frac
            resto  = espera * (1 - frac)
            esperar(primer)
            t_pau += espera * frac  # solo la espera real cuenta como pausa
            if not detener.is_set():
                micro_pesos = dirichlet_weights([0.28, 0.26, 0.24, 0.22],
                                               concentracion=random.uniform(4, 8))
                micro = random.choices(
                    ["mouse", "scroll", "teclas", "escritura"],
                    weights=micro_pesos
                )[0]
                t0_micro = time.time()
                ejecutar_accion(micro)
                t_act += time.time() - t0_micro  # micro-actividad cuenta como ACTIVIDAD
            esperar(resto)
            t_pau += espera * (1 - frac)  # segunda espera como pausa
        else:
            esperar(espera)
            t_pau += time.time() - t0

    # ── Resumen final ──────────────────────────────────────────
    elapsed = int(time.time() - inicio)
    mm, ss  = divmod(elapsed, 60)
    total   = t_act + t_pau
    pct_p   = (t_pau / total * 100) if total > 0 else 0
    print()
    print()
    print(f"  Detenido (F10). Sesión: {mm:02d}:{ss:02d} | "
          f"{ciclos} ciclos | {pct_p:.0f}% en pausa.")
    print("  ¡Hasta luego!")


if __name__ == "__main__":
    main()
