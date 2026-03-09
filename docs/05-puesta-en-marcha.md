# Puesta en marcha
Esta sección detalla el procedimiento de puesta en marcha y prueba del sistema desarollado dentro del sistema en funcionamiento. Todos los pasos del despliegue se puede hacer y probar sin interferir con el resto de usuarios que estén utilizando el sistema, con excepción de la fase 4.5 donde se prueba la resistencia y arranque del sistema tras un apagado y reinicio del sistema.


## Prerrequisitos del sistema
Antes de comenzar la puesta en marcha se tienen que validar los siguientes aspectos:
- El sistema dispone de al menos una GPU NVIDIA funcional.
- Los drivers NVIDIA están correctamente instalados.
- `nvidia-smi` funciona sin errores.
- Las GPUs son visibles desde el host.
- Los dispositivos `/dev/nvidia*` existen y son accesibles.
- `systemd` está disponible y operativo.
- `docker` está instalado y funcional en modo Rootless.
- NVIDIA Container Toolkit está instalado.
- Un contenedor puede acceder correctamente a la GPU. 
- Python3 y pip debe estar instalado en el sistema.

## Plan de rollback
En caso de que suceda algún error durante la puesta en marcha y prueba del sistema hay tres planes de Rollback para evitar que el sistema afecte al resto de usuarios del sistema.

### Nivel 1
El nivel 1 del plan de rollback consiste en parar y deshabilitar el servicio de dispatcher para que no se procesen trabajo ni se ejecute nada. Para ello es necesario ejecutar lo siguiente.

```bash
systemctl stop gpuq-dispatcher
systemctl disable gpuq-dispatcher
```

En la mayoría de casos este rollback sería suficiente hasta analizar el problema, explorar soluciones y diseñar un nuevo plan de acción.

### Nivel 2
El nivel 2 es un plan incrementar, que se ejecutaría tras el nivel 1 y que consiste en la eliminación estructural de los elementos que falicitan la ejecución del CLI por parte de los usuarios y permiten la ejecución del servicio. Este plan engloba:

1. Eliminar servicio systemd

```bash
rm /etc/systemd/system/gpuq-dispatcher.service
systemctl daemon-reload
```

2. Eliminar enlace simbólico del CLI

```bash
rm /usr/local/bin/gpuq
```

3. Eliminar a todos los usuarios del grupo `gpuq`.

```bash
gpasswd -d <usuario> gpuq
```

### Nivel 3
En este último nivel incrementar, que se ejecutaría tras el nivel 2, se hace una desinstalación completa eliminando todos los elementos de gpuq del sistema. Consiste en:

1. Desactivar la auditoria

```bash
rm /etc/audit/rules.d/gpuq.rules
augenrules --load
```

2. Eliminar las estructuras de cola

```bash
rm -rf /var/lib/gpuq
```

3. Eliminar el usuario y grupo asignado a la ejecución del software.

```bash
groupdel gpuq
userdel gpuq
```

4. Eliminación completa del software.

```bash
rm -rf /opt/gpuq
```


## Fase 1: Despliegue del software
En esta fase se instalará el software `gpuq` en el sistema de producción en una ubicación definitiva, sin activar todavía su uso ni modificar el comportamiento actual del servidor. Esta fase no debe interferir con el uso actual de GPU ni con los flujos de trabajo existentes.

1. Clonar el código del software en el directorio `/opt` que será donde se instalará.

```bash
cd /opt
git clone https://github.com/enolgargon/gpuq.git
```

2. Crear entorno virtual para la ejecución de la herramienta e instalar las dependencias del proyecto.

