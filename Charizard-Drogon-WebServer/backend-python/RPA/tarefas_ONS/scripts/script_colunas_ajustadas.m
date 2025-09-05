let
    Fonte = Pdf.Tables(
        File.Contents("C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO_ONS_PVRV_2025\AUTOMACÕES ONS\arquivos\CUST-2002-123-41 - JAGUARI - RECON 2025-2028.pdf"),
        [Implementation="1.3"]
    ),
    Table010 = Fonte{[Id="Table011"]}[Data],

    // Força todas as colunas como texto
    #"Tipo Alterado" = Table.TransformColumnTypes(
        Table010,
        List.Transform(Table.ColumnNames(Table010), each {_, type text})
    ),

    // Captura as duas primeiras linhas
    Linha1 = Record.ToList(#"Tipo Alterado"{0}),
    Linha2 = Record.ToList(#"Tipo Alterado"{1}),

    // Remove as duas primeiras linhas
    Restante = Table.Skip(#"Tipo Alterado", 2),

    // Cria nomes concatenados seguros
    ColunasConcatenadas = List.Transform(
        {0..List.Count(Linha1)-1},
        each 
            let 
                Parte1 = if Linha1{_} = null then "" else Text.Trim(Text.From(Linha1{_})),
                Parte2 = if Linha2{_} = null then "" else Text.Trim(Text.From(Linha2{_})),
                Nome = if (Parte1 = "" or Parte1 = "_") and (Parte2 = "" or Parte2 = "_") then "Coluna" & Text.From(_ + 1) else Text.Combine({Parte1, Parte2}, " ")
            in
                Nome
    ),

    // Garante que nomes são únicos (evita duplicidade de colunas)
    ColunasUnicas = List.Transform(
        List.Positions(ColunasConcatenadas),
        each 
            let 
                currentName = ColunasConcatenadas{_}
            in
                if List.PositionOf(List.FirstN(ColunasConcatenadas, _), currentName) <> -1
                then currentName & " " & Text.From(List.Count(List.Select(List.FirstN(ColunasConcatenadas, _), (n) => n = currentName)))
                else currentName
    ),

    ParesRenome = List.Transform(
        List.Positions(Table.ColumnNames(Restante)),
        each { Table.ColumnNames(Restante){_}, ColunasUnicas{_} }
    ),

    TabelaFinal = Table.RenameColumns(Restante, ParesRenome, MissingField.Ignore),

    // --- LÓGICA DE DIVISÃO POR DELIMITADOR ^ ---
    ColunasParaDividir = List.Select(
        Table.ColumnNames(TabelaFinal),
        each 
            let 
                valoresExemplo = List.FirstN(Table.Column(TabelaFinal, _), 100)
            in
                List.AnyTrue(List.Transform(valoresExemplo, (v) => v <> null and Text.Contains(Text.From(v), "^")))
    ),

    // SEPARAR O PONTA E FORA PONTA COM SEU VALOR E ANOTACAO
    TabelaComDivisoesETipos = List.Accumulate(
        ColunasParaDividir,
        TabelaFinal,
        (tabelaAtual, nomeColuna) => 
            let
                Dividida = Table.SplitColumn(
                    tabelaAtual, 
                    nomeColuna, 
                    Splitter.SplitTextByDelimiter("^", QuoteStyle.None),
                    {nomeColuna & " Valor", nomeColuna & " Anotacao"}
                ),
                Tipada = Table.TransformColumnTypes(
                    Dividida,
                    {
                        {nomeColuna & " Valor", type text}, 
                        {nomeColuna & " Anotacao", type text}
                    }
                )
            in
                Tipada
    ),

    // --- NOVA ETAPA FINAL: PADRONIZAR NOMES DE COLUNAS ---
    // Esta etapa garante que os nomes das colunas sejam exatamente como esperado, independentemente do que aconteceu antes.
    TabelaPadronizada = Table.RenameColumns(TabelaComDivisoesETipos, {
        // Colunas de Identificação
        {"Ponto de Conexão Cód ONS¹", "Cód ONS"},
        {"Ponto de Conexão Instalação", "Instalação"},
        {"Ponto de Conexão Tensão (kV)", "Tensão (kV)"},
        {"Período de Contratação De", "De"},
        {"Período de Contratação Até", "Até"},

        // Colunas de Dados 2025
        {"MUST - 2025 Ponta (MW) Valor", "Ponta 2025 Valor"},
        {"MUST - 2025 Ponta (MW) Anotacao", "Ponta 2025 Anotacao"},
        {"MUST - 2025 Fora Ponta (MW) Valor", "Fora Ponta 2025 Valor"},
        {"MUST - 2025 Fora Ponta (MW) Anotacao", "Fora Ponta 2025 Anotacao"},

        // Colunas de Dados 2026
        {"MUST - 2026 Ponta (MW) Valor", "Ponta 2026 Valor"},
        {"MUST - 2026 Ponta (MW) Anotacao", "Ponta 2026 Anotacao"},
        {"MUST - 2026 Fora Ponta (MW) Valor", "Fora Ponta 2026 Valor"},
        {"MUST - 2026 Fora Ponta (MW) Anotacao", "Fora Ponta 2026 Anotacao"},
        
        // Colunas de Dados 2027
        {"MUST - 2027 Ponta (MW) Valor", "Ponta 2027 Valor"},
        {"MUST - 2027 Ponta (MW) Anotacao", "Ponta 2027 Anotacao"},
        {"MUST - 2027 Fora Ponta (MW) Valor", "Fora Ponta 2027 Valor"},
        {"MUST - 2027 Ponta (MW) 1 Anotacao", "Fora Ponta 2027 Anotacao"}, // Corrigindo o nome duplicado que causa o erro

        // Colunas de Dados 2028
        {"MUST - 2028 Ponta (MW) Valor", "Ponta 2028 Valor"},
        {"MUST - 2028 Ponta (MW) Anotacao", "Ponta 2028 Anotacao"},
        {"Fora Ponta (MW) 2 Valor", "Fora Ponta 2028 Valor"}, // Corrigindo nome genérico
        {"Fora Ponta (MW) 2 Anotacao", "Fora Ponta 2028 Anotacao"} // Corrigindo nome genérico
    }, MissingField.Ignore) // MissingField.Ignore é importante para pular colunas que não existam

in
    TabelaPadronizada