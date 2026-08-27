import * as vscode from "vscode";
import { ChildProcess, execFile } from "child_process";
import {
    ExorcismHoverProvider
} from "./hoverProvider";


const LANGUAGE_ID = "exorcism";
const DIAGNOSTIC_SOURCE = "exorcism";
let exorcismTerminal: vscode.Terminal | undefined;


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


interface ExorcismScope {
    kind: string;
    name?: string;

    startLine: number;
    startColumn: number;

    endLine: number;
    endColumn: number;

    symbols: string[];
    children: ExorcismScope[];
}


interface SymbolResponse {
    symbols: ExorcismSymbol[];
    scopes: ExorcismScope[];
}


// ============================================================
// Cached symbols
// ============================================================

interface SymbolCacheEntry {
    symbols: ExorcismSymbol[];
    scopes: ExorcismScope[];
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


    
    // ---------------------------------------------
    // Cancel stale symbol processes
    // ---------------------------------------------    
    
    function cancelSymbolProcess(
        documentKey: string
    ) {

        const entry =
            symbolProcesses.get(
                documentKey
            );


        if (
            !entry ||
            entry.cancelled
        ) {
            return;
        }


        // Mark as cancelled BEFORE killing.
        //
        // This is important because kill() can cause
        // the callback to execute asynchronously.

        entry.cancelled = true;


        try {

            if (
                !entry.process.killed
            ) {

                entry.process.kill();
            }

        } catch {
            // Process may already have exited.
        }


        symbolProcesses.delete(
            documentKey
        );
    }

    // ---------------------------------------------
    // Schedule diagnostic analysis
    // ---------------------------------------------    
        
    function scheduleDiagnosticAnalysis(
        document: vscode.TextDocument
    ) {

        const documentKey =
            document.uri.toString();


        // ---------------------------------------------
        // Cancel previously scheduled analysis
        // ---------------------------------------------

        const existingTimer =
            diagnosticTimers.get(
                documentKey
            );

        if (existingTimer) {

            clearTimeout(
                existingTimer
            );
        }


        // ---------------------------------------------
        // Schedule new analysis
        // ---------------------------------------------

        const timer =
            setTimeout(
                () => {

                    diagnosticTimers.delete(
                        documentKey
                    );

                    analyzeDocument(
                        document
                    );

                },
                250
            );


        diagnosticTimers.set(
            documentKey,
            timer
        );
    }


    // ========================================================
    // Run / Build Exorcism command
    // ========================================================

    function getExorcismTerminal(): vscode.Terminal {

        if (
            exorcismTerminal &&
            exorcismTerminal.exitStatus === undefined
        ) {

            return exorcismTerminal;
        }


        exorcismTerminal =
            vscode.window.createTerminal(
                "Exorcism"
            );


        return exorcismTerminal;
    }


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
            getExorcismTerminal();


        terminal.show();


        terminal.sendText(
            `exrc ${command} "${document.fileName}"`
        );
    }


    // ========================================================
    // Doctor Exorcism command
    // ========================================================

    async function runExorcismDoctor() {

        const terminal =
            getExorcismTerminal();


        terminal.show();


        terminal.sendText(
            "exrc doctor"
        );
    }


    // ========================================================
    // Run/Build Commands
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

    
    const doctorCommand = 
        vscode.commands.registerCommand(
            "exorcism.doctor", 
            () => 
                runExorcismDoctor()
        );


    context.subscriptions.push(
        runCommand,
        buildCommand,
        doctorCommand
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
        "String",
        "bool",
        "void",
        "print",
        "if",
        "else",
        "alt",
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



    // -----------------------------------------
    // Find symbol in this scope chain
    // -----------------------------------------

    function createDefinitionLocation(
        document: vscode.TextDocument,
        symbol: ExorcismSymbol
    ): vscode.Location {

        const line =
            Math.max(
                0,
                symbol.line - 1
            );


        const column =
            Math.max(
                0,
                symbol.column - 1
            );


        const start =
            new vscode.Position(
                line,
                column
            );


        const end =
            new vscode.Position(
                line,
                column +
                    symbol.name.length
            );


        return new vscode.Location(
            document.uri,
            new vscode.Range(
                start,
                end
            )
        );
    }


    // findParentScope

    function findParentScope(
        target: ExorcismScope,
        root: ExorcismScope
    ): ExorcismScope | undefined {

        for (
            const child of root.children ?? []
        ) {

            if (
                child === target
            ) {
                return root;
            }


            const parent =
                findParentScope(
                    target,
                    child
                );


            if (parent) {
                return parent;
            }
        }


        return undefined;
    }


    // isSymbolInScope

    function isSymbolInScope(
        symbol: ExorcismSymbol,
        scope: ExorcismScope
    ): boolean {

        const line =
            symbol.line;


        const column =
            symbol.column;


        const startLine =
            scope.startLine;


        const startColumn =
            scope.startColumn;


        const endLine =
            scope.endLine;


        const endColumn =
            scope.endColumn;


        // -----------------------------------------
        // Global scope
        // -----------------------------------------

        if (
            scope.kind === "global"
        ) {
            return true;
        }


        // -----------------------------------------
        // Before scope
        // -----------------------------------------

        if (
            line < startLine
        ) {
            return false;
        }


        if (
            line === startLine &&
            column < startColumn
        ) {
            return false;
        }


        // -----------------------------------------
        // After scope
        // -----------------------------------------

        if (
            endLine !== null &&
            endLine !== undefined
        ) {

            if (
                line > endLine
            ) {
                return false;
            }


            if (
                line === endLine &&
                endColumn !== null &&
                endColumn !== undefined &&
                column > endColumn
            ) {
                return false;
            }
        }


        return true;
    }


    // findSymbolInScopeChain

    function findSymbolInScopeChain(
        symbolName: string,
        scope: ExorcismScope,
        root: ExorcismScope,
        allSymbols: ExorcismSymbol[]
    ): ExorcismSymbol | undefined {

        let current:
            ExorcismScope | undefined =
                scope;


        while (current !== undefined) {

            // -----------------------------------------
            // Store the narrowed scope.
            // -----------------------------------------

            const currentScope =
                current;


            // -----------------------------------------
            // Look for symbol in this scope
            // -----------------------------------------

            const symbolNames =
                currentScope.symbols ?? [];


            if (
                symbolNames.includes(
                    symbolName
                )
            ) {

                const symbol =
                    allSymbols.find(
                        candidate =>
                            candidate.name ===
                            symbolName &&
                            isSymbolInScope(
                                candidate,
                                currentScope
                            )
                    );


                if (symbol) {
                    return symbol;
                }
            }


            // -----------------------------------------
            // Move toward parent scope
            // -----------------------------------------

            current =
                findParentScope(
                    currentScope,
                    root
                );
        }


        return undefined;
    }



    // ========================================================
    // Go to Definition
    // ========================================================

    const definitionProvider =
        vscode.languages.registerDefinitionProvider(
            LANGUAGE_ID,

            {

                provideDefinition(
                    document,
                    position,
                    token
                ) {

                    // -----------------------------------------
                    // Cancellation
                    // -----------------------------------------

                    if (
                        token.isCancellationRequested
                    ) {
                        return undefined;
                    }


                    // -----------------------------------------
                    // Get word under cursor
                    // -----------------------------------------

                    const wordRange =
                        document.getWordRangeAtPosition(
                            position
                        );


                    if (!wordRange) {
                        return undefined;
                    }


                    const symbolName =
                        document.getText(
                            wordRange
                        );


                    if (!symbolName) {
                        return undefined;
                    }


                    // -----------------------------------------
                    // Get symbol cache
                    // -----------------------------------------

                    const documentKey =
                        document.uri.toString();


                    const cache =
                        symbolCache.get(
                            documentKey
                        );


                    if (!cache) {
                        return undefined;
                    }


                    // -----------------------------------------
                    // Get root scope
                    // -----------------------------------------

                    const rootScope =
                        cache.scopes.find(
                            scope =>
                                scope.kind === "global"
                        );


                    if (!rootScope) {

                        // Fallback for older symbol data
                        // without scope information.

                        const symbol =
                            cache.symbols.find(
                                candidate =>
                                    candidate.name ===
                                    symbolName
                            );


                        if (!symbol) {
                            return undefined;
                        }


                        return createDefinitionLocation(
                            document,
                            symbol
                        );
                    }


                    // -----------------------------------------
                    // Find innermost scope
                    // -----------------------------------------

                    const currentScope =
                        findInnermostScope(
                            position,
                            rootScope
                        );


                    if (!currentScope) {
                        return undefined;
                    }


                    // -----------------------------------------
                    // Resolve symbol from current scope
                    // and then walk outward.
                    // -----------------------------------------

                    const symbol =
                        findSymbolInScopeChain(
                            symbolName,
                            currentScope,
                            rootScope,
                            cache.symbols
                        );


                    if (!symbol) {
                        return undefined;
                    }


                    // -----------------------------------------
                    // Create VS Code definition
                    // location.
                    // -----------------------------------------

                    return createDefinitionLocation(
                        document,
                        symbol
                    );
                }
            }
        );


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


                    // -----------------------------------------
                    // Root scope
                    // -----------------------------------------

                    if (
                        cache.scopes.length === 0
                    ) {

                        console.log(
                            "COMPLETION: no scopes"
                        );

                        return items;
                    }


                    const root =
                        cache.scopes[0];


                    // -----------------------------------------
                    // Find innermost scope
                    // -----------------------------------------

                    const scope =
                        findInnermostScope(
                            _position,
                            root
                        );


                    // -----------------------------------------
                    // Get visible symbols
                    // -----------------------------------------

                    const visibleSymbols =
                        getVisibleSymbols(
                            _position,
                            scope ?? root,
                            cache.symbols
                        );


                    // -----------------------------------------
                    // Add visible symbols
                    // -----------------------------------------

                    for (
                        const symbol of visibleSymbols
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
                        "visible symbols:",
                        visibleSymbols.length
                    );


                    return items;
                }
            }
    );


    context.subscriptions.push(
        completionProvider,
        definitionProvider
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
    ): Promise<SymbolResponse | undefined> {

        return new Promise(
            resolve => {

                // -----------------------------------------
                // Cancel previous process
                // -----------------------------------------

                cancelSymbolProcess(
                    documentKey
                );


                // -----------------------------------------
                // Start new process
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

                            const entry =
                                symbolProcesses.get(
                                    documentKey
                                );


                            // ---------------------------------
                            // Ignore callbacks from a process
                            // that has already been replaced
                            // or cancelled.
                            // ---------------------------------

                            if (
                                !entry ||
                                entry.process !== child ||
                                entry.cancelled
                            ) {
                                return;
                            }


                            // ---------------------------------
                            // Remove current process
                            // ---------------------------------

                            symbolProcesses.delete(
                                documentKey
                            );


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


                                resolve(
                                    undefined
                                );

                                return;
                            }


                            try {

                                const result =
                                    JSON.parse(
                                        stdout
                                    ) as SymbolResponse;


                                console.log(
                                    "EXORCISM SYMBOLS:",
                                    result.symbols?.length ?? 0
                                );


                                resolve(
                                    result
                                );

                            } catch (
                                parseError
                            ) {

                                console.error(
                                    "EXORCISM SYMBOLS JSON ERROR:",
                                    parseError
                                );


                                resolve(
                                    undefined
                                );
                            }
                        }
                    );


                // -----------------------------------------
                // Register process
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
            document.isUntitled ||
            document.isClosed
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
        // Cancel pending timer
        // -----------------------------------------------

        const existingTimer =
            symbolTimers.get(
                documentKey
            );

        if (existingTimer) {

            clearTimeout(
                existingTimer
            );

            symbolTimers.delete(
                documentKey
            );
        }


        // -----------------------------------------------
        // Cancel running symbol process
        // -----------------------------------------------

        cancelSymbolProcess(
            documentKey
        );


        // -----------------------------------------------
        // Start debounced refresh
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


                    const result =
                        await getSymbols(
                            document.uri.fsPath,
                            documentKey
                        );


                    if (
                        !result ||
                        document.isClosed
                    ) {
                        return;
                    }


                    const symbols =
                        result.symbols ?? [];


                    symbolCache.set(
                        documentKey,
                        {
                            symbols,
                            scopes:
                                result.scopes ?? [],
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


    // --------------------------------------------------------
    // Check whether a position is inside a scope
    // --------------------------------------------------------

    function positionInScope(
        position: vscode.Position,
        scope: ExorcismScope
    ): boolean {

        const start =
            new vscode.Position(
                scope.startLine,
                scope.startColumn
            );


        // Global scope has no finite end.
        if (
            scope.endLine === null ||
            scope.endColumn === null
        ) {

            return (
                position.isAfterOrEqual(
                    start
                )
            );
        }


        const end =
            new vscode.Position(
                scope.endLine,
                scope.endColumn
            );


        return (
            position.isAfterOrEqual(start) &&
            position.isBeforeOrEqual(end)
        );
    }


    // --------------------------------------------------------
    // Find the deepest scope containing the cursor
    // --------------------------------------------------------

    function findInnermostScope(
        position: vscode.Position,
        root: ExorcismScope
    ): ExorcismScope | undefined {

        if (
            !positionInScope(
                position,
                root
            )
        ) {
            return undefined;
        }


        for (
            const child of root.children ?? []
        ) {

            const nested =
                findInnermostScope(
                    position,
                    child
                );


            if (nested) {
                return nested;
            }
        }


        return root;
    }


    // --------------------------------------------------------
    // Get all visible symbols
    // --------------------------------------------------------

    function getVisibleSymbols(
        position: vscode.Position,
        root: ExorcismScope,
        allSymbols: ExorcismSymbol[]
    ): ExorcismSymbol[] {

        const visible =
            new Map<string, ExorcismSymbol>();


        function addScopeSymbols(
            scope: ExorcismScope
        ) {

            for (
                const symbolName of scope.symbols ?? []
            ) {

                const symbol =
                    allSymbols.find(
                        candidate =>
                            candidate.name === symbolName
                    );


                if (symbol) {

                    visible.set(
                        symbol.name,
                        symbol
                    );
                }
            }
        }


        function visit(
            scope: ExorcismScope
        ): boolean {

            if (
                !positionInScope(
                    position,
                    scope
                )
            ) {
                return false;
            }


            // Parent symbols are added first.
            addScopeSymbols(
                scope
            );


            // Then descend into the scope containing
            // the cursor.
            for (
                const child of scope.children ?? []
            ) {

                if (
                    visit(child)
                ) {
                    break;
                }
            }


            return true;
        }


        visit(root);


        return Array.from(
            visible.values()
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
                //
                // Debounced.
                //
                // Do NOT execute analyzeDocument()
                // directly on every keystroke.
                //

                scheduleDiagnosticAnalysis(
                    document
                );

                //
                // Do NOT run `exrc symbols` here.
                //
                // Symbols are refreshed on save/open.
                //
            }
        );


    // ========================================================
    // Document opened
    // ========================================================

    const openSubscription =
        vscode.workspace.onDidOpenTextDocument(
            document => {

                if (
                    document.languageId !==
                    LANGUAGE_ID
                ) {
                    return;
                }


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