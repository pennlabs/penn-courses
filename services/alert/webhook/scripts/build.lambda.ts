import { exec } from "child_process"
import fs from "fs/promises"
import path from "path"

import * as esbuild from "esbuild"

const main = async () => {
	const rootdir = path.resolve(import.meta.dirname, "..")
	const outdir = path.resolve(rootdir, "dist", "build.lambda")
	const packageFile = await fs.readFile(
		path.resolve(rootdir, "package.json"),
		"utf-8"
	)
	const packageJSON = JSON.parse(packageFile)
	try {
		await fs.rm(outdir, {
			recursive: true,
		})
	} catch (error) {}
	await fs.mkdir(outdir, { recursive: true })
	await Promise.all([
		esbuild.build({
			absWorkingDir: rootdir,
			tsconfig: path.resolve(rootdir, "tsconfig.build.json"),
			entryPoints: [path.resolve(rootdir, "src", "main.ts")],
			outfile: path.resolve(outdir, "main.js"),
			minify: true,
			sourcemap: true,
			bundle: true,
			treeShaking: true,
			platform: "node",
			format: "cjs",
			logLevel: "info",
			resolveExtensions: [".ts", ".d.ts"],
			external: [
				...Object.keys(packageJSON.dependencies),
				...Object.keys(packageJSON.devDependencies),
			],
		}),
		fs.writeFile(
			path.resolve(outdir, "package.json"),
			JSON.stringify(
				{
					dependencies: packageJSON.dependencies,
				},
				null,
				4
			)
		),
		fs.copyFile(
			path.resolve(rootdir, "yarn.lock"),
			path.resolve(outdir, "yarn.lock")
		),
	])
	await new Promise((resolve, reject) => {
		const yarnProcess = exec("yarn install", {
			cwd: outdir,
		})
		yarnProcess.stdout?.pipe(process.stdout)
		yarnProcess.stderr?.pipe(process.stderr)
		yarnProcess.on("exit", (code) => {
			if (code === 0) {
				resolve(null)
			} else {
				reject(code)
			}
		})
	})
}

main()
