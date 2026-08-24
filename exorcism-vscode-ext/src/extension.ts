import * as vscode from "vscode";
import { execFile } from "child_process";
import {
    ExorcismHoverProvider
} from "./hoverProvider";

const LANGUAGE_ID = "exorcism";
const DIAGNOSTIC_SOURCE = "exorcism";

// Diagnostic interface 
interface ExorcismDiagnostic {
	severity: "error" | "warning" | "info";
	message: string;
	line: number;
	column: number;
	length: number;
	code?: string;
}

// Symbols interfaces
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

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(
	context: vscode.ExtensionContext
) {

	// ========================================================
	// Run Exorcism command
	// ========================================================

	async function runExorcismCommand(command: string) {

		const editor = vscode.window.activeTextEditor;

		if (!editor) {
			return;
		}

		const document = editor.document;

		if (document.languageId !== "exorcism") {
			return;
		}

		if (!document.fileName.toLowerCase().endsWith(".exrc")) {
			return;
		}

		await document.save();

		const terminal = vscode.window.createTerminal(
			"Exorcism"
		);

		terminal.show();

		terminal.sendText(
			`exrc ${command} "${document.fileName}"`
		);
	}

	
	// ========================================================
	// Register commands
	// ========================================================
	
	const runCommand = vscode.commands.registerCommand(
		"exorcism.run",
		() => runExorcismCommand("run")
	);

	const buildCommand = vscode.commands.registerCommand(
		"exorcism.build",
		() => runExorcismCommand("build")
	);


	// ========================================================
	// Push commands to subscriptions
	// ========================================================

	context.subscriptions.push(
		runCommand,
        buildCommand
	);


	// ========================================================
	// Push hover provider to subscriptions
	// ========================================================
	
	context.subscriptions.push(
		vscode.languages.registerHoverProvider(
			{ language: "exorcism" },
			new ExorcismHoverProvider()
		)
	);


	// ========================================================
	// Keyword completion
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
	// Register completion item provider
	// ========================================================
	
	const completionProvider =
		vscode.languages.registerCompletionItemProvider(
			LANGUAGE_ID,

			{
				async provideCompletionItems() {

					const editor =
						vscode.window.activeTextEditor;

					if (!editor) {
						return [];
					}

					const filePath =
						editor.document.fileName;

					const items: vscode.CompletionItem[] = [];

					// ---------------------------------------------
					// Keywords
					// ---------------------------------------------

					for (const keyword of keywords) {

						const item =
							new vscode.CompletionItem(
								keyword,
								vscode.CompletionItemKind.Keyword
							);

						item.detail = "Exorcism keyword";

						items.push(item);
					}

					// ---------------------------------------------
					// Symbols
					// ---------------------------------------------

					const symbols =
						await getSymbols(filePath);
					
						
					console.log(
						"COMPLETION SYMBOLS:",
						symbols
					);	


					for (const symbol of symbols) {

						let kind =
							vscode.CompletionItemKind.Variable;

						if (symbol.kind === "function") {
							kind =
								vscode.CompletionItemKind.Function;
						}

						const item =
							new vscode.CompletionItem(
								symbol.name,
								kind
							);

						item.detail =
							symbol.kind === "function"
								? symbol.returnType ?? symbol.type
								: symbol.type;

						items.push(item);
					}

					return items;
				}
			}
		);


	// ========================================================
	// Diagnostics
	// ========================================================

	const diagnosticCollection =
		vscode.languages.createDiagnosticCollection(
			DIAGNOSTIC_SOURCE
		);


	// ========================================================
	// Run Exorcism analyzer
	// ========================================================

	function analyzeDocument(
		document: vscode.TextDocument
	) {

		if (
			document.languageId !== LANGUAGE_ID
		) {
			return;
		}


		if (
			document.isUntitled
		) {
			return;
		}


		const filePath =
			document.uri.fsPath;


		const child = execFile(
			"exorcism",
			[
				"analyze", 
				"--stdin", 
				"--json"
			],
			{ 
				windowsHide: true 
			},
			(error, stdout, stderr) => {
				if (!stdout && error) {
					console.error("Exorcism analyzer failed:", stderr || error.message);
					return;
				}

				try {
					const diagnostics: ExorcismDiagnostic[] = JSON.parse(stdout || "[]");
					const vscodeDiagnostics: vscode.Diagnostic[] = [];
					
					for (const diagnostic of diagnostics) {
						const line = Math.max(0, diagnostic.line - 1);
						const column = Math.max(0, diagnostic.column - 1);
						const length = Math.max(1, diagnostic.length);
						const start = new vscode.Position(line, column);
						const end = new vscode.Position(line, column + length);
						const range = new vscode.Range(start, end);
						let severity = vscode.DiagnosticSeverity.Error;
						
						if (diagnostic.severity === "warning") {
							severity = vscode.DiagnosticSeverity.Warning;
						} else if (diagnostic.severity === "info") {
							severity = vscode.DiagnosticSeverity.Information;
						}
						
						const vscodeDiagnostic = new vscode.Diagnostic(
							range,
							diagnostic.message,
							severity
						);
						
						vscodeDiagnostic.source = DIAGNOSTIC_SOURCE;
						
						if (diagnostic.code) {
							vscodeDiagnostic.code = diagnostic.code;
						}
						
						vscodeDiagnostics.push(vscodeDiagnostic);
					}
					
					diagnosticCollection.set(document.uri, vscodeDiagnostics);
				} catch (parseError) {
					console.error("Failed to parse Exorcism diagnostics:", parseError);
				}
			}
		);

		if (child.stdin) { 
			
			child.stdin.write(
				document.getText()
			); 
			
			child.stdin.end(); 
		}

	}


	// ========================================================
	// Validate currently open document
	// ========================================================

	if (
		vscode.window.activeTextEditor
	) {

		analyzeDocument(
			vscode.window.activeTextEditor.document
		);

	}


	// ========================================================
	// Get the symbols output from a .exrc file
	// ========================================================

	function getSymbols(
		filePath: string
	): Promise<ExorcismSymbol[]> {

		return new Promise((resolve) => {

			execFile(
				"exrc",
				[
					"symbols",
					filePath,
					"--json"
				],
				(error, stdout, stderr) => {

					console.log(
						"EXORCISM SYMBOLS FILE:",
						filePath
					);

					console.log(
						"EXORCISM SYMBOLS ERROR:",
						error
					);

					console.log(
						"EXORCISM SYMBOLS STDOUT:",
						stdout
					);

					console.log(
						"EXORCISM SYMBOLS STDERR:",
						stderr
					);

					if (error) {
						resolve([]);
						return;
					}

					try {

						const result =
							JSON.parse(stdout) as SymbolResponse;

						console.log(
							"EXORCISM PARSED SYMBOLS:",
							result.symbols
						);

						resolve(
							result.symbols ?? []
						);

					} catch (parseError) {

						console.error(
							"EXORCISM JSON PARSE ERROR:",
							parseError
						);

						resolve([]);

					}
				}
			);
		});
	}


	// ========================================================
	// Validate when document changes
	// ========================================================

	const changeSubscription =
		vscode.workspace.onDidChangeTextDocument(
			event => {

				analyzeDocument(
					event.document
				);

			}
		);


	// ========================================================
	// Validate when document is opened
	// ========================================================

	const openSubscription =
		vscode.workspace.onDidOpenTextDocument(
			document => {

				analyzeDocument(
					document
				);

			}
		);


	// ========================================================
	// Clear diagnostics when document closes
	// ========================================================

	const closeSubscription =
		vscode.workspace.onDidCloseTextDocument(
			document => {

				diagnosticCollection.delete(
					document.uri
				);

			}
		);


	// ========================================================
	// Hello World command
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
		completionProvider,
		diagnosticCollection,
		changeSubscription,
		openSubscription,
		closeSubscription,
		disposable
	);


	console.log(
		'Exorcism extension is now active.'
	);

}


export function deactivate() { }