```bash
cd /opt/gpuq
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Crear el fichero bin/gpuq que hará la ejecución con el entorno de Python correcto. Se puede tomar como plantilla el incluido en el directorio `bin_templates`.

4. Modificar los permisos del bin para que permita su ejecución

```bash
chmod +x bin/gpuq
```

3. Verificar la integridad del software copiado.

```bash
/opt/gpuq/bin/gpuq --help
```


## Fase 2: Configuración estructural
En esta fase se configurará todo lo necesario dentro del sistema operativo para que la ejecución del software se haga de forma cómoda y segura.

1. Protección del código instalado en `/opt`. Para que el código no pueda ser modificado por cualquier usuario vamos a asignarle el directorio al usuario root evitar la modificación por parte de cualquier otro usuario.

```bash
chown -R root:root /opt/gpuq
chmod -R 755 /opt/gpuq
```

2. Exposición del CLI en el sistema. Para evitar que los usuarios escriban la ruta completa vamos a crear un enlace simbólico al ejecutable en `/usr/local/bin`, lo que peritirá ejecutar la orden sólamente escribiendo `gpuq`. Para ello se ejecuta la orden:

```bash
ln -s /opt/gpuq/bin/gpuq /usr/local/bin/gpuq
```

Asignarele correctamente los permisos al nuevo fichero y verificar este paso ejecutando:

```bash
chown root:root /usr/local/bin/gpuq
chmod 755 /usr/local/bin/gpuq
gpuq --help
```

3. Crear el usuario que se encargará de ejecutar el dispatcher y el grupo de usuarios permitidos para utilizarlo.

```bash
groupadd gpuq
useradd --system --home /var/lib/gpuq --shell /usr/sbin/nologin -g gpuq gpuq
```

**NOTA:** *Cada vez que se cree un usuario se debe autorizar al usuario a usar la herramienta añadiéndolo al grupo correspondiente. También es necesario activar el linger para el usuario, lo que permitirá que los procesos del usuario se ejecuten sin que haya una sesión suya iniciada.*
```bash
usermod -aG gpuq <usuario>
loginctl enable-linger <usuario>
```

4. Crear estructura de la cola.

```bash
mkdir -p /var/lib/gpuq/queue/{queued,running,finished,failed,canceled}
mkdir -p /var/lib/gpuq/signals/cancel

```

5. Proteger la estructura de la cola. Para proteger la estructura se asignará su propiedad al usuario y grupo `gpuq` y se asignarar permisos para evitar modificaciones manuales de la cola en la medida de lo posible.

```bash
chown -R gpuq:gpuq /var/lib/gpuq
chmod 2770 /var/lib/gpuq/queue
chmod 2770 /var/lib/gpuq/signals
chmod 2770 /var/lib/gpuq/signals/cancel
chmod 2770 /var/lib/gpuq/queue/queued
chmod 2750 /var/lib/gpuq/queue/{running,finished,failed,canceled}
```

6. Creación del lock de la GPU.

```bash
touch /var/lib/gpuq/gpu.lock
chown gpuq:gpuq /var/lib/gpuq/gpu.lock
chmod 660 /var/lib/gpuq/gpu.lock
```

## Fase 3: Configuración de la auditoría de la cola
Para poder comprender mejor el comportamiento de la cola, como han llegado a crearse los trabajos y como se mueven dentro del ciclo de vida se va a configurar un sistema de de auditoria: `auditd`.

1. Instalación del paquete `auditd`

```bash
apt install auditd
```

2. Arrancar el servicio de auditoría y verificar su funcionamiento.

```bash
systemctl enable auditd
systemctl start auditd
systemctl status auditd
```

3. Definir las reglas para auditar los directorios de gpuq. Crear el fichero `/etc/audit/rules.d/gpuq.rules` con el siguiente contenido:

```plain
-w /var/lib/gpuq/queue -p rwa -k gpuq_queue
-w /var/lib/gpuq/gpu.lock -p rwa -k gpuq_lock
```

4. Confirmar la carga de las nuevas reglas.
```bash
augenrules --load
```

Una vez cargadas se puede verificar con la orden `auditctl -l` y deberá aparecer lo siguiente:
```plain
gpuq_queue
gpuq_lock
```

## Fase 3: Configuración del servicio
En esta fase se configurará el dispatcher como un servicio del sistema.

1. Definir el nuevo servicio creando el fichero `/etc/systemd/system/gpuq-dispatcher.service` con el siguiente contenido:

```ini
[Unit]
Description=GPUQ Dispatcher Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/gpuq
ExecStart=/opt/gpuq/venv/bin/python -m gpuq_dispatcher.dispatcher
Restart=on-failure
RestartSec=5
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=/opt/gpuq/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="GPUQ_QUEUE_ROOT=/var/lib/gpuq/queue/"
UMask=0007

# Seguridad adicional
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=false

