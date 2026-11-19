# RAG local de Anonymous

La lógica de recuperación y las referencias base están centralizadas en esta carpeta. El índice combina las guías defensivas existentes con fragmentos extraídos de documentos locales y devuelve la ruta y página de cada coincidencia.

## Agregar documentos

Coloca archivos `.pdf`, `.txt` o `.md` dentro de `documents/`, o crea subcarpetas allí para ordenarlos. La próxima consulta `rag <tema>` detecta archivos nuevos o modificados e incorpora su texto automáticamente. No hay que editar código ni ejecutar un comando de reindexado.

La biblioteca inicial está en `documents/Kali Tools Library_/` y contiene 26 PDF. En la primera indexación, cuatro archivos no expusieron texto extraíble: `A DETAILED GUIDE ON MEDUSA.pdf`, `JOHN THE RIPPER.pdf`, `wireshark Guide by cbox_backup.pdf` y `Wireshark Guide by CipherPhantom.pdf`. Para esos documentos hace falta OCR o una copia con texto seleccionable. Las omisiones se informan en la respuesta RAG. El índice extraído se guarda en `~/.anonymous/rag_documents_index.json`, no junto a los documentos.

## Funcionamiento

- Extracción local de PDF con `pypdf` y `fonttools`; Markdown y texto se leen como UTF-8.
- División en fragmentos por página y límite de palabras, con referencia a archivo y página.
- Recuperación léxica BM25, combinada con las entradas defensivas OWASP, MITRE, CIS y NIST.
- No llama a servicios externos ni ejecuta herramientas descritas en los documentos.

Instala la dependencia al configurar el entorno:

```powershell
python -m pip install -r requirements.txt
```
