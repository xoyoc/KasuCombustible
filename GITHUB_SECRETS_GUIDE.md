# 🔐 Guía Visual: Configurar Secrets en GitHub Actions

## 📍 **Paso a Paso Visual**

### **1. Acceder a la Configuración**
```
GitHub Repository → Settings → Secrets and variables → Actions
```

### **2. Interfaz de Secrets**
```
┌─────────────────────────────────────────────────────────────┐
│ Repository secrets                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Name: [SECRET_KEY                    ] [Update] [Delete]│ │
│ │ Name: [DJANGO_DB_URL                 ] [Update] [Delete]│ │
│ │ Name: [DO_SPACES_ACCESS_KEY          ] [Update] [Delete]│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [+ New repository secret]                                   │
└─────────────────────────────────────────────────────────────┘
```

### **3. Agregar Nuevo Secret**
```
┌─────────────────────────────────────────────────────────────┐
│ New secret                                                   │
│                                                             │
│ Name*                                                       │
│ [SECRET_KEY                                    ]            │
│                                                             │
│ Secret*                                                     │
│ [django-insecure-abc123def456ghi789jkl012mno345pqr678stu901]│
│                                                             │
│ [Add secret]                                                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 **Lista Completa de Secrets**

### **🔑 Django Core**
| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-abc123...` |
| `DEBUG` | Modo debug | `False` |
| `ALLOWED_HOSTS` | Hosts permitidos | `squid-app-5j4xm.ondigitalocean.app` |

### **🗄️ Base de Datos**
| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `DJANGO_DB_URL` | URL de PostgreSQL | `postgresql://user:pass@host:port/db` |

### **☁️ DigitalOcean Spaces**
| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `DO_SPACES_ACCESS_KEY` | Access Key | `DO00ABC123DEF456GHI789` |
| `DO_SPACES_SECRET_KEY` | Secret Key | `abc123def456ghi789jkl012...` |
| `DO_SPACES_BUCKET_NAME` | Nombre del bucket | `combustible-files-prod` |
| `DO_SPACES_ENDPOINT_URL` | URL del endpoint | `https://nyc3.digitaloceanspaces.com` |
| `DO_SPACES_REGION` | Región | `nyc3` |

### **📱 WhatsApp Business API**
| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número | `123456789012345` |
| `WHATSAPP_ACCESS_TOKEN` | Token de acceso | `EAAxxxxxxxxxxxxxxxxxxxxx` |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación | `mi_token_verificacion_123` |

### **📧 Email (SendGrid)**
| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `EMAIL_HOST_PASSWORD` | API Key de SendGrid | `SG.abc123def456ghi789...` |

## 🛠️ **Cómo Obtener Cada Secret**

### **🔑 SECRET_KEY**
```bash
# Generar automáticamente
python3 -c "import secrets; print('django-insecure-' + secrets.token_urlsafe(50))"

# O usar el script
./scripts/generate_secrets.sh
```

### **🗄️ DJANGO_DB_URL**
```bash
# En DigitalOcean Database
# Connection Details → Connection Parameters
# Formato: postgresql://usuario:password@host:port/database?sslmode=require
```

### **☁️ DigitalOcean Spaces**
```bash
# En DigitalOcean Control Panel
# API → Spaces Keys → Generate New Key
# O usar doctl:
doctl spaces keys list
```

### **📱 WhatsApp Business API**
```bash
# En Meta for Developers
# WhatsApp → API Setup → Phone Number ID
# WhatsApp → API Setup → Access Token
```

### **📧 SendGrid API Key**
```bash
# En SendGrid Dashboard
# Settings → API Keys → Create API Key
# Dar permisos de "Mail Send"
```

## 🔍 **Verificar Configuración**

