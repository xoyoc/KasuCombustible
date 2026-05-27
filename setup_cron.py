import sys
from crontab import CronTab
import os
import getpass

def setup_monthly_report_cron():
    """Configura el cron job para envío automático el día 1 de cada mes"""
    
    # Obtener el usuario actual
    user = getpass.getuser()
    cron = CronTab(user=user)
    
    # Ruta al proyecto Django
    project_path = input("Ingresa la ruta completa a tu proyecto Django: ")
    python_path = input("Ingresa la ruta al Python virtual env (o presiona Enter para usar el actual): ")
    
    if not python_path:
        python_path = sys.executable
    
    # Comando para ejecutar
    command = f'cd {project_path} && {python_path} manage.py enviar_reporte_mensual'
    
    # Crear el job para ejecutar el día 1 de cada mes a las 8:00 AM
    job = cron.new(command=command, comment='Reporte mensual de combustible')
    job.setall('0 8 1 * *')  # minuto hora día mes día_semana
    
    # Escribir el crontab
    cron.write()
    
    print("🎯 Cron job configurado exitosamente!")
    print(f"📅 Se ejecutará el día 1 de cada mes a las 8:00 AM")
    print(f"💻 Comando: {command}")
    print("\n📋 Para verificar: crontab -l")
    print("🗑️ Para eliminar: crontab -e (y eliminar la línea)")