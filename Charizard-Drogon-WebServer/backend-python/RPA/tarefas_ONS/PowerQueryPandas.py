from ClassPowerQuery import MiniPowerQuery


path = "/home/pedrov12/Downloads"

# Carrega do PDF que você me mandou
mpq = MiniPowerQuery(rf"{path}/quadro_horarios_telecom.pdf")

# Faz limpeza básica
(mpq
    .trim_spaces()
    .drop_nulls()
    .drop_duplicates()
    .rename_columns({"Disciplina": "Materia"})
    .preview(10)
    .export("saida_limpa.xlsx")
)
