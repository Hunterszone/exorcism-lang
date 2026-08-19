import * as vscode from "vscode";
import { execFile } from "child_process";


const LANGUAGE_ID = "exorcism";
const DIAGNOSTIC_SOURCE = "exorcism";


interface ExorcismDiagnostic {
	severity: "error" | "warning" | "info";
	message: string;
	line: number;
	column: number;
	length: number;
	code?: string;
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(
	context: vscode.ExtensionContext
) {

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
		"while",
		"for",
		"return",
		"break",
		"continue",
		"function",
		"struct"
	];


	const completionProvider =
		vscode.languages.registerCompletionItemProvider(
			LANGUAGE_ID,

			{

				provideCompletionItems() {

					return keywords.map(
						keyword => {

							return new vscode.CompletionItem(
								keyword,
								vscode.CompletionItemKind.Keyword
							);

						}
					);

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