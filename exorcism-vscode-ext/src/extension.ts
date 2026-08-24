import * as vscode from "vscode";
import { ChildProcess, execFile } from "child_process";
import {
    ExorcismHoverProvider
} from "./hoverProvider";


const LANGUAGE_ID = "exorcism";
const DIAGNOSTIC_SOURCE = "exorcism";


// ============================================================
// Configuration
// ============================================================

const DIAGNOSTIC_DEBOUNCE_MS = 350;
const SYMBOL_DEBOUNCE_MS = 500;


// ============================================================
// Diagnostic interfaces
// ============================================================

interface ExorcismDiagnostic {
    severity: "error" | "warning" | "info";
    message: string;
    line: number;
    column: number;
    length: number;
    code?: string;
}


// ============================================================
// Symbol interfaces
// ============================================================

interface ExorcismSymbol {
    name: string;
    kind: "variable" | "function";
    type: string;
    line: number;
    column: number;
    returnType?: string;
    parameters?: {
        name: string;
        type: string;
    }[];
}


interface SymbolResponse {
    symbols: ExorcismSymbol[];
}


// ============================================================
// Cached symbols
// ============================================================

interface SymbolCacheEntry {
    symbols: ExorcismSymbol[];
    documentVersion: number;
}


// ============================================================
// Extension activation
// ============================================================

