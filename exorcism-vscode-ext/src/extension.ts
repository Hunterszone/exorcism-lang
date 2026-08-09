import * as vscode from "vscode";
import { execFile } from "child_process";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	const config = vscode.workspace.getConfiguration("exorcism");
	const exorcismPath = config.get<string>("executablePath", "exorcism");

	// ========================================================
	// Keyword completion
	// ========================================================

	const keywords = [
		"var",
		"int",
		"float",
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

	const completionProvider = vscode.languages.registerCompletionItemProvider(
		"exorcism",
		{
			provideCompletionItems() {
				return keywords.map(
					keyword =>
						new vscode.CompletionItem(
							keyword,
							vscode.CompletionItemKind.Keyword
						)
				);
			}
		}
	);

	context.subscriptions.push(completionProvider);

	// ========================================================
	// Helper - execute Exorcism commands
	// ========================================================

	function runExorcism(
		args: string[]
	): Promise<void> {
		return new Promise((resolve, reject) => {
			execFile(
				exorcismPath,
				args,
				{
					cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
				},
				(error, stdout, stderr) => {
					const output =
						vscode.window.createOutputChannel("Exorcism");

					if (stdout) {
						output.appendLine(stdout);
					}

					if (stderr) {
						output.appendLine(stderr);
					}

					output.show(true);

					if (error) {
						reject(error);
						return;
					}

					resolve();
				}
			);
		});
	}

	// ========================================================
	// Build
	// ========================================================

	const buildCommand = vscode.commands.registerCommand(
		"exorcism.build",
		async () => {
			const editor = vscode.window.activeTextEditor;

			if (!editor) {
				vscode.window.showErrorMessage(
					"No Exorcism file is open."
				);
				return;
			}

			if (editor.document.languageId !== "exorcism") {
				vscode.window.showErrorMessage(
					"The active file is not an Exorcism source file."
				);
				return;
			}

			const sourceFile = editor.document.fileName;

			try {
				await runExorcism([
					"build",
					sourceFile
				]);

				vscode.window.showInformationMessage(
					"Exorcism build succeeded."
				);
			} catch {
				vscode.window.showErrorMessage(
					"Exorcism build failed."
				);
			}
		}
	);

	context.subscriptions.push(buildCommand);

	// ========================================================
	// Run
	// ========================================================

	const runCommand = vscode.commands.registerCommand(
		"exorcism.run",
		() => {
			const editor = vscode.window.activeTextEditor;

			if (!editor) {
				vscode.window.showErrorMessage(
					"No Exorcism file is open."
				);
				return;
			}

			if (editor.document.languageId !== "exorcism") {
				vscode.window.showErrorMessage(
					"The active file is not an Exorcism source file."
				);
				return;
			}

			const sourceFile = editor.document.fileName;
			const sourceDir = vscode.Uri.file(sourceFile).fsPath
				.replace(/[\\/][^\\/]+$/, "");

			const terminal = vscode.window.createTerminal({
				name: "Exorcism",
				cwd: sourceDir
			});

			terminal.show();

			terminal.sendText(
				`"${exorcismPath}" run "${sourceFile}"`
			);
		}
	);

	context.subscriptions.push(runCommand);

	// ========================================================
	// Doctor
	// ========================================================

	const doctorCommand = vscode.commands.registerCommand(
		"exorcism.doctor",
		async () => {
			try {
				await runExorcism(["doctor"]);
			} catch {
				vscode.window.showErrorMessage(
					"Exorcism doctor failed. Is Exorcism installed and available on PATH?"
				);
			}
		}
	);

	context.subscriptions.push(doctorCommand);

	// ========================================================
	// Activation
	// ========================================================

	console.log(
		'Exorcism extension is now active.'
	);
}

export function deactivate() {}