# Ejemplos de calibración — clasificación de feedback (Latam/Bolivia)

Usa estos pares entrada/salida como referencia de tono, jerga y criterio de urgencia.

## Ejemplo 1
Entrada: La app se cierra sola cuando quiero pagar con QR, ya van 3 veces.
Salida: {"sentimiento":"Negativo","categorias":["App","Pagos"],"urgencia":"Alta","idioma":"Español","confianza":0.93,"resumen":"La app se cierra al intentar pagar con QR repetidamente."}

## Ejemplo 2
Entrada: Excelente atención de Carla en soporte, me solucionó altiro el tema de la factura.
Salida: {"sentimiento":"Positivo","categorias":["Atención al Cliente","Facturación"],"urgencia":"Baja","idioma":"Español","confianza":0.95,"resumen":"Destaca la buena atención de soporte con la factura."}

## Ejemplo 3
Entrada: ¿Cuánto tarda el envío a Santa Cruz? No encuentro esa info en la web.
Salida: {"sentimiento":"Neutral","categorias":["Logística","Sitio Web"],"urgencia":"Baja","idioma":"Español","confianza":0.88,"resumen":"Consulta sobre tiempos de envío a Santa Cruz no hallada en la web."}

## Ejemplo 4
Entrada: Me cobraron doble en la tarjeta y nadie responde el chat, pésimo servicio.
Salida: {"sentimiento":"Negativo","categorias":["Pagos","Atención al Cliente"],"urgencia":"Alta","idioma":"Español","confianza":0.94,"resumen":"Doble cobro en tarjeta sin respuesta de soporte."}

## Ejemplo 5
Entrada: weno el producto pero la entrega llegó 2 días tarde xq no avisaron nada
Salida: {"sentimiento":"Negativo","categorias":["Logística","Producto"],"urgencia":"Media","idioma":"Español","confianza":0.9,"resumen":"Producto bien pero entrega tardía sin aviso."}

## Ejemplo 6
Entrada: Gracias por la yapa en el pedido, se nota que valoran al cliente.
Salida: {"sentimiento":"Positivo","categorias":["Producto","Atención al Cliente"],"urgencia":"Baja","idioma":"Español","confianza":0.92,"resumen":"Agradece detalle extra (yapa) en el pedido."}

## Ejemplo 7
Entrada: Voy a cancelar mi cuenta si no arreglan el login, esto es inaceptable.
Salida: {"sentimiento":"Negativo","categorias":["App","Cuenta"],"urgencia":"Alta","idioma":"Español","confianza":0.96,"resumen":"Amenaza de cancelación por fallas de login."}

## Ejemplo 8
Entrada: El precio subió mucho este mes, ¿hay alguna promo para clientes antiguos?
Salida: {"sentimiento":"Neutral","categorias":["Precios"],"urgencia":"Media","idioma":"Español","confianza":0.87,"resumen":"Pregunta por promoción tras suba de precios."}

## Ejemplo 9
Entrada: Toy esperando hace 40 min en la fila del local de Sopocachi, mal organizados.
Salida: {"sentimiento":"Negativo","categorias":["Atención al Cliente","Logística"],"urgencia":"Media","idioma":"Español","confianza":0.91,"resumen":"Queja por larga espera en sucursal Sopocachi."}

## Ejemplo 10
Entrada: Todo ok, sin observaciones.
Salida: {"sentimiento":"Neutral","categorias":[],"urgencia":"Baja","idioma":"Español","confianza":0.85,"resumen":"Sin observaciones particulares."}

## Ejemplo 11
Entrada: El menú vegetariano tiene pocas opciones, sería chévere ampliarlo.
Salida: {"sentimiento":"Neutral","categorias":["Producto"],"urgencia":"Baja","idioma":"Español","confianza":0.89,"resumen":"Sugerencia de ampliar opciones vegetarianas."}

## Ejemplo 12
Entrada: ERROR 500 en el portal todo el día, pierdo plata sin poder facturar.
Salida: {"sentimiento":"Negativo","categorias":["Error Técnico","Facturación"],"urgencia":"Alta","idioma":"Español","confianza":0.97,"resumen":"Error 500 impide facturar con impacto económico."}

## Ejemplo 13
Entrada: Muy buena la nueva función de seguimiento en tiempo real del pedido.
Salida: {"sentimiento":"Positivo","categorias":["App","Logística"],"urgencia":"Baja","idioma":"Español","confianza":0.94,"resumen":"Elogia el seguimiento en tiempo real del pedido."}

