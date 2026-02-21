# Definición del problema

## 1. Contexto

En entornos Linux compartidos es habitual disponer de **recursos GPU limitados**, a menudo una única GPU, que debe ser utilizada por varios usuarios de forma concurrente.  
Este escenario es común en:

- servidores de investigación
- entornos académicos
- equipos de I+D
- servidores internos de experimentación en IA

En estos sistemas, los usuarios suelen ejecutar cargas de trabajo intensivas (entrenamiento de modelos, inferencia, simulaciones, etc.) que requieren acceso exclusivo o prioritario a la GPU.

Adicionalmente, es frecuente que los usuarios trabajen con **contenedores Docker**, y que exista la necesidad de preservar la propiedad correcta de los ficheros generados, lo que favorece el uso de **Docker en modo rootless**.

---

## 2. Problema identificado

En ausencia de un mecanismo de coordinación, el uso compartido de una GPU presenta varios problemas recurrentes:

### 2.1 Conflictos de uso de la GPU
Múltiples usuarios pueden lanzar trabajos simultáneamente que intentan utilizar la GPU al mismo tiempo, provocando:

- degradación severa del rendimiento
- errores de ejecución
- resultados no reproducibles
- consumo ineficiente del recurso

### 2.2 Falta de control y visibilidad
Sin un sistema común:

- no existe una cola de ejecución clara
- no se sabe qué trabajos están en espera o en ejecución
- no hay un orden definido de uso del recurso

Esto dificulta tanto la planificación del trabajo como la resolución de incidencias.

### 2.3 Problemas de propiedad de ficheros
Cuando los contenedores se ejecutan con privilegios elevados o mediante mecanismos no alineados con el usuario real, los ficheros generados pueden quedar con propietarios incorrectos, lo que introduce:

- problemas de permisos
- necesidad de correcciones manuales (`chown`)
- riesgos de seguridad y mantenimiento

### 2.4 Falta de trazabilidad y auditoría
Sin un mecanismo común, resulta difícil responder a preguntas básicas como:

- quién ejecutó un trabajo
- cuándo se ejecutó
- qué recursos utilizó
- qué acciones se realizaron sobre el sistema

Esta falta de trazabilidad complica la depuración, la rendición de cuentas y el mantenimiento del sistema.

---

## 3. Motivación de la solución

La motivación principal es **garantizar un uso ordenado, predecible y auditable de la GPU**, sin introducir una complejidad excesiva ni depender de sistemas de orquestación pesados.

Los objetivos que motivan la solución son:

- asegurar que la GPU sea utilizada por **un único trabajo a la vez**
- proporcionar un mecanismo sencillo de **encolado de trabajos**
- preservar la **identidad real del usuario** durante la ejecución
- evitar el uso de privilegios innecesarios
- mantener la solución alineada con herramientas estándar de Linux
- facilitar la trazabilidad y el análisis posterior de eventos

---

## 4. Alcance del problema

Este proyecto aborda específicamente:

- la coordinación del acceso a una GPU compartida
- la ejecución secuencial de trabajos GPU
- la correcta atribución de identidad y propiedad de ficheros
- la auditabilidad de las acciones relacionadas con la cola

El sistema **no pretende** resolver problemas de:

- planificación compleja de recursos
- ejecución distribuida en múltiples nodos
- aislamiento fuerte frente a usuarios maliciosos
- gestión avanzada de cuotas o prioridades (en esta fase)