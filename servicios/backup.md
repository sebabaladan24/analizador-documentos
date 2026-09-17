---
nombre: Backup
categoria: Continuidad y resguardo
---

## Descripción
Servicio de respaldo periódico de datos/servidores del cliente, con
retención configurable y restauración ante pérdida de información.

⚠️ COMPLETAR CON DATOS REALES antes de usar este archivo para generar
propuestas — los valores marcados "X" son placeholders.

## Especificaciones técnicas
- Capacidad de respaldo: hasta X TB por cliente
- Frecuencia: diaria / semanal / configurable, indicar granularidad mínima
- Retención: hasta X días/meses de histórico
- Tipo de backup: completo / incremental / diferencial (indicar cuáles soporta)

## SLA
- Ventana de backup garantizada: X horas
- Tiempo de restauración (RTO): X horas
- Punto de recuperación (RPO): X horas

## Cuándo ofrecerlo
Cualquier cliente con requisitos de continuidad de negocio o
compliance que exija resguardo de datos con retención definida.

## Cuándo NO ofrecerlo
Si el cliente requiere replicación en caliente / failover automático
sin pérdida de datos (evaluar un servicio de continuidad de mayor
nivel, si existe).