## Ejemplo 14
Entrada: No entiendo la factura, los montos no coinciden con lo que pedí.
Salida: {"sentimiento":"Negativo","categorias":["Facturación"],"urgencia":"Media","idioma":"Español","confianza":0.9,"resumen":"Montos de factura no coinciden con el pedido."}

## Ejemplo 15
Entrada: Hola, ¿tienen delivery los domingos en La Paz?
Salida: {"sentimiento":"Neutral","categorias":["Logística"],"urgencia":"Baja","idioma":"Español","confianza":0.93,"resumen":"Consulta delivery dominical en La Paz."}

## Ejemplo 16
Entrada: Pésimo, el repartidor tiró el paquete y llegó roto, quiero reembolso YA.
Salida: {"sentimiento":"Negativo","categorias":["Logística","Producto"],"urgencia":"Alta","idioma":"Español","confianza":0.95,"resumen":"Paquete dañado en entrega con exigencia de reembolso."}

## Ejemplo 17
Entrada: La promo del 2x1 funcionó bien, volveré a comprar.
Salida: {"sentimiento":"Positivo","categorias":["Precios","Producto"],"urgencia":"Baja","idioma":"Español","confianza":0.92,"resumen":"Experiencia positiva con promoción 2x1."}

## Ejemplo 18
Entrada: El bot no entiende nada, repite lo mismo, mejor hablar con una persona.
Salida: {"sentimiento":"Negativo","categorias":["Atención al Cliente","App"],"urgencia":"Media","idioma":"Español","confianza":0.9,"resumen":"Frustración con chatbot que no resuelve."}

## Ejemplo 19
Entrada: Demora en acreditar el pago por transferencia, ya pasaron 48 horas.
Salida: {"sentimiento":"Negativo","categorias":["Pagos"],"urgencia":"Media","idioma":"Español","confianza":0.91,"resumen":"Pago por transferencia sin acreditar en 48h."}

## Ejemplo 20
Entrada: Buenísima la capacitación que dieron al equipo en el local de Cochabamba.
Salida: {"sentimiento":"Positivo","categorias":["Atención al Cliente"],"urgencia":"Baja","idioma":"Español","confianza":0.9,"resumen":"Valoración positiva de capacitación en tienda Cochabamba."}

## Ejemplo 21
Entrada: Me van a denunciar a Indecopi si no devuelven mi dinero hoy.
Salida: {"sentimiento":"Negativo","categorias":["Pagos"],"urgencia":"Alta","idioma":"Español","confianza":0.96,"resumen":"Amenaza de denuncia legal por falta de devolución."}

## Ejemplo 22
Entrada: Could you send the invoice in English please?
Salida: {"sentimiento":"Neutral","categorias":["Facturación"],"urgencia":"Baja","idioma":"Inglés","confianza":0.94,"resumen":"Solicita factura en inglés."}

## Ejemplo 23
Entrada: La señal en el ascensor del edificio no alcanza y la app no carga, molesto.
Salida: {"sentimiento":"Negativo","categorias":["App"],"urgencia":"Media","idioma":"Español","confianza":0.88,"resumen":"App no carga por mala señal en edificio."}

## Ejemplo 24
Entrada: Gracias por responder rápido por WhatsApp, eso ayuda mucho.
Salida: {"sentimiento":"Positivo","categorias":["Atención al Cliente"],"urgencia":"Baja","idioma":"Español","confianza":0.93,"resumen":"Agradece respuesta rápida por WhatsApp."}

## Ejemplo 25
Entrada: El sabor del nuevo combo está feo, parece rehecho, no lo recomiendo.
Salida: {"sentimiento":"Negativo","categorias":["Producto"],"urgencia":"Media","idioma":"Español","confianza":0.9,"resumen":"Queja por calidad del nuevo combo."}

## Notas de criterio
- Alta urgencia: amenaza de baja, furia extrema, riesgo legal, caída del sistema, pérdida económica inmediata.
- Media: quejas operativas estándar, demoras, errores recuperables, sugerencias con fricción.
- Baja: consultas, halagos, feedback neutro sin presión.
- Respeta ortografía informal del cliente en el resumen pero clasifica con criterio profesional.
- Si el mensaje mezcla positivo y negativo, prioriza el sentimiento dominante.
- categorias: lista vacía solo si no hay tema identificable; preferir al menos un tag cuando sea posible.
