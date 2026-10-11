"""
Knowledge Base for Defensive Cybersecurity (Blue Team).
Incorporates curated entries from OWASP Top 10, MITRE ATT&CK, and CIS Controls.
"""

from typing import List, Dict, Any

KNOWLEDGE_ENTRIES: List[Dict[str, Any]] = [
    {
        "id": "OWASP-A01",
        "framework": "OWASP Top 10",
        "title": "A01:2021 - Pérdida de Control de Acceso (Broken Access Control)",
        "keywords": ["acceso", "permisos", "autorizacion", "privilegios", "idor", "bypass"],
        "description": "Las fallas en los controles de acceso permiten a usuarios no autenticados o con bajos privilegios acceder a recursos no autorizados o escalar privilegios.",
        "mitigation": "Aplicar el principio de mínimo privilegio. Denegar el acceso por defecto. Validar permisos en cada endpoint en el lado del servidor y deshabilitar el listado de directorios.",
    },
    {
        "id": "OWASP-A03",
        "framework": "OWASP Top 10",
        "title": "A03:2021 - Inyección (Injection: SQL, Command, LDAP)",
        "keywords": ["inyeccion", "sql", "sqli", "comandos", "ldap", "xss", "payload"],
        "description": "Ocurre cuando datos no confiables son enviados a un intérprete como parte de un comando o consulta, provocando ejecución no intencionada de código.",
        "mitigation": "Utilizar consultas parametrizadas (Prepared Statements / ORM), validación estricta de entradas mediante lista blanca (allowlist) y escapar caracteres especiales.",
    },
    {
        "id": "OWASP-A05",
        "framework": "OWASP Top 10",
        "title": "A05:2021 - Configuración de Seguridad Defectuosa (Security Misconfiguration)",
        "keywords": ["configuracion", "puertos", "credenciales", "defaults", "debug", "headers"],
        "description": "Uso de contraseñas por defecto, puertos innecesarios habilitados, encabezados HTTP de seguridad ausentes o mensajes de error detallados expuestos.",
        "mitigation": "Cerrar todos los puertos no requeridos, cambiar contraseñas por defecto de inmediato, habilitar cabeceras HSTS/CSP y automatizar auditorías de configuración.",
    },
    {
        "id": "MITRE-T1046",
        "framework": "MITRE ATT&CK",
        "title": "T1046: Network Service Discovery",
        "keywords": ["escaneo", "puertos", "servicios", "reconocimiento", "nmap", "scan"],
        "description": "Técnica de adversarios para enumerar servicios de red activos buscando vectores de entrada y versiones desactualizadas.",
        "mitigation": "Implementar segmentación de red con VLANs, firewalls locales por host, detección de anomalías con IDS/IPS (Snort/Suricata) y desactivar servicios prescindibles.",
    },
    {
        "id": "MITRE-T1078",
        "framework": "MITRE ATT&CK",
        "title": "T1078: Valid Accounts (Cuentas Válidas)",
        "keywords": ["cuentas", "credenciales", "fuerza bruta", "password", "login", "rdp", "ssh"],
        "description": "Uso de credenciales legítimas robadas, filtradas o por defecto para obtener acceso inicial o persistencia sin activar alarmas tradicionales.",
        "mitigation": "Obligar el uso de autenticación multifactor (MFA/2FA), políticas de contraseñas robustas y monitoreo de accesos en horarios o ubicaciones inusuales.",
    },
    {
        "id": "CIS-04",
        "framework": "CIS Controls v8",
        "title": "CIS Control 4: Configuración Segura de Activos y Software",
        "keywords": ["hardening", "linea base", "cifrado", "parches", "servicios", "tls"],
        "description": "Establecer y mantener configuraciones de seguridad robustas para todos los sistemas operativos, servicios y aplicaciones de la organización.",
        "mitigation": "Adoptar guías de hardening (CIS Benchmarks), deshabilitar protocolos inseguros (Telnet, SMBv1, SSLv3) y forzar TLS 1.3 con certificados válidos.",
    },
    {
        "id": "CIS-06",
        "framework": "CIS Controls v8",
        "title": "CIS Control 6: Gestión del Control de Acceso",
        "keywords": ["acceso", "usuarios", "sesiones", "privilegios", "rbac"],
        "description": "Uso de procesos y herramientas para asignar y revocar credenciales y privilegios para identidades de usuarios y servicios autorizados.",
        "mitigation": "Auditar periódicamente cuentas de administrador, centralizar la gestión de identidad (IAM) y bloquear sesiones inactivas automáticamente.",
    },
]