### **Script de Verificación**
```bash
# Crear script para verificar secrets
cat > verify_secrets.py << 'EOF'
import os
import sys

required_secrets = [
    'SECRET_KEY',
    'DJANGO_DB_URL',
    'DO_SPACES_ACCESS_KEY',
    'DO_SPACES_SECRET_KEY',
    'DO_SPACES_BUCKET_NAME',
    'DO_SPACES_ENDPOINT_URL',
    'DO_SPACES_REGION',
    'WHATSAPP_PHONE_NUMBER_ID',
    'WHATSAPP_ACCESS_TOKEN',
    'WHATSAPP_VERIFY_TOKEN',
    'EMAIL_HOST_PASSWORD'
]

print("🔍 Verificando Secrets...")
print("=" * 50)

missing_secrets = []
for secret in required_secrets:
    if os.getenv(secret):
        print(f"✅ {secret}: Configurado")
    else:
        print(f"❌ {secret}: FALTANTE")
        missing_secrets.append(secret)

print("=" * 50)
if missing_secrets:
    print(f"❌ Faltan {len(missing_secrets)} secrets:")
    for secret in missing_secrets:
        print(f"   - {secret}")
    sys.exit(1)
else:
    print("✅ Todos los secrets están configurados")
EOF

python verify_secrets.py
```

## 🚨 **Problemas Comunes**

### **❌ Secret no encontrado**
```
Error: Environment variable 'SECRET_KEY' not found
```
**Solución**: Verificar que el nombre del secret sea exactamente igual (case-sensitive)

### **❌ Formato incorrecto**
```
Error: Invalid database URL format
```
**Solución**: Verificar que `DJANGO_DB_URL` tenga el formato correcto de PostgreSQL

### **❌ Permisos insuficientes**
```
Error: Access denied to DigitalOcean Spaces
```
**Solución**: Verificar que las keys de Spaces tengan permisos de lectura/escritura

## 🔒 **Mejores Prácticas de Seguridad**

### **✅ Hacer**
- Usar nombres descriptivos para los secrets
- Rotar keys regularmente
- Usar diferentes keys para desarrollo/producción
- Verificar permisos mínimos necesarios

### **❌ No Hacer**
- Nunca commitear secrets al código
- No usar la misma key para múltiples propósitos
- No compartir secrets por email/chat
- No usar keys de producción en desarrollo

## 📊 **Monitoreo de Secrets**

### **Verificar en GitHub Actions**
```yaml
# En el workflow, agregar step de verificación
- name: Verify secrets
  run: |
    echo "🔍 Verificando secrets..."
    python verify_secrets.py
```

### **Logs de Verificación**
```bash
# Los secrets aparecen como *** en los logs
echo "SECRET_KEY: ***"
echo "DJANGO_DB_URL: ***"
```

## 🎯 **Checklist de Configuración**

- [ ] **SECRET_KEY** configurado
- [ ] **DEBUG** configurado como "False"
- [ ] **ALLOWED_HOSTS** configurado
- [ ] **DJANGO_DB_URL** configurado
- [ ] **DO_SPACES_ACCESS_KEY** configurado
- [ ] **DO_SPACES_SECRET_KEY** configurado
- [ ] **DO_SPACES_BUCKET_NAME** configurado
- [ ] **DO_SPACES_ENDPOINT_URL** configurado
- [ ] **DO_SPACES_REGION** configurado
- [ ] **WHATSAPP_PHONE_NUMBER_ID** configurado
- [ ] **WHATSAPP_ACCESS_TOKEN** configurado
- [ ] **WHATSAPP_VERIFY_TOKEN** configurado
- [ ] **EMAIL_HOST_PASSWORD** configurado
- [ ] **Workflow ejecutado** exitosamente
- [ ] **Logs verificados** sin errores

## 🚀 **Próximos Pasos**

1. **Configurar todos los secrets** usando la lista anterior
2. **Ejecutar el workflow** manualmente para probar
3. **Verificar logs** en GitHub Actions
4. **Probar envío** de reporte en modo test
5. **Configurar notificaciones** de éxito/fallo

---

**¡Con esta configuración, tu sistema de reportes automáticos estará listo! 🎉**
