# 🛡️ SOC-Automatizado
Cómo instalar y configurar un SIEM (Graylog) para gestión de incidentes, para luego, con un SOAR (Shuffle) poder automatizar las acciones dependiendo del tipo de evento. Además, miraremos cómo representar y gestionar las incidencias a través de Jira. 

El objetivo de este proyecto, es acercar el SOC (Centro de Operaciones de Seguridad) a empresas que están empezado en el sector de la ciberseguridad y no se pueden permitir el precio de las herramientas ya establecidas. No solo quiero amuentar la accesibilidad, sinó también reducir el coste, ya que, en este post, se va a explicar cómo llevar a cabo todo con herramientas y servicios que pueden salir a coste 0.

---

## 📘 Wiki del Proyecto

Toda la documentación detallada está disponible en la [Wiki del repositorio](https://github.com/Arnoise/SOC-Automatizado/wiki).

---

## 🔍 Índice de Contenidos

### ⚙️ Graylog - SIEM
> Primero veremos una guía de cómo se instaló Graylog en una máquina AWS (se podría hacer en máquinas virtuales perfectamente), además de su configuración para la ingesta de logs de las diferentes herramientas de Cisco y la creación de notificaciones.

- Capítulo 1 - [Instalación Graylog OPEN](https://github.com/Arnoise/SOC-Automatizado/wiki/Instalaci%C3%B3n-Graylog-OPEN)
- Capítulo 2 - [Creación de los INPUTS](https://github.com/Arnoise/SOC-Automatizado/wiki/Creaci%C3%B3n-de-los-INPUTS)
- Capítulo 3 - [Scripts - De la herramienta al SIEM](https://github.com/Arnoise/SOC-Automatizado/wiki/Scripts-%E2%80%90-De-la-herramienta-al-SIEM)
- Capítulo 4 - [Creación de los Extractores](https://github.com/Arnoise/SOC-Automatizado/wiki/Creaci%C3%B3n-de-los-Extractores)
- Capítulo 5 - [Creación de Dashboards](https://github.com/Arnoise/SOC-Automatizado/wiki/Creaci%C3%B3n-de-Dashboards)
- Capítulo 6 - [Servidor SMTP](https://github.com/Arnoise/SOC-Automatizado/wiki/Servidor-SMTP)
- Capítulo 7 - [Configuración de la Notificación](https://github.com/Arnoise/SOC-Automatizado/wiki/Configuraci%C3%B3n-de-la-Notificaci%C3%B3n)
- Capítulo 8 - [Definición de Eventos](https://github.com/Arnoise/SOC-Automatizado/wiki/Definici%C3%B3n-de-Eventos)

Una vez seguidos estos pasos, tendremos un SIEM funcional que ingiere logs de las herramientas de Cisco (Umbrella, Secure Endpoint, DUO y Meraki). Gracias al formato que le daremos, Graylog los podrá interpretar, lo que no ayudará a crear dashboards y notificaciones segun el tipo de evento.

---

### 🔄 Shuffle - SOAR

> El siguiente paso, es decidir qué hacer con todas las incidencias. Para automatizar los procesos tan repetitivos, entra en juego el SOAR, en este caso, Shuffle. Para ello, usaremos docker con tal de desplegar el servicio en una maquina virtual. En el siguiente tutorial, veremos cómo crear los flujos de trabajo, además de integrar la herramienta con Jira, el cual, nos ayudará a tener una constancia del estado de los incidentes y también de su correlación con otros que sean similares.

- Capítulo 1 - [Instalación (Linux Docker)](https://github.com/Arnoise/SOC-Automatizado/wiki/Instalaci%C3%B3n-(Linux-Docker))
- Capítulo 2 - [Workflow de Ejemplo](https://github.com/Arnoise/SOC-Automatizado/wiki/Workflow-de-Ejemplo)
- Capítulo 3 - [Outlook OpenAPI + Auth2 (Azure)](https://github.com/Arnoise/SOC-Automatizado/wiki/Outlook-OpenAPI---OAuth2-(Azure))
- Capítulo 4 - [Get_oldest_not_readen_email](https://github.com/Arnoise/SOC-Automatizado/wiki/Get_oldest_not_readen_mail)
- Capítulo 5 - [HTML_to_JSON](https://github.com/Arnoise/SOC-Automatizado/wiki/HTML_to_JSON)
- Capítulo 6 - [MISP OpenAPI + Event Conditions + Create Event](https://github.com/Arnoise/SOC-Automatizado/wiki/MISP-OpenAPI_Event-Conditions_Create-Event)
- Capítulo 7 - [Virustotal OpenAPI](https://github.com/Arnoise/SOC-Automatizado/wiki/Virustotal-OpenAPI)
- Capítulo 8 - [Bot Creation + Webex Notification](https://github.com/Arnoise/SOC-Automatizado/wiki/Bot-Creation-AND-Webex-Notification)
- Capítulo 9 - [Creación de Ticket en Jira](https://github.com/Arnoise/SOC-Automatizado/wiki/Creaci%C3%B3n-de-Ticket-en-Jira)
- Capítulo 10 - [Defang Domain + Prepare Message + Mark As Read](https://github.com/Arnoise/SOC-Automatizado/wiki/Defang-Domain_Prepare-Message_Mark-As-Read)
- Capítulo 11 - [Automatización de Workflows](https://github.com/Arnoise/SOC-Automatizado/wiki/Automatizaci%C3%B3n-de-Workflows)
- Capítulo 12 - [Limpieza Periódica de Logs](https://github.com/Arnoise/SOC-Automatizado/wiki/Limpieza-Peri%C3%B3dica-de-Logs)

Una vez seguidos todos estos pasos, podremos disfrutar de las ventajas de tener un SOC automatizado. Reducirá tiempo de trabajo notablemente.
