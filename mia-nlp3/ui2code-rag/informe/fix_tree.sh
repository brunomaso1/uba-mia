#!/bin/bash

# Backup
cp informe.tex informe.tex.backup

# Reemplazar caracteres del árbol
sed -i 's/├──/  +--/g; s/│/|/g; s/└──/  \`--/g; s/─/--/g' informe.tex

# Reemplazar tildes y caracteres especiales dentro de lstlisting
sed -i '
/begin{lstlisting}/,/end{lstlisting}/ {
    s/á/a/g
    s/é/e/g
    s/í/i/g
    s/ó/o/g
    s/ú/u/g
    s/ñ/n/g
    s/Á/A/g
    s/É/E/g
    s/Í/I/g
    s/Ó/O/g
    s/Ú/U/g
    s/Ñ/N/g
}
' informe.tex

echo "✓ Archivo corregido. Backup en informe.tex.backup"