export function activate(
    context: vscode.ExtensionContext
) {

    console.log(
        "Exorcism extension is now active."
    );


    // ========================================================
    // State
    // ========================================================

    const symbolCache =
        new Map<string, SymbolCacheEntry>();


    const symbolTimers =
        new Map<
            string,
            ReturnType<typeof setTimeout>
        >();


    const symbolProcesses =
        new Map<
            string,
            {
                process: ChildProcess;
                cancelled: boolean;
            }
        >();


    const diagnosticTimers =
        new Map<
            string,
            ReturnType<typeof setTimeout>
        >();


    const diagnosticProcesses =
        new Map<
            string,
            {
                process: ChildProcess;
                cancelled: boolean;
            }
        >();


    // ========================================================
    // Run / Build Exorcism command
    // ========================================================

    async function runExorcismCommand(
        command: string
    ) {

        const editor =
            vscode.window.activeTextEditor;

        if (!editor) {
            return;
        }


        const document =
            editor.document;


        if (
            document.languageId !==
            LANGUAGE_ID
        ) {
            return;
        }


        if (
            !document.fileName
                .toLowerCase()
                .endsWith(".exrc")
        ) {
            return;
        }


        await document.save();


        const terminal =
            vscode.window.createTerminal(
                "Exorcism"
            );


        terminal.show();


        terminal.sendText(
            `exrc ${command} "${document.fileName}"`
        );
    }


    // ========================================================
    // Commands
    // ========================================================

    const runCommand =
        vscode.commands.registerCommand(
            "exorcism.run",
            () =>
                runExorcismCommand("run")
        );


    const buildCommand =
        vscode.commands.registerCommand(
            "exorcism.build",
            () =>
                runExorcismCommand("build")
        );


    context.subscriptions.push(
        runCommand,
        buildCommand
    );


    // ========================================================
    // Hover provider
    // ========================================================

    context.subscriptions.push(
        vscode.languages.registerHoverProvider(
            {
                language: LANGUAGE_ID
            },
            new ExorcismHoverProvider()
        )
    );


    // ========================================================
    // Exorcism keywords
    // ========================================================

    const keywords = [
        "var",
        "int",
        "float",
        "double",
        "char",
        "string",
        "bool",
        "void",
        "if",
        "else",
        "option",
        "while",
        "for",
        "return",
        "break",
        "continue",
        "function",
        "struct"
    ];


    // ========================================================
    // Create keyword completion items
    // ========================================================

    function createKeywordCompletion(
        keyword: string
    ): vscode.CompletionItem {

        const item =
            new vscode.CompletionItem(
                keyword,
                vscode.CompletionItemKind.Keyword
            );


        item.detail =
            "Exorcism keyword";


        return item;
    }


    // ========================================================
    // Create punctuation completion items
    // ========================================================

    function createPunctuationCompletion(
        character: string,
        detail: string
    ): vscode.CompletionItem {

        const item =
            new vscode.CompletionItem(
                character,
                vscode.CompletionItemKind.Text
            );

        item.detail = detail;

        item.insertText = character;

        return item;
    }


    // ========================================================
    // Create semicolon completion items
    // ========================================================

    function createSemicolonCompletion(
        document: vscode.TextDocument,
        position: vscode.Position
    ): vscode.CompletionItem | undefined {

        const line =
            document.lineAt(position.line).text;

        const textBeforeCursor =
            line.substring(0, position.character);

        const textAfterCursor =
            line.substring(position.character);


        // ---------------------------------------------
        // Don't suggest if semicolon already exists
        // ---------------------------------------------

        if (
            textBeforeCursor.trimEnd().endsWith(";")
        ) {
            return undefined;
        }


        // ---------------------------------------------
        // Don't suggest if the next non-whitespace
        // character is already a semicolon.
        // ---------------------------------------------

        if (
            textAfterCursor.trimStart().startsWith(";")
        ) {
            return undefined;
        }


        // ---------------------------------------------
        // Don't suggest on an empty line
        // ---------------------------------------------

        if (
            textBeforeCursor.trim().length === 0
        ) {
            return undefined;
        }


        const item =
            new vscode.CompletionItem(
                ";",
                vscode.CompletionItemKind.Keyword
            );


        item.detail =
            "Exorcism statement terminator";


        item.insertText =
            new vscode.SnippetString(";");


        return item;
    }


    // ========================================================
    // Create symbol completion item
    // ========================================================

    function createSymbolCompletion(
        symbol: ExorcismSymbol
    ): vscode.CompletionItem {

        let kind =
            vscode.CompletionItemKind.Variable;


        if (
            symbol.kind === "function"
        ) {
            kind =
                vscode.CompletionItemKind.Function;
        }


        const item =
            new vscode.CompletionItem(
                symbol.name,
                kind
            );


        if (
            symbol.kind === "function"
        ) {

            item.detail =
                symbol.returnType ??
                symbol.type;


            if (
                symbol.parameters &&
                symbol.parameters.length > 0
            ) {

                const parameters =
                    symbol.parameters
                        .map(
                            parameter =>
                                `${parameter.name}: ${parameter.type}`
                        )
                        .join(", ");


                item.detail =
                    `(${parameters}) → ${
                        symbol.returnType ??
                        symbol.type
                    }`;
            }

        } else {

            item.detail =
                symbol.type;
        }


        return item;
    }


    function shouldSuggestClosingParenthesis(
        document: vscode.TextDocument,
        position: vscode.Position,
        textBeforeCursor: string
    ): boolean {

        let open = 0;
        let close = 0;


        for (const character of textBeforeCursor) {

            if (character === "(") {
                open++;
            }

            if (character === ")") {
                close++;
            }
        }


        return open > close;
    }


    // ========================================================
    // Completion provider
    //
    // IMPORTANT:
    // This provider NEVER starts exrc.exe.
    //
    // It only returns:
    //   1. keywords
    //   2. cached symbols
    //
    // This makes completion effectively instantaneous.
    // ========================================================

    const completionProvider =
        vscode.languages.registerCompletionItemProvider(
            LANGUAGE_ID,

            {

                provideCompletionItems(
                    document,
                    _position,
                    token,
                    _context
                ) {

                    const items:
                        vscode.CompletionItem[] = [];


                    // -----------------------------------------
                    // Keywords
                    // -----------------------------------------

                    for (
                        const keyword of keywords
                    ) {

                        if (
                            token.isCancellationRequested
                        ) {
                            return items;
                        }


                        items.push(
                            createKeywordCompletion(
                                keyword
                            )
                        );
                    }

                    
                    // -----------------------------------------
                    // Semicolon
                    // -----------------------------------------

                    const semicolon =
                        createSemicolonCompletion(
                            document,
                            _position
                        );

                    if (semicolon) {
                        items.push(semicolon);
                    }


                    // -----------------------------------------
                    // Punctuation
                    // -----------------------------------------

                    const line =
                        document.lineAt(
                            _position.line
                        ).text;

                    const textBeforeCursor =
                        line.substring(
                            0,
                            _position.character
                        );


                    // -----------------------------------------
                    // Closing parenthesis
                    // -----------------------------------------

                    if (
                        shouldSuggestClosingParenthesis(
                            document,
                            _position,
                            textBeforeCursor
                        )
                    ) {

                        items.push(
                            createPunctuationCompletion(
                                ")",
                                "Close parenthesis"
                            )
                        );
                    }


                    // -----------------------------------------
                    // Cached symbols
                    // -----------------------------------------

                    const cache =
                        symbolCache.get(
                            document.uri.toString()
                        );


                    if (!cache) {

                        console.log(
                            "COMPLETION: no symbol cache"
                        );

                        return items;
                    }


                    for (
                        const symbol of cache.symbols
                    ) {

                        if (
                            token.isCancellationRequested
                        ) {
                            return items;
                        }


                        items.push(
                            createSymbolCompletion(
                                symbol
                            )
                        );
                    }


                    console.log(
                        "COMPLETION:",
                        items.length,
                        "items",
                        "symbols:",
                        cache.symbols.length
                    );


                    return items;
                }
            }
        );


    context.subscriptions.push(
        completionProvider
    );


    // ========================================================
    // Diagnostics
    // ========================================================

    const diagnosticCollection =
        vscode.languages.createDiagnosticCollection(
            DIAGNOSTIC_SOURCE
        );


    // ========================================================
    // Kill previous diagnostic process
    // ========================================================

    function cancelDiagnosticProcess(
        documentKey: string
    ) {

        const entry =
            diagnosticProcesses.get(
                documentKey
            );

        if (!entry) {
            return;
        }


        // Mark as intentionally cancelled
        // before killing the process.
        entry.cancelled = true;


        try {

            if (!entry.process.killed) {
                entry.process.kill();
            }

        } catch {
            // Process may already have exited.
        }


        diagnosticProcesses.delete(
            documentKey
        );
    }


    // ========================================================
    // Analyze document
    // ========================================================

    function analyzeDocument(
        document: vscode.TextDocument
    ) {

        if (
            document.languageId !==
            LANGUAGE_ID
        ) {
            return;
        }


        if (
            document.isUntitled
        ) {
            return;
        }


        const documentKey =
            document.uri.toString();


        // -----------------------------------------------
        // Cancel previous debounce timer
        // -----------------------------------------------

        const existingTimer =
            diagnosticTimers.get(
                documentKey
            );


        if (existingTimer) {

            clearTimeout(
                existingTimer
            );
        }


        // -----------------------------------------------
        // Cancel previous analyzer
        // -----------------------------------------------

        cancelDiagnosticProcess(
            documentKey
        );


        // -----------------------------------------------
        // Debounce analysis
        // -----------------------------------------------

        const timer =
            setTimeout(
                () => {

                    diagnosticTimers.delete(
                        documentKey
                    );


                    runDocumentAnalysis(
                        document
                    );

                },
                DIAGNOSTIC_DEBOUNCE_MS
            );


        diagnosticTimers.set(
            documentKey,
            timer
        );
    }


    // ========================================================
    // Actually run analyzer
    // ========================================================

    function runDocumentAnalysis(
        document: vscode.TextDocument
    ) {

        if (
            document.isClosed
        ) {
            return;
        }


        const documentKey =
            document.uri.toString();


        // -----------------------------------------------
        // Cancel any previous process
        // -----------------------------------------------

        cancelDiagnosticProcess(
            documentKey
        );


        // -----------------------------------------------
        // Start analyzer
        // -----------------------------------------------

        let processEntry:
            {
                process: ChildProcess;
                cancelled: boolean;
            };


        const child =
            execFile(
                "exorcism",
                [
                    "analyze",
                    "--stdin",
                    "--json"
                ],
                {
                    windowsHide: true
                },
                (
                    error,
                    stdout,
                    stderr
                ) => {

                    const entry =
                        diagnosticProcesses.get(
                            documentKey
                        );


                    // -----------------------------------------
                    // Process was intentionally cancelled.
                    // Don't report it as an error.
                    // -----------------------------------------

                    if (
                        !entry ||
                        entry.cancelled
                    ) {
                        return;
                    }


                    diagnosticProcesses.delete(
                        documentKey
                    );


                    // -----------------------------------------
                    // Real failure
                    // -----------------------------------------

                    if (
                        error &&
                        !stdout
                    ) {

                        console.error(
                            "Exorcism analyzer failed:",
                            stderr ||
                            error.message
                        );

                        return;
                    }


                    // -----------------------------------------
                    // Parse diagnostics
                    // -----------------------------------------

                    try {

                        const diagnostics:
                            ExorcismDiagnostic[] =
                                JSON.parse(
                                    stdout || "[]"
                                );


                        const vscodeDiagnostics:
                            vscode.Diagnostic[] = [];


                        for (
                            const diagnostic
                            of diagnostics
                        ) {

                            const line =
                                Math.max(
                                    0,
                                    diagnostic.line - 1
                                );


                            const column =
                                Math.max(
                                    0,
                                    diagnostic.column - 1
                                );


                            const length =
                                Math.max(
                                    1,
                                    diagnostic.length
                                );


                            const safeLine =
                                Math.min(
                                    line,
                                    Math.max(
                                        0,
                                        document.lineCount - 1
                                    )
                                );


                            const lineLength =
                                document
                                    .lineAt(
                                        safeLine
                                    )
                                    .text.length;


                            const safeColumn =
                                Math.min(
                                    column,
                                    lineLength
                                );


                            const safeEndColumn =
                                Math.min(
                                    safeColumn + length,
                                    lineLength
                                );


                            const start =
                                new vscode.Position(
                                    safeLine,
                                    safeColumn
                                );


                            const end =
                                new vscode.Position(
                                    safeLine,
                                    safeEndColumn
                                );


                            const range =
                                new vscode.Range(
                                    start,
                                    end
                                );


                            let severity =
                                vscode.DiagnosticSeverity.Error;


                            if (
                                diagnostic.severity ===
                                "warning"
                            ) {

                                severity =
                                    vscode.DiagnosticSeverity.Warning;

                            } else if (
                                diagnostic.severity ===
                                "info"
                            ) {

                                severity =
                                    vscode.DiagnosticSeverity.Information;
                            }


                            const vscodeDiagnostic =
                                new vscode.Diagnostic(
                                    range,
                                    diagnostic.message,
                                    severity
                                );


                            vscodeDiagnostic.source =
                                DIAGNOSTIC_SOURCE;


                            if (
                                diagnostic.code
                            ) {

                                vscodeDiagnostic.code =
                                    diagnostic.code;
                            }


                            vscodeDiagnostics.push(
                                vscodeDiagnostic
                            );
                        }


                        diagnosticCollection.set(
                            document.uri,
                            vscodeDiagnostics
                        );

                    } catch (
                        parseError
                    ) {

                        console.error(
                            "Failed to parse Exorcism diagnostics:",
                            parseError
                        );
                    }
                }
            );


        processEntry = {
            process: child,
            cancelled: false
        };


        diagnosticProcesses.set(
            documentKey,
            processEntry
        );


        // -----------------------------------------------
        // Send current editor contents
        // -----------------------------------------------

        if (child.stdin) {

            child.stdin.write(
                document.getText()
            );

            child.stdin.end();
        }
    }


    // ========================================================
    // Get symbols from Exorcism CLI
    //
    // IMPORTANT:
    // This function is only called by the background
    // symbol refresh mechanism.
    //
    // Completion itself NEVER calls this.
    // ========================================================

    function getSymbols(
        filePath: string,
        documentKey: string
    ): Promise<ExorcismSymbol[]> {

        return new Promise(
            resolve => {

                // -----------------------------------------
                // Kill previous symbol process
                // -----------------------------------------

                const existingEntry =
                    symbolProcesses.get(
                        documentKey
                    );


                if (existingEntry) {

                    // Mark as intentionally cancelled
                    // BEFORE killing the process.
                    existingEntry.cancelled = true;


                    try {

                        if (
                            !existingEntry.process.killed
                        ) {
                            existingEntry.process.kill();
                        }

                    } catch {
                        // Process may already have exited.
                    }


                    symbolProcesses.delete(
                        documentKey
                    );
                }


                // -----------------------------------------
                // Start symbol process
                // -----------------------------------------

                const child =
                    execFile(
                        "exrc",
                        [
                            "symbols",
                            filePath,
                            "--json"
                        ],
                        {
                            windowsHide: true
                        },
                        (
                            error,
                            stdout,
                            stderr
                        ) => {

                            // ---------------------------------
                            // Get the current process entry
                            // ---------------------------------

                            const entry =
                                symbolProcesses.get(
                                    documentKey
                                );


                            // ---------------------------------
                            // Process was cancelled or replaced
                            // ---------------------------------

                            if (
                                !entry ||
                                entry.process !== child ||
                                entry.cancelled
                            ) {
                                return;
                            }


                            // ---------------------------------
                            // Process completed normally
                            // ---------------------------------

                            symbolProcesses.delete(
                                documentKey
                            );


                            // ---------------------------------
                            // Real process error
                            // ---------------------------------

                            if (error) {

                                console.error(
                                    "EXORCISM SYMBOLS ERROR:",
                                    error.message
                                );


                                if (stderr) {

                                    console.error(
                                        "EXORCISM SYMBOLS STDERR:",
                                        stderr
                                    );
                                }


                                resolve([]);

                                return;
                            }


                            // ---------------------------------
                            // Parse JSON
                            // ---------------------------------

                            try {

                                const result =
                                    JSON.parse(
                                        stdout
                                    ) as SymbolResponse;


                                const symbols =
                                    result.symbols ??
                                    [];


                                console.log(
                                    "EXORCISM SYMBOLS:",
                                    symbols.length
                                );


                                resolve(
                                    symbols
                                );

                            } catch (
                                parseError
                            ) {

                                console.error(
                                    "EXORCISM SYMBOLS JSON ERROR:",
                                    parseError
                                );


                                resolve([]);
                            }
                        }
                    );


                // -----------------------------------------
                // Store process
                // -----------------------------------------

                symbolProcesses.set(
                    documentKey,
                    {
                        process: child,
                        cancelled: false
                    }
                );
            }
        );
    }


    // ========================================================
    // Refresh symbols
    //
    // Symbols are currently file-based, so we only refresh
    // after the document has been saved.
    // ========================================================

    function refreshSymbols(
        document: vscode.TextDocument
    ) {

        if (
            document.languageId !==
            LANGUAGE_ID
        ) {
            return;
        }


        if (
            document.isUntitled
        ) {
            return;
        }


        if (
            !document.fileName
                .toLowerCase()
                .endsWith(".exrc")
        ) {
            return;
        }


        const documentKey =
            document.uri.toString();


        // -----------------------------------------------
        // Cancel existing timer
        // -----------------------------------------------

        const existingTimer =
            symbolTimers.get(
                documentKey
            );


        if (existingTimer) {

            clearTimeout(
                existingTimer
            );
        }


        // -----------------------------------------------
        // Debounce symbol extraction
        // -----------------------------------------------

        const timer =
            setTimeout(
                async () => {

                    symbolTimers.delete(
                        documentKey
                    );


                    if (
                        document.isClosed
                    ) {
                        return;
                    }


                    const symbols =
                        await getSymbols(
                            document.uri.fsPath,
                            documentKey
                        );


                    if (
                        document.isClosed
                    ) {
                        return;
                    }


                    symbolCache.set(
                        documentKey,
                        {
                            symbols,
                            documentVersion:
                                document.version
                        }
                    );


                    console.log(
                        "SYMBOL CACHE UPDATED:",
                        symbols.length,
                        "symbols"
                    );

                },
                SYMBOL_DEBOUNCE_MS
            );


        symbolTimers.set(
            documentKey,
            timer
        );
    }


    // ========================================================
    // Initial document analysis
    // ========================================================

    if (
        vscode.window.activeTextEditor
    ) {

        const document =
            vscode.window
                .activeTextEditor
                .document;


        analyzeDocument(
            document
        );


        // Initial symbols are only useful if the file
        // is already saved.

        if (
            !document.isUntitled
        ) {

            refreshSymbols(
                document
            );
        }
    }


    // ========================================================
    // Document changed
    // ========================================================

    const changeSubscription =
        vscode.workspace.onDidChangeTextDocument(
            event => {

                const document =
                    event.document;


                if (
                    document.languageId !==
                    LANGUAGE_ID
                ) {
                    return;
                }


                // -------------------------------------------
                // Diagnostics
                // -------------------------------------------

                analyzeDocument(
                    document
                );


                // -------------------------------------------
                // IMPORTANT:
                //
                // Do NOT run `exrc symbols` here.
                //
                // The document may be changing rapidly.
                //
                // Symbols will be refreshed after save.
                // -------------------------------------------
            }
        );


    // ========================================================
    // Document opened
    // ========================================================

    const openSubscription =
        vscode.workspace.onDidOpenTextDocument(
            document => {

                analyzeDocument(
                    document
                );


                if (
                    !document.isUntitled
                ) {

                    refreshSymbols(
                        document
                    );
                }
            }
        );


    // ========================================================
    // Document saved
    //
    // This is where symbol extraction happens.
    // ========================================================

    const saveSubscription =
        vscode.workspace.onDidSaveTextDocument(
            document => {

                if (
                    document.languageId !==
                    LANGUAGE_ID
                ) {
                    return;
                }


                refreshSymbols(
                    document
                );
            }
        );


    // ========================================================
    // Document closed
    // ========================================================

    const closeSubscription =
        vscode.workspace.onDidCloseTextDocument(
            document => {

                const documentKey =
                    document.uri.toString();


                // -------------------------------------------
                // Diagnostics
                // -------------------------------------------

                diagnosticCollection.delete(
                    document.uri
                );


                const diagnosticTimer =
                    diagnosticTimers.get(
                        documentKey
                    );


                if (diagnosticTimer) {

                    clearTimeout(
                        diagnosticTimer
                    );

                    diagnosticTimers.delete(
                        documentKey
                    );
                }


                cancelDiagnosticProcess(
                    documentKey
                );


                // -------------------------------------------
                // Symbols
                // -------------------------------------------

                const symbolTimer =
                    symbolTimers.get(
                        documentKey
                    );


                if (symbolTimer) {

                    clearTimeout(
                        symbolTimer
                    );

                    symbolTimers.delete(
                        documentKey
                    );
                }


                const existing =
                    symbolProcesses.get(
                        documentKey
                    );

                if (existing) {

                    existing.cancelled = true;

                    try {

                        if (!existing.process.killed) {
                            existing.process.kill();
                        }

                    } catch {
                        // Already exited.
                    }

                    symbolProcesses.delete(
                        documentKey
                    );
                }


                symbolCache.delete(
                    documentKey
                );
            }
        );


    // ========================================================
    // Hello World
    // ========================================================

    const disposable =
        vscode.commands.registerCommand(
            "exorcism.helloWorld",
            () => {

                vscode.window.showInformationMessage(
                    "Hello World from exorcism!"
                );

            }
        );


    // ========================================================
    // Subscriptions
    // ========================================================

    context.subscriptions.push(
        diagnosticCollection,
        changeSubscription,
        openSubscription,
        saveSubscription,
        closeSubscription,
        disposable
    );
}


// ============================================================
// Deactivate
// ============================================================

export function deactivate() {
    // VS Code disposes registered subscriptions.
}