[Install]
WantedBy=multi-user.target
```

2. Recargar los servicios del sistema y comprobar que el nuevo servicio se indexa correctamente:

``` bash
systemctl daemon-reload
systemctl status gpuq-dispatcher
```

## Fase 4: Validaciones
### Fase 4.1: Verificación de arranque básico

Una vez realizadas todas las configuraciones se habilita el servicio del dispatcher y se configura para que siempre se arranque de forma automática.

```bash
systemctl start gpuq-dispatcher
systemctl enable gpuq-dispatcher
```

Tras esta prueba comprobar los logs para ver si aparecen errores en su ejecución.

```bash
journalctl -u gpuq-dispatcher -f
```

Verificar también que el proceso se está ejecutando como el usuario gpuq.
```bash
ps aux | grep gpuq
```


### Fase 4.2: Pruebas funcionales básicas
En esta fase se validará el flujo completo del sistema utilizando el comportamiento real del CLI: registro persistente del trabajo, transición de estados y ejecución delegada al dispatcher.

1. Crear un proyecto de prueba. Preparar un directorio con un docker-compose.yml mínimo que utilice GPU.

2. Encolar un trabajo
```bash
gpuq submit ./test_gpuq --description "test inicial"
```

Resultado esperado:

- El comando devuelve código de salida 0.
- Se genera un identificador único de trabajo.
- Se crea un fichero JOB_ID.yaml en `/var/lib/gpuq/queue/queued`

3. Verificar listado de trabajos

``` bash
gpuq list
```

4. Verificar transición a running. El dispatcher debe mover automáticamente el trabajo a:

```bash
ls /var/lib/gpuq/queue/running
```

Durante la ejecución, verificar:

```bash
gpuq list --state running
```

5. Verificar finalización. Tras finalizar la ejecución:

```bash
gpuq list --state finished
ls /var/lib/gpuq/queue/finished
```

### Fase 4.3: Validación de comportamiento interno
En esta fase se valida el modelo de permisos, separación de responsabilidades y auditoría.

1. Validar restricción de escritura en estados finales. Como usuario normal intentar:

```bash
touch /var/lib/gpuq/queue/running/test.yaml
mv /var/lib/gpuq/queue/queued/<JOB_ID>.yaml /var/lib/gpuq/queue/running/
```

Debe fallas dos órdenes deben fallar por permisos.


2. Validar permisos de los ficheros creados
```bash
ls -l /var/lib/gpuq/queue/queued
```
Los trabajos deben tener: `-rw-rw----` y grupo gpuq.

3. Validar cancelación en estado queued. Para ello, encolar nuevo trabajo habiendo algún otro en ejecución:
```bash
gpuq submit --project ./test_gpuq --description "cancel test"
gpuq list --state queued
```

Antes de que pase a running:

```bash
gpuq cancel <JOB_ID>
```

Verificar:

```bash
gpuq list --state canceled
ls /var/lib/gpuq/queue/canceled
```

4. Validar cancelación en estado running. Para ello, encolar nuevo trabajo y cuando esté en running:

```bash
gpuq cancel <JOB_ID>
```

Verificar:

- El estado cambia a canceled.
- El dispatcher gestiona la terminación.
- No quedan locks inconsistentes.

5. Verificar auditoría

```bash
ausearch -k gpuq_queue -ts recent
```

Debe registrarse:

- Creación de YAML en queued
- Movimiento entre estados
- Cancelaciones

### Fase 4.4: Pruebas de resiliencia (parar servicio)

En esta fase se valida el comportamiento ante parada controlada del dispatcher.

1. Encolar un trabajo.

```bash
gpuq submit --project ./test_gpuq --description "resilience test"
```

2. Cuando el estado sea running, detener el servicio y verificar que esté detenido.

```bash
systemctl stop gpuq-dispatcher
systemctl status gpuq-dispatcher
```

3. Evaluar estado de la cola

```bash
ls /var/lib/gpuq/queue/running
```

Y verificar que:

- El trabajo permanece en running.
- No se produce corrupción del fichero YAML.
- El lock no queda bloqueado permanentemente.

4. Reiniciar servicio

```bash
systemctl start gpuq-dispatcher
```

5. Verificar que el sistema detecta correctamente trabajos pendientes, no hay inconsistencias y el flujo continúa o se resuelve correctamente.

```bash
journalctl -u gpuq-dispatcher
```

### Fase 4.5: Validación tras reinicio del sistema
Esta fase requiere una ventana controlada ya que durante el reinicio no puede haber trabajos de otros usuarios en marcha o se puede perder el trabajo ejecutado.

Una vez verificado que la prueba no afectará a otros usuarios:

1. Reiniciar el sistema

```bash
reboot
```

2. Comprobar que el servicio del dispatcher se arranca correctamente tras el reinicio.

```bash
systemctl status gpuq-dispatcher
```

3. Ejecutar un trabajo de prueba

```bash
gpuq submit --project ./test_gpuq --description "post-reboot test"
```