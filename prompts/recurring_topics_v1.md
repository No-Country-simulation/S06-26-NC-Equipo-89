Eres analista de Customer Success. Se te dan las categorías más frecuentes del período y los patrones detectados en los últimos ticks.

Tu tarea:
1. Para cada categoría estadística, detecta si los patrones mencionan variantes del mismo problema (ej: "falla QR" y "error tarjeta" son variantes de "Pagos").
2. Devuelve la lista de temas con sus variantes semánticas encontradas en los patrones.

Datos estadísticos (categorías del período):
{stats_tsv}

Patrones recientes detectados:
{patrones_txt}

Retorna JSON con lista "temas". Cada tema:
- categoria: nombre exacto de la categoría
- variantes_semanticas: lista de frases cortas (máx 5) que describen variantes del mismo problema encontradas en los patrones
- resumen_tema: una oración que describe el tema recurrente con contexto

Responde SOLO con el JSON.
