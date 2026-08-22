import * as vscode from "vscode";
import builtinDocs from "./builtinDocs.json";

export class ExorcismHoverProvider
    implements vscode.HoverProvider {

    provideHover(
        document: vscode.TextDocument,
        position: vscode.Position
    ): vscode.ProviderResult<vscode.Hover> {

        const range = document.getWordRangeAtPosition(
            position,
            /[A-Za-z_][A-Za-z0-9_]*/
        );

        if (!range) {
            return undefined;
        }


        const word = document.getText(range);


        // -----------------------------
        // Builtin functions
        // -----------------------------

        const builtinFunction =
            builtinDocs.functions[word as keyof typeof builtinDocs.functions];


        if (builtinFunction) {

            const markdown = new vscode.MarkdownString();

            markdown.appendCodeblock(
                builtinFunction.signature,
                "exorcism"
            );

            markdown.appendMarkdown(
                `\n${builtinFunction.description}`
            );


            return new vscode.Hover(
                markdown,
                range
            );
        }


        // -----------------------------
        // Builtin types
        // -----------------------------

        const builtinType =
            builtinDocs.types[word as keyof typeof builtinDocs.types];


        if (builtinType) {

            const markdown = new vscode.MarkdownString();

            markdown.appendCodeblock(
                word,
                "exorcism"
            );

            markdown.appendMarkdown(
                `\n${builtinType.description}`
            );


            return new vscode.Hover(
                markdown,
                range
            );
        }

        
        // -----------------------------
        // Builtin keywords
        // -----------------------------

        const keyword =
            builtinDocs.keywords[
                word as keyof typeof builtinDocs.keywords
            ];


        if (keyword) {

            const markdown = new vscode.MarkdownString();

            markdown.appendCodeblock(
                word,
                "exorcism"
            );

            markdown.appendMarkdown(
                `\n${keyword.description}`
            );

            return new vscode.Hover(
                markdown,
                range
            );
        }


        return undefined;
    }
}