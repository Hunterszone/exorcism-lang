const esbuild = require("esbuild");

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

/**
 * @type {import('esbuild').Plugin}
 */
const esbuildProblemMatcherPlugin = {
	name: 'esbuild-problem-matcher',

	setup(build) {
		build.onStart(() => {
			console.log(watch ? '[watch] build started' : '[build] started');
		});
		build.onEnd((result) => {
			result.errors.forEach(({ text, location }) => {
				console.error(`✘ [ERROR] ${text}`);
				console.error(`    ${location.file}:${location.line}:${location.column}:`);
			});
			console.log(watch ? '[watch] build finished' : '[build] finished');
		});
	},
};

async function main() {
	// Common esbuild config
	const config = {
		entryPoints: ['src/extension.ts'],
		bundle: true,
		format: 'cjs',
		minify: production,
		sourcemap: !production,
		sourcesContent: false,
		platform: 'node',
		outfile: 'dist/extension.js',
		external: ['vscode'],
		logLevel: 'silent',
		plugins: [esbuildProblemMatcherPlugin],
	};

	if (watch) {
		// Context is only used in Development mode
		const ctx = await esbuild.context(config);
		await ctx.watch();
	} else {
		// Used in Production mode
		await esbuild.build(config);
	}
}

main().catch(e => {
	console.error(e);
	process.exit(1);
});
