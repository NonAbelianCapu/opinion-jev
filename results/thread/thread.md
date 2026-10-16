1/
Inventé un rumor de barrio y lo dejé circular por una red de 64 personas simuladas. Cada una decide si lo cree, si lo comparte y cómo lo reescribe antes de reenviarlo.

Este es el árbol de versiones que salió de un solo mensaje:

[imagen: 1_arbol.png]

2/
El mensaje original: "La pileta municipal va a estar cerrada este verano porque un análisis de rutina del agua encontró un problema."

Seis reenvíos después alguien escribía: "El personal de la pileta confirmó que la cierran para siempre. Busquen otro lugar ya."

3/
El camino completo:
→ "contaminación tóxica, que nadie se acerque" (exagera)
→ "escuché rumores, conviene esperar" (suaviza)
→ "charla sin confirmar" (suaviza)
→ "el personal lo confirmó" (exagera e inventa la fuente)
→ "cerrada para siempre" (exagera)

[imagen: 3_red_y_linaje.png]

4/
Cómo funciona: un modelo de decisiones (Jev, de TypeSafe) lee el mensaje, quién lo manda y cómo es la persona, y devuelve probabilidades de creer, compartir y cada tipo de cambio. Un LLM escribe el texto nuevo. El azar de la simulación sortea qué pasa.

5/
El resultado principal, con 20 corridas por mensaje: creer y compartir se separan.

Al final cree el 12% de la red, pero comparte el 21%. Muchos reenvían algo de lo que dudan: con creencia menor a 0,5, la probabilidad media de compartir fue 0,33.

[imagen: 2_resumen.png]

6/
Lo comparé con una regla logística fija, como en los modelos clásicos de difusión. Misma red, mismas semillas: la regla termina con 39% de creyentes; Jev, con 12%.

La regla casi siempre exagera, así que el rumor escala. Con Jev, suavizar (42%) es tan común como exagerar (40%).

7/
Por eso el texto oscila en lugar de escalar sin freno: alguien lo infla, el siguiente le agrega dudas, otro inventa que "lo confirmó el personal".

El mensaje de la pileta arrancó menos extremo que otro de prueba (multas por los contenedores) y terminó más deformado.

8/
Advertencias:
- Jev es un modelo cerrado, entrenado con datos sintéticos. Esto muestra lo que el modelo supone sobre la gente, no cómo se comporta la gente.
- Nadie verificó si sus probabilidades están calibradas.
- Son 64 nodos, 2 mensajes y 20 semillas.

9/
Las 80 corridas costaron unos 13 centavos de dólar: US$0,05 de Jev y US$0,08 de reescrituras.

Todo queda en caché y se reproduce sin llamar a las APIs. Código y página interactiva: github.com/NonAbelianCapu/opinion-jev
