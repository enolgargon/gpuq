# Requisitos del sistema

## 1. Requisitos funcionales

Los requisitos funcionales describen **qué debe hacer el sistema** desde el punto de vista del comportamiento observable.

### RF-01 Encolado de trabajos GPU
El sistema deberá permitir a un usuario encolar un trabajo que requiera acceso a la GPU mediante una interfaz de línea de comandos.

### RF-02 Ejecución secuencial de trabajos
El sistema deberá garantizar que **solo un trabajo GPU se ejecute simultáneamente** en el sistema.

### RF-03 Persistencia de la cola
El sistema deberá mantener el estado de la cola de trabajos de forma persistente, de modo que no se pierdan trabajos encolados ante reinicios del sistema o caídas de procesos.

### RF-04 Ejecución con identidad del usuario
El sistema deberá ejecutar cada trabajo bajo la identidad del usuario que lo haya encolado, preservando su UID y GID.

### RF-05 Ejecución no interactiva
El sistema deberá permitir que los trabajos se ejecuten correctamente incluso si el usuario no mantiene una sesión activa en el sistema.

### RF-06 Consulta del estado de la cola
El sistema deberá permitir a los usuarios consultar el estado de la cola de trabajos, incluyendo:
- trabajos en espera
- trabajos en ejecución
- trabajos finalizados o fallidos

### RF-07 Cancelación de trabajos
El sistema deberá permitir a un usuario cancelar:
- trabajos propios encolados
- trabajos propios en ejecución (sujeto a las capacidades del sistema)

### RF-08 Aislamiento lógico entre trabajos
El sistema deberá impedir que un usuario pueda modificar, cancelar o ejecutar trabajos pertenecientes a otros usuarios.

### RF-09 Registro de eventos relevantes
El sistema deberá registrar los eventos relevantes asociados a la gestión de la cola, incluyendo:
- encolado de trabajos
- inicio de ejecución
- finalización correcta
- finalización con error
- cancelación

---

## 2. Requisitos no funcionales

Los requisitos no funcionales describen **restricciones, cualidades y propiedades del sistema**.

### RNF-01 Uso de Docker en modo rootless
El sistema deberá ejecutar las cargas de trabajo utilizando Docker en modo rootless, evitando el uso de privilegios elevados.

### RNF-02 Preservación de la propiedad de ficheros
El sistema deberá garantizar que los ficheros generados por los trabajos mantengan como propietario al usuario que los ejecuta.

### RNF-03 Dependencias mínimas
El sistema deberá basarse exclusivamente en componentes estándar de un sistema Linux moderno, evitando dependencias externas como bases de datos o servicios adicionales.

### RNF-04 Alineación con mecanismos estándar de Linux
El sistema deberá apoyarse en mecanismos estándar del sistema operativo (sistema de ficheros, permisos, systemd, herramientas de auditoría).

### RNF-05 Auditabilidad
El sistema deberá permitir la auditoría de las acciones realizadas sobre la cola de trabajos y sus ficheros asociados, incluyendo acciones manuales y automáticas.

### RNF-06 Tolerancia a fallos
El sistema deberá ser capaz de recuperarse de fallos parciales, como la caída del proceso de gestión de la cola, sin pérdida de información crítica.

### RNF-07 Simplicidad operativa
El sistema deberá mantener un diseño simple, favoreciendo la transparencia y facilidad de depuración frente a soluciones complejas u opacas.

### RNF-08 Seguridad contextual
El sistema deberá proporcionar un nivel de seguridad adecuado para un entorno de usuarios cooperativos, sin pretender ofrecer aislamiento fuerte frente a actores maliciosos.

---

## 3. Restricciones del sistema

Las siguientes restricciones condicionan explícitamente el diseño del sistema:

- El sistema está diseñado inicialmente para entornos con una única GPU.
- El sistema no implementa planificación avanzada de recursos ni reparto dinámico de GPU.
- El sistema no impone políticas de tiempo máximo de ejecución en su versión inicial.
- El sistema no proporciona una interfaz gráfica en su versión inicial.

---

## 4. Suposiciones

El diseño del sistema se basa en las siguientes suposiciones:

- Los usuarios tienen cuentas locales en el sistema Linux.
- El sistema cuenta con soporte funcional de Docker rootless.
- El sistema utiliza `systemd` como gestor de servicios.