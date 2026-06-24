import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Configuración de la página
st.set_page_config(page_title="Turnos de Cooper 🐾", page_icon="🐾", layout="centered")

st.title("🐾 El Planificador de Cooper")
st.write("Registrad los turnos reales y descargad el informe oficial en PDF.")

# --- BASE DE DATOS REAL (AHORA SÍ, COMPLETAMENTE VACÍA AL PRINCIPIO) ---
if "historico_paseos" not in st.session_state:
    st.session_state.historico_paseos = []

if "razones" not in st.session_state:
    st.session_state.razones = {}

# Generación de los próximos 7 días
meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
dias_semana_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

DIAS_DINAMICOS = []
hoy = datetime.now()

for i in range(7):
    fecha_futura = hoy + timedelta(days=i)
    texto_pestaña = f"{dias_semana_es[fecha_futura.weekday()]} {fecha_futura.day} {meses_es[fecha_futura.month - 1]}"
    DIAS_DINAMICOS.append(texto_pestaña)

TURNOS = ["Mañana", "Mediodía", "Noche"]
OPCIONES = ["Seleccionar...", "No puedo", "Puedo", "Me viene genial", "Lo sacan Papá/Mamá"]

# --- PLANIFICADOR SEMANAL ---
st.header("🗓️ Planificación de esta semana")
tabs = st.tabs(DIAS_DINAMICOS)

for i, dia_texto in enumerate(DIAS_DINAMICOS):
    with tabs[i]:
        st.subheader(f"📅 Paseos del {dia_texto}")
        
        for turno in TURNOS:
            st.write(f"**Turno de la {turno}:**")
            col1, col2 = st.columns(2)
            
            with col1:
                pref_nerea = st.selectbox(f"Preferencia de Nerea ({turno})", OPCIONES, key=f"nerea_{dia_texto}_{turno}")
            with col2:
                pref_aitana = st.selectbox(f"Preferencia de Aitana ({turno})", OPCIONES, key=f"aitana_{dia_texto}_{turno}")
            
            encargado_final = None
            
            if "Papá/Mamá" in pref_nerea or "Papá/Mamá" in pref_aitana:
                st.success("😎 ¡Salvadas! Este turno se lo comen Papá/Mamá.")
                encargado_final = "Papá/Mamá"
            elif pref_nerea == "No puedo" and pref_aitana == "No puedo":
                st.error("⚠️ ¡CONFLICTO! Ni Nerea ni Aitana pueden.")
                clave_razon = f"razon_{dia_texto}_{turno}"
                razon = st.text_input(f"Motivo del conflicto:", key=clave_razon, placeholder="Ej: Examen / Trabajo")
                if razon:
                    st.session_state.razones[f"{dia_texto}_{turno}"] = razon
            elif pref_nerea in ["Puedo", "Me viene genial"] and pref_aitana == "No puedo":
                st.success("✅ ¡Le toca a Nerea!")
                encargado_final = "Nerea"
            elif pref_aitana in ["Puedo", "Me viene genial"] and pref_nerea == "No puedo":
                st.success("✅ ¡Le toca a Aitana!")
                encargado_final = "Aitana"
            elif pref_nerea == "Me viene genial" and pref_aitana == "Puedo":
                st.success("✅ Le toca a Nerea (le viene mejor).")
                encargado_final = "Nerea"
            elif pref_aitana == "Me viene genial" and pref_nerea == "Puedo":
                st.success("✅ Le toca a Aitana (le viene mejor).")
                encargado_final = "Aitana"
            elif pref_nerea != "Seleccionar..." and pref_aitana != "Seleccionar...":
                st.warning("🤝 Empate. Decidid quién va.")
            
            if encargado_final:
                if st.button(f"📌 Confirmar que se ha hecho este paseo", key=f"btn_{dia_texto}_{turno}"):
                    nuevo_registro = {"Fecha": dia_texto, "Turno": turno, "Encargado": encargado_final}
                    if nuevo_registro not in st.session_state.historico_paseos:
                        st.session_state.historico_paseos.append(nuevo_registro)
                        st.toast(f"¡Paseo anotado para {encargado_final}!")

st.markdown("---")

# --- SECCIÓN DE HISTORIAL REAL Y EXPORTACIÓN ---
st.header("📊 Auditoría e Informe Mensual")
st.write("Historial de paseos confirmados de verdad:")

# Si hay datos de verdad introducidos por vosotras...
if st.session_state.historico_paseos:
    df_real = pd.DataFrame(st.session_state.historico_paseos)
    st.dataframe(df_real, use_container_width=True)
    
    conteo = df_real["Encargado"].value_counts()
    t_nerea = conteo.get("Nerea", 0)
    t_aitana = conteo.get("Aitana", 0)
    t_padres = conteo.get("Papá/Mamá", 0)
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Paseos de Nerea", f"{t_nerea} 🐾")
    col_m2.metric("Paseos de Aitana", f"{t_aitana} 🐾")
    col_m3.metric("Papá/Mamá", f"{t_padres} 🐾")
    
    # Generador de PDF personalizado con el nombre de Cooper
    def generar_pdf(data_frame):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        styles = getSampleStyleSheet()
        titulo = Paragraph("<b>INFORME OFICIAL DE PASEOS DE COOPER</b>", styles["Title"])
        story.append(titulo)
        story.append(Spacer(1, 20))
        
        tabla_datos = [["Fecha", "Turno de Paseo", "Persona Encargada"]]
        for _, fila in data_frame.iterrows():
            tabla_datos.append([fila["Fecha"], fila["Turno"], fila["Encargado"]])
            
        t = Table(tabla_datos, colWidths=[150, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FF4B4B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0F2F6")),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#DDDDDD")),
            ('FONTSIZE', (0,0), (-1,-1), 11),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    pdf_data = generar_pdf(df_real)
    st.download_button(
        label="📥 Descargar Historial en PDF",
        data=pdf_data,
        file_name=f"registro_paseos_cooper_{datetime.now().strftime('%m_%Y')}.pdf",
        mime="application/pdf"
    )
else:
    # Mensaje limpio si todavía no habéis confirmado nada
    st.info("Aún no hay ningún paseo guardado para Cooper. ¡Empezad a confirmar turnos arriba